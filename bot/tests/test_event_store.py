import asyncio

from app.event_store import (
    PipelineEvent,
    _error_history,
    _subscribers,
    emit,
    get_error,
    get_history,
    make_event,
    subscribe,
)


def _clear():
    _error_history.clear()
    _subscribers.clear()


async def test_emit_stores_event():
    _clear()
    event = make_event("abc", "received", "에러 수신")
    await emit(event)

    history = get_history()
    assert len(history) == 1
    assert history[0]["error_id"] == "abc"
    assert history[0]["step"] == "received"


async def test_emit_updates_same_error_id():
    _clear()
    await emit(make_event("abc", "received", "수신"))
    await emit(make_event("abc", "parsing", "파싱 중"))

    history = get_history()
    assert len(history) == 1
    assert history[0]["step"] == "parsing"


async def test_history_max_50():
    _clear()
    for i in range(55):
        await emit(make_event(f"err-{i}", "received", f"에러 {i}"))

    history = get_history()
    assert len(history) == 50
    # 가장 최근이 먼저
    assert history[0]["error_id"] == "err-54"


async def test_subscribe_receives_events():
    _clear()
    received = []

    async def reader():
        async for event in subscribe():
            received.append(event)
            if len(received) >= 2:
                break

    task = asyncio.create_task(reader())
    await asyncio.sleep(0.01)

    await emit(make_event("x", "received", "수신"))
    await emit(make_event("x", "done", "완료"))

    await asyncio.wait_for(task, timeout=2.0)
    assert len(received) == 2
    assert received[0]["step"] == "received"
    assert received[1]["step"] == "done"


async def test_get_history_returns_newest_first():
    _clear()
    await emit(make_event("a", "received", "first"))
    await emit(make_event("b", "received", "second"))

    history = get_history()
    assert history[0]["error_id"] == "b"
    assert history[1]["error_id"] == "a"


async def test_data_merge_across_events():
    _clear()
    await emit(make_event("abc", "received", "수신", data={"errorType": "NPE", "errorMessage": "null"}))
    await emit(make_event("abc", "done", "완료", data={"pr_url": "https://github.com/pr/1", "root_cause": "null check 누락"}))

    history = get_history()
    assert len(history) == 1
    data = history[0]["data"]
    # received 데이터 유지
    assert data["errorType"] == "NPE"
    assert data["errorMessage"] == "null"
    # done 데이터 merge
    assert data["pr_url"] == "https://github.com/pr/1"
    assert data["root_cause"] == "null check 누락"


async def test_data_not_overwritten_when_none():
    _clear()
    await emit(make_event("abc", "received", "수신", data={"errorType": "NPE"}))
    await emit(make_event("abc", "parsing", "파싱 중"))  # data=None

    history = get_history()
    assert history[0]["data"]["errorType"] == "NPE"


async def test_get_error_found():
    _clear()
    await emit(make_event("abc", "received", "수신", data={"errorType": "NPE"}))

    result = get_error("abc")
    assert result is not None
    assert result["error_id"] == "abc"
    assert result["data"]["errorType"] == "NPE"


async def test_get_error_not_found():
    _clear()
    assert get_error("nonexistent") is None
