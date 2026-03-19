import asyncio
import logging
from typing import Any, TypeVar, Generic, Literal, Callable, Awaitable
from dataclasses import dataclass, field

from tqdm.asyncio import tqdm

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=Awaitable[Callable])

@dataclass
class Manager(Generic[T]):
    """Basic implementation of an async batch manager"""
    client: T
    concurency: int = 1
    dont_raise_erors: bool = False
    error_behavior: Literal["raise", "ignore", "forward"] = "raise" 
    progress_bar: bool = False
    _latest_path: list[str] = field(default_factory = list)
    _tasks: list[dict[str, Any]] = field(default_factory = list)
    _logger = logger

    def __getattr__(self, name):
        self._latest_path.append(name)
        return self

    def __call__(self, *args, **kwargs):
        to_call = self.client
        for path in self._latest_path:
            to_call = getattr(to_call, path)

        self._tasks.append({
            "path": self._latest_path.copy(),
            "func": to_call,
            "args": args,
            "kwargs": kwargs,
        })
        self._latest_path = list()
        return self
    
    async def process(self):
        pbar = tqdm(total=len(self._tasks)) if self.progress_bar else None

        semaphore = asyncio.Semaphore(self.concurency)

        async def semaphore_wrapper(func):
            async with semaphore:
                try:
                    res = await func
                except Exception as e:
                    if self.error_behavior == "raise":
                        raise e
                    elif self.error_behavior == "ignore":
                        self._logger.exception(e)
                        res = None
                    else:
                        res = e

                if pbar:
                    pbar.update()
                return res

        tasks_to_gather = []
        for task in self._tasks:
            self._logger.debug("calling %s's method %s with *args: `%s` and **kwargs: `%s`", self.client, task["func"], task["args"], task["kwargs"])
            tasks_to_gather.append(semaphore_wrapper(task["func"](*task["args"], **task["kwargs"])))

        return await asyncio.gather(*tasks_to_gather)
    
    def sync_process(self):
        """best effort to run async from sync, async version should be prefered"""
        try:
            asyncio.get_running_loop().run_until_complete(self.process())
        except RuntimeError: # no loop running
            asyncio.run(self.process())
