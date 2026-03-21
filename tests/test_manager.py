import asyncio
import logging
from typing import Any, cast
from dataclasses import dataclass, field

import pytest

from batchedllm import Manager


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


def test_generally_works():
    manager = Manager(MockAI())

    partial = manager.chat.completions

    partial.create("hello")
    returned = partial.create("world", delay=1).chat.completions.create(value="!")

    assert returned is manager
    assert len(manager._queue) == 3
    assert manager._queue[0].path == ("chat", "completions", "create")
    assert manager._queue[0].args == ("hello",)
    assert manager._queue[0].kwargs is None
    assert manager._queue[1].path == ("chat", "completions", "create")
    assert manager._queue[1].args == ("world",)
    assert manager._queue[1].kwargs == {"delay": 1}
    assert manager._queue[2].path == ("chat", "completions", "create")
    assert manager._queue[2].args is None
    assert manager._queue[2].kwargs == {"value": "!"}


def test_paths_dont_cross():
    manager = Manager(MockAI())

    manager.chat
    manager.chat.completions
    manager.chat.completions.create
    manager.this.can.be.any.path_we.dont.care.until.you.call.process
    manager.chat.completions.create("only one")

    assert len(manager._queue) == 1
    assert manager._queue[0].path == ("chat", "completions", "create")


def test_paths_dont_cross_even_when_error():
    manager = Manager(MockAI())

    with pytest.raises(TypeError, match="is not callable"):
        manager.history()

    manager.chat.completions.create("only one even if previous errors")

    assert len(manager._queue) == 1
    assert manager._queue[0].path == ("chat", "completions", "create")


def test_sync_works():
    manager = Manager(MockAI())
    manager.chat.completions.sync_create("sync")

    result = manager.sync_process()

    assert result == ["sync"]
    assert len(manager._queue) == 0


@pytest.mark.asyncio
async def test_async_works():
    client = MockAI()
    manager = Manager(client)

    manager.chat.completions.create("first")
    manager.chat.completions.sync_create("second")

    result = await manager.process()

    assert result == [
        "first",
        "second",
    ]
    assert client.history == [
        ("chat.completions.create", "first"),
        ("chat.completions.sync_create", "second"),
    ]
    assert len(manager._queue) == 0


@pytest.mark.asyncio
async def test_error_behavior_is_raise():
    manager = Manager(MockAI(), error_behavior="raise")

    manager.chat.completions.create("fail", fail=True)

    with pytest.raises(ValueError, match="fail"):
        await manager.process()


@pytest.mark.asyncio
async def test_error_behavior_is_ignore(caplog):
    manager = Manager(MockAI(), error_behavior="ignore")
    manager.chat.completions.create("ok")
    manager.chat.completions.create("fail", fail=True)

    with caplog.at_level(logging.DEBUG):
        result = await manager.process()

    assert result == ["ok", None]
    assert any(record.exc_info for record in caplog.records)


@pytest.mark.asyncio
async def test_error_behavior_is_forward():
    manager = Manager(MockAI(), error_behavior="forward")
    manager.chat.completions.create("ok")
    manager.chat.completions.create("fail", fail=True)

    result = await manager.process()

    assert result[0] == "ok"
    assert isinstance(result[1], ValueError)
    assert str(result[1]) == "fail"


@pytest.mark.asyncio
async def test_concurency_respected():
    client = MockAI()
    manager = Manager(client, concurrency=2)

    for value in range(5):
        manager.chat.completions.create(f"task-{value}")

    result = await manager.process()

    assert result == [
        "task-0",
        "task-1",
        "task-2",
        "task-3",
        "task-4",
    ]
    assert client.max_active == 2


def test_typechecks_concurrency():
    with pytest.raises(ValueError, match="positive integer"):
        Manager(MockAI(), concurrency=0)


def test_typechecks_error_behavior():
    with pytest.raises(ValueError, match="error_behavior"):
        Manager(MockAI(), error_behavior=cast(Any, "nope"))
