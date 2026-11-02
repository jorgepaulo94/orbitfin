from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from .config import settings

ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()

# Hash de uma senha qualquer. No login, se o e-mail não existe, conferimos a senha
# contra ele só para gastar o mesmo tempo e não revelar quais e-mails existem.
DUMMY_HASH = password_hash.hash("senha-falsa-para-igualar-o-tempo")


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Devolve o id do usuário, ou None se o token for inválido ou estiver expirado."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None

    