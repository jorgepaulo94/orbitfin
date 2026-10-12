from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models
from .reports import month_range

WARNING_PERCENT = 80


def classify(spent_cents: int, limit_cents: int) -> str:
    """'over' só quando passa do limite; 80% ou mais já é 'warning'."""
    if spent_cents > limit_cents:
        return "over"
    if spent_cents * 100 >= limit_cents * WARNING_PERCENT:
        return "warning"
    return "ok"


def budget_status(db: Session, month: str) -> list[dict]:
    start, end = month_range(month)

    # Quanto foi gasto em cada categoria no mês (só despesas)
    spent_by_category = {
        category_id: total
        for category_id, total in db.execute(
            select(models.Transaction.category_id, func.sum(models.Transaction.amount_cents))
            .where(
                models.Transaction.type == "expense",
                models.Transaction.occurred_on >= start,
                models.Transaction.occurred_on < end,
            )
            .group_by(models.Transaction.category_id)
        ).all()
    }

    rows = db.execute(
        select(models.Budget, models.Category.name)
        .select_from(models.Budget)
        .join(models.Category, models.Category.id == models.Budget.category_id)
        .order_by(models.Category.name)
    ).all()

    result = []
    for budget, category_name in rows:
        spent = spent_by_category.get(budget.category_id, 0)
        result.append(
            {
                "category_id": budget.category_id,
                "category": category_name,
                "limit_cents": budget.limit_cents,
                "spent_cents": spent,
                "remaining_cents": budget.limit_cents - spent,
                "percent_used": spent * 100 // budget.limit_cents,
                "status": classify(spent, budget.limit_cents),
            }
        )
    return result
 