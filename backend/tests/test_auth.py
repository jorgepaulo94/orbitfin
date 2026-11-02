from datetime import UTC, datetime, timedelta

import jwt

from app.config import settings
from app.security import hash_password, verify_password


def register(client, email="ana@example.com", password="senha-forte-123"):
    return client.post("/auth/register", json={"email": email, "password": password})


def login(client, email="ana@example.com", password="senha-forte-123"):
    return client.post("/auth/login", data={"username": email, "password": password})


def test_registro_cria_usuario_sem_expor_a_senha(client):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert "password" not in body
    assert "hashed_password" not in body


def test_email_duplicado_retorna_409_ignorando_maiusculas(client):
    assert register(client).status_code == 201
    assert register(client, email="ANA@example.com").status_code == 409


def test_registro_rejeita_dados_invalidos(client):
    assert register(client, password="1234567").status_code == 422  # curta demais
    assert register(client, email="nao-e-um-email").status_code == 422
    assert register(client, password="x" * 129).status_code == 422  # longa demais


def test_login_retorna_token_e_me_identifica_o_usuario(client):
    register(client)

    response = login(client, email="ANA@Example.com")  # e-mail não diferencia maiúsculas
    assert response.status_code == 200
    token = response.json()
    assert token["token_type"] == "bearer"

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ana@example.com"


def test_login_rejeita_credenciais_erradas(client):
    register(client)

    senha_errada = login(client, password="outra-senha-123")
    email_inexistente = login(client, email="outra@example.com")

    assert senha_errada.status_code == 401
    assert email_inexistente.status_code == 401
    # Mesma resposta nos dois casos: não revela se o e-mail existe
    assert senha_errada.json() == email_inexistente.json()


def test_me_exige_token_valido(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer lixo"}).status_code == 401


def test_token_expirado_e_rejeitado(client):
    user_id = register(client).json()["id"]
    expirado = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm="HS256",
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expirado}"})

    assert response.status_code == 401


def test_token_com_assinatura_falsa_e_rejeitado(client):
    user_id = register(client).json()["id"]
    falso = jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        "outra-chave-qualquer-com-mais-de-32-caracteres",
        algorithm="HS256",
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {falso}"})

    assert response.status_code == 401


def test_hash_de_senha_nao_guarda_texto_puro():
    hashed = hash_password("senha-forte-123")

    assert hashed != "senha-forte-123"
    assert verify_password("senha-forte-123", hashed)
    assert not verify_password("outra-senha-123", hashed)

    