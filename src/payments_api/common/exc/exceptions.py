class BaseAppError(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        self.message = message
        self.status_code = status_code


class PaymentNotFoundError(BaseAppError):
    def __init__(
        self,
        message: str = "Payment not found",
    ) -> None:
        super().__init__(message, 404)
