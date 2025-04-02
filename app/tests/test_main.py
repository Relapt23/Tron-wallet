from decimal import Decimal

from dotenv import load_dotenv

from app.core.models import WalletInfo

load_dotenv(".env.test")

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, delete
from unittest.mock import AsyncMock
from app.tron_service import TronService, get_tron_service, TronAddressInfo
from app.core.db import create_async_engine, Base, get_session
from main import app


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


@pytest.mark.asyncio
async def test_record_wallet_info_with_mock(client: AsyncClient, run_before_and_after_tests, test_engine):
    async_session_maker = async_sessionmaker(bind=test_engine, expire_on_commit=False, autocommit=False,
                                             autoflush=False)

    async with async_session_maker() as session:
        await session.execute(delete(WalletInfo))
        await session.commit()

    mock_tron_service = AsyncMock(spec=TronService)
    mock_tron_service.get_address_info.return_value = TronAddressInfo(
        address="TR6NmBJLuCXpmK9G75FgbqJE87szz1RTSx",
        balance=Decimal(100),
        energy=50,
        bandwidth=20
    )

    app.dependency_overrides[get_tron_service] = lambda: mock_tron_service

    address_request = {"address": "TR6NmBJLuCXpmK9G75FgbqJE87szz1RTSx"}

    response = await client.post("/address", json=address_request)

    assert response.status_code == 200
    data = response.json()

    async with async_session_maker() as session:
        result = await session.execute(select(WalletInfo).where(WalletInfo.wallet_address == data["address"]))
        wallet = result.scalar_one_or_none()

    assert wallet is not None
    assert wallet.wallet_address == data["address"]
    assert wallet.balance == Decimal(data["balance"])
    assert wallet.energy == data["energy"]
    assert wallet.bandwidth == data["bandwidth"]

    app.dependency_overrides.pop(get_tron_service)
