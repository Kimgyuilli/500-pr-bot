import asyncio
import logging

from pydantic import BaseModel

from discord_service import send_error_alert

logger = logging.getLogger(__name__)


class ErrorReport(BaseModel):
    errorType: str
    errorMessage: str
    stackTrace: str
    requestUrl: str
    timestamp: str


async def process_error(report: ErrorReport) -> None:
    try:
        await send_error_alert(report)
    except Exception:
        logger.exception("에러 처리 중 실패")
