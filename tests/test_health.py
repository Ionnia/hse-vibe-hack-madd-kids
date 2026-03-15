import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(api_client: AsyncClient):
    response = await api_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_ready_endpoint(api_client: AsyncClient):
    response = await api_client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
