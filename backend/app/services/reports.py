import csv
import io
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models


def month_range(month: str) -> tuple[date, date]:
    """Converte '2026-10' em (1º dia do mês, 1º dia do mês seguinte)."""
    year, mon = map(int, month.split("-"))
    start = date(year, mon, 1)
    end = date(year + 1, 1, 1) if mon == 12 else date(year, mon + 1, 1)
    return start, end


def monthly_summary(db: Session, month: str) -> dict:
    start, end = month_range(month)
    in_month = (
        models.Transaction.occurred_on >= start,
        models.Transaction.occurred_on < end,
    )

    # Total de receitas e de despesas do mês
    totals = {
        kind: total
        for kind, total in db.execute(
            select(
                models.Transaction.type,
                func.coalesce(func.sum(models.Transaction.amount_cents), 0),
            )
            .where(*in_month)
            .group_by(models.Transaction.type)
        ).all()
    }
    income = totals.get("income", 0)
    expense = totals.get("expense", 0)

    # Despesas por categoria, da maior para a menor
    by_category = [
        {"category_id": category_id, "category": name, "total_cents": total}
        for category_id, name, total in db.execute(
            select(
                models.Category.id,
                models.Category.name,
                func.sum(models.Transaction.amount_cents),
            )
            .select_from(models.Category)
            .join(models.Transaction, models.Transaction.category_id == models.Category.id)
            .where(*in_month, models.Transaction.type == "expense")
            .group_by(models.Category.id, models.Category.name)
            .order_by(func.sum(models.Transaction.amount_cents).desc())
        ).all()
    ]

    # Maior despesa individual do mês
    biggest_expense = db.scalars(
        select(models.Transaction)
        .where(*in_month, models.Transaction.type == "expense")
        .order_by(models.Transaction.amount_cents.desc(), models.Transaction.id)
        .limit(1)
    ).first()

    return {
        "month": month,
        "income_cents": income,
        "expense_cents": expense,
        "balance_cents": income - expense,
        "by_category": by_category,
        "biggest_expense": biggest_expense,
    }


def format_cents(cents: int) -> str:
    """4590 -> '45.90'. Só inteiros, sem números decimais."""
    return f"{cents // 100}.{cents % 100:02d}"


def safe_cell(text: str) -> str:
    """Evita 'injeção de fórmula': o Excel executa células que começam com = + - @."""
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def transactions_to_csv(db: Session, month: str) -> str:
    start, end = month_range(month)
    rows = db.execute(
        select(models.Transaction, models.Category.name)
        .select_from(models.Transaction)
        .join(models.Category, models.Category.id == models.Transaction.category_id)
        .where(
            models.Transaction.occurred_on >= start,
            models.Transaction.occurred_on < end,
        )
        .order_by(models.Transaction.occurred_on, models.Transaction.id)
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "data", "tipo", "categoria", "descricao", "valor"])
    for transaction, category_name in rows:
        writer.writerow(
            [
                transaction.id,
                transaction.occurred_on.isoformat(),
                transaction.type,
                safe_cell(category_name),
                safe_cell(transaction.description),
                format_cents(transaction.amount_cents),
            ]
        )
    return buffer.getvalue()
