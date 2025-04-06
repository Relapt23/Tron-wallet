from decimal import Decimal

from pydantic import BaseModel


class WalletRequest(BaseModel):
    address: str


class AddressInfo(BaseModel):
    address: str
    balance: Decimal
    energy: int
    bandwidth: int
