from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any, Self

from .infinitely_callable import InfinitelyCallable, Call


@dataclass
class Batch(InfinitelyCallable["Batch"]):
    """A class to store future calls"""

    # TODO: even with future doesn't work without quotes
    # TODO(py3.14): remove quotess
    _queue: list[Call] = field(default_factory=list)

    def callback(self, call):
        self._queue.append(call)
        return self

    def __add__(self, other: Batch | None):
        if isinstance(other, Batch):
            return Batch(self._queue + other._queue)
        elif other is None:
            return self
        else:
            raise TypeError("can't combine Batch with non-Batch")

    def __iter__(self):
        return iter(self._queue)
