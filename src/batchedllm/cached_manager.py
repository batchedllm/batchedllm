import asyncio
import inspect
import logging
from collections.abc import MutableMapping
from dataclasses import dataclass, field
from typing import Any, ClassVar

from tqdm.asyncio import tqdm

from .manager import Manager, QueuedCall

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CachedManager(Manager):
    """version of Manager with a minimal cache for succesfull calls"""

    # TODO: assumes same client
    cacher: MutableMapping[Any, Any] = field(default_factory=dict)

    _logger: ClassVar[logging.Logger] = logger

    async def process(self) -> list[Any | Exception]:
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

        async def cached_semaphore_wrapper(task: QueuedCall) -> Any:
            key = task.as_cache_key()

            if key not in self.cacher:
                self.cacher[key] = semaphore_wrapper(task)
            else:
                if pbar:
                    pbar.update()

            return self.cacher[key]

        try:
            return await asyncio.gather(*map(cached_semaphore_wrapper, queue))
        finally:
            if pbar:
                pbar.close()
