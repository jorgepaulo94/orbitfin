from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services import reports

router = APIRouter(prefix="/reports", tags=["reports"])

Month = Annotated[
    str,
    Query(pattern=r"^[12]\d{3}-(0[1-9]|1[0-2])$", description="Formato AAAA-MM, ex.: 2026-10"),
]


@router.get("/monthly", response_model=schemas.MonthlySummary)
def monthly_report(month: Month, db: Session = Depends(get_db)):
    return reports.monthly_summary(db, month)


@router.get("/monthly.csv")
def monthly_csv(month: Month, db: Session = Depends(get_db)):
    # O "\ufeff" no início faz o Excel mostrar os acentos corretamente.
    content = "\ufeff" + reports.transactions_to_csv(db, month)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="orbitfin-{month}.csv"'},
    )