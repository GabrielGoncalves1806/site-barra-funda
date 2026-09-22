"""Utilidades de autenticação: JWT em cookie httpOnly."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException, Response

from models import Condominium
from tenancy import get_current_condominium


COOKIE_NAME = "admin_session"
JWT_ALGORITHM = "HS256"
TOKEN_TTL_HOURS = 8
MIN_PASSWORD_LENGTH = 8


def hash_password(password: str) -> str:
    """Valida o tamanho e devolve o hash bcrypt. Levanta ValueError se inválida."""
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"A senha precisa ter pelo menos {MIN_PASSWORD_LENGTH} caracteres.")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Senha muito longa (máximo 72 bytes).")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Hash inválido (ex.: "!" de condomínio sem senha definida) nunca bate.
        return False


def _secret_key() -> str:
    key = os.getenv("SECRET_KEY", "")
    if not key:
        raise RuntimeError("SECRET_KEY não configurado no .env.")
    return key


def _cookie_secure() -> bool:
    """Exige COOKIE_SECURE explícito (sem default silencioso).

    Um default 'false' silencioso faria o cookie de sessão viajar em HTTP
    puro se alguém esquecesse de configurar isso em produção.
    """
    value = os.getenv("COOKIE_SECURE")
    if value is None:
        raise RuntimeError(
            "COOKIE_SECURE não configurado no .env. Use 'true' em produção "
            "(exige HTTPS) ou 'false' apenas em desenvolvimento local sem HTTPS."
        )
    return value.strip().lower() == "true"


def create_access_token(condominium_id: int, subject: str = "admin") -> str:
    """Gera um JWT assinado válido por TOKEN_TTL_HOURS, preso a um condomínio."""
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "cid": condominium_id,
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
        secure=_cookie_secure(),
        samesite="strict",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def require_admin(
    condominium: Condominium = Depends(get_current_condominium),
    admin_session: Optional[str] = Cookie(default=None),
) -> str:
    """Dependency: valida o cookie JWT do condomínio do Host. Retorna o subject ou 401."""
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
    # Token de outro condomínio (cookie copiado de um domínio pro outro)
    if payload.get("cid") != condominium.id:
        raise HTTPException(status_code=401, detail="Sessão inválida para este condomínio")
    return sub
