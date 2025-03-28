from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.models import TronWallet
from app.schemas import WalletRequest
from app.tron_service import client

router = APIRouter()


@router.post("/address")
async def fetch_address_info(address_request: WalletRequest,
                             session: AsyncSession = Depends(get_session)):
    address = address_request.address
    account_info = client.get_account(address)
    trx_balance = client.get_account_balance(address)
    bandwidth = client.get_bandwidth(address)
    energy = account_info.get("account_resource", {}).get("energy_usage", 0)
    wallet = TronWallet(wallet_address=address, bandwidth=bandwidth, balance=trx_balance, energy=energy)
    session.add(wallet)
    await session.commit()
    return {"address": address,
            "energy": energy,
            "balance": trx_balance,
            "bandwidth": bandwidth}
