from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_all_ok():
    """모든 서비스 정상이면 status=ok."""
    mock_openai = MagicMock()
    mock_repo = MagicMock()
    mock_repo.full_name = "owner/repo"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    with patch("app.main.OpenAI", return_value=mock_openai), \
         patch("app.main._get_repo", return_value=mock_repo), \
         patch("httpx.AsyncClient.head", new_callable=AsyncMock, return_value=mock_response):
        resp = client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["services"]["openai"]["status"] == "ok"
    assert data["services"]["github"]["status"] == "ok"
    assert data["services"]["discord"]["status"] == "ok"


def test_health_degraded_on_openai_failure():
    """OpenAI 실패 시 status=degraded."""
    mock_openai = MagicMock()
    mock_openai.models.list.side_effect = RuntimeError("API key invalid")
    mock_repo = MagicMock()
    mock_repo.full_name = "owner/repo"

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("app.main.OpenAI", return_value=mock_openai), \
         patch("app.main._get_repo", return_value=mock_repo), \
         patch("httpx.AsyncClient.head", new_callable=AsyncMock, return_value=mock_response):
        resp = client.get("/health")

    data = resp.json()
    assert data["status"] == "degraded"
    assert data["services"]["openai"]["status"] == "error"
    assert "API key invalid" in data["services"]["openai"]["detail"]
    assert data["services"]["github"]["status"] == "ok"


def test_health_degraded_on_github_failure():
    """GitHub 실패 시 status=degraded."""
    mock_openai = MagicMock()
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()

    with patch("app.main.OpenAI", return_value=mock_openai), \
         patch("app.main._get_repo", side_effect=RuntimeError("Bad token")), \
         patch("httpx.AsyncClient.head", new_callable=AsyncMock, return_value=mock_response):
        resp = client.get("/health")

    data = resp.json()
    assert data["status"] == "degraded"
    assert data["services"]["github"]["status"] == "error"


def test_health_degraded_on_discord_failure():
    """Discord 실패 시 status=degraded."""
    mock_openai = MagicMock()
    mock_repo = MagicMock()
    mock_repo.full_name = "owner/repo"

    with patch("app.main.OpenAI", return_value=mock_openai), \
         patch("app.main._get_repo", return_value=mock_repo), \
         patch("httpx.AsyncClient.head", new_callable=AsyncMock, side_effect=httpx.HTTPError("Webhook not found")):
        resp = client.get("/health")

    data = resp.json()
    assert data["status"] == "degraded"
    assert data["services"]["discord"]["status"] == "error"


@patch("app.main.process_error", new_callable=AsyncMock)
def test_webhook_returns_received(mock_process):
    resp = client.post("/webhook/error", json={
        "errorType": "NPE",
        "errorMessage": "msg",
        "stackTrace": "trace",
        "requestUrl": "GET /",
        "timestamp": "2026-01-01T00:00:00Z",
    })
    assert resp.status_code == 200
    assert resp.json() == {"status": "received"}


def test_webhook_rejects_invalid_body():
    resp = client.post("/webhook/error", json={"errorType": "NPE"})
    assert resp.status_code == 422
