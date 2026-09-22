from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import JSON, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Condomínios ──────────────────────────────────────────
class Condominium(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(max_length=60, unique=True)
    name: str = Field(max_length=200)
    password_hash: str = Field(max_length=100)
    active: bool = Field(default=True)
    # Configuração editável pelo admin (identidade, contatos, documentos...).
    # JSONB no Postgres; no SQLite dos testes vira JSON comum.
    config: dict = Field(
        default_factory=dict,
        sa_column=Column(JSON().with_variant(JSONB(), "postgresql"), nullable=False),
    )
    created_at: datetime = Field(default_factory=_utcnow)


class Domain(SQLModel, table=True):
    """Host pelo qual o portal de um condomínio é acessado."""
    host: str = Field(primary_key=True, max_length=253)
    condominium_id: int = Field(foreign_key="condominium.id", index=True)


class LoginAttempt(SQLModel, table=True):
    """Tentativa de login, pra limitar por IP. Fica no banco porque em
    serverless cada instância teria o próprio contador em memória."""
    id: Optional[int] = Field(default=None, primary_key=True)
    ip: str = Field(max_length=64)
    created_at: datetime = Field(index=True)


# ── Notices ──────────────────────────────────────────────
class NoticeBase(SQLModel):
    title: str = Field(max_length=200)
    text: str = Field(max_length=5000)
    level: str = Field(default="normal", max_length=20)
    author: str = Field(default="Síndico", max_length=100)
    date: str = Field(default="", max_length=50)


class Notice(NoticeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    condominium_id: int = Field(foreign_key="condominium.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)


class NoticeCreate(NoticeBase):
    pass


class NoticeUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=200)
    text: Optional[str] = Field(default=None, max_length=5000)
    level: Optional[str] = Field(default=None, max_length=20)
    author: Optional[str] = Field(default=None, max_length=100)
    date: Optional[str] = Field(default=None, max_length=50)


# ── Sales ────────────────────────────────────────────────
class SaleBase(SQLModel):
    title: str = Field(max_length=150)
    description: str = Field(max_length=2000)
    price: str = Field(max_length=50)
    image: str = Field(default="/static/assets/placeholder-sale.jpg", max_length=500)
    seller: str = Field(max_length=100)
    whatsapp: str = Field(max_length=30)
    active: bool = Field(default=True)


class Sale(SaleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    condominium_id: int = Field(foreign_key="condominium.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)


class SaleCreate(SaleBase):
    pass


class SaleUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=150)
    description: Optional[str] = Field(default=None, max_length=2000)
    price: Optional[str] = Field(default=None, max_length=50)
    image: Optional[str] = Field(default=None, max_length=500)
    seller: Optional[str] = Field(default=None, max_length=100)
    whatsapp: Optional[str] = Field(default=None, max_length=30)
    active: Optional[bool] = None


# ── Areas ────────────────────────────────────────────────
class AreaBase(SQLModel):
    title: str = Field(max_length=150)
    slug: str = Field(max_length=80)
    icon: str = Field(default="🏢", max_length=10)
    tag: str = Field(default="", max_length=50)
    description: str = Field(default="", max_length=2000)
    image: str = Field(default="", max_length=500)
    highlights: str = Field(default="[]", max_length=3000)
    meta: str = Field(default="[]", max_length=2000)
    rules: str = Field(default="[]", max_length=5000)
    display_order: int = Field(default=0)


class Area(AreaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    condominium_id: int = Field(foreign_key="condominium.id", index=True)


class AreaCreate(AreaBase):
    pass


class AreaUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=150)
    slug: Optional[str] = Field(default=None, max_length=80)
    icon: Optional[str] = Field(default=None, max_length=10)
    tag: Optional[str] = Field(default=None, max_length=50)
    description: Optional[str] = Field(default=None, max_length=2000)
    image: Optional[str] = Field(default=None, max_length=500)
    highlights: Optional[str] = Field(default=None, max_length=3000)
    meta: Optional[str] = Field(default=None, max_length=2000)
    rules: Optional[str] = Field(default=None, max_length=5000)
    display_order: Optional[int] = None


# ── FAQs ─────────────────────────────────────────────────
class FAQBase(SQLModel):
    question: str = Field(max_length=300)
    answer: str = Field(max_length=3000)
    icon: str = Field(default="❓", max_length=10)
    anchor_id: str = Field(default="", max_length=80)
    display_order: int = Field(default=0)


class FAQ(FAQBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    condominium_id: int = Field(foreign_key="condominium.id", index=True)


class FAQCreate(FAQBase):
    pass


class FAQUpdate(SQLModel):
    question: Optional[str] = Field(default=None, max_length=300)
    answer: Optional[str] = Field(default=None, max_length=3000)
    icon: Optional[str] = Field(default=None, max_length=10)
    anchor_id: Optional[str] = Field(default=None, max_length=80)
    display_order: Optional[int] = None
