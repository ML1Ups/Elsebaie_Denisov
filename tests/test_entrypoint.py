from typing import Any

import pytest
from fastapi import FastAPI

from resume_classifier import __main__ as entrypoint
from resume_classifier.config import get_settings


@pytest.mark.usefixtures("restore_logging")
def test_main_runs_uvicorn_with_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[Any, dict[str, Any]]] = []
    monkeypatch.setattr(
        entrypoint.uvicorn,
        "run",
        lambda app, **kwargs: calls.append((app, kwargs)),
    )

    entrypoint.main()

    settings = get_settings()
    [(app, kwargs)] = calls
    assert isinstance(app, FastAPI)
    assert kwargs == {
        "host": settings.app_host,
        "port": settings.app_port,
        "log_config": None,
        "access_log": False,
    }
