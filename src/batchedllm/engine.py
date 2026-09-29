import asyncio
import inspect
from decimal import Decimal
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Awaitable, Callable
from contextlib import AbstractContextManager, AbstractAsyncContextManager
from dataclasses import dataclass, field
from typing import Annotated, Any
from datetime import timedelta

from annotated_types import Ge, Gt


@dataclass
class BudgetLimit:
    total: Decimal
    per_token_type: dict[str, tuple[int, Decimal]]


@dataclass
class AbstractEngine(ABC):
    concurrency_limit: Annotated[int, Ge(1)] | None = None
    rate_limit: tuple[int, timedelta] | None = None
    budget_limit: BudgetLimit | None = None


# @dataclass(slots=True)
# class AbstractSyncEngine(AbstractEngine, AbstractContextManager):
#     """Base class for synchronous execution engines."""


@dataclass(slots=True)
class AbstractAsyncEngine(AbstractEngine, AbstractAsyncContextManager):
    """Base class for asynchronous execution engines."""


@dataclass(slots=True)
class AsyncEngine(AbstractAsyncEngine):
    # TODO: implement
    ...


# @dataclass
# class MultiprocessingEngine(AbstractEngine):
#     """multiprocessing-based enging for Manager"""


# @dataclass
# class MultithreadingEngine(AbstractEngine):
#     """multithreading-based enging for Manager"""
