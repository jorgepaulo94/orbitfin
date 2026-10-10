from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50)


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TransactionCreate(BaseModel):
    type: Literal["income", "expense"]
    amount_cents: int = Field(gt=0)
    description: str = Field(min_length=1, max_length=200)
    occurred_on: date
    category_id: int


class TransactionUpdate(BaseModel):
    type: Literal["income", "expense"] | None = None
    amount_cents: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, min_length=1, max_length=200)
    occurred_on: date | None = None
    category_id: int | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    amount_cents: int
    description: str
    occurred_on: date
    category_id: int


class TransactionPage(BaseModel):
    items: list[TransactionOut]
    total: int
    page: int
    page_size: int

    

class CategoryTotal(BaseModel):
    category_id: int
    category: str
    total_cents: int


class MonthlySummary(BaseModel):
    month: str
    income_cents: int
    expense_cents: int
    balance_cents: int
    by_category: list[CategoryTotal]
    biggest_expense: TransactionOut | None
    