from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..security import DUMMY_HASH, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def invalid_credentials() -> HTTPException:
    # Mesma mensagem para "e-mail não existe" e "senha errada".
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="E-mail ou senha incorretos",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = models.User(email=data.email.lower(), hashed_password=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # O banco garante a unicidade, então não há corrida entre dois cadastros simultâneos.
        db.rollback()
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    # O formulário padrão do OAuth2 chama o campo de "username"; aqui ele recebe o e-mail.
    user = db.scalar(select(models.User).where(models.User.email == form.username.lower()))
    if user is None:
        verify_password(form.password, DUMMY_HASH)
        raise invalid_credentials()
    if not verify_password(form.password, user.hashed_password):
        raise invalid_credentials()
    return schemas.Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=schemas.UserOut)
def read_me(user: Annotated[models.User, Depends(get_current_user)]):
    return user