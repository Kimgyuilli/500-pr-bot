import asyncio
import hashlib
import logging
import time
from datetime import datetime, timezone
from functools import partial

from pydantic import BaseModel

from app.services.ai_service import analyze_error
from app.config import settings
from app.services.discord_service import send_error_alert, send_failure_alert, send_pr_alert
from app.services.github_service import create_pull_request, fetch_files
from app.utils.stack_trace_parser import extract_related_imports, parse_stack_trace

logger = logging.getLogger(__name__)

# 중복 에러 필터링
_recent_errors: dict[str, float] = {}  # {dedup_key: timestamp}
DEDUP_TTL = 1800  # 30분


def _is_duplicate(report: "ErrorReport") -> bool:
    key = hashlib.sha256(
        f"{report.errorType}{report.errorMessage}{report.stackTrace[:200]}".encode()
    ).hexdigest()
    now = time.time()
    # 만료된 항목 정리
    expired = [k for k, t in _recent_errors.items() if now - t > DEDUP_TTL]
    for k in expired:
        del _recent_errors[k]
    # 중복 체크
    if key in _recent_errors:
        return True
    _recent_errors[key] = now
    return False


class ErrorReport(BaseModel):
    errorType: str
    errorMessage: str
    stackTrace: str
    requestUrl: str
    timestamp: str


PR_BODY_TEMPLATE = """\
## 자동 생성된 에러 수정 PR

### 에러 정보
| 항목 | 내용 |
|------|------|
| 타입 | `{error_type}` |
| 메시지 | {error_message} |
| 요청 | {request_url} |
| 발생 시간 | {timestamp} |

### 근본 원인
{root_cause}

### AI 분석
{analysis}

### 수정 내용
{fix_description}

### 수정된 파일
{changed_files}

---
> 이 PR은 Error Bot이 자동으로 생성했습니다.
> 반드시 코드 리뷰 후 머지하세요."""


def _build_pr_body(report: "ErrorReport", result: dict) -> str:
    changed_files_list = result.get("files", [])
    changed_files = "\n".join(
        f"- `{f['path']}`" for f in changed_files_list
    ) or "- 없음"

    return PR_BODY_TEMPLATE.format(
        error_type=report.errorType,
        error_message=report.errorMessage,
        request_url=report.requestUrl,
        timestamp=report.timestamp,
        root_cause=result.get("root_cause", ""),
        analysis=result.get("analysis", ""),
        fix_description=result.get("fix_description", ""),
        changed_files=changed_files,
    )


async def process_error(report: ErrorReport) -> None:
    try:
        # 0. 중복 에러 필터링
        if _is_duplicate(report):
            logger.info("중복 에러 무시: %s", report.errorType)
            return

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

        # 2-1. import 기반 관련 파일 추가 fetch (1 depth)
        error_files = dict(files)  # 스택트레이스 파일 = error_files
        fetched_paths = set(files.keys())
        related_paths = []
        for source_code in files.values():
            related_paths.extend(
                extract_related_imports(source_code, settings.base_package, fetched_paths)
            )
        related_paths = list(dict.fromkeys(p for p in related_paths if p not in fetched_paths))
        context_files: dict[str, str] = {}
        if related_paths:
            context_files = await loop.run_in_executor(
                None, partial(fetch_files, related_paths)
            )

        # 3. AI API로 분석 (동기 → run_in_executor)
        result = await loop.run_in_executor(
            None,
            partial(
                analyze_error,
                error_type=report.errorType,
                error_message=report.errorMessage,
                stack_trace=report.stackTrace,
                error_files=error_files,
                context_files=context_files,
            ),
        )
        if not result:
            logger.warning("AI 분석 결과 없음")
            await send_failure_alert(report, "AI 분석 실패")
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
        pr_body = _build_pr_body(report, result)

        # 6. GitHub PR 생성 (동기 → run_in_executor)
        try:
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
        except Exception as e:
            logger.exception("PR 생성 실패")
            await send_failure_alert(report, f"PR 생성 실패: {e}")
            return

        logger.info("PR 생성 완료: %s", pr_url)

        # 7. Discord PR 완료 알림
        await send_pr_alert(pr_url, summary)

    except Exception:
        logger.exception("에러 처리 중 실패")
