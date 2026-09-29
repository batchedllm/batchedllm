from abc import ABC, abstractmethod
from collections.abc import Sized
from typing import Protocol
from dataclasses import dataclass
from types import TracebackType
from typing import Any, Self


class Progress(Protocol):
    def __call__(self, iterable: Sized) -> Self: ...

    def update(self, response: Any) -> None: ...


@dataclass
class SimpleProgress(Progress):
    step: int = 0
    total: int = -1

    def update(self, response: Any) -> None:
        self.step += 1
        print(f"{self.step}/{self.total}")

    def __call__(self, iterable: Sized):
        self.total = len(iterable)

        print(f"{self.step}/{self.total}")

        return self
