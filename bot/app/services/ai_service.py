import json
import logging

from openai import OpenAI
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client

SYSTEM_PROMPT = """\
너는 Spring Boot 코드를 분석하고 수정하는 봇이다.
에러 정보와 소스코드를 받아서 수정된 코드를 반환한다.
"에러 발생 소스 코드"는 스택트레이스에 직접 등장한 파일이고,
"관련 참고 코드"는 import로 연결된 참고용 파일이다. 참고 코드는 수정 맥락 파악용이다.
반드시 한국어로만 응답하라. 중국어, 일본어 등 다른 언어를 섞지 마라."""

USER_PROMPT_TEMPLATE = """\
## 에러
- 타입: {error_type}
- 메시지: {error_message}

## 스택 트레이스
{stack_trace}

{source_code_section}

## 지시사항
1. 에러 원인을 분석하라
2. 수정이 필요한 파일의 전체 코드를 제공하라
3. 수정 사항을 설명하라

아래 JSON 형식으로만 응답하라:
{{"analysis": "에러 원인 상세 분석", "root_cause": "근본 원인 한 줄 요약", "fix_description": "수정 내용 상세 설명 (마크다운)", "files": [{{"path": "파일 경로", "content": "수정된 전체 코드"}}], "summary": "변경 사항 요약 (PR 제목용, 한 줄)"}}"""


def _build_source_section(
    error_files: dict[str, str], context_files: dict[str, str]
) -> str:
    parts = ["## 에러 발생 소스 코드 (스택트레이스에 포함된 파일)"]
    for path, content in error_files.items():
        parts.append(f"### {path}\n```java\n{content}\n```")
    if context_files:
        parts.append("\n## 관련 참고 코드 (import된 프로젝트 내부 파일)")
        for path, content in context_files.items():
            parts.append(f"### {path}\n```java\n{content}\n```")
    return "\n\n".join(parts)


@retry(
    stop=stop_after_attempt(2),
    wait=wait_fixed(2),
    retry=retry_if_not_exception_type((json.JSONDecodeError, IndexError, KeyError)),
    reraise=True,
)
def _call_openai(user_prompt: str) -> dict:
    """OpenAI API 호출 + JSON 파싱. 네트워크 오류만 재시도."""
    response = _get_client().chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    text = response.choices[0].message.content
    return json.loads(text)


def analyze_error(
    error_type: str,
    error_message: str,
    stack_trace: str,
    error_files: dict[str, str],
    context_files: dict[str, str] | None = None,
) -> dict | None:
    """OpenAI API로 에러를 분석하고 수정안을 반환한다. 실패 시 None."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        error_type=error_type,
        error_message=error_message,
        stack_trace=stack_trace,
        source_code_section=_build_source_section(error_files, context_files or {}),
    )

    try:
        return _call_openai(user_prompt)
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.error("OpenAI 응답 파싱 실패: %s", e)
        return None
    except Exception:
        logger.exception("OpenAI API 호출 실패")
        return None
