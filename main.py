from contextlib import asynccontextmanager
from pathlib import Path
import os
import uuid

import bcrypt
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Depends, HTTPException, UploadFile, File, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

load_dotenv()

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from auth import (
    create_access_token,
    set_session_cookie,
    clear_session_cookie,
    require_admin,
)
from database import create_db_and_tables, get_session
from logging_config import setup_logging, audit

setup_logging()
from models import (
    Notice, NoticeCreate, NoticeUpdate,
    Sale, SaleCreate, SaleUpdate,
    Area, AreaCreate, AreaUpdate,
    FAQ, FAQCreate, FAQUpdate,
)


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOAD_DIR = STATIC_DIR / "uploads"


def ensure_upload_dir():
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    ensure_upload_dir()
    yield


app = FastAPI(title="Portal do Morador", lifespan=lifespan)

# Rate limiter: chave por IP, registrado para uso via decorator.
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS restrito aos domínios configurados em .env (separados por vírgula).
_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
_allowed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()] or [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── Páginas ──────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def page_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def page_admin(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


# ── API: Avisos ──────────────────────────────────────────
@app.get("/api/notices")
def list_notices(session: Session = Depends(get_session)):
    return session.exec(select(Notice).order_by(Notice.id.desc())).all()


@app.post("/api/notices", status_code=201)
def create_notice(data: NoticeCreate, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    notice = Notice(**data.model_dump())
    session.add(notice)
    session.commit()
    session.refresh(notice)
    return notice


@app.put("/api/notices/{notice_id}")
def update_notice(notice_id: int, data: NoticeUpdate, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    notice = session.get(Notice, notice_id)
    if not notice:
        raise HTTPException(404, "Aviso não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(notice, key, value)
    session.add(notice)
    session.commit()
    session.refresh(notice)
    return notice


@app.delete("/api/notices/{notice_id}")
def delete_notice(notice_id: int, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    notice = session.get(Notice, notice_id)
    if not notice:
        raise HTTPException(404, "Aviso não encontrado")
    session.delete(notice)
    session.commit()
    return {"ok": True}


# ── API: Vendas ──────────────────────────────────────────
@app.get("/api/sales")
def list_sales(session: Session = Depends(get_session)):
    return session.exec(select(Sale).order_by(Sale.id.desc())).all()


@app.post("/api/sales", status_code=201)
def create_sale(data: SaleCreate, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    sale = Sale(**data.model_dump())
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return sale


@app.put("/api/sales/{sale_id}")
def update_sale(sale_id: int, data: SaleUpdate, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Produto não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(sale, key, value)
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return sale


@app.patch("/api/sales/{sale_id}/toggle")
def toggle_sale(sale_id: int, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Produto não encontrado")
    sale.active = not sale.active
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return sale


@app.delete("/api/sales/{sale_id}")
def delete_sale(sale_id: int, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Produto não encontrado")
    remove_uploaded_file(sale.image)
    session.delete(sale)
    session.commit()
    return {"ok": True}


# ── API: Áreas Comuns ────────────────────────────────────
@app.get("/api/areas")
def list_areas(session: Session = Depends(get_session)):
    return session.exec(select(Area).order_by(Area.display_order)).all()


@app.post("/api/areas", status_code=201)
def create_area(data: AreaCreate, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    area = Area(**data.model_dump())
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


@app.put("/api/areas/{area_id}")
def update_area(area_id: int, data: AreaUpdate, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    area = session.get(Area, area_id)
    if not area:
        raise HTTPException(404, "Área não encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(area, key, value)
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


@app.delete("/api/areas/{area_id}")
def delete_area(area_id: int, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    area = session.get(Area, area_id)
    if not area:
        raise HTTPException(404, "Área não encontrada")
    remove_uploaded_file(area.image)
    session.delete(area)
    session.commit()
    return {"ok": True}


# ── API: FAQs ────────────────────────────────────────────
@app.get("/api/faqs")
def list_faqs(session: Session = Depends(get_session)):
    return session.exec(select(FAQ).order_by(FAQ.display_order)).all()


@app.post("/api/faqs", status_code=201)
def create_faq(data: FAQCreate, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    faq = FAQ(**data.model_dump())
    session.add(faq)
    session.commit()
    session.refresh(faq)
    return faq


@app.put("/api/faqs/{faq_id}")
def update_faq(faq_id: int, data: FAQUpdate, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    faq = session.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(404, "FAQ não encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(faq, key, value)
    session.add(faq)
    session.commit()
    session.refresh(faq)
    return faq


@app.delete("/api/faqs/{faq_id}")
def delete_faq(faq_id: int, session: Session = Depends(get_session), _: str = Depends(require_admin)):
    faq = session.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(404, "FAQ não encontrada")
    session.delete(faq)
    session.commit()
    return {"ok": True}


# ── Upload de arquivos ───────────────────────────────────
ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def save_upload_file(upload: UploadFile) -> str:
    ensure_upload_dir()
    extension = Path(upload.filename or "").suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTS:
        raise HTTPException(400, f"Extensão não permitida. Use: {', '.join(sorted(ALLOWED_IMAGE_EXTS))}")

    if upload.content_type not in ALLOWED_IMAGE_MIME:
        raise HTTPException(400, "Tipo de arquivo inválido (apenas imagens).")

    filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename

    size = 0
    with destination.open("wb") as buffer:
        while chunk := upload.file.read(64 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE_BYTES:
                buffer.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(413, f"Arquivo maior que {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB.")
            buffer.write(chunk)

    return f"/static/uploads/{filename}"


def remove_uploaded_file(url: str | None):
    if not url or not url.startswith("/static/uploads/"):
        return
    file_path = Path(url.lstrip("/"))
    try:
        if file_path.exists():
            file_path.unlink()
    except OSError:
        pass


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), _: str = Depends(require_admin)):
    if not file.filename:
        raise HTTPException(400, "Arquivo inválido")
    url = save_upload_file(file)
    return {"url": url}


# ── Auth (login + JWT em cookie httpOnly) ────────────────
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

if not ADMIN_PASSWORD_HASH:
    raise RuntimeError(
        "ADMIN_PASSWORD_HASH não configurado. Crie um .env baseado no .env.example "
        "e gere o hash com scripts/generate_password_hash.py."
    )


@app.post("/api/auth")
@limiter.limit("5/minute")
def auth_check(request: Request, request_body: dict, response: Response):
    client_ip = request.client.host if request.client else "unknown"
    password = request_body.get("password", "")
    if not isinstance(password, str):
        audit("login_failed", ip=client_ip, reason="invalid_payload")
        raise HTTPException(401, "Senha incorreta")
    try:
        ok = bcrypt.checkpw(password.encode("utf-8"), ADMIN_PASSWORD_HASH.encode("utf-8"))
    except (ValueError, TypeError):
        ok = False
    if not ok:
        audit("login_failed", ip=client_ip)
        raise HTTPException(401, "Senha incorreta")

    token = create_access_token(subject="admin")
    set_session_cookie(response, token)
    audit("login_success", ip=client_ip)
    return {"ok": True}


@app.post("/api/logout")
def logout(response: Response):
    clear_session_cookie(response)
    audit("logout")
    return {"ok": True}


@app.get("/api/me")
def me(subject: str = Depends(require_admin)):
    return {"subject": subject}
