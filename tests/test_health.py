from httpx import AsyncClient


async def test_health_reports_postgres_version_and_response_time(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    [postgres] = body["components"]
    assert postgres["name"] == "postgres"
    assert postgres["status"] == "ok"
    assert postgres["version"]
    assert postgres["response_time_ms"] >= 0


async def test_health_returns_503_when_database_unavailable(
    unreachable_client: AsyncClient,
) -> None:
    response = await unreachable_client.get("/api/v1/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    [postgres] = body["components"]
    assert postgres["name"] == "postgres"
    assert postgres["status"] == "error"
    assert postgres["version"] is None
