from decimal import Decimal
from src.core.db.base import Base
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SAEnum, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2),
    )
    currency: Mapped[Currency] = mapped_column(
        SAEnum(Currency, length=3, create_constraint=False),
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    meta_data: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus, length=10, create_constraint=False),
        index=True,
        default=PaymentStatus.PENDING,
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )
    webhook_url: Mapped[str] = mapped_column(
        Text,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
