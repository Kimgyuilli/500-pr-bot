import asyncio

from fastapi import FastAPI

from error_handler import ErrorReport, process_error

app = FastAPI(title="500 Error Auto-Fix Bot")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/error")
async def receive_error(report: ErrorReport):
    asyncio.create_task(process_error(report))
    return {"status": "received"}
