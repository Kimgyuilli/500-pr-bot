from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_all_ok():
    """모든 서비스 정상이면 status=ok."""
    with (
        patch("app.routers.health.ai_health_check", return_value={"status": "ok"}),
        patch("app.routers.health.github_health_check", return_value={"status": "ok"}),
        patch("app.routers.health.discord_health_check", new_callable=AsyncMock, return_value={"status": "ok"}),
    ):
        resp = client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["services"]["openai"]["status"] == "ok"
    assert data["services"]["github"]["status"] == "ok"
    assert data["services"]["discord"]["status"] == "ok"


def test_health_degraded_on_openai_failure():
    """OpenAI 실패 시 status=degraded."""
    with (
        patch("app.routers.health.ai_health_check", return_value={"status": "error", "detail": "API key invalid"}),
        patch("app.routers.health.github_health_check", return_value={"status": "ok"}),
        patch("app.routers.health.discord_health_check", new_callable=AsyncMock, return_value={"status": "ok"}),
    ):
        resp = client.get("/health")

    data = resp.json()
    assert data["status"] == "degraded"
    assert data["services"]["openai"]["status"] == "error"
    assert "API key invalid" in data["services"]["openai"]["detail"]
    assert data["services"]["github"]["status"] == "ok"


def test_health_degraded_on_github_failure():
    """GitHub 실패 시 status=degraded."""
    with (
        patch("app.routers.health.ai_health_check", return_value={"status": "ok"}),
        patch("app.routers.health.github_health_check", return_value={"status": "error", "detail": "Bad token"}),
        patch("app.routers.health.discord_health_check", new_callable=AsyncMock, return_value={"status": "ok"}),
    ):
        resp = client.get("/health")

    data = resp.json()
    assert data["status"] == "degraded"
    assert data["services"]["github"]["status"] == "error"


def test_health_degraded_on_discord_failure():
    """Discord 실패 시 status=degraded."""
    with (
        patch("app.routers.health.ai_health_check", return_value={"status": "ok"}),
        patch("app.routers.health.github_health_check", return_value={"status": "ok"}),
        patch("app.routers.health.discord_health_check", new_callable=AsyncMock, return_value={"status": "error", "detail": "Webhook not found"}),
    ):
        resp = client.get("/health")

    data = resp.json()
    assert data["status"] == "degraded"
    assert data["services"]["discord"]["status"] == "error"


@patch("app.routers.webhook.process_error", new_callable=AsyncMock)
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
