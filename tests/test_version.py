import tomllib
from pathlib import Path

from httpx import AsyncClient

PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


async def test_version_matches_pyproject(client: AsyncClient) -> None:
    expected = tomllib.loads(PYPROJECT.read_text())["project"]["version"]

    response = await client.get("/api/v1/version")

    assert response.status_code == 200
    assert response.json() == {"version": expected}


async def test_version_is_not_served_without_api_prefix(client: AsyncClient) -> None:
    response = await client.get("/version")

    assert response.status_code == 404
