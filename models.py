from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


# ── Notices ──────────────────────────────────────────────
class NoticeBase(SQLModel):
    title: str
    text: str
    level: str = "normal"
    author: str = "Síndico"
    date: str = ""


class Notice(NoticeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NoticeCreate(NoticeBase):
    pass


class NoticeUpdate(SQLModel):
    title: Optional[str] = None
    text: Optional[str] = None
    level: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None


# ── Sales ────────────────────────────────────────────────
class SaleBase(SQLModel):
    title: str
    description: str
    price: str
    image: str = "/static/assets/placeholder-sale.jpg"
    seller: str
    whatsapp: str
    active: bool = True


class Sale(SaleBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SaleCreate(SaleBase):
    pass


class SaleUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    image: Optional[str] = None
    seller: Optional[str] = None
    whatsapp: Optional[str] = None
    active: Optional[bool] = None
