import json
from unittest.mock import MagicMock, patch

from app.services.ai_service import analyze_error


def _make_mock_client(content: str):
    """OpenAI 응답 mock 생성 헬퍼."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client = MagicMock()
    client.chat.completions.create.return_value = response
    return client


def test_analyze_error_returns_parsed_response():
    expected = {"analysis": "원인", "files": [], "summary": "수정"}
    client = _make_mock_client(json.dumps(expected))

    with patch("app.services.ai_service._get_client", return_value=client):
        result = analyze_error("NPE", "msg", "trace", {"a.java": "code"})

    assert result == expected


def test_analyze_error_returns_none_on_invalid_json():
    client = _make_mock_client("not json")

    with patch("app.services.ai_service._get_client", return_value=client):
        result = analyze_error("NPE", "msg", "trace", {"a.java": "code"})

    assert result is None


def test_analyze_error_returns_none_on_api_exception():
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("API down")

    with patch("app.services.ai_service._get_client", return_value=client):
        result = analyze_error("NPE", "msg", "trace", {"a.java": "code"})

    assert result is None
    # tenacity retry(2회)로 2번 호출됨
    assert client.chat.completions.create.call_count == 2
