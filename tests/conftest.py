import pytest
import asyncio

from dataclasses import dataclass, field


@dataclass
class MockAI:
    history: list = field(default_factory=list)
    active: int = 0
    max_active: int = 0

    chat: "Chat" = field(init=False)

    def __post_init__(self):
        self.chat = Chat(self)


@dataclass
class Chat:
    parent: MockAI

    completions: "Completions" = field(init=False)

    def __post_init__(self):
        self.completions = Completions(self)


@dataclass
class Completions:
    parent: Chat

    async def create(self, value, *, delay: int = 0, fail: bool = False):
        self.parent.parent.active += 1
        self.parent.parent.max_active = max(
            self.parent.parent.max_active, self.parent.parent.active
        )
        self.parent.parent.history.append(("chat.completions.create", value))

        try:
            await asyncio.sleep(delay)
            if fail:
                raise ValueError(value)
            return value
        finally:
            self.parent.parent.active -= 1

    def sync_create(self, value):
        self.parent.parent.history.append(("chat.completions.sync_create", value))
        return value


@pytest.fixture()
def mockAI():
    return MockAI()
