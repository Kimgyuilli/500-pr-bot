import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.pipeline import process_error
from app.schemas import ErrorReport

logger = logging.getLogger(__name__)

router = APIRouter()


def _log_task_exception(task: asyncio.Task) -> None:
    if not task.cancelled() and task.exception():
        logger.error("백그라운드 태스크 실패", exc_info=task.exception())


@router.post("/webhook/error")
async def receive_error(report: ErrorReport):
    task = asyncio.create_task(process_error(report))
    task.add_done_callback(_log_task_exception)
    return {"status": "received"}


@router.post("/api/test-webhook")
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
