from collections.abc import Callable
from typing import TypeVar

from fastapi import HTTPException, status

from app.exceptions.domain import DomainConflictError, DomainNotFoundError

T = TypeVar("T")


def require_found(value: T | None, message: str) -> T:
    if value is None:
        raise DomainNotFoundError(message)
    return value


def call_domain(operation: Callable[[], T]) -> T:
    try:
        return operation()
    except DomainNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except DomainConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
