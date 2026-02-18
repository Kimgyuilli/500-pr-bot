from fastapi import APIRouter

from app.services.ai_provider import health_check as ai_health_check
from app.services.discord_service import health_check as discord_health_check
from app.services.github_service import health_check as github_health_check

router = APIRouter()


@router.get("/health")
async def health():
    services = {
        "openai": ai_health_check(),
        "github": github_health_check(),
        "discord": await discord_health_check(),
    }
    all_ok = all(s["status"] == "ok" for s in services.values())
    return {"status": "ok" if all_ok else "degraded", "services": services}
