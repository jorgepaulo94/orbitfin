from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(10))  # "income" ou "expense"
    amount_cents: Mapped[int]
    description: Mapped[str] = mapped_column(String(200))
    occurred_on: Mapped[date]
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    category: Mapped[Category] = relationship(back_populates="transactions")

    

class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), unique=True)
    limit_cents: Mapped[int]

    category: Mapped[Category] = relationship()

    