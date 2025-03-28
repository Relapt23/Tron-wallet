from pydantic import BaseModel


class WalletRequest(BaseModel):
    address: str
