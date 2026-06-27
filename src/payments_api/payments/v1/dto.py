from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from src.core.db.models import (
    Currency,
    OutboxMessageStatus,
    OutboxMessageType,
    PaymentStatus,
)


@dataclass(frozen=True)
class PaymentCreateDTO:
    amount: Decimal
    currency: Currency
    idempotency_key: str
    webhook_url: str
    description: str | None = None
    meta_data: dict | None = None


@dataclass(frozen=True)
class PaymentResponseDTO:
    id: UUID
    external_id: str | None
    amount: Decimal
    currency: Currency
    description: str | None
    meta_data: dict | None
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    is_webhook_sent: bool
    created_at: datetime
    is_processed: bool
    processed_at: datetime | None


@dataclass(frozen=True)
class OutboxMessageCreateDTO:
    event_type: OutboxMessageType
    payload: OutboxMessagePayloadDTO


@dataclass(frozen=True)
class OutboxMessagePayloadDTO:
    payment_id: str


@dataclass(frozen=True)
class OutboxMessageResponseDTO:
    id: UUID
    event_type: OutboxMessageType
    status: OutboxMessageStatus
    payload: dict
    created_at: datetime
    processed_at: datetime | None
