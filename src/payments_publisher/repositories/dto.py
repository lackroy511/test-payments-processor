from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.core.db.models import OutboxMessageStatus, OutboxMessageType


class OutboxMessageDTO(BaseModel):
    id: UUID
    event_type: OutboxMessageType
    status: OutboxMessageStatus
    payload: dict
    created_at: datetime
    processed_at: datetime | None
