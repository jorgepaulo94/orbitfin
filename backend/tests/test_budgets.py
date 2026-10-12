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


def set_budget(client, category_id, limit_cents):
    response = client.put(f"/budgets/{category_id}", json={"limit_cents": limit_cents})
    assert response.status_code == 200
    return response.json()


def test_definir_e_atualizar_orcamento(client):
    mercado = create_category(client, "Mercado")

    assert set_budget(client, mercado, 80000) == {"category_id": mercado, "limit_cents": 80000}
    assert set_budget(client, mercado, 90000)["limit_cents"] == 90000

    # Atualizar não pode criar um segundo orçamento para a mesma categoria
    assert client.get("/budgets").json() == [{"category_id": mercado, "limit_cents": 90000}]


def test_orcamento_rejeita_dados_invalidos(client):
    mercado = create_category(client, "Mercado")

    assert client.put(f"/budgets/{mercado}", json={"limit_cents": 0}).status_code == 422
    assert client.put(f"/budgets/{mercado}", json={"limit_cents": -5}).status_code == 422
    assert client.put("/budgets/999", json={"limit_cents": 1000}).status_code == 404


def test_status_classifica_ok_alerta_e_estourado(client):
    casos = {
        "Mercado": 7999,  # 79% -> ok
        "Lazer": 8000,  # 80% -> warning
        "Transporte": 10000,  # 100% -> warning (no limite, ainda não estourou)
        "Casa": 10001,  # 1 centavo acima -> over
    }
    for nome, gasto in casos.items():
        categoria = create_category(client, nome)
        set_budget(client, categoria, 10000)
        create_transaction(client, categoria, "expense", gasto, "2026-10-10")

    data = client.get("/budgets/status", params={"month": "2026-10"}).json()
    por_nome = {item["category"]: item for item in data}

    assert por_nome["Mercado"]["status"] == "ok"
    assert por_nome["Mercado"]["percent_used"] == 79
    assert por_nome["Lazer"]["status"] == "warning"
    assert por_nome["Transporte"]["status"] == "warning"
    assert por_nome["Transporte"]["remaining_cents"] == 0
    assert por_nome["Casa"]["status"] == "over"
    assert por_nome["Casa"]["remaining_cents"] == -1
    assert [item["category"] for item in data] == ["Casa", "Lazer", "Mercado", "Transporte"]


def test_status_ignora_receitas_e_outros_meses(client):
    categoria = create_category(client, "Mercado")
    set_budget(client, categoria, 50000)

    create_transaction(client, categoria, "expense", 10000, "2026-10-05")
    create_transaction(client, categoria, "income", 99999, "2026-10-06")  # receita: não conta
    create_transaction(client, categoria, "expense", 99999, "2026-09-30")  # outro mês
    create_transaction(client, categoria, "expense", 99999, "2026-11-01")  # outro mês

    item = client.get("/budgets/status", params={"month": "2026-10"}).json()[0]

    assert item["spent_cents"] == 10000
    assert item["remaining_cents"] == 40000
    assert item["percent_used"] == 20
    assert item["status"] == "ok"


def test_status_de_categoria_sem_gastos(client):
    categoria = create_category(client, "Lazer")
    set_budget(client, categoria, 30000)

    item = client.get("/budgets/status", params={"month": "2026-10"}).json()[0]

    assert item["spent_cents"] == 0
    assert item["remaining_cents"] == 30000
    assert item["percent_used"] == 0
    assert item["status"] == "ok"


def test_remover_orcamento(client):
    categoria = create_category(client, "Lazer")
    set_budget(client, categoria, 30000)

    assert client.delete(f"/budgets/{categoria}").status_code == 204
    assert client.delete(f"/budgets/{categoria}").status_code == 404
    assert client.get("/budgets").json() == []


def test_status_exige_mes_valido(client):
    assert client.get("/budgets/status").status_code == 422
    assert client.get("/budgets/status", params={"month": "2026-13"}).status_code == 422
    