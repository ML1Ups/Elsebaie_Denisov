import asyncio

from resume_classifier.checks import check_component


async def test_check_component_reports_version() -> None:
    async def check() -> str:
        return "1.2.3"

    result = await check_component("service", check, timeout_seconds=1)

    assert result.name == "service"
    assert result.status == "ok"
    assert result.version == "1.2.3"
    assert result.response_time_ms >= 0


async def test_check_component_reports_error_on_exception() -> None:
    async def check() -> str:
        raise ConnectionRefusedError

    result = await check_component("service", check, timeout_seconds=1)

    assert result.status == "error"
    assert result.version is None


async def test_check_component_stops_waiting_after_timeout() -> None:
    async def check() -> str:
        await asyncio.sleep(10)
        return "never"

    result = await check_component("service", check, timeout_seconds=0.05)

    assert result.status == "error"
    assert result.version is None
    assert result.response_time_ms < 1000
