from collections.abc import Container
from typing import Any, Protocol
from dataclasses import dataclass, field

from .infinitely_callable import Call


class Cache[T](Container, Protocol):
    def __getitem__(self, key: Call) -> T: ...

    def __setitem__(self, key: Call, value: T, /) -> None: ...


@dataclass
class SimpleCache[T](Cache[T]):
    cache: dict[tuple[Any, ...], T] = field(default_factory=dict)

    @staticmethod
    def get_key(call: Call, kwd_mark=(object(),)) -> tuple[Any, ...]:
        key = call.path
        for arg in call.args:
            key += arg
        if call.kwargs:
            key += kwd_mark
            for item in call.kwargs.items():
                key += item
        return key

    def __getitem__(self, key: Call) -> T:
        return self.cache[self.get_key(key)]

    def __setitem__(self, key: Call, value: T):
        self.cache[self.get_key(key)] = value

    def __contains__(self, item: Call) -> bool:
        return item in self.cache
