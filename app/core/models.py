from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WalletInfo(Base):
    __tablename__ = "wallet_info"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    wallet_address: Mapped[str] = mapped_column(nullable=False)
    bandwidth: Mapped[int]
    energy: Mapped[int]
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
