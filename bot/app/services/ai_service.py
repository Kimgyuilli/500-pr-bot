import json
import logging
from typing import Protocol

from openai import OpenAI
from tenacity import retry, retry_if_not_exception_type, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger(__name__)


class AIProvider(Protocol):
    """AI API 호출 후 텍스트 응답 반환."""

    def call(self, system_prompt: str, user_prompt: str) -> str: ...


class OpenAIProvider:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = OpenAI(api_key=settings.openai_api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_fixed(2),
        reraise=True,
    )
    def call(self, system_prompt: str, user_prompt: str) -> str:
        response = self._get_client().chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=4096,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content


_provider: AIProvider | None = None

_PROVIDERS: dict[str, type] = {
    "openai": OpenAIProvider,
}


def _get_provider() -> AIProvider:
    global _provider
    if _provider is None:
        name = settings.ai_provider
        cls = _PROVIDERS.get(name)
        if cls is None:
            raise ValueError(f"알 수 없는 AI provider: {name!r} (지원: {list(_PROVIDERS)})")
        _provider = cls()
    return _provider


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


def analyze_error(
    error_type: str,
    error_message: str,
    stack_trace: str,
    error_files: dict[str, str],
    context_files: dict[str, str] | None = None,
) -> dict | None:
    """AI API로 에러를 분석하고 수정안을 반환한다. 실패 시 None."""
    user_prompt = USER_PROMPT_TEMPLATE.format(
        error_type=error_type,
        error_message=error_message,
        stack_trace=stack_trace,
        source_code_section=_build_source_section(error_files, context_files or {}),
    )

    provider = _get_provider()

    # 1차 시도
    try:
        text = provider.call(SYSTEM_PROMPT, user_prompt)
        return json.loads(text)
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.warning("1차 AI 응답 파싱 실패, 재시도: %s", e)
    except Exception:
        logger.exception("AI API 호출 실패")
        return None

    # 2차 시도: 피드백 포함
    retry_prompt = (
        user_prompt + "\n\n## 주의\n"
        "이전 응답이 유효한 JSON이 아니었다. "
        "반드시 위에 명시된 JSON 형식으로만 응답하라. "
        "JSON 외의 텍스트를 절대 포함하지 마라."
    )
    try:
        text = provider.call(SYSTEM_PROMPT, retry_prompt)
        return json.loads(text)
    except (json.JSONDecodeError, IndexError, KeyError) as e:
        logger.error("2차 AI 응답 파싱도 실패: %s", e)
        return None
    except Exception:
        logger.exception("AI API 재시도 호출 실패")
        return None
