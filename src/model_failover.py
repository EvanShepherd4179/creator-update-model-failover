from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


class AllModelsFailed(RuntimeError):
    """Raised when neither configured model can process a request."""


def with_failover(primary: Callable[[], T], backup: Callable[[], T]) -> T:
    try:
        return primary()
    except Exception as first_error:
        try:
            return backup()
        except Exception as second_error:
            raise AllModelsFailed("content processing failed on both models") from second_error

