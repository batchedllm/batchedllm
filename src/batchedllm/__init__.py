"""like itertools.batched but for calling LLM"""

from .manager import Manager
from .cached_manager import CachedManager

__version__ = "0.3.0"

__all__ = ["Manager", "CachedManager"]
