import asyncio
import logging
from inspect import isawaitable
from dataclasses import dataclass, field
from typing import Any, ClassVar, Literal, cast
from asyncio import Task, create_task, AbstractEventLoop, get_event_loop, Future, gather
from collections.abc import Callable
from warnings import warn

from .cache import Cache, SimpleCache
from .engine import (
    AbstractAsyncEngine,
    AsyncEngine,
)
from .progress import Progress, SimpleProgress
from .infinitely_callable import InfinitelyCallable, Call
from .batch import Batch

logger = logging.getLogger(__name__)

type ErrorBehavior = Literal["raise", "ignore", "forward"]


@dataclass(slots=True)
class Promise[T]:
    fn: Callable
    path: tuple[str, ...]
    args: tuple[Any, ...]
    kwars: dict[str, Any]
    _result: Any | T = None
    _done: bool = False
    
    def result(self) -> T:
        if not self._done:
            raise ValueError("Promise is not fulfilled")
        else:
            return self._result
    
    def set_result(self, value: T):
        self._done, self._result = True, value

    def done(self) -> bool:
        return self._done 

    
@dataclass
class AsyncManager(InfinitelyCallable):
    """implementation of an async client manager"""

    client: object
    cache: Cache = field(default_factory=SimpleCache)
    engine: AbstractAsyncEngine = field(default_factory=AsyncEngine)
    progress: Progress = field(default_factory=SimpleProgress)

    error_behavior: ErrorBehavior = "raise"

    _logger: ClassVar[logging.Logger] = logger

    _tasks: list[Promise] = field(default_factory=list)

    def callback(self, call: Call):
        target = self.client
        for path in call.path:
            if not hasattr(target, path):
                raise ValueError(f"{target} doesn't have attribute {path}")
            target = getattr(target, path)

        if not callable(target):
            raise TypeError(f"{target} isn't callable")

        promise = Promise(target, call.path, call.args, call.kwargs)
        self._tasks.append(promise)
        return promise

    async def __call_(self, batch: Batch | None = None) -> list[Any]:
        if batch:
            for call in batch:
                self.callback(call)

        self._tasks, tasks = [], self._tasks

        pbar = self.progress(self._tasks)

        async def engine_wrapper(prom):
            self._logger.debug(
                "executing `%s.%s(*%s, **%s)",
                self.client,
                ".".join(prom.path),
                prom.args,
                prom.kwargs,
            )
            async with self.engine as engine:
                try:
                    result = prom.fn(*prom.args, **prom.kwargs)
                    if isawaitable(result):
                        result = await result
                    else:
                        warn
                except Exception as exc:
                    result = exc

                    self._logger.exception(
                        "exception when executing `%s.%s(*%s, **%s)",
                        self.client,
                        ".".join(prom.path),
                        prom.args,
                        prom.kwargs,
                        exc_info=exc,
                    )
                    if self.error_behavior == "raise":
                        raise exc
                    elif self.error_behavior == "ignore":
                        result = None
                    elif self.error_behavior == "forward":
                        result = exc

                engine.update(result)
                pbar.update(result)
                
                prom.set_result(result)
                return result

        return await gather(*map(engine_wrapper, tasks))
