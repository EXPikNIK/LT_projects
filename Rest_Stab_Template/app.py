"""Simple REST stub for load testing."""

from __future__ import annotations

import random
import time
from typing import Any, Dict

from fastapi import FastAPI, Header, HTTPException, Request, Response
from pydantic import BaseModel

app = FastAPI(title="Load Test Stub", version="0.1.0")


class EchoBody(BaseModel):
    message: str
    payload: Dict[str, Any] | None = None


class StatusBody(BaseModel):
    status: int
    delay_ms: int | None = None
    body: Dict[str, Any] | None = None


class RandomBody(BaseModel):
    min_ms: int = 0
    max_ms: int = 1000
    statuses: list[int] = [200, 201, 202, 400, 401, 403, 404, 409, 429, 500]


METRICS = {
    "requests": 0,
    "errors": 0,
    "total_ms": 0.0,
}


def _sleep_ms(delay_ms: int) -> None:
    if delay_ms <= 0:
        return
    time.sleep(delay_ms / 1000.0)


@app.middleware("http")
async def track_metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000.0
    METRICS["requests"] += 1
    METRICS["total_ms"] += elapsed
    if response.status_code >= 400:
        METRICS["errors"] += 1
    return response


@app.get("/health")
def health():
    return {"ok": True, "service": "stub"}


@app.get("/metrics")
def metrics():
    avg_ms = 0.0
    if METRICS["requests"]:
        avg_ms = METRICS["total_ms"] / METRICS["requests"]
    return {
        "requests": METRICS["requests"],
        "errors": METRICS["errors"],
        "avg_ms": round(avg_ms, 3),
    }


@app.post("/echo")
def echo(body: EchoBody, x_delay_ms: int | None = Header(default=None)):
    delay_ms = int(x_delay_ms) if x_delay_ms is not None else 0
    _sleep_ms(delay_ms)
    return {"message": body.message, "payload": body.payload, "delay_ms": delay_ms}


@app.post("/status")
def status(body: StatusBody):
    delay_ms = int(body.delay_ms or 0)
    _sleep_ms(delay_ms)
    if body.status < 100 or body.status > 599:
        raise HTTPException(status_code=400, detail="Invalid status code")
    return Response(
        status_code=body.status,
        content=None if body.body is None else str(body.body),
        media_type="application/json" if body.body is not None else None,
    )


@app.post("/random")
def random_response(body: RandomBody):
    if body.min_ms < 0 or body.max_ms < body.min_ms:
        raise HTTPException(status_code=400, detail="Invalid delay range")
    delay_ms = random.randint(body.min_ms, body.max_ms)
    _sleep_ms(delay_ms)
    status_code = random.choice(body.statuses)
    return Response(status_code=status_code)


@app.get("/params")
def params(delay_ms: int = 0, size: int = 0):
    _sleep_ms(delay_ms)
    payload = "x" * max(0, size)
    return {"delay_ms": delay_ms, "size": size, "payload": payload}
