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
에러 정보와 소스코드를 받아서 수정된 코드를 반환한다."""

USER_PROMPT_TEMPLATE = """\
## 에러
- 타입: {error_type}
- 메시지: {error_message}

## 스택 트레이스
{stack_trace}

## 소스 코드
{source_code_section}

## 지시사항
1. 에러 원인을 분석하라
2. 수정이 필요한 파일의 전체 코드를 제공하라
3. 수정 사항을 설명하라

아래 JSON 형식으로만 응답하라:
{{"analysis": "에러 원인 분석", "files": [{{"path": "파일 경로", "content": "수정된 전체 코드"}}], "summary": "변경 사항 요약 (PR 제목용, 한 줄)"}}"""


def _build_source_section(files: dict[str, str]) -> str:
    parts = []
    for path, content in files.items():
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
    files: dict[str, str],
) -> dict | None:
    """OpenAI API로 에러를 분석하고 수정안을 반환한다. 실패 시 None."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        error_type=error_type,
        error_message=error_message,
        stack_trace=stack_trace,
        source_code_section=_build_source_section(files),
    )

    try:
        return _call_openai(user_prompt)
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.error("OpenAI 응답 파싱 실패: %s", e)
        return None
    except Exception:
        logger.exception("OpenAI API 호출 실패")
        return None
