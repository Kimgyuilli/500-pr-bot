import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from functools import partial

from pydantic import BaseModel

from claude_service import analyze_error
from config import settings
from discord_service import send_error_alert, send_pr_alert
from github_service import create_pull_request, fetch_files
from stack_trace_parser import parse_stack_trace

logger = logging.getLogger(__name__)


class ErrorReport(BaseModel):
    errorType: str
    errorMessage: str
    stackTrace: str
    requestUrl: str
    timestamp: str


PR_BODY_TEMPLATE = """\
## 자동 생성된 에러 수정 PR

### 에러 정보
- **타입**: {error_type}
- **메시지**: {error_message}
- **요청**: {request_url}
- **발생 시간**: {timestamp}

### AI 분석
{analysis}

### 변경 사항
{summary}

---
> 이 PR은 Error Bot이 자동으로 생성했습니다.
> 반드시 코드 리뷰 후 머지하세요."""


def _build_pr_body(report: "ErrorReport", analysis: str, summary: str) -> str:
    return PR_BODY_TEMPLATE.format(
        error_type=report.errorType,
        error_message=report.errorMessage,
        request_url=report.requestUrl,
        timestamp=report.timestamp,
        analysis=analysis,
        summary=summary,
    )


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

        summary = result.get("summary", "에러 자동 수정")
        analysis = result.get("analysis", "")
        logger.info("분석 완료: %s", summary)

        # 4. 브랜치명 생성
        short_hash = hashlib.sha256(
            f"{report.errorType}{report.errorMessage}".encode()
        ).hexdigest()[:7]
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        branch_name = f"fix/error-{short_hash}-{ts}"

        # 5. PR 본문 생성
        pr_body = _build_pr_body(report, analysis, summary)

        # 6. GitHub PR 생성 (동기 → run_in_executor)
        pr_url = await loop.run_in_executor(
            None,
            partial(
                create_pull_request,
                files=result["files"],
                summary=summary,
                pr_body=pr_body,
                branch_name=branch_name,
            ),
        )
        logger.info("PR 생성 완료: %s", pr_url)

        # 7. Discord PR 완료 알림
        await send_pr_alert(pr_url, summary)

    except Exception:
        logger.exception("에러 처리 중 실패")
