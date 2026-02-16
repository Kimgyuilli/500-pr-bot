from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


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
