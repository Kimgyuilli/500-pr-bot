import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.routers import admin, errors, health, webhook

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="500 Error Auto-Fix Bot")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(errors.router)
app.include_router(admin.router)


@app.get("/")
async def dashboard():
    return FileResponse(str(STATIC_DIR / "index.html"))
