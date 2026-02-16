import httpx

from app.config import settings


async def send_error_alert(report) -> None:
    embed = {
        "title": "🚨 500 에러 발생",
        "color": 0xFF0000,
        "fields": [
            {"name": "에러 타입", "value": report.errorType, "inline": True},
            {"name": "요청", "value": report.requestUrl, "inline": True},
            {"name": "메시지", "value": report.errorMessage[:1024]},
            {"name": "발생 시간", "value": report.timestamp, "inline": True},
        ],
    }

    payload = {"embeds": [embed]}

    async with httpx.AsyncClient() as client:
        response = await client.post(settings.discord_webhook_url, json=payload)
        response.raise_for_status()


async def send_pr_alert(pr_url: str, summary: str) -> None:
    embed = {
        "title": "✅ 자동 수정 PR 생성",
        "color": 0x00FF00,
        "fields": [
            {"name": "변경 사항", "value": summary[:1024]},
            {"name": "PR 링크", "value": pr_url},
        ],
    }

    payload = {"embeds": [embed]}

    async with httpx.AsyncClient() as client:
        response = await client.post(settings.discord_webhook_url, json=payload)
        response.raise_for_status()
