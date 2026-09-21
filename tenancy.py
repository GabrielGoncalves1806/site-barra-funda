"""Descobre de qual condomínio é cada requisição, pelo domínio (Host)."""
from fastapi import Depends, HTTPException, Request
from sqlmodel import Session

from database import get_session
from models import Condominium, Domain


class CondominiumNotFound(Exception):
    """Host sem condomínio ativo. O handler no main transforma em 404."""


def normalize_host(host: str) -> str:
    """'Portal.Exemplo.com.br:443' -> 'portal.exemplo.com.br'."""
    return host.split(":", 1)[0].strip().lower()


def get_current_condominium(request: Request, session: Session = Depends(get_session)) -> Condominium:
    host = normalize_host(request.headers.get("host", ""))
    domain = session.get(Domain, host) if host else None
    condominium = session.get(Condominium, domain.condominium_id) if domain else None
    if not condominium or not condominium.active:
        raise CondominiumNotFound()
    return condominium


def get_owned(session: Session, model, item_id: int, condominium: Condominium, not_found_detail: str):
    """Busca um registro do condomínio atual.

    Registro de outro condomínio responde igual a inexistente (404), pra não
    confirmar que aquele id existe.
    """
    item = session.get(model, item_id)
    if not item or item.condominium_id != condominium.id:
        raise HTTPException(404, not_found_detail)
    return item
