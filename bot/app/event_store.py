import asyncio
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import AsyncGenerator


@dataclass
class PipelineEvent:
    error_id: str
    step: str  # received | parsing | fetching | analyzing | creating_pr | done | failed
    message: str
    timestamp: str
    data: dict | None = None


# 최근 에러 50건 (error_id → 이벤트 목록)
_error_history: deque[dict] = deque(maxlen=50)

# SSE 구독자
_subscribers: set[asyncio.Queue] = set()


async def emit(event: PipelineEvent) -> None:
    """이벤트 저장 + SSE 브로드캐스트."""
    payload = asdict(event)

    # 히스토리 업데이트: 같은 error_id면 마지막 항목 갱신, 아니면 새로 추가
    for item in _error_history:
        if item["error_id"] == event.error_id:
            item["step"] = event.step
            item["message"] = event.message
            item["timestamp"] = event.timestamp
            if event.data:
                if not item.get("data"):
                    item["data"] = {}
                item["data"].update(event.data)
            break
    else:
        _error_history.append(dict(payload))

    # SSE 브로드캐스트
    dead: list[asyncio.Queue] = []
    for q in _subscribers:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _subscribers.discard(q)


def get_history() -> list[dict]:
    """최근 에러 목록 반환 (최신 순)."""
    return list(reversed(_error_history))


def get_error(error_id: str) -> dict | None:
    """특정 에러의 상세 정보 반환."""
    for item in _error_history:
        if item["error_id"] == error_id:
            return item
    return None


async def subscribe() -> AsyncGenerator[dict, None]:
    """SSE 이벤트 스트림."""
    q: asyncio.Queue = asyncio.Queue(maxsize=256)
    _subscribers.add(q)
    try:
        while True:
            event = await q.get()
            yield event
    finally:
        _subscribers.discard(q)


def make_event(error_id: str, step: str, message: str, data: dict | None = None) -> PipelineEvent:
    """PipelineEvent 생성 헬퍼."""
    return PipelineEvent(
        error_id=error_id,
        step=step,
        message=message,
        timestamp=datetime.now(timezone.utc).isoformat(),
        data=data,
    )
