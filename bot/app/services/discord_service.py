import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from app.config import settings

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
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


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
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


@retry(stop=stop_after_attempt(2), wait=wait_fixed(1), reraise=True)
async def send_failure_alert(report, reason: str) -> None:
    embed = {
        "title": "⚠️ 에러 자동 수정 실패",
        "color": 0xFFA500,
        "fields": [
            {"name": "에러 타입", "value": report.errorType, "inline": True},
            {"name": "요청", "value": report.requestUrl, "inline": True},
            {"name": "메시지", "value": report.errorMessage[:1024]},
            {"name": "실패 사유", "value": reason[:1024]},
        ],
    }

    payload = {"embeds": [embed]}

    async with httpx.AsyncClient() as client:
        response = await client.post(settings.discord_webhook_url, json=payload)
        response.raise_for_status()
