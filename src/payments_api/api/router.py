from fastapi import APIRouter

from src.payments_api.payments.v1.api import router as v1_payments_router

router = APIRouter(prefix="/api")
router.include_router(v1_payments_router)