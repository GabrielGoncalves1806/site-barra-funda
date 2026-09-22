from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File, Response, Body
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, ValidationError
from sqlmodel import Session, delete, func, select

load_dotenv()

from starlette.middleware.base import BaseHTTPMiddleware

import condo_config
from auth import (
    create_access_token,
    set_session_cookie,
    clear_session_cookie,
    hash_password,
    require_admin,
    verify_password,
)
from database import get_session
from logging_config import setup_logging, audit
from static_assets import VersionedStaticFiles, static_url
from storage import get_storage
from tenancy import CondominiumNotFound, get_current_condominium, get_owned

setup_logging()
from models import (
    Condominium, LoginAttempt,
    Notice, NoticeCreate, NoticeUpdate,
    Sale, SaleCreate, SaleUpdate,
    Area, AreaCreate, AreaUpdate,
    FAQ, FAQCreate, FAQUpdate,
)


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# O schema do banco é responsabilidade do Alembic (`alembic upgrade head`),
# não do startup do app.
app = FastAPI(title="Portal do Morador")

# Sem CORS: site e API de cada condomínio sempre ficam no mesmo domínio.
# Sem rate limit global: em serverless cada instância contaria sozinha; abuso
# nas rotas públicas fica com o firewall da Vercel. O login tem limite próprio.


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)

# O versionado vem antes: senão o mount do /static captura /static/v/... e dá 404.
app.mount("/static/v/{version}", VersionedStaticFiles(directory=str(STATIC_DIR)), name="static_versioned")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.filters.update(
    whatsapp_url=condo_config.whatsapp_url,
    tel_url=condo_config.tel_url,
    hex_to_rgb=condo_config.hex_to_rgb,
)
templates.env.globals["maps_url"] = condo_config.maps_url
templates.env.globals["static_url"] = static_url


@app.exception_handler(CondominiumNotFound)
async def condominium_not_found(request: Request, exc: CondominiumNotFound):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": "Portal não encontrado"}, status_code=404)
    return templates.TemplateResponse(request, "not_found.html", status_code=404)


# ── Páginas ──────────────────────────────────────────────
def _page_context(condominium: Condominium) -> dict:
    config = condo_config.load_config(condominium.config)
    return {
        "condominium": condominium,
        "config": config,
        "display_name": config.identity.name or condominium.name,
    }


@app.get("/", response_class=HTMLResponse)
async def page_home(request: Request, condominium: Condominium = Depends(get_current_condominium)):
    return templates.TemplateResponse(request, "index.html", _page_context(condominium))


@app.get("/admin", response_class=HTMLResponse)
async def page_admin(request: Request, condominium: Condominium = Depends(get_current_condominium)):
    return templates.TemplateResponse(request, "admin.html", _page_context(condominium))


# ── API: Config do condomínio ────────────────────────────
@app.get("/api/config")
def get_config(condominium: Condominium = Depends(get_current_condominium)):
    return condo_config.load_config(condominium.config).model_dump(mode="json")


@app.put("/api/config/{section}")
def update_config_section(
    section: str,
    value: Any = Body(...),
    session: Session = Depends(get_session),
    condominium: Condominium = Depends(get_current_condominium),
    _: str = Depends(require_admin),
):
    if section not in condo_config.SECTIONS:
        raise HTTPException(404, "Seção de configuração não encontrada")
    try:
        validated = condo_config.validate_section(section, value)
    except ValidationError as exc:
        raise HTTPException(422, exc.errors(include_url=False, include_context=False))
    # Reatribui o dict inteiro: mutação in-place num campo JSON não é detectada.
    condominium.config = {**(condominium.config or {}), section: validated}
    session.add(condominium)
    session.commit()
    audit("config_updated", condominium=condominium.slug, section=section)
    return validated


# ── API: Avisos ──────────────────────────────────────────
@app.get("/api/notices")
def list_notices(session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium)):
    query = select(Notice).where(Notice.condominium_id == condominium.id).order_by(Notice.id.desc())
    return session.exec(query).all()


@app.post("/api/notices", status_code=201)
def create_notice(data: NoticeCreate, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    notice = Notice(**data.model_dump(), condominium_id=condominium.id)
    session.add(notice)
    session.commit()
    session.refresh(notice)
    return notice


@app.put("/api/notices/{notice_id}")
def update_notice(notice_id: int, data: NoticeUpdate, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    notice = get_owned(session, Notice, notice_id, condominium, "Aviso não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(notice, key, value)
    session.add(notice)
    session.commit()
    session.refresh(notice)
    return notice


@app.delete("/api/notices/{notice_id}")
def delete_notice(notice_id: int, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    notice = get_owned(session, Notice, notice_id, condominium, "Aviso não encontrado")
    session.delete(notice)
    session.commit()
    return {"ok": True}


# ── API: Vendas ──────────────────────────────────────────
@app.get("/api/sales")
def list_sales(session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium)):
    query = select(Sale).where(Sale.condominium_id == condominium.id).order_by(Sale.id.desc())
    return session.exec(query).all()


@app.post("/api/sales", status_code=201)
def create_sale(data: SaleCreate, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    sale = Sale(**data.model_dump(), condominium_id=condominium.id)
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return sale


@app.put("/api/sales/{sale_id}")
def update_sale(sale_id: int, data: SaleUpdate, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    sale = get_owned(session, Sale, sale_id, condominium, "Produto não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(sale, key, value)
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return sale


@app.patch("/api/sales/{sale_id}/toggle")
def toggle_sale(sale_id: int, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    sale = get_owned(session, Sale, sale_id, condominium, "Produto não encontrado")
    sale.active = not sale.active
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return sale


@app.delete("/api/sales/{sale_id}")
def delete_sale(sale_id: int, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), storage=Depends(get_storage), _: str = Depends(require_admin)):
    sale = get_owned(session, Sale, sale_id, condominium, "Produto não encontrado")
    storage.delete(sale.image, condominium.slug)
    session.delete(sale)
    session.commit()
    return {"ok": True}


# ── API: Áreas Comuns ────────────────────────────────────
@app.get("/api/areas")
def list_areas(session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium)):
    query = select(Area).where(Area.condominium_id == condominium.id).order_by(Area.display_order)
    return session.exec(query).all()


@app.post("/api/areas", status_code=201)
def create_area(data: AreaCreate, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    area = Area(**data.model_dump(), condominium_id=condominium.id)
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


@app.put("/api/areas/{area_id}")
def update_area(area_id: int, data: AreaUpdate, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    area = get_owned(session, Area, area_id, condominium, "Área não encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(area, key, value)
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


@app.delete("/api/areas/{area_id}")
def delete_area(area_id: int, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), storage=Depends(get_storage), _: str = Depends(require_admin)):
    area = get_owned(session, Area, area_id, condominium, "Área não encontrada")
    storage.delete(area.image, condominium.slug)
    session.delete(area)
    session.commit()
    return {"ok": True}


# ── API: FAQs ────────────────────────────────────────────
@app.get("/api/faqs")
def list_faqs(session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium)):
    query = select(FAQ).where(FAQ.condominium_id == condominium.id).order_by(FAQ.display_order)
    return session.exec(query).all()


@app.post("/api/faqs", status_code=201)
def create_faq(data: FAQCreate, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    faq = FAQ(**data.model_dump(), condominium_id=condominium.id)
    session.add(faq)
    session.commit()
    session.refresh(faq)
    return faq


@app.put("/api/faqs/{faq_id}")
def update_faq(faq_id: int, data: FAQUpdate, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    faq = get_owned(session, FAQ, faq_id, condominium, "FAQ não encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(faq, key, value)
    session.add(faq)
    session.commit()
    session.refresh(faq)
    return faq


@app.delete("/api/faqs/{faq_id}")
def delete_faq(faq_id: int, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium), _: str = Depends(require_admin)):
    faq = get_owned(session, FAQ, faq_id, condominium, "FAQ não encontrada")
    session.delete(faq)
    session.commit()
    return {"ok": True}


# ── Upload de arquivos ───────────────────────────────────
# Extensão -> tipos aceitos. PDF é pros documentos do condomínio.
ALLOWED_UPLOADS = {
    ".jpg": {"image/jpeg"},
    ".jpeg": {"image/jpeg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".gif": {"image/gif"},
    ".pdf": {"application/pdf"},
}
# A Vercel recusa request com corpo acima de 4,5 MB antes de chegar no app.
MAX_UPLOAD_SIZE_BYTES = 4 * 1024 * 1024


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    condominium: Condominium = Depends(get_current_condominium),
    storage=Depends(get_storage),
    _: str = Depends(require_admin),
):
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_UPLOADS:
        raise HTTPException(400, f"Extensão não permitida. Use: {', '.join(sorted(ALLOWED_UPLOADS))}")
    if file.content_type not in ALLOWED_UPLOADS[extension]:
        raise HTTPException(400, "Tipo de arquivo não bate com a extensão.")

    data = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(data) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(413, f"Arquivo maior que {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB.")
    # O tipo vem do navegador; pra PDF, confere a assinatura do próprio arquivo.
    if extension == ".pdf" and not data.startswith(b"%PDF"):
        raise HTTPException(400, "O arquivo não é um PDF válido.")

    url = storage.save(data, extension, file.content_type, condominium.slug)
    return {"url": url}


# ── Auth (login + JWT em cookie httpOnly) ────────────────
LOGIN_ATTEMPTS_PER_MINUTE = 5


def get_client_ip(request: Request) -> str:
    # Na Vercel o X-Forwarded-For é reescrito pela borda, então o primeiro IP
    # é o do visitante. Fora dela, cai no IP da conexão.
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_login_rate_limit(session: Session, ip: str) -> None:
    """Máximo de LOGIN_ATTEMPTS_PER_MINUTE tentativas por IP por minuto.

    Conta no banco porque em serverless cada instância teria o próprio
    contador em memória. Tentativas com mais de 1h são apagadas aqui mesmo.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session.exec(delete(LoginAttempt).where(LoginAttempt.created_at < now - timedelta(hours=1)))
    recent = session.exec(
        select(func.count())
        .select_from(LoginAttempt)
        .where(LoginAttempt.ip == ip, LoginAttempt.created_at >= now - timedelta(minutes=1))
    ).one()
    if recent >= LOGIN_ATTEMPTS_PER_MINUTE:
        session.commit()
        raise HTTPException(429, "Muitas tentativas. Aguarde um minuto.")
    session.add(LoginAttempt(ip=ip[:64], created_at=now))
    session.commit()


@app.post("/api/auth")
def auth_check(request: Request, request_body: dict, response: Response, session: Session = Depends(get_session), condominium: Condominium = Depends(get_current_condominium)):
    client_ip = get_client_ip(request)
    check_login_rate_limit(session, client_ip)
    password = request_body.get("password", "")
    if not isinstance(password, str):
        audit("login_failed", ip=client_ip, condominium=condominium.slug, reason="invalid_payload")
        raise HTTPException(401, "Senha incorreta")
    if not verify_password(password, condominium.password_hash):
        audit("login_failed", ip=client_ip, condominium=condominium.slug)
        raise HTTPException(401, "Senha incorreta")

    token = create_access_token(condominium.id)
    set_session_cookie(response, token)
    audit("login_success", ip=client_ip, condominium=condominium.slug)
    return {"ok": True}


class PasswordChange(BaseModel):
    current_password: str = Field(max_length=200)
    new_password: str = Field(min_length=8, max_length=72)


@app.post("/api/password")
def change_password(
    data: PasswordChange,
    session: Session = Depends(get_session),
    condominium: Condominium = Depends(get_current_condominium),
    _: str = Depends(require_admin),
):
    if not verify_password(data.current_password, condominium.password_hash):
        raise HTTPException(400, "Senha atual incorreta")
    try:
        condominium.password_hash = hash_password(data.new_password)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    session.add(condominium)
    session.commit()
    audit("password_changed", condominium=condominium.slug)
    return {"ok": True}


@app.post("/api/logout")
def logout(response: Response):
    clear_session_cookie(response)
    audit("logout")
    return {"ok": True}


@app.get("/api/me")
def me(subject: str = Depends(require_admin)):
    return {"subject": subject}
