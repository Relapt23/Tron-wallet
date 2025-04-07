from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.models import WalletInfo
from app.schemas import WalletRequest, AddressInfo
from app.tron_service import TronService, get_tron_service

router = APIRouter()


@router.post("/address", response_model=AddressInfo)
async def fetch_address_info(
    address_request: WalletRequest,
    session: AsyncSession = Depends(get_session),
    tron_service: TronService = Depends(get_tron_service),
) -> dict:
    address = address_request.address
    info = tron_service.get_address_info(address)

    address_info = AddressInfo(
        address=address,
        balance=info.balance,
        bandwidth=info.bandwidth,
        energy=info.energy,
    )
    wallet = WalletInfo(
        wallet_address=address,
        bandwidth=address_info.bandwidth,
        balance=address_info.balance,
        energy=address_info.energy,
    )
    session.add(wallet)

    await session.commit()

    return address_info


@router.get("/items")
async def get_wallet_list(
    session: AsyncSession = Depends(get_session),
    cursor: int | None = Query(None, ge=1),
    limit: int = Query(20, ge=0),
):
    query = await session.execute(select(WalletInfo.id).where(WalletInfo.id == cursor))
    result = query.scalar_one_or_none()

    if not result:
        raise HTTPException(detail="cursor_not_found", status_code=404)

    query = select(WalletInfo).limit(limit + 1).order_by(WalletInfo.id.desc())
    if cursor:
        query = query.where(WalletInfo.id <= cursor)

    result = await session.execute(query)
    items = result.scalars().all()

    if len(items) == limit + 1:
        return {"items": items[:-1], "next_cursor": items[-1].id}

    else:
        return {"items": items, "next_cursor": None}
