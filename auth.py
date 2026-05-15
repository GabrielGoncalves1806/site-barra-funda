"""Utilidades de autenticação: JWT em cookie httpOnly."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Cookie, HTTPException, Response


COOKIE_NAME = "admin_session"
JWT_ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 8


def _secret_key() -> str:
    key = os.getenv("SECRET_KEY", "")
    if not key:
        raise RuntimeError("SECRET_KEY não configurado no .env.")
    return key


def create_access_token(subject: str = "admin") -> str:
    """Gera um JWT assinado válido por TOKEN_TTL_HOURS."""
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=TOKEN_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, _secret_key(), algorithm=JWT_ALGORITHM)


def set_session_cookie(response: Response, token: str) -> None:
    """Configura o cookie httpOnly com o JWT."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=TOKEN_TTL_HOURS * 3600,
        httponly=True,
        secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        samesite="strict",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def require_admin(admin_session: Optional[str] = Cookie(default=None)) -> str:
    """Dependency: valida o cookie JWT. Retorna o subject ou 401."""
    if not admin_session:
        raise HTTPException(status_code=401, detail="Não autenticado")
    try:
        payload = jwt.decode(admin_session, _secret_key(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sessão expirada")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token sem subject")
    return sub
