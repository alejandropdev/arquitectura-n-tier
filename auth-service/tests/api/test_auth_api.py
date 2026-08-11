"""Pruebas de la API del Tier 2 sobre la aplicación completa (middlewares + handlers)."""

from __future__ import annotations


def test_registro_devuelve_201(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "ana.perez", "email": "ana@example.com", "password": "Segura123"})

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "ana.perez"
    assert "password" not in body and "password_hash" not in body


def test_registro_duplicado_devuelve_409(client, registered_user):
    response = client.post("/api/v1/auth/register", json=registered_user)

    assert response.status_code == 409
    assert response.json()["code"] == "user_already_exists"


def test_registro_con_password_debil_devuelve_422(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "ana.perez", "email": "ana@example.com", "password": "corta"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_registro_con_password_sin_digitos_devuelve_422(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "ana.perez", "email": "ana@example.com", "password": "SinDigitos"})

    assert response.status_code == 422
    assert response.json()["code"] == "weak_password"


def test_login_exitoso_devuelve_token(client, registered_user):
    response = client.post("/api/v1/auth/login", json={
        "username": registered_user["username"], "password": registered_user["password"]})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["username"] == registered_user["username"]


def test_login_con_password_incorrecta_devuelve_401(client, registered_user):
    response = client.post("/api/v1/auth/login", json={
        "username": registered_user["username"], "password": "Incorrecta1"})

    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "invalid_credentials"
    # No se filtra si el usuario existe o no.
    assert "no existe" not in body["message"].lower()


def test_login_de_usuario_inexistente_devuelve_401(client):
    response = client.post("/api/v1/auth/login",
                           json={"username": "fantasma", "password": "Segura123"})

    assert response.status_code == 401


def test_cuenta_se_bloquea_tras_los_intentos_configurados(client, registered_user):
    for _ in range(3):   # max_failed_attempts=3 en las pruebas
        client.post("/api/v1/auth/login", json={
            "username": registered_user["username"], "password": "Incorrecta1"})

    response = client.post("/api/v1/auth/login", json={
        "username": registered_user["username"], "password": registered_user["password"]})

    assert response.status_code == 423
    assert response.json()["code"] == "account_locked"


def test_verificacion_de_token_valido(client, registered_user):
    token = client.post("/api/v1/auth/login", json={
        "username": registered_user["username"],
        "password": registered_user["password"]}).json()["access_token"]

    response = client.post("/api/v1/auth/verify", json={"token": token})

    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_verificacion_de_token_invalido_devuelve_401(client):
    response = client.post("/api/v1/auth/verify", json={"token": "no-es-un-jwt"})

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


def test_campos_extra_son_rechazados(client):
    response = client.post("/api/v1/auth/login", json={
        "username": "ana", "password": "Segura123", "rol": "admin"})

    assert response.status_code == 422


def test_todo_error_incluye_el_contrato_uniforme(client):
    response = client.post("/api/v1/auth/verify", json={"token": "invalido"})

    body = response.json()
    assert set(body) >= {"code", "message", "request_id"}
    assert body["request_id"] != "-"


def test_el_request_id_del_cliente_se_propaga(client, registered_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": registered_user["username"], "password": "Incorrecta1"},
        headers={"X-Request-ID": "traza-de-prueba"},
    )

    assert response.headers["X-Request-ID"] == "traza-de-prueba"
    assert response.json()["request_id"] == "traza-de-prueba"
