from unittest.mock import AsyncMock, patch

from app.services.discord_service import send_error_alert, send_failure_alert, send_pr_alert


@patch("app.services.discord_service._post_webhook", new_callable=AsyncMock)
async def test_send_error_alert_posts_correct_embed(mock_post, sample_error_report):
    await send_error_alert(sample_error_report)
    payload = mock_post.call_args[0][0]
    embed = payload["embeds"][0]
    assert embed["title"] == "🚨 500 에러 발생"
    assert embed["color"] == 0xFF0000
    assert any(f["name"] == "에러 타입" for f in embed["fields"])


@patch("app.services.discord_service._post_webhook", new_callable=AsyncMock)
async def test_send_pr_alert_posts_correct_embed(mock_post):
    await send_pr_alert("https://github.com/pr/1", "수정 요약")
    payload = mock_post.call_args[0][0]
    embed = payload["embeds"][0]
    assert embed["title"] == "✅ 자동 수정 PR 생성"
    assert embed["color"] == 0x00FF00


@patch("app.services.discord_service._post_webhook", new_callable=AsyncMock)
async def test_send_failure_alert_posts_correct_embed(mock_post, sample_error_report):
    await send_failure_alert(sample_error_report, "AI 실패")
    payload = mock_post.call_args[0][0]
    embed = payload["embeds"][0]
    assert embed["title"] == "⚠️ 에러 자동 수정 실패"
    assert embed["color"] == 0xFFA500
    assert any(f["value"] == "AI 실패" for f in embed["fields"])
