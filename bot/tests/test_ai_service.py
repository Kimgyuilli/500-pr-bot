import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.ai_provider import OpenAIProvider, _PROVIDERS, get_provider
from app.services.ai_service import analyze_error


def _make_mock_provider(content: str):
    """AIProvider mock 생성 헬퍼."""
    provider = MagicMock()
    provider.call.return_value = content
    return provider


def test_analyze_error_returns_parsed_response():
    expected = {
        "analysis": "원인",
        "root_cause": "null 체크 누락",
        "fix_description": "null 체크 추가",
        "files": [],
        "summary": "수정",
    }
    provider = _make_mock_provider(json.dumps(expected))

    with patch("app.services.ai_service.get_provider", return_value=provider):
        result = analyze_error(
            "NPE", "msg", "trace",
            error_files={"a.java": "code"},
            context_files={"b.java": "ref code"},
        )

    assert result == expected


def test_analyze_error_returns_none_on_invalid_json():
    """1차, 2차 모두 invalid JSON이면 None."""
    provider = _make_mock_provider("not json")

    with patch("app.services.ai_service.get_provider", return_value=provider):
        result = analyze_error("NPE", "msg", "trace", error_files={"a.java": "code"})

    assert result is None
    # 1차 + 2차 = 2번 호출
    assert provider.call.call_count == 2


def test_analyze_error_retry_succeeds_on_second_attempt():
    """1차 invalid JSON → 2차 유효 JSON이면 성공."""
    expected = {
        "analysis": "원인",
        "root_cause": "근본",
        "fix_description": "수정",
        "files": [],
        "summary": "요약",
    }
    provider = MagicMock()
    provider.call.side_effect = ["not json", json.dumps(expected)]

    with patch("app.services.ai_service.get_provider", return_value=provider):
        result = analyze_error("NPE", "msg", "trace", error_files={"a.java": "code"})

    assert result == expected


def test_analyze_error_returns_none_on_api_exception():
    provider = MagicMock()
    provider.call.side_effect = RuntimeError("API down")

    with patch("app.services.ai_service.get_provider", return_value=provider):
        result = analyze_error("NPE", "msg", "trace", error_files={"a.java": "code"})

    assert result is None
    # 1차 실패 → 바로 None (네트워크 에러는 재시도 안 함)
    assert provider.call.call_count == 1


def test_get_provider_returns_openai_by_default():
    """ai_provider=openai일 때 OpenAIProvider 반환."""
    with patch("app.services.ai_provider._provider", None), \
         patch("app.services.ai_provider.settings") as mock_settings:
        mock_settings.ai_provider = "openai"
        provider = get_provider()
        assert isinstance(provider, OpenAIProvider)


def test_get_provider_raises_on_unknown():
    """알 수 없는 provider 이름이면 ValueError."""
    with patch("app.services.ai_provider._provider", None), \
         patch("app.services.ai_provider.settings") as mock_settings:
        mock_settings.ai_provider = "unknown"
        with pytest.raises(ValueError, match="알 수 없는 AI provider"):
            get_provider()


def test_providers_registry_contains_openai():
    assert "openai" in _PROVIDERS
    assert _PROVIDERS["openai"] is OpenAIProvider
