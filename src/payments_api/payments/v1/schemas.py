from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.core.db.models import Currency, PaymentStatus


class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    currency: Currency
    description: str | None = None
    meta_data: dict | None = None
    webhook_url: str


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: str | None
    amount: Decimal
    currency: Currency
    description: str | None
    meta_data: dict | None
    status: PaymentStatus
    idempotency_key: str
    webhook_url: HttpUrl
    is_webhook_sent: bool
    created_at: datetime
    is_processed: bool
    processed_at: datetime | None


class CreatePaymentResponse(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime
