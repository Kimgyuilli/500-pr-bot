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
    expected = {
        "analysis": "원인",
        "root_cause": "null 체크 누락",
        "fix_description": "null 체크 추가",
        "files": [],
        "summary": "수정",
    }
    client = _make_mock_client(json.dumps(expected))

    with patch("app.services.ai_service._get_client", return_value=client):
        result = analyze_error(
            "NPE", "msg", "trace",
            error_files={"a.java": "code"},
            context_files={"b.java": "ref code"},
        )

    assert result == expected


def test_analyze_error_returns_none_on_invalid_json():
    """1차, 2차 모두 invalid JSON이면 None."""
    client = _make_mock_client("not json")

    with patch("app.services.ai_service._get_client", return_value=client):
        result = analyze_error("NPE", "msg", "trace", error_files={"a.java": "code"})

    assert result is None
    # 1차 + 2차 = 2번 호출
    assert client.chat.completions.create.call_count == 2


def test_analyze_error_retry_succeeds_on_second_attempt():
    """1차 invalid JSON → 2차 유효 JSON이면 성공."""
    expected = {
        "analysis": "원인",
        "root_cause": "근본",
        "fix_description": "수정",
        "files": [],
        "summary": "요약",
    }
    # 1차: invalid, 2차: valid
    first_client = _make_mock_client("not json")
    second_client = _make_mock_client(json.dumps(expected))

    call_count = {"n": 0}
    original_get_client = None

    def _switching_client():
        call_count["n"] += 1
        if call_count["n"] <= 1:
            return first_client
        return second_client

    with patch("app.services.ai_service._get_client", side_effect=_switching_client):
        result = analyze_error("NPE", "msg", "trace", error_files={"a.java": "code"})

    assert result == expected


def test_analyze_error_returns_none_on_api_exception():
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("API down")

    with patch("app.services.ai_service._get_client", return_value=client):
        result = analyze_error("NPE", "msg", "trace", error_files={"a.java": "code"})

    assert result is None
    # tenacity retry(2회)로 2번 호출됨
    assert client.chat.completions.create.call_count == 2
