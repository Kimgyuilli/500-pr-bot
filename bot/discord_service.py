import httpx

from config import settings


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
