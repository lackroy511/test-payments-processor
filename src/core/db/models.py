from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db.base import Base


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class Payment(Base):
    __tablename__ = "payments"

    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=14, scale=2),
    )
    currency: Mapped[Currency] = mapped_column(
        SAEnum(Currency),
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    meta_data: Mapped[dict | None] = mapped_column(
        JSONB,
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(PaymentStatus),
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


class OutboxMessageStatus(str, Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"


class OutboxMessageType(str, Enum):
    PAYMENT_CREATED = "PAYMENT_CREATED"


class OutboxMessage(Base):
    __tablename__ = "outbox_messages"

    event_type: Mapped[OutboxMessageType] = mapped_column(
        SAEnum(OutboxMessageType),
        index=True,
        default=OutboxMessageType.PAYMENT_CREATED,
    )
    status: Mapped[OutboxMessageStatus] = mapped_column(
        SAEnum(OutboxMessageStatus),
        index=True,
        default=OutboxMessageStatus.PENDING,
    )
    payload: Mapped[dict] = mapped_column(
        JSONB,
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
