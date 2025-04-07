from decimal import Decimal
import pytest
from httpx import AsyncClient, ASGITransport
from app.core.models import WalletInfo

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select
from unittest.mock import AsyncMock
from app.tron_service import TronService, get_tron_service, TronAddressInfo
from app.core.db import create_async_engine, Base, get_session
from main import app
from dotenv import load_dotenv

load_dotenv(".env.test")


@pytest.fixture()
async def test_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_sess = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def override_get_session() -> AsyncSession:
        async with test_sess() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    yield test_sess

    await engine.dispose()
    app.dependency_overrides.clear()


@pytest.fixture()
async def client(test_session):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.asyncio
async def test_fetch_address_info(client):
    response = await client.post(
        "/address",
        json={"address": "TR6NmBJLuCXpmK9G75FgbqJE87szz1RTSx"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["address"] == "TR6NmBJLuCXpmK9G75FgbqJE87szz1RTSx"
    assert "energy" in data and isinstance(data["energy"], int)
    assert "balance" in data and isinstance(data["balance"], (int, float, Decimal))
    assert "bandwidth" in data and isinstance(data["bandwidth"], int)


@pytest.mark.asyncio
async def test_record_wallet_info_with_mock(client: AsyncClient, test_session):
    mock_tron_service = AsyncMock(spec=TronService)
    mock_tron_service.get_address_info.return_value = TronAddressInfo(
        address="TR6NmBJLuCXpmK9G75FgbqJE87szz1RTSx",
        balance=Decimal(100),
        energy=50,
        bandwidth=20,
    )
    app.dependency_overrides[get_tron_service] = lambda: mock_tron_service

    response = await client.post(
        "/address", json={"address": "TR6NmBJLuCXpmK9G75FgbqJE87szz1RTSx"}
    )
    assert response.status_code == 200
    data = response.json()

    async with test_session() as session:
        result = await session.execute(
            select(WalletInfo).where(WalletInfo.wallet_address == data["address"])
        )
        wallet = result.scalar_one_or_none()

    assert wallet is not None
    assert wallet.wallet_address == data["address"]
    assert wallet.balance == Decimal(data["balance"])
    assert wallet.energy == data["energy"]
    assert wallet.bandwidth == data["bandwidth"]

    app.dependency_overrides.pop(get_tron_service, None)
