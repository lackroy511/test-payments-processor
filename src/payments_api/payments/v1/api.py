from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header

from src.payments_api.payments.v1.schemas import (
    CreatePaymentRequest,
    CreatePaymentResponse,
    PaymentResponse,
)
from src.payments_api.payments.v1.service import (
    PaymentService,
    get_payment_service,
)

router = APIRouter(prefix="/v1/payments", tags=["Payments"])


@router.post("/", status_code=202, response_model=CreatePaymentResponse)
async def create_payment(
    body: CreatePaymentRequest,
    idempotency_key: Annotated[str, Header()],
    service: Annotated[PaymentService, Depends(get_payment_service)],
) -> CreatePaymentResponse:
    payment = await service.create_payment(
        amount=body.amount,
        currency=body.currency,
        idempotency_key=idempotency_key,
        webhook_url=body.webhook_url,
        description=body.description,
        meta_data=body.meta_data,
    )
    return CreatePaymentResponse(
        payment_id=payment.id,
        status=payment.status,
        created_at=payment.created_at,
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    service: Annotated[PaymentService, Depends(get_payment_service)],
) -> PaymentResponse:
    payment = await service.get_payment(payment_id)
    return PaymentResponse(
        id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        description=payment.description,
        meta_data=payment.meta_data,
        status=payment.status,
        idempotency_key=payment.idempotency_key,
        webhook_url=payment.webhook_url,
        created_at=payment.created_at,
        processed_at=payment.processed_at,
    )
