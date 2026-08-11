"""Controlador de la página inicial."""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["home"])


@router.get("/")
async def home(request: Request) -> RedirectResponse:
    destination = "/dashboard" if request.cookies.get("auth_session") else "/login"
    return RedirectResponse(destination, status_code=status.HTTP_303_SEE_OTHER)
