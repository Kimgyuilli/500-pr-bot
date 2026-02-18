import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.error_handler import process_error
from app.schemas import ErrorReport
from app.event_store import get_error, get_history, subscribe
from app.services.ai_provider import health_check as ai_health_check
from app.services.discord_service import health_check as discord_health_check
from app.services.github_service import health_check as github_health_check
from app.test_runner import run_tests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="500 Error Auto-Fix Bot")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        logger.error("백그라운드 태스크 실패", exc_info=task.exception())


@app.get("/")
async def dashboard():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/health")
async def health():
    services = {
        "openai": ai_health_check(),
        "github": github_health_check(),
        "discord": await discord_health_check(),
    }
    all_ok = all(s["status"] == "ok" for s in services.values())
    return {"status": "ok" if all_ok else "degraded", "services": services}


@app.post("/webhook/error")
async def receive_error(report: ErrorReport):
    task = asyncio.create_task(process_error(report))
    task.add_done_callback(_log_task_exception)
    return {"status": "received"}


@app.get("/api/events")
async def event_stream():
    return EventSourceResponse(
        _sse_generator(),
        media_type="text/event-stream",
    )


async def _sse_generator():
    async for event in subscribe():
        yield {"data": json.dumps(event, ensure_ascii=False)}


@app.get("/api/errors/{error_id}")
async def get_error_detail(error_id: str):
    error = get_error(error_id)
    if not error:
        return JSONResponse(status_code=404, content={"detail": "에러를 찾을 수 없습니다"})
    return error


@app.get("/api/errors")
async def get_errors():
    return get_history()


@app.get("/api/tests/stream")
async def test_stream():
    return EventSourceResponse(_test_sse_generator(), media_type="text/event-stream")


async def _test_sse_generator():
    async for event in run_tests():
        yield {"data": json.dumps(event, ensure_ascii=False)}


@app.get("/api/source-mode")
async def get_source_mode():
    return {"source_mode": settings.source_mode}


@app.put("/api/source-mode")
async def set_source_mode(body: dict):
    mode = body.get("source_mode", "")
    if mode not in ("github", "local"):
        return JSONResponse(status_code=400, content={"detail": "github 또는 local만 가능"})
    if mode == "local" and not settings.local_source_path:
        return JSONResponse(status_code=400, content={"detail": "LOCAL_SOURCE_PATH가 설정되지 않음"})
    settings.source_mode = mode
    return {"source_mode": mode}


@app.post("/api/test-webhook")
async def test_webhook():
    now = datetime.now(timezone.utc)
    sample = ErrorReport(
        errorType="NullPointerException",
        errorMessage=f"Cannot invoke method on null object (test-{now.strftime('%H%M%S')})",
        stackTrace=(
            "at com.myapp.service.UserService.getUser(UserService.java:45)\n"
            "at com.myapp.controller.UserController.show(UserController.java:30)\n"
            "at org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:97)"
        ),
        requestUrl="GET /api/users/1",
        timestamp=now.isoformat(),
    )
    task = asyncio.create_task(process_error(sample))
    task.add_done_callback(_log_task_exception)
    return {"status": "test sent"}
