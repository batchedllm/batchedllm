import logging
from typing import Any, cast

import pytest

from batchedllm import Manager


def test_generally_works(mockAI):
    manager = Manager(mockAI)

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


def test_paths_dont_cross(mockAI):
    manager = Manager(mockAI)

    manager.chat
    manager.chat.completions
    manager.chat.completions.create
    manager.this.can.be.any.path_we.dont.care.until.you.call.it
    manager.chat.completions.create("only one")

    assert len(manager._queue) == 1
    assert manager._queue[0].path == ("chat", "completions", "create")


def test_paths_dont_cross_even_when_error(mockAI):
    manager = Manager(mockAI)

    with pytest.raises(TypeError, match="is not callable"):
        manager.history()

    manager.chat.completions.create("only one even if previous errors")

    assert len(manager._queue) == 1
    assert manager._queue[0].path == ("chat", "completions", "create")


def test_sync_works(mockAI):
    manager = Manager(mockAI)
    manager.chat.completions.sync_create("sync")

    result = manager.sync_process()

    assert result == ["sync"]
    assert len(manager._queue) == 0


async def test_async_works(mockAI):
    manager = Manager(mockAI)

    manager.chat.completions.create("first")
    manager.chat.completions.sync_create("second")

    result = await manager.process()

    assert result == [
        "first",
        "second",
    ]
    assert mockAI.history == [
        ("chat.completions.create", "first"),
        ("chat.completions.sync_create", "second"),
    ]
    assert len(manager._queue) == 0


async def test_error_behavior_is_raise(mockAI):
    manager = Manager(mockAI, error_behavior="raise")

    manager.chat.completions.create("fail", fail=True)

    with pytest.raises(ValueError, match="fail"):
        await manager.process()


async def test_error_behavior_is_ignore(mockAI, caplog):
    manager = Manager(mockAI, error_behavior="ignore")
    manager.chat.completions.create("ok")
    manager.chat.completions.create("fail", fail=True)

    with caplog.at_level(logging.DEBUG):
        result = await manager.process()

    assert result == ["ok", None]
    assert any(record.exc_info for record in caplog.records)


async def test_error_behavior_is_forward(mockAI):
    manager = Manager(mockAI, error_behavior="forward")
    manager.chat.completions.create("ok")
    manager.chat.completions.create("fail", fail=True)

    result = await manager.process()

    assert result[0] == "ok"
    assert isinstance(result[1], ValueError)
    assert str(result[1]) == "fail"


async def test_concurency_respected(mockAI):
    manager = Manager(mockAI, concurrency=2)

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
    assert mockAI.max_active == 2


def test_typechecks_concurrency(mockAI):
    with pytest.raises(ValueError, match="positive integer"):
        Manager(mockAI, concurrency=0)


def test_typechecks_error_behavior(mockAI):
    with pytest.raises(ValueError, match="error_behavior"):
        Manager(mockAI, error_behavior=cast(Any, "nope"))
