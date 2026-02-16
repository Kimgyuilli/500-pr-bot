import os

# config.py가 import되기 전에 환경변수 설정 필요
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("GITHUB_TOKEN", "test-token")
os.environ.setdefault("GITHUB_REPO", "owner/repo")
os.environ.setdefault("BASE_PACKAGE", "com.myapp")
os.environ.setdefault("DISCORD_WEBHOOK_URL", "https://discord.test/webhook")

from unittest.mock import AsyncMock, patch

import pytest

from app.error_handler import ErrorReport, _recent_errors


@pytest.fixture
def sample_error_report():
    return ErrorReport(
        errorType="NullPointerException",
        errorMessage="Cannot invoke method on null",
        stackTrace=(
            "at com.myapp.service.UserService.getUser(UserService.java:45)\n"
            "at com.myapp.controller.UserController.show(UserController.java:30)"
        ),
        requestUrl="GET /api/users/1",
        timestamp="2026-02-17T12:00:00Z",
    )


@pytest.fixture(autouse=True)
def _clear_dedup_cache():
    yield
    _recent_errors.clear()


@pytest.fixture
def mock_discord():
    """discord 함수 3개를 AsyncMock으로 교체."""
    with (
        patch("app.services.discord_service.send_error_alert", new_callable=AsyncMock) as m_error,
        patch("app.services.discord_service.send_pr_alert", new_callable=AsyncMock) as m_pr,
        patch("app.services.discord_service.send_failure_alert", new_callable=AsyncMock) as m_fail,
        patch("app.error_handler.send_error_alert", m_error),
        patch("app.error_handler.send_pr_alert", m_pr),
        patch("app.error_handler.send_failure_alert", m_fail),
    ):
        yield {"error": m_error, "pr": m_pr, "failure": m_fail}
