from decimal import Decimal

from dotenv import load_dotenv

load_dotenv(".env.test")

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.db import create_async_engine, Base, get_session
from main import app

load_dotenv(".env.test")


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def run_before_and_after_tests(test_engine):
    async_sess = async_sessionmaker(bind=test_engine, expire_on_commit=False, autocommit=False, autoflush=False)

    async def get_session_override():
        async with async_sess() as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    yield


@pytest.fixture
async def client(run_before_and_after_tests):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_fetch_address_info(client):
    response = await client.post("/address",
                                 json={"address": "TR6NmBJLuCXpmK9G75FgbqJE87szz1RTSx"},
                                 )
    assert response.status_code == 200
    data = response.json()
    assert data["address"] == "TR6NmBJLuCXpmK9G75FgbqJE87szz1RTSx"
    assert "energy" in data and isinstance(data["energy"], int)
    assert "balance" in data and isinstance(data["balance"], (int, float, Decimal))
    assert "bandwidth" in data and isinstance(data["bandwidth"], int)
