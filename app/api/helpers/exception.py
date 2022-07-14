import http
from http.client import BAD_REQUEST


class IntegrityException(Exception):
    pass


class RelatedIntegrityError(Exception):
    pass


class DomainException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.error_code = "no_code"


class CouponAlreadyConfirmed(DomainException):
    def __init__(self, message="coupon already confirmed."):
        super().__init__(message)
        self.error_code = "coupon_already_confirmed"


class MaxUsageException(DomainException):
    def __init__(self, message="Max usage was reached."):
        super().__init__(message)
        self.error_code = "max_usage_reached"


class LimitPerCustomerException(DomainException):
    def __init__(self, message="Limit per customer was reached."):
        super().__init__(message)
        self.error_code = "limit_per_customer_reached"


class ExceedBudgetLimitException(DomainException):
    def __init__(self, message="Discount amount exceed the budget limit."):
        super().__init__(message)
        self.error_code = "exceed_budget_limit"


class MinPurchaseAmountException(DomainException):
    def __init__(
        self, message="Min purchase amount is bigger than purchase amout."
    ):
        super().__init__(message)
        self.error_code = "min_purchase_amount_error"


class FirstPurchaseException(DomainException):
    def __init__(
        self, message="Only first purchase users can use this coupon."
    ):
        super().__init__(message)
        self.error_code = "first_purchase_error"


class FileNotFoundException(DomainException):
    def __init__(self, message="File not found."):
        super().__init__(message)
        self.error_code = "file_not_found"


class TransactionIdException(DomainException):
    def __init__(
        self, message="Already exist a reserve with this transaction id."
    ):
        super().__init__(message)
        self.error_code = "transaction_id_error"


class HTTPError(Exception):
    def __init__(
        self,
        status_code: int = None,
        error_message: str = None,
        error_code: str = None,
    ) -> None:
        if status_code is None:
            status_code = BAD_REQUEST
        if error_message is None:
            error_message = http.HTTPStatus(status_code).phrase
        if error_code is None:
            error_code = http.HTTPStatus(  # pylint: disable=E1101
                status_code,
            ).name.lower()
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return (
            f"{class_name}(status_code={self.status_code!r},"
            f"error_code={self.error_code!r},"
            f"error_message={self.error_message!r})"
        )
