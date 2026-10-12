from fastapi import FastAPI

from .routers import budgets, categories, reports, transactions

app = FastAPI(title="OrbitFin API", version="0.4.0")

app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(budgets.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

