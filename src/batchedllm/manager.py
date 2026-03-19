import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Self, cast

from tqdm.asyncio import tqdm

logger = logging.getLogger(__name__)

type QueuedCallable = Callable[..., Awaitable[Any] | Any]


@dataclass(slots=True)
class QueuedCall:
    path: tuple[str, ...]
    func: QueuedCallable
    args: tuple[Any, ...]
    kwargs: dict[str, Any] | None


@dataclass
class Manager:
    """Basic implementation of an async batch manager"""
    client: object
    concurency: int = 1
    dont_raise_erors: bool = False
    error_behavior: Literal["raise", "ignore", "forward"] = "raise" 
    progress_bar: bool = False
    _latest_path: list[str] = field(default_factory=list)
    _tasks: list[QueuedCall] = field(default_factory=list)
    _logger = logger

    def __getattr__(self, name: str) -> Self:
        self._latest_path.append(name)
        return self

    def __call__(self, *args: Any, **kwargs: Any) -> Self:
        to_call: object = self.client
        for path in self._latest_path:
            to_call = getattr(to_call, path)

        if not callable(to_call):
            msg = f"Resolved target {'.'.join(self._latest_path)!r} is not callable"
            raise TypeError(msg)

        self._tasks.append(
            QueuedCall(
                path=tuple(self._latest_path),
                func=cast(QueuedCallable, to_call),
                args=args,
                kwargs=kwargs or None,
            )
        )
        self._latest_path = []
        return self

    async def process(self) -> list[Any]:
        pbar = tqdm(total=len(self._tasks)) if self.progress_bar else None

        semaphore = asyncio.Semaphore(self.concurency)

        async def semaphore_wrapper(task: QueuedCall) -> Any:
            async with semaphore:
                try:
                    result = task.func(*task.args, **(task.kwargs if task.kwargs is not None else {}))
                    if inspect.isawaitable(result):
                        res = await result
                    else:
                        res = result
                except Exception as e:
                    if self.error_behavior == "raise":
                        raise e
                    if self.error_behavior == "ignore":
                        self._logger.exception(e)
                        res = None
                    else:
                        res = e

                if pbar:
                    pbar.update()
                return res

        tasks_to_gather = []
        for task in self._tasks:
            self._logger.debug(
                "calling %s's method %s with *args: `%s` and **kwargs: `%s`",
                self.client,
                task.func,
                task.args,
                task.kwargs,
            )
            tasks_to_gather.append(semaphore_wrapper(task))

        return await asyncio.gather(*tasks_to_gather)

    def sync_process(self) -> list[Any]:
        """best effort to run async from sync, async version should be prefered"""
        try:
            return asyncio.get_running_loop().run_until_complete(self.process())
        except RuntimeError: # no loop running
            return asyncio.run(self.process())
