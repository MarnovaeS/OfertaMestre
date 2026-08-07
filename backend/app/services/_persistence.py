from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions.domain import DomainConflictError


def commit_refresh(db: Session, instance: object) -> object:
    try:
        db.add(instance)
        db.commit()
        db.refresh(instance)
    except IntegrityError as exc:
        db.rollback()
        raise DomainConflictError() from exc
    return instance


def commit_delete(db: Session, instance: object) -> None:
    try:
        db.delete(instance)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DomainConflictError("Resource has related records") from exc
