from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
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
    wallet = TronWallet(wallet_address=address,
                        bandwidth=bandwidth,
                        balance=trx_balance,
                        energy=energy
                        )
    session.add(wallet)
    await session.commit()
    return {"address": address,
            "energy": energy,
            "balance": trx_balance,
            "bandwidth": bandwidth
            }


@router.get("/items")
async def get_wallet_list(session: AsyncSession = Depends(get_session),
                          cursor: int | None = Query(None, ge=1),
                          limit: int = Query(20, ge=0)):
    query = await session.execute(select(TronWallet.id).where(TronWallet.id == cursor))
    result = query.scalar_one_or_none()
    if not result:
        raise HTTPException(detail="cursor_not_found", status_code=404)

    query = select(TronWallet).limit(limit + 1).order_by(TronWallet.id.desc())
    if cursor:
        query = query.where(TronWallet.id <= cursor)

    result = await session.execute(query)
    items = result.scalars().all()
    if len(items) == limit + 1:
        return {"items": items[:-1],
                "next_cursor": items[-1].id}
    else:
        return {"items": items,
                "next_cursor": None}
