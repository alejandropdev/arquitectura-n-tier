"""Pruebas del controlador MVC (Tier 1) con el Tier 2 simulado."""

from __future__ import annotations


def test_la_raiz_redirige_al_login(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_muestra_el_formulario_de_login(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "Iniciar sesión" in response.text


def test_login_exitoso_redirige_y_crea_cookie(client, usuario_registrado):
    response = client.post("/login", data=usuario_registrado, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"
    cookie = response.cookies.get("auth_session")
    assert cookie == "token::ana.perez"
    assert "httponly" in response.headers["set-cookie"].lower()


def test_login_con_credenciales_incorrectas_muestra_el_error(client, usuario_registrado):
    response = client.post("/login", data={"username": "ana.perez", "password": "Mala1234"})

    assert response.status_code == 401
    assert "Usuario o contraseña incorrectos" in response.text
    assert "Traceback" not in response.text


def test_formulario_invalido_no_llega_al_microservicio(client, stub):
    response = client.post("/login", data={"username": "ab", "password": ""})

    assert response.status_code == 400
    assert stub.llamadas == []          # validación en el borde


def test_registro_exitoso_lleva_al_login(client):
    response = client.post("/register", data={
        "username": "nuevo.user", "email": "nuevo@example.com",
        "password": "Segura123", "password_confirm": "Segura123"})

    assert response.status_code == 200
    assert "Cuenta creada correctamente" in response.text


def test_registro_con_passwords_distintas(client, stub):
    response = client.post("/register", data={
        "username": "nuevo.user", "email": "nuevo@example.com",
        "password": "Segura123", "password_confirm": "Otra12345"})

    assert response.status_code == 400
    assert "no coinciden" in response.text
    assert stub.llamadas == []


def test_registro_duplicado_muestra_el_mensaje_del_microservicio(client, usuario_registrado):
    response = client.post("/register", data={
        "username": "ana.perez", "email": "ana@example.com",
        "password": "Segura123", "password_confirm": "Segura123"})

    assert response.status_code == 400
    assert "Ya existe un usuario" in response.text


def test_dashboard_sin_sesion_redirige_al_login(client):
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_dashboard_con_sesion_valida(client, usuario_registrado):
    client.post("/login", data=usuario_registrado)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "ana.perez" in response.text


def test_logout_borra_la_cookie(client, usuario_registrado):
    client.post("/login", data=usuario_registrado)

    response = client.post("/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert client.cookies.get("auth_session") in (None, "")


# --------------------------- Degradación controlada ---------------------------

def test_login_con_el_microservicio_caido_muestra_503(client, stub, usuario_registrado):
    stub.caido = True

    response = client.post("/login", data=usuario_registrado)

    assert response.status_code == 503
    assert "no está disponible" in response.text
    assert "Traceback" not in response.text        # nunca se filtra la traza


def test_dashboard_con_el_microservicio_caido_muestra_503(client, stub, usuario_registrado):
    client.post("/login", data=usuario_registrado)
    stub.caido = True

    response = client.get("/dashboard")

    assert response.status_code == 503


def test_readiness_refleja_el_estado_del_microservicio(client, stub):
    assert client.get("/health/ready").status_code == 200

    stub.caido = True
    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["dependencies"]["auth-service"] == "down"


def test_liveness_no_depende_del_microservicio(client, stub):
    stub.caido = True

    assert client.get("/health").status_code == 200
