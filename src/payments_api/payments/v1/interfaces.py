from abc import ABC, abstractmethod
from typing import Self
from uuid import UUID

from src.payments_api.payments.v1.dto import (
    OutboxMessageCreateDTO,
    OutboxMessageResponseDTO,
    PaymentCreateDTO,
    PaymentResponseDTO,
)


class PaymentRepoInterface(ABC):
    @abstractmethod
    async def get_or_create(
        self,
        dto: PaymentCreateDTO,
    ) -> tuple[PaymentResponseDTO, bool]: ...

    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> PaymentResponseDTO: ...


class OutboxMessageRepoInterface(ABC):
    @abstractmethod
    async def create(
        self,
        dto: OutboxMessageCreateDTO,
    ) -> OutboxMessageResponseDTO: ...


class PaymentsUnitOfWorkInterface(ABC):
    payment_repo: PaymentRepoInterface
    outbox_repo: OutboxMessageRepoInterface

    @abstractmethod
    async def __aenter__(
        self,
    ) -> Self: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None: ...

    @abstractmethod
    async def commit(
        self,
    ) -> None: ...

    @abstractmethod
    async def rollback(
        self,
    ) -> None: ...
