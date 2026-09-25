import json
import logging

import pytest
import structlog
from httpx import AsyncClient
from structlog.testing import capture_logs

from resume_classifier.logs import configure_logging


async def test_response_has_generated_request_id(client: AsyncClient) -> None:
    response = await client.get("/healthz")

    assert len(response.headers["X-Request-ID"]) == 32


async def test_request_id_is_taken_from_request(client: AsyncClient) -> None:
    response = await client.get("/healthz", headers={"X-Request-ID": "test-request"})

    assert response.headers["X-Request-ID"] == "test-request"


async def test_request_is_logged(client: AsyncClient) -> None:
    with capture_logs() as logs:
        await client.get("/healthz")

    [entry] = [log for log in logs if log["event"] == "request_finished"]
    assert entry["method"] == "GET"
    assert entry["path"] == "/healthz"
    assert entry["status_code"] == 200
    assert entry["duration_ms"] >= 0


@pytest.mark.usefixtures("restore_logging")
def test_json_logs_include_structlog_and_stdlib_records(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO", json_logs=True)

    structlog.get_logger("test").info("structlog_event", key="value")
    logging.getLogger("uvicorn.error").warning("stdlib event")

    first, second = (json.loads(line) for line in capsys.readouterr().out.splitlines())
    assert first["event"] == "structlog_event"
    assert first["key"] == "value"
    assert first["level"] == "info"
    assert first["logger"] == "test"
    assert "timestamp" in first
    assert second["event"] == "stdlib event"
    assert second["level"] == "warning"
    assert second["logger"] == "uvicorn.error"


@pytest.mark.usefixtures("restore_logging")
def test_logs_below_level_are_dropped(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("WARNING", json_logs=True)

    structlog.get_logger("test").info("hidden_event")

    assert capsys.readouterr().out == ""


@pytest.mark.usefixtures("restore_logging")
def test_console_logs_are_human_readable(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", json_logs=False)

    structlog.get_logger("test").info("console_event")

    assert "console_event" in capsys.readouterr().out
