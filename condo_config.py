"""Configuração editável de cada condomínio (guardada em Condominium.config).

Todo campo tem default: um config antigo continua válido quando o schema
cresce, e um condomínio novo nasce funcionando, com listas vazias.
"""
import logging
import re
from typing import Annotated, Any
from urllib.parse import quote

from pydantic import AfterValidator, BaseModel, Field, TypeAdapter, ValidationError

logger = logging.getLogger(__name__)

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


def _safe_url(value: str) -> str:
    """Só https://, http:// ou caminho do próprio site (/...).

    Bloqueia javascript:, data: e afins, que viram XSS num href.
    """
    value = value.strip()
    if value == "":
        return value
    if value.startswith("/") and not value.startswith("//"):
        return value
    if re.match(r"^https?://", value, re.IGNORECASE):
        return value
    raise ValueError("URL precisa começar com https://, http:// ou /")


Url = Annotated[str, Field(max_length=500), AfterValidator(_safe_url)]
Emoji = Annotated[str, Field(max_length=10)]
Line = Annotated[str, Field(max_length=300)]


class Identity(BaseModel):
    name: str = Field("", max_length=120)  # vazio: usa o nome do cadastro
    subtitle: str = Field("Portal do Morador", max_length=80)
    logo: Emoji = "🏢"
    accent: str = Field("#667eea", pattern=HEX_COLOR)
    accent2: str = Field("#764ba2", pattern=HEX_COLOR)


class Address(BaseModel):
    text: str = Field("", max_length=200)
    map_url: Url = ""  # vazio: busca o endereço no Google Maps


class HeroImage(BaseModel):
    url: Url
    alt: str = Field("", max_length=120)


class Hero(BaseModel):
    title: str = Field("Bem-vindo ao portal do morador", max_length=120)
    subtitle: str = Field(
        "Encontre avisos, regras, documentos, contatos e informações das áreas comuns.",
        max_length=400,
    )
    images: list[HeroImage] = Field(default_factory=list, max_length=10)


class Contact(BaseModel):
    label: str = Field(max_length=80)
    phone: str = Field("", max_length=30)
    whatsapp: bool = False
    email: str = Field("", max_length=120)


class Place(BaseModel):
    icon: Emoji = "🏥"
    name: str = Field(max_length=120)
    tag: str = Field("", max_length=120)
    details: str = Field("", max_length=300)
    url: Url = ""


class Document(BaseModel):
    icon: Emoji = "📄"
    title: str = Field(max_length=120)
    url: Url


class Link(BaseModel):
    icon: Emoji = "🔗"
    label: str = Field(max_length=60)
    url: Url


class OnboardingStep(BaseModel):
    icon: Emoji = "✅"
    title: str = Field(max_length=120)
    items: list[Line] = Field(default_factory=list, max_length=20)
    links: list[Link] = Field(default_factory=list, max_length=6)


class Callout(BaseModel):
    title: str = Field(max_length=120)
    text: str = Field(max_length=500)


class AreasInfo(BaseModel):
    intro: str = Field("Conheça os espaços de lazer e convivência do condomínio.", max_length=400)
    callout: Callout | None = None


class Tabs(BaseModel):
    """Abas que o morador vê. A Início é sempre visível."""
    areas: bool = True
    documentos: bool = True
    faq: bool = True
    novo_morador: bool = True
    vendas: bool = True
    contatos: bool = True


class CondominiumConfig(BaseModel):
    identity: Identity = Field(default_factory=Identity)
    address: Address = Field(default_factory=Address)
    hero: Hero = Field(default_factory=Hero)
    contacts: list[Contact] = Field(default_factory=list, max_length=30)
    nearby: list[Place] = Field(default_factory=list, max_length=20)
    documents: list[Document] = Field(default_factory=list, max_length=30)
    onboarding: list[OnboardingStep] = Field(default_factory=list, max_length=12)
    areas: AreasInfo = Field(default_factory=AreasInfo)
    tabs: Tabs = Field(default_factory=Tabs)


SECTIONS = tuple(CondominiumConfig.model_fields)
_SECTION_ADAPTERS = {
    name: TypeAdapter(field.annotation) for name, field in CondominiumConfig.model_fields.items()
}


def validate_section(section: str, value: Any) -> Any:
    """Valida uma seção e devolve ela pronta pra guardar em JSON.

    Levanta ValidationError se o valor for inválido.
    """
    adapter = _SECTION_ADAPTERS[section]
    return adapter.dump_python(adapter.validate_python(value), mode="json")


def load_config(raw: dict | None) -> CondominiumConfig:
    """Lê o config guardado seção por seção.

    Uma seção que não valida mais (dado antigo, edição manual no banco) cai no
    default e é logada — o portal continua de pé em vez de dar 500.
    """
    sections = {}
    for name, value in (raw or {}).items():
        if name not in _SECTION_ADAPTERS:
            continue
        try:
            sections[name] = _SECTION_ADAPTERS[name].validate_python(value)
        except ValidationError:
            logger.warning("Seção '%s' do config inválida; usando o padrão.", name)
    return CondominiumConfig(**sections)


# ── Helpers usados nos templates ─────────────────────────
def _phone_digits(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    # Número brasileiro sem DDI (DDD + 8 ou 9 dígitos) ganha o 55.
    return f"55{digits}" if len(digits) in (10, 11) else digits


def whatsapp_url(phone: str) -> str:
    return f"https://wa.me/{_phone_digits(phone)}"


def tel_url(phone: str) -> str:
    return f"tel:+{_phone_digits(phone)}"


def maps_url(map_url: str, address: str) -> str:
    if map_url:
        return map_url
    return f"https://www.google.com/maps/search/?api=1&query={quote(address)}"


def hex_to_rgb(color: str) -> str:
    """'#667eea' -> '102, 126, 234' (pro rgba() do CSS)."""
    color = color.lstrip("#")
    return ", ".join(str(int(color[i:i + 2], 16)) for i in (0, 2, 4))
