import logging
from typing import Any
from dataclasses import dataclass, field
from collections.abc import MutableMapping

from .manager import Manager

logger = logging.getLogger(__name__)
# T = TypeVar("T", bound=Awaitable[Callable])

@dataclass
class CachedManager(Manager):
    """Version of a `batchedllm.Manager` with caching
    Note:
    without provider all requests are stored in memory
    """
    provider: MutableMapping[Any, Any] = field(default_factory=dict)
    _logger = logger

    def __init__(self, *args, **kwargs):    
        raise NotImplementedError
        
    
    # async def process(self):
    #     pbar = tqdm(total=len(self._tasks)) if self.progress_bar else None

    #     semaphore = asyncio.Semaphore(self.concurency)

    #     async def semaphore_wrapper(func):
    #         async with semaphore:
    #             try:
    #                 res = await func
    #             except Exception as e:
    #                 if self.error_behavior == "raise":
    #                     raise e
    #                 elif self.error_behavior == "ignore":
    #                     logger.exception(e)
    #                     res = None
    #                 else:
    #                     res = e

    #             if pbar:
    #                 pbar.update()
    #             return res

    #     tasks_to_gather = []
    #     for task in self._tasks:
    #         logger.debug("calling %s's method %s with *args: `%s` and **kwargs: `%s`", self.client, task["func"], task["args"], task["kwargs"])
            
    #         key = dumps({"path": self._latest_path, "args": task["args"], "kwargs": task["kwargs"]})
    #         if key in self.provider:
    #             tasks_to_gather.append(self.provider[key])
    #         else:
    #             value = await to_call(*args, **kwargs)

    #             self.provider[key] = value
                
    #             self._latest_path = list()
            
    #         tasks_to_gather.append(semaphore_wrapper(task["func"](*task["args"], **task["kwargs"])))

    #     return await asyncio.gather(*tasks_to_gather)
    
