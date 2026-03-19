import asyncio
import logging

import pytest

from batchedllm import Manager


class MockAI:
    def __init__(self):
        self.history = []
        self.active = 0
        self.max_active = 0
        self.responses = self.Responses(self)
        self.not_callable = "not callable"

    class Responses:
        def __init__(self, parent):
            self.parent = parent

        async def create(self, input, *, delay=0, fail=False):
            self.parent.active += 1
            self.parent.max_active = max(self.parent.max_active, self.parent.active)

            self.parent.history.append(("responses.create", input))

            try:
                await asyncio.sleep(delay)
                if fail:
                    raise ValueError("fail")
                return {"result": input}
            finally:
                self.parent.active -= 1

    class Files:
        def list(self):
            return {"result": "not awaitable"}


class BrokenAI:
    def __init__(self):
        self.files = MockAI.Files()


def test_call_records_latest_path_and_task_details():
    manager = Manager(client=MockAI())

    returned = manager.responses.create("hello")

    assert returned is manager
    assert manager._latest_path == []
    assert len(manager._tasks) == 1
    assert manager._tasks[0].path == ("responses", "create")
    assert manager._tasks[0].args == ("hello",)
    assert manager._tasks[0].kwargs is None


@pytest.mark.asyncio
async def test_process_returns_results_in_submission_order():
    client = MockAI()
    manager = Manager(client=client)

    manager.responses.create("first")
    manager.responses.create("second")

    result = await manager.process()

    assert result == [
        {"result": "first"},
        {"result": "second"},
    ]
    assert client.history == [
        ("responses.create", "first"),
        ("responses.create", "second"),
    ]


@pytest.mark.asyncio
async def test_process_raises_when_error_behavior_is_raise():
    manager = Manager(client=MockAI(), error_behavior="raise")

    manager.responses.create("fail", fail=True)

    with pytest.raises(ValueError, match="fail"):
        await manager.process()


@pytest.mark.asyncio
async def test_process_ignores_errors_and_logs_them(caplog):
    manager = Manager(client=MockAI(), error_behavior="ignore")
    manager.responses.create("ok")
    manager.responses.create("fail", fail=True)

    with caplog.at_level(logging.ERROR):
        result = await manager.process()

    assert result == [{"result": "ok"}, None]
    assert any(record.exc_info for record in caplog.records)


@pytest.mark.asyncio
async def test_process_forwards_exceptions_as_results():
    manager = Manager(client=MockAI(), error_behavior="forward")
    manager.responses.create("ok")
    manager.responses.create("fail", fail=True)

    result = await manager.process()

    assert result[0] == {"result": "ok"}
    assert isinstance(result[1], ValueError)
    assert str(result[1]) == "fail"


@pytest.mark.asyncio
async def test_process_respects_concurrency_limit():
    client = MockAI()
    manager = Manager(client=client, concurency=2)

    for value in range(5):
        manager.responses.create(f"job-{value}", delay=0.01)

    result = await manager.process()

    assert result == [
        {"result": "job-0"},
        {"result": "job-1"},
        {"result": "job-2"},
        {"result": "job-3"},
        {"result": "job-4"},
    ]
    assert client.max_active == 2


def test_call_raises_type_error_for_not_callable_target():
    manager = Manager(client=MockAI())

    with pytest.raises(TypeError, match="is not callable"):
        manager.not_callable()


def test_sync_process_returns_results_without_running_loop():
    manager = Manager(client=MockAI())
    manager.responses.create("sync")

    result = manager.sync_process()

    assert result == [{"result": "sync"}]
