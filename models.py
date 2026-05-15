from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


# ── Notices ──────────────────────────────────────────────
class NoticeBase(SQLModel):
    title: str = Field(max_length=200)
    text: str = Field(max_length=5000)
    level: str = Field(default="normal", max_length=20)
    author: str = Field(default="Síndico", max_length=100)
    date: str = Field(default="", max_length=50)


class Notice(NoticeBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
    tag: str = Field(default="", max_length=50)
    description: str = Field(default="", max_length=2000)
    image: str = Field(default="", max_length=500)
    highlights: str = Field(default="[]", max_length=3000)
    meta: str = Field(default="[]", max_length=2000)
    rules: str = Field(default="[]", max_length=5000)
    display_order: int = Field(default=0)


class Area(AreaBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class AreaCreate(AreaBase):
    pass


class AreaUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=150)
    slug: Optional[str] = Field(default=None, max_length=80)
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


class FAQCreate(FAQBase):
    pass


class FAQUpdate(SQLModel):
    question: Optional[str] = Field(default=None, max_length=300)
    answer: Optional[str] = Field(default=None, max_length=3000)
    icon: Optional[str] = Field(default=None, max_length=10)
    anchor_id: Optional[str] = Field(default=None, max_length=80)
    display_order: Optional[int] = None
