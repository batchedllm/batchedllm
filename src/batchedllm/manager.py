import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Literal, cast, get_args

from tqdm.asyncio import tqdm

logger = logging.getLogger(__name__)

type QueuedCallable = Callable[..., Awaitable[Any] | Any]
type ErrorBehavior = Literal["raise", "ignore", "forward"]


@dataclass(slots=True)
class QueuedCall:
    path: tuple[str, ...]
    func: QueuedCallable
    args: tuple[Any, ...] | None
    kwargs: dict[str, Any] | None

    def as_cache_key(self) -> str:
        # TODO: maybe sort args/kwargs
        return f"{'.'.join(self.path)}.{self.func}(*({self.args or tuple()}), **{{{self.kwargs or dict()}}})"


@dataclass(slots=True, frozen=True)
class _PathBuilder:
    """immutable path builder to avoid path leakage and allow for path reuse"""

    manager: "Manager"
    path: tuple[str, ...]

    def __getattr__(self, name: str) -> "_PathBuilder":
        return _PathBuilder(self.manager, (*self.path, name))

    def __call__(self, *args: Any | None, **kwargs: Any | None) -> "Manager":
        target = self.manager.client
        for part in self.path:
            target = getattr(target, part)

        # if not isinstance(target, QueuedCallable):
        if not callable(target):
            raise TypeError(f"Resolved target `{'.'.join(self.path)}` is not callable")

        self.manager._queue.append(
            QueuedCall(
                path=self.path,
                func=cast(QueuedCallable, target),
                args=args or None,
                kwargs=dict(kwargs) or None,
            )
        )
        return self.manager


@dataclass(slots=True)
class Manager:
    """basic implementation of an async batch manager"""

    client: object
    concurrency: int = 1
    error_behavior: ErrorBehavior = "raise"
    progress_bar: bool = False

    _queue: list[QueuedCall] = field(default_factory=list, init=False, repr=False)

    _logger: ClassVar[logging.Logger] = logger

    def __post_init__(self) -> None:
        #
        if not (isinstance(self.concurrency, int) and self.concurrency >= 1):
            raise ValueError("concurrency must be a positive integer")

        error_behavior_acceptable_values = get_args(ErrorBehavior.__value__)
        if self.error_behavior not in error_behavior_acceptable_values:
            raise ValueError(
                f"error_behavior must be one of {', '.join(map('`{}`'.format, error_behavior_acceptable_values))}"
            )

    def __getattr__(self, name: str) -> _PathBuilder:
        return _PathBuilder(self, (name,))

    async def process(self) -> list[Any]:
        queue, self._queue = self._queue, []

        if not queue:
            return []

        pbar = tqdm(total=len(queue)) if self.progress_bar else None
        semaphore = asyncio.Semaphore(self.concurrency)

        async def semaphore_wrapper(task: QueuedCall) -> Any:
            self._logger.debug(
                "executing `%s.%s(*%s, **%s)",
                self.client,
                ".".join(task.path),
                task.args or tuple(),
                task.kwargs or dict(),
            )

            try:
                async with semaphore:
                    try:
                        result = task.func(
                            *(task.args or tuple()), **(task.kwargs or dict())
                        )
                        if inspect.isawaitable(result):
                            return await result
                        return result
                    except Exception as exc:
                        self._logger.debug(
                            "executing `%s.%s(*%s, **%s) failed",
                            self.client,
                            ".".join(task.path),
                            task.args or tuple(),
                            task.kwargs or dict(),
                            exc_info=exc,
                        )
                        if self.error_behavior == "raise":
                            raise exc
                        elif self.error_behavior == "ignore":
                            return None
                        elif self.error_behavior == "forward":
                            return exc
            finally:
                if pbar:
                    pbar.update()

        try:
            return await asyncio.gather(*map(semaphore_wrapper, queue))
        finally:
            if pbar:
                pbar.close()

    def sync_process(self) -> list[Any | Exception]:
        """best effort to run async from sync, async version should be prefered"""
        try:
            return asyncio.get_running_loop().run_until_complete(self.process())
        except RuntimeError:  # no loop running
            return asyncio.run(self.process())
