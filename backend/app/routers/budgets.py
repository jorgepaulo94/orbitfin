from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import budgets
from .reports import Month

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.put("/{category_id}", response_model=schemas.BudgetOut)
def set_budget(category_id: int, data: schemas.BudgetSet, db: Session = Depends(get_db)):
    if db.get(models.Category, category_id) is None:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")

    budget = db.scalar(select(models.Budget).where(models.Budget.category_id == category_id))
    if budget is None:
        budget = models.Budget(category_id=category_id, limit_cents=data.limit_cents)
        db.add(budget)
    else:
        budget.limit_cents = data.limit_cents

    db.commit()
    db.refresh(budget)
    return budget


@router.get("", response_model=list[schemas.BudgetOut])
def list_budgets(db: Session = Depends(get_db)):
    return db.scalars(select(models.Budget).order_by(models.Budget.category_id)).all()


@router.get("/status", response_model=list[schemas.BudgetStatus])
def budgets_status(month: Month, db: Session = Depends(get_db)):
    return budgets.budget_status(db, month)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(category_id: int, db: Session = Depends(get_db)):
    budget = db.scalar(select(models.Budget).where(models.Budget.category_id == category_id))
    if budget is None:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado")
    db.delete(budget)
    db.commit()
    