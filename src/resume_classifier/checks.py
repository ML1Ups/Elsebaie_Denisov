import asyncio
import time
from collections.abc import Awaitable, Callable

import asyncpg
import structlog

from resume_classifier.db import fetch_postgres_version
from resume_classifier.schemas import ComponentHealth, HealthResponse, Status

logger = structlog.get_logger(__name__)


async def check_component(
    name: str,
    check: Callable[[], Awaitable[str]],
    timeout_seconds: float,
) -> ComponentHealth:
    started = time.perf_counter()
    status: Status
    try:
        async with asyncio.timeout(timeout_seconds):
            version = await check()
    except Exception as exc:
        logger.warning("health_check_failed", component=name, error=repr(exc))
        status, version = "error", None
    else:
        status = "ok"
    response_time_ms = round((time.perf_counter() - started) * 1000, 2)
    return ComponentHealth(
        name=name,
        status=status,
        version=version,
        response_time_ms=response_time_ms,
    )


async def collect_health(pool: asyncpg.Pool, timeout_seconds: float) -> HealthResponse:
    components = [
        await check_component("postgres", lambda: fetch_postgres_version(pool), timeout_seconds),
    ]
    status: Status = "ok" if all(c.status == "ok" for c in components) else "error"
    return HealthResponse(status=status, components=components)
