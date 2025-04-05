import os
from dataclasses import dataclass
from decimal import Decimal

from tronpy import Tron
from tronpy.providers import HTTPProvider


def get_tron_service():
    yield TronService()


@dataclass
class TronAddressInfo:
    address: str
    balance: Decimal
    energy: int
    bandwidth: int


class TronService:
    client = Tron(HTTPProvider(
        api_key=os.getenv("API_KEY")
    ))

    def get_address_info(self, address):
        account_info = self.client.get_account(address)
        trx_balance = Decimal(self.client.get_account_balance(address))
        bandwidth = self.client.get_bandwidth(address)
        energy = account_info.get("account_resource", {}).get("energy_usage", 0)
        return TronAddressInfo(address, trx_balance, energy, bandwidth)
