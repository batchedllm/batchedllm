"""like itertools.batched but for calling LLM"""

from .manager import Manager
from .cached_manager import CachedManager
from .batch import Batch
from .util import *

__version__ = "0.3.0"
