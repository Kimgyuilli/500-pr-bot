import asyncio
import re
from typing import AsyncGenerator

_running = False

_RESULT_RE = re.compile(
    r"^(tests/\S+\.py)::(\S+)\s+(PASSED|FAILED|ERROR)",
)


def _parse_test_line(line: str) -> dict | None:
    m = _RESULT_RE.match(line)
    if not m:
        return None
    return {
        "file": m.group(1),
        "name": m.group(2),
        "status": m.group(3).lower(),
    }


async def run_tests() -> AsyncGenerator[dict, None]:
    global _running
    if _running:
        yield {"type": "error", "message": "테스트가 이미 실행 중입니다."}
        return
    _running = True
    try:
        proc = await asyncio.create_subprocess_exec(
            "python", "-m", "pytest", "tests/", "-v", "--tb=short", "--no-header",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        results = []
        async for raw in proc.stdout:
            text = raw.decode().rstrip()
            yield {"type": "log", "line": text}
            parsed = _parse_test_line(text)
            if parsed:
                results.append(parsed)
                yield {"type": "result", **parsed}

        await proc.wait()
        yield {
            "type": "summary",
            "total": len(results),
            "passed": sum(1 for r in results if r["status"] == "passed"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "error": sum(1 for r in results if r["status"] == "error"),
            "returncode": proc.returncode,
        }
    finally:
        _running = False
