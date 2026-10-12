from fastapi import FastAPI

from .database import Base, engine
from .routers import budgets, categories, reports, transactions

# Temporário: cria as tabelas automaticamente. Na Etapa 3 trocamos por Alembic.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="OrbitFin API", version="0.3.0")

app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(budgets.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
