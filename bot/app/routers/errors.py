import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app.event_store import get_error, get_history, subscribe

router = APIRouter(prefix="/api")


@router.get("/events")
async def event_stream():
    return EventSourceResponse(
        _sse_generator(),
        media_type="text/event-stream",
    )


async def _sse_generator():
    async for event in subscribe():
        yield {"data": json.dumps(event, ensure_ascii=False)}


@router.get("/errors/{error_id}")
async def get_error_detail(error_id: str):
    error = get_error(error_id)
    if not error:
        return JSONResponse(status_code=404, content={"detail": "에러를 찾을 수 없습니다"})
    return error


@router.get("/errors")
async def get_errors():
    return get_history()
