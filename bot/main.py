from fastapi import FastAPI

app = FastAPI(title="500 Error Auto-Fix Bot")


@app.get("/health")
async def health():
    return {"status": "ok"}
