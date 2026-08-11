"""C del MVC: controlador de autenticación.

Responsabilidad: recibir la petición HTTP, validar el formulario, delegar en el
`AuthClient` (Tier 2) y elegir la vista. **No** contiene reglas de negocio ni
accede a la base de datos.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import ValidationError

from app.controllers.dependencies import get_auth_client, get_current_user
from app.core.config import get_settings
from app.core.exceptions import AuthApiError, AuthServiceUnavailable, SessionExpired
from app.core.logging import actor_var, audit, get_logger
from app.models.view_models import LoginForm, RegisterForm, SessionUser, form_errors
from app.services.auth_client import AuthClient
from app.views.renderer import templates

router = APIRouter(tags=["auth"])
_logger = get_logger("controllers")

ClientDep = Annotated[AuthClient, Depends(get_auth_client)]


# --------------------------- Login ---------------------------

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html", {"errors": [], "username": ""})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    client: ClientDep,
    username: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
) -> Response:
    actor_var.set(username or "anonymous")

    try:
        form = LoginForm(username=username, password=password)
    except ValidationError as exc:
        return _login_error(request, username, form_errors(exc), "formulario_invalido")

    try:
        user, token = await client.login(form.username, form.password)
    except AuthApiError as exc:
        return _login_error(request, username, [exc.message, *exc.reasons], exc.code,
                            status_code=status.HTTP_401_UNAUTHORIZED)
    except AuthServiceUnavailable as exc:
        return _unavailable(request, exc, "web.login")

    audit(_logger, "web.login", "SUCCESS", actor=user.username, component="auth_controller",
          message="Sesión iniciada; se emite cookie de sesión")

    response = RedirectResponse("/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    _set_session_cookie(response, token)
    return response


# --------------------------- Registro ---------------------------

@router.get("/register", response_class=HTMLResponse)
async def register_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "register.html", {"errors": [], "username": "", "email": ""}
    )


@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    client: ClientDep,
    username: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    password_confirm: Annotated[str, Form()] = "",
) -> Response:
    actor_var.set(username or "anonymous")

    try:
        form = RegisterForm(username=username, email=email, password=password,
                            password_confirm=password_confirm)
        mismatch = form.check_confirmation()
        if mismatch:
            return _register_error(request, username, email, mismatch, "password_mismatch")
    except ValidationError as exc:
        return _register_error(request, username, email, form_errors(exc),
                               "formulario_invalido")

    try:
        await client.register(form.username, form.email, form.password)
    except AuthApiError as exc:
        return _register_error(request, username, email, [exc.message, *exc.reasons], exc.code)
    except AuthServiceUnavailable as exc:
        return _unavailable(request, exc, "web.register")

    audit(_logger, "web.register", "SUCCESS", actor=form.username,
          component="auth_controller", message="Usuario registrado desde la web")

    return templates.TemplateResponse(
        request, "login.html",
        {"errors": [], "username": form.username,
         "info": "Cuenta creada correctamente. Ya puede iniciar sesión."},
    )


# --------------------------- Sesión ---------------------------

@router.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    audit(_logger, "web.logout", "SUCCESS", component="auth_controller",
          message="Sesión cerrada")
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(get_settings().session_cookie)
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> Response:
    try:
        user: SessionUser = await get_current_user(request)
    except SessionExpired:
        audit(_logger, "web.dashboard", "FAILURE", component="auth_controller",
              message="Acceso sin sesión válida; se redirige al login",
              level=logging.INFO, error_code="session_expired")
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    except AuthServiceUnavailable as exc:
        return _unavailable(request, exc, "web.dashboard")

    actor_var.set(user.username)
    audit(_logger, "web.dashboard", "SUCCESS", actor=user.username,
          component="auth_controller", message="Panel mostrado")
    return templates.TemplateResponse(request, "dashboard.html", {"user": user})


# --------------------------- Helpers de vista ---------------------------

def _set_session_cookie(response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie, token,
        httponly=True, samesite="lax", secure=settings.cookie_secure, path="/",
    )


def _login_error(request: Request, username: str, errors: list[str], code: str,
                 status_code: int = status.HTTP_400_BAD_REQUEST) -> HTMLResponse:
    audit(_logger, "web.login", "FAILURE", component="auth_controller",
          message=errors[0] if errors else "Login rechazado", level=logging.WARNING,
          error_code=code)
    return templates.TemplateResponse(
        request, "login.html", {"errors": errors, "username": username},
        status_code=status_code,
    )


def _register_error(request: Request, username: str, email: str, errors: list[str],
                    code: str) -> HTMLResponse:
    audit(_logger, "web.register", "FAILURE", component="auth_controller",
          message=errors[0] if errors else "Registro rechazado", level=logging.WARNING,
          error_code=code)
    return templates.TemplateResponse(
        request, "register.html",
        {"errors": errors, "username": username, "email": email},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def _unavailable(request: Request, exc: AuthServiceUnavailable, action: str) -> HTMLResponse:
    """Degradación controlada: el usuario ve un mensaje, nunca un stacktrace."""
    audit(_logger, action, "FAILURE", component="auth_controller", message=exc.message,
          level=logging.ERROR, error_code=exc.code)
    return templates.TemplateResponse(
        request, "error.html",
        {"title": "Servicio no disponible", "message": exc.message, "status_code": 503},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
