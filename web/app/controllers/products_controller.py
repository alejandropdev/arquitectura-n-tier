"""C del MVC: controlador de productos.

Responsabilidad: recibir la petición HTTP, validar el formulario, delegar en el
`ProductsClient` (Tier 2) y elegir la vista. **No** contiene reglas de negocio
ni accede a la base de datos.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import ValidationError

from app.controllers.dependencies import get_current_user, get_products_client
from app.core.exceptions import (
    AuthServiceUnavailable,
    ProductApiError,
    ProductServiceUnavailable,
    SessionExpired,
)
from app.core.logging import actor_var, audit, get_logger
from app.models.view_models import PRODUCT_STATUSES, ProductForm, ProductListQuery, form_errors
from app.services.products_client import ProductsClient
from app.views.renderer import templates

router = APIRouter(prefix="/products", tags=["products"])
_logger = get_logger("controllers")

ClientDep = Annotated[ProductsClient, Depends(get_products_client)]


# --------------------------- Listado ---------------------------

@router.get("", response_class=HTMLResponse)
async def list_products(
    request: Request,
    client: ClientDep,
    page: Annotated[int, Query()] = 1,
    size: Annotated[int, Query()] = 10,
    search: Annotated[str, Query()] = "",
    status_filter: Annotated[str, Query(alias="status")] = "",
    brand: Annotated[str, Query()] = "",
    category_id: Annotated[str, Query(alias="categoryId")] = "",
    sort: Annotated[str, Query()] = "createdAt",
    order: Annotated[str, Query()] = "DESC",
) -> Response:
    user = await _require_user(request)
    if isinstance(user, Response):
        return user

    try:
        query = ProductListQuery(
            page=page, size=size, search=search or None,
            status=status_filter or None, brand=brand or None,
            category_id=category_id or None, sort=sort, order=order,
        )
    except ValidationError as exc:
        categories = await _safe_category_options(request, client, user)
        if isinstance(categories, Response):
            return categories
        return templates.TemplateResponse(
            request, "products_list.html",
            {"user": user, "errors": form_errors(exc), "products": [], "meta": None,
             "filters": ProductListQuery(), "statuses": PRODUCT_STATUSES,
             "categories": categories},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    categories = await _safe_category_options(request, client, user)
    if isinstance(categories, Response):
        return categories

    try:
        result = await client.list_products(query.to_query_params(), actor=user.username)
    except ProductApiError as exc:
        return templates.TemplateResponse(
            request, "products_list.html",
            {"user": user, "errors": [exc.message], "products": [], "meta": None,
             "filters": query, "statuses": PRODUCT_STATUSES, "categories": categories},
            status_code=exc.status_code,
        )
    except ProductServiceUnavailable as exc:
        return _unavailable(request, exc, "web.products.list")

    audit(_logger, "web.products.list", "SUCCESS", actor=user.username,
          component="products_controller", message="Listado de productos mostrado")
    return templates.TemplateResponse(
        request, "products_list.html",
        {"user": user, "errors": [], "products": result["data"], "meta": result["meta"],
         "filters": query, "statuses": PRODUCT_STATUSES, "categories": categories},
    )


# --------------------------- Alta ---------------------------

@router.get("/new", response_class=HTMLResponse)
async def new_product_form(request: Request, client: ClientDep) -> Response:
    user = await _require_user(request)
    if isinstance(user, Response):
        return user

    categories = await _safe_category_options(request, client, user)
    if isinstance(categories, Response):
        return categories

    return templates.TemplateResponse(
        request, "product_form.html",
        {"user": user, "errors": [], "product": None, "mode": "create",
         "statuses": PRODUCT_STATUSES, "categories": categories},
    )


@router.post("/new", response_class=HTMLResponse)
async def create_product(
    request: Request,
    client: ClientDep,
    name: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    brand: Annotated[str, Form()] = "",
    category_id: Annotated[str, Form(alias="categoryId")] = "",
    product_status: Annotated[str, Form(alias="status")] = "borrador",
) -> Response:
    user = await _require_user(request)
    if isinstance(user, Response):
        return user
    actor_var.set(user.username)

    submitted = {"name": name, "description": description, "brand": brand,
                 "categoryId": category_id, "status": product_status}

    try:
        form = ProductForm(name=name, description=description or None, brand=brand or None,
                           category_id=category_id, status=product_status)
    except ValidationError as exc:
        return await _create_error(request, client, user, form_errors(exc),
                                   "formulario_invalido", submitted)

    try:
        product = await client.create_product(_form_payload(form), actor=user.username)
    except ProductApiError as exc:
        return await _create_error(request, client, user, [exc.message], exc.code, submitted,
                                   status_code=exc.status_code)
    except ProductServiceUnavailable as exc:
        return _unavailable(request, exc, "web.products.create")

    audit(_logger, "web.products.create", "SUCCESS", actor=user.username,
          component="products_controller", message="Producto creado",
          product_id=product["id"])
    return RedirectResponse(f"/products/{product['id']}", status_code=status.HTTP_303_SEE_OTHER)


# --------------------------- Detalle / edición ---------------------------

@router.get("/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, client: ClientDep, product_id: str) -> Response:
    user = await _require_user(request)
    if isinstance(user, Response):
        return user

    try:
        product = await client.get_product(product_id, actor=user.username)
    except ProductApiError as exc:
        return templates.TemplateResponse(
            request, "error.html",
            {"title": "Producto no encontrado", "message": exc.message,
             "status_code": exc.status_code},
            status_code=exc.status_code,
        )
    except ProductServiceUnavailable as exc:
        return _unavailable(request, exc, "web.products.detail")

    categories = await _safe_category_options(request, client, user)
    if isinstance(categories, Response):
        return categories

    return templates.TemplateResponse(
        request, "product_form.html",
        {"user": user, "errors": [], "product": product, "mode": "edit",
         "statuses": PRODUCT_STATUSES, "categories": categories},
    )


@router.post("/{product_id}", response_class=HTMLResponse)
async def update_product(
    request: Request,
    client: ClientDep,
    product_id: str,
    name: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    brand: Annotated[str, Form()] = "",
    category_id: Annotated[str, Form(alias="categoryId")] = "",
    product_status: Annotated[str, Form(alias="status")] = "borrador",
) -> Response:
    user = await _require_user(request)
    if isinstance(user, Response):
        return user
    actor_var.set(user.username)

    submitted = {"id": product_id, "name": name, "description": description, "brand": brand,
                 "categoryId": category_id, "status": product_status}

    try:
        form = ProductForm(name=name, description=description or None, brand=brand or None,
                           category_id=category_id, status=product_status)
    except ValidationError as exc:
        return await _update_error(request, client, user, form_errors(exc),
                                   "formulario_invalido", submitted)

    try:
        await client.update_product(product_id, _form_payload(form), actor=user.username)
    except ProductApiError as exc:
        return await _update_error(request, client, user, [exc.message], exc.code, submitted,
                                   status_code=exc.status_code)
    except ProductServiceUnavailable as exc:
        return _unavailable(request, exc, "web.products.update")

    audit(_logger, "web.products.update", "SUCCESS", actor=user.username,
          component="products_controller", message="Producto actualizado",
          product_id=product_id)
    return RedirectResponse(f"/products/{product_id}", status_code=status.HTTP_303_SEE_OTHER)


# --------------------------- Descontinuar ---------------------------

@router.post("/{product_id}/discontinue")
async def discontinue_product(request: Request, client: ClientDep, product_id: str) -> Response:
    user = await _require_user(request)
    if isinstance(user, Response):
        return user
    actor_var.set(user.username)

    try:
        await client.discontinue_product(product_id, actor=user.username)
    except ProductApiError as exc:
        return templates.TemplateResponse(
            request, "error.html",
            {"title": "No se pudo descontinuar", "message": exc.message,
             "status_code": exc.status_code},
            status_code=exc.status_code,
        )
    except ProductServiceUnavailable as exc:
        return _unavailable(request, exc, "web.products.discontinue")

    audit(_logger, "web.products.discontinue", "SUCCESS", actor=user.username,
          component="products_controller", message="Producto descontinuado",
          product_id=product_id)
    return RedirectResponse("/products", status_code=status.HTTP_303_SEE_OTHER)


# --------------------------- Helpers de vista ---------------------------

async def _require_user(request: Request):
    """No delega en un microservicio de identidad distinto: reutiliza la sesión
    ya validada por `auth-service` para proteger el catálogo de productos."""
    try:
        user = await get_current_user(request)
    except SessionExpired:
        audit(_logger, "web.products.access", "FAILURE", component="products_controller",
              message="Acceso sin sesión válida; se redirige al login",
              level=logging.INFO, error_code="session_expired")
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    except AuthServiceUnavailable as exc:
        return _unavailable(request, exc, "web.products.access")
    actor_var.set(user.username)
    return user


async def _safe_category_options(request: Request, client: ProductsClient, user) -> list[dict] | Response:
    """Trae las categorías para un <select>; si el servicio falla devuelve
    directamente la Response de error para que el caller la propague."""
    try:
        categories = await client.list_categories(actor=user.username)
    except ProductApiError as exc:
        return templates.TemplateResponse(
            request, "error.html",
            {"title": "No se pudieron cargar las categorías", "message": exc.message,
             "status_code": exc.status_code},
            status_code=exc.status_code,
        )
    except ProductServiceUnavailable as exc:
        return _unavailable(request, exc, "web.categories.list")
    return _category_options(categories)


def _category_options(categories: list[dict]) -> list[dict]:
    """Aplana el árbol de categorías en opciones ordenadas para el <select>,
    con las hijas indentadas bajo su padre (ej. "Electrónica — Smartphones")."""
    children_by_parent: dict[str | None, list[dict]] = {}
    for category in categories:
        children_by_parent.setdefault(category["parentId"], []).append(category)
    for siblings in children_by_parent.values():
        siblings.sort(key=lambda c: c["name"])

    options: list[dict] = []

    def _walk(parent_id: str | None, depth: int) -> None:
        for category in children_by_parent.get(parent_id, []):
            prefix = "— " * depth
            options.append({"id": category["id"], "label": f"{prefix}{category['name']}"})
            _walk(category["id"], depth + 1)

    _walk(None, 0)
    # Categorías huérfanas (padre inexistente en la lista) igual deben poder elegirse.
    seen = {o["id"] for o in options}
    for category in categories:
        if category["id"] not in seen:
            options.append({"id": category["id"], "label": category["name"]})
    return options


def _form_payload(form: ProductForm) -> dict:
    return {
        "name": form.name,
        "description": form.description,
        "brand": form.brand,
        "categoryId": form.category_id,
        "status": form.status,
    }


async def _create_error(request: Request, client: ProductsClient, user, errors: list[str],
                        code: str, submitted: dict,
                        status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    audit(_logger, "web.products.create", "FAILURE", component="products_controller",
          actor=user.username, message=errors[0] if errors else "Alta rechazada",
          level=logging.WARNING, error_code=code)
    categories = await _safe_category_options(request, client, user)
    if isinstance(categories, Response):
        return categories
    return templates.TemplateResponse(
        request, "product_form.html",
        {"user": user, "errors": errors, "product": submitted, "mode": "create",
         "statuses": PRODUCT_STATUSES, "categories": categories},
        status_code=status_code,
    )


async def _update_error(request: Request, client: ProductsClient, user, errors: list[str],
                        code: str, submitted: dict,
                        status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    audit(_logger, "web.products.update", "FAILURE", component="products_controller",
          actor=user.username, message=errors[0] if errors else "Actualización rechazada",
          level=logging.WARNING, error_code=code)
    categories = await _safe_category_options(request, client, user)
    if isinstance(categories, Response):
        return categories
    return templates.TemplateResponse(
        request, "product_form.html",
        {"user": user, "errors": errors, "product": submitted, "mode": "edit",
         "statuses": PRODUCT_STATUSES, "categories": categories},
        status_code=status_code,
    )


def _unavailable(request: Request, exc, action: str) -> HTMLResponse:
    """Degradación controlada: el usuario ve un mensaje, nunca un stacktrace."""
    audit(_logger, action, "FAILURE", component="products_controller", message=exc.message,
          level=logging.ERROR, error_code=exc.code)
    return templates.TemplateResponse(
        request, "error.html",
        {"title": "Servicio no disponible", "message": exc.message, "status_code": 503},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
