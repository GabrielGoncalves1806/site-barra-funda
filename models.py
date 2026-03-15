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


# ── Areas ────────────────────────────────────────────────
class AreaBase(SQLModel):
    title: str
    slug: str
    tag: str = ""
    description: str = ""
    image: str = ""
    highlights: str = "[]"
    meta: str = "[]"
    rules: str = "[]"
    display_order: int = 0


class Area(AreaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class AreaCreate(AreaBase):
    pass


class AreaUpdate(SQLModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    tag: Optional[str] = None
    description: Optional[str] = None
    image: Optional[str] = None
    highlights: Optional[str] = None
    meta: Optional[str] = None
    rules: Optional[str] = None
    display_order: Optional[int] = None


# ── FAQs ─────────────────────────────────────────────────
class FAQBase(SQLModel):
    question: str
    answer: str
    icon: str = "❓"
    anchor_id: str = ""
    display_order: int = 0


class FAQ(FAQBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class FAQCreate(FAQBase):
    pass


class FAQUpdate(SQLModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    icon: Optional[str] = None
    anchor_id: Optional[str] = None
    display_order: Optional[int] = None
