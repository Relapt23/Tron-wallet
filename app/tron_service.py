import os

from tronpy import Tron
from tronpy.providers import HTTPProvider

provider = HTTPProvider(api_key=os.getenv("APY_KEY"))

client = Tron(provider)
