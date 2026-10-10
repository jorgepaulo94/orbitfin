def create_category(client, name):
    response = client.post("/categories", json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def create_transaction(client, category_id, kind, cents, day, description="teste"):
    response = client.post(
        "/transactions",
        json={
            "type": kind,
            "amount_cents": cents,
            "description": description,
            "occurred_on": day,
            "category_id": category_id,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_resumo_calcula_saldo_e_categorias(client):
    mercado = create_category(client, "Mercado")
    lazer = create_category(client, "Lazer")
    salario = create_category(client, "Salário")

    create_transaction(client, salario, "income", 500000, "2026-10-05")
    create_transaction(client, mercado, "expense", 20000, "2026-10-06")
    create_transaction(client, mercado, "expense", 10050, "2026-10-12")
    create_transaction(client, lazer, "expense", 15000, "2026-10-20")
    # Fora do mês: não podem entrar na conta
    create_transaction(client, lazer, "expense", 99999, "2026-09-30")
    create_transaction(client, lazer, "expense", 99999, "2026-11-01")

    data = client.get("/reports/monthly", params={"month": "2026-10"}).json()

    assert data["income_cents"] == 500000
    assert data["expense_cents"] == 45050
    assert data["balance_cents"] == 454950
    assert data["by_category"] == [
        {"category_id": mercado, "category": "Mercado", "total_cents": 30050},
        {"category_id": lazer, "category": "Lazer", "total_cents": 15000},
    ]
    assert data["biggest_expense"]["amount_cents"] == 20000


def test_resumo_de_mes_vazio(client):
    data = client.get("/reports/monthly", params={"month": "2026-10"}).json()

    assert data == {
        "month": "2026-10",
        "income_cents": 0,
        "expense_cents": 0,
        "balance_cents": 0,
        "by_category": [],
        "biggest_expense": None,
    }


def test_mes_invalido_retorna_422(client):
    assert client.get("/reports/monthly", params={"month": "2026-13"}).status_code == 422
    assert client.get("/reports/monthly").status_code == 422


def test_dezembro_nao_vaza_para_o_ano_seguinte(client):
    categoria = create_category(client, "Mercado")
    create_transaction(client, categoria, "expense", 1000, "2026-12-31")
    create_transaction(client, categoria, "expense", 2000, "2027-01-01")

    data = client.get("/reports/monthly", params={"month": "2026-12"}).json()

    assert data["expense_cents"] == 1000


def test_csv_exporta_valores_e_protege_formulas(client):
    categoria = create_category(client, "Mercado")
    create_transaction(client, categoria, "expense", 4590, "2026-10-07", "Compras")
    create_transaction(client, categoria, "expense", 105, "2026-10-08", "=SOMA(A1)")

    response = client.get("/reports/monthly.csv", params={"month": "2026-10"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    linhas = response.text.lstrip("\ufeff").splitlines()
    assert linhas[0] == "id,data,tipo,categoria,descricao,valor"
    assert linhas[1].endswith("Compras,45.90")
    assert linhas[2].endswith("'=SOMA(A1),1.05")
    