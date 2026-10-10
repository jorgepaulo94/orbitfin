from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_transaction_or_404(db: Session, transaction_id: int) -> models.Transaction:
    transaction = db.get(models.Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado")
    return transaction


def ensure_category_exists(db: Session, category_id: int) -> None:
    if db.get(models.Category, category_id) is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")


@router.post("", response_model=schemas.TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(data: schemas.TransactionCreate, db: Session = Depends(get_db)):
    ensure_category_exists(db, data.category_id)
    transaction = models.Transaction(**data.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("", response_model=schemas.TransactionPage)
def list_transactions(
    month: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    category_id: int | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(models.Transaction)

    if month:
        year, mon = map(int, month.split("-"))
        start = date(year, mon, 1)
        end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
        query = query.where(
            models.Transaction.occurred_on >= start,
            models.Transaction.occurred_on < end,
        )
    if category_id is not None:
        query = query.where(models.Transaction.category_id == category_id)

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    items = db.scalars(
        query.order_by(models.Transaction.occurred_on.desc(), models.Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{transaction_id}", response_model=schemas.TransactionOut)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    return get_transaction_or_404(db, transaction_id)


@router.patch("/{transaction_id}", response_model=schemas.TransactionOut)
def update_transaction(
    transaction_id: int, data: schemas.TransactionUpdate, db: Session = Depends(get_db)
):
    transaction = get_transaction_or_404(db, transaction_id)
    changes = data.model_dump(exclude_unset=True)

    if "category_id" in changes:
        ensure_category_exists(db, changes["category_id"])

    for field, value in changes.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = get_transaction_or_404(db, transaction_id)
    db.delete(transaction)
    db.commit()