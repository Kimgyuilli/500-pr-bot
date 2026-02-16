import asyncio
import logging
from functools import partial

from pydantic import BaseModel

from claude_service import analyze_error
from config import settings
from discord_service import send_error_alert
from github_service import fetch_files
from stack_trace_parser import parse_stack_trace

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

        # 1. 스택트레이스 파싱
        entries = parse_stack_trace(report.stackTrace, settings.base_package)
        if not entries:
            logger.warning("스택트레이스에서 프로젝트 코드를 찾지 못함")
            return

        # 2. GitHub에서 소스코드 조회 (동기 → run_in_executor)
        file_paths = [e["file"] for e in entries]
        loop = asyncio.get_running_loop()
        files = await loop.run_in_executor(None, partial(fetch_files, file_paths))
        if not files:
            logger.warning("GitHub에서 파일을 조회하지 못함: %s", file_paths)
            return

        # 3. Claude API로 분석 (동기 → run_in_executor)
        result = await loop.run_in_executor(
            None,
            partial(
                analyze_error,
                error_type=report.errorType,
                error_message=report.errorMessage,
                stack_trace=report.stackTrace,
                files=files,
            ),
        )
        if not result:
            logger.warning("Claude 분석 결과 없음")
            return

        logger.info("분석 완료: %s", result.get("summary", ""))
        # Phase 3에서 여기에 PR 생성 로직 추가 예정

    except Exception:
        logger.exception("에러 처리 중 실패")
