"""like itertools.batched but for calling LLM"""

from .manager import Manager as Manager
from .cached_manager import CachedManager as CachedManager
from .batch import Batch as Batch

__version__ = "0.3.0"
