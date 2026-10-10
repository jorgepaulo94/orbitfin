from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(data: schemas.CategoryCreate, db: Session = Depends(get_db)):
    exists = db.scalar(select(models.Category).where(models.Category.name == data.name))
    if exists:
        raise HTTPException(status_code=409, detail="Categoria já existe")

    category = models.Category(name=data.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("", response_model=list[schemas.CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.scalars(select(models.Category).order_by(models.Category.name)).all()