from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import (
    Notice, NoticeCreate, NoticeUpdate,
    Sale, SaleCreate, SaleUpdate,
    Area, AreaCreate, AreaUpdate,
    FAQ, FAQCreate, FAQUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="Portal do Morador", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


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
def create_notice(data: NoticeCreate, session: Session = Depends(get_session)):
    notice = Notice(**data.model_dump())
    session.add(notice)
    session.commit()
    session.refresh(notice)
    return notice


@app.put("/api/notices/{notice_id}")
def update_notice(notice_id: int, data: NoticeUpdate, session: Session = Depends(get_session)):
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
def delete_notice(notice_id: int, session: Session = Depends(get_session)):
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
def create_sale(data: SaleCreate, session: Session = Depends(get_session)):
    sale = Sale(**data.model_dump())
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return sale


@app.put("/api/sales/{sale_id}")
def update_sale(sale_id: int, data: SaleUpdate, session: Session = Depends(get_session)):
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
def toggle_sale(sale_id: int, session: Session = Depends(get_session)):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Produto não encontrado")
    sale.active = not sale.active
    session.add(sale)
    session.commit()
    session.refresh(sale)
    return sale


@app.delete("/api/sales/{sale_id}")
def delete_sale(sale_id: int, session: Session = Depends(get_session)):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise HTTPException(404, "Produto não encontrado")
    session.delete(sale)
    session.commit()
    return {"ok": True}


# ── API: Áreas Comuns ────────────────────────────────────
@app.get("/api/areas")
def list_areas(session: Session = Depends(get_session)):
    return session.exec(select(Area).order_by(Area.display_order)).all()


@app.post("/api/areas", status_code=201)
def create_area(data: AreaCreate, session: Session = Depends(get_session)):
    area = Area(**data.model_dump())
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


@app.put("/api/areas/{area_id}")
def update_area(area_id: int, data: AreaUpdate, session: Session = Depends(get_session)):
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
def delete_area(area_id: int, session: Session = Depends(get_session)):
    area = session.get(Area, area_id)
    if not area:
        raise HTTPException(404, "Área não encontrada")
    session.delete(area)
    session.commit()
    return {"ok": True}


# ── API: FAQs ────────────────────────────────────────────
@app.get("/api/faqs")
def list_faqs(session: Session = Depends(get_session)):
    return session.exec(select(FAQ).order_by(FAQ.display_order)).all()


@app.post("/api/faqs", status_code=201)
def create_faq(data: FAQCreate, session: Session = Depends(get_session)):
    faq = FAQ(**data.model_dump())
    session.add(faq)
    session.commit()
    session.refresh(faq)
    return faq


@app.put("/api/faqs/{faq_id}")
def update_faq(faq_id: int, data: FAQUpdate, session: Session = Depends(get_session)):
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
def delete_faq(faq_id: int, session: Session = Depends(get_session)):
    faq = session.get(FAQ, faq_id)
    if not faq:
        raise HTTPException(404, "FAQ não encontrada")
    session.delete(faq)
    session.commit()
    return {"ok": True}


# ── Auth simples (verificação de senha) ──────────────────
ADMIN_PASSWORD = "sindico2026"


@app.post("/api/auth")
def auth_check(request_body: dict):
    if request_body.get("password") == ADMIN_PASSWORD:
        return {"ok": True}
    raise HTTPException(401, "Senha incorreta")
