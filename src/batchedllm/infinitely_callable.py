from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, NamedTuple
from collections.abc import Callable


class Call(NamedTuple):
    path: tuple[str, ...]
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


@dataclass(slots=True, frozen=True)
class PathBuilder[T]:
    """Immutable path builder to avoid path leakage and allow for path reuse"""

    _callback: Callable[[Call], T]
    _path: tuple[str, ...]

    def __getattr__(self, name: str):
        return PathBuilder(self._callback, (*self._path, name))

    def __call__(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> T:
        return self._callback(
            Call(
                path=self._path,
                args=args,
                kwargs=dict(kwargs),
            )
        )


class InfinitelyCallable[T](ABC):
    """Abstract generic to implement inifinite callable on other classes"""

    @abstractmethod
    def callback(self, call: Call) -> T:
        """default implementation should follow
        ```
        def callback(call):
            ...
        return callback
        ```
        """
        raise NotImplementedError

    def __getattr__(self, name: str) -> PathBuilder[T]:
        return PathBuilder(self.callback, (name,))
