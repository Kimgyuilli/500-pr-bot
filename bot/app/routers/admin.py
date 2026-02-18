import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.services.test_runner import run_tests

router = APIRouter(prefix="/api")


@router.get("/source-mode")
async def get_source_mode():
    return {"source_mode": settings.source_mode}


@router.put("/source-mode")
async def set_source_mode(body: dict):
    mode = body.get("source_mode", "")
    if mode not in ("github", "local"):
        return JSONResponse(status_code=400, content={"detail": "github 또는 local만 가능"})
    if mode == "local" and not settings.local_source_path:
        return JSONResponse(status_code=400, content={"detail": "LOCAL_SOURCE_PATH가 설정되지 않음"})
    settings.source_mode = mode
    return {"source_mode": mode}


@router.get("/tests/stream")
async def test_stream():
    return EventSourceResponse(_test_sse_generator(), media_type="text/event-stream")


async def _test_sse_generator():
    async for event in run_tests():
        yield {"data": json.dumps(event, ensure_ascii=False)}
