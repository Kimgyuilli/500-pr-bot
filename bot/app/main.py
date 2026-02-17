import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.error_handler import ErrorReport, process_error
from fastapi.responses import JSONResponse
from app.event_store import get_error, get_history, subscribe

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
    return {"status": "ok"}


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
    import json
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


@app.post("/api/test-webhook")
async def test_webhook():
    sample = ErrorReport(
        errorType="NullPointerException",
        errorMessage="Cannot invoke method on null object",
        stackTrace=(
            "at com.myapp.service.UserService.getUser(UserService.java:45)\n"
            "at com.myapp.controller.UserController.show(UserController.java:30)\n"
            "at org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:97)"
        ),
        requestUrl="GET /api/users/1",
        timestamp="2026-02-17T12:00:00Z",
    )
    task = asyncio.create_task(process_error(sample))
    task.add_done_callback(_log_task_exception)
    return {"status": "test sent"}
