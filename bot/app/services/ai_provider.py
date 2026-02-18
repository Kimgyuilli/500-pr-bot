import logging
from typing import Protocol

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

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


def health_check() -> dict:
    """OpenAI API 연결 상태 확인."""
    try:
        provider = get_provider()
        if isinstance(provider, OpenAIProvider):
            provider._get_client().models.list()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


_provider: AIProvider | None = None

_PROVIDERS: dict[str, type] = {
    "openai": OpenAIProvider,
}


def get_provider() -> AIProvider:
    global _provider
    if _provider is None:
        name = settings.ai_provider
        cls = _PROVIDERS.get(name)
        if cls is None:
            raise ValueError(f"알 수 없는 AI provider: {name!r} (지원: {list(_PROVIDERS)})")
        _provider = cls()
    return _provider
