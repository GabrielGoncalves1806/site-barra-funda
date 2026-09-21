"""Super-admin do portal: cadastra condomínios, domínios e senhas.

Usa o banco do DATABASE_URL (.env). Senhas são pedidas sem eco no terminal,
então não ficam no histórico do shell.

    python manage.py create-condominium <slug> "<nome>"
    python manage.py add-domain <slug> <host>
    python manage.py remove-domain <host>
    python manage.py set-password <slug>
    python manage.py list
"""
import argparse
import getpass
import re
import sys

import bcrypt
from sqlmodel import Session, select

from database import engine
from models import Condominium, Domain
from tenancy import normalize_host

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MIN_PASSWORD_LENGTH = 8


def _hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"A senha precisa ter pelo menos {MIN_PASSWORD_LENGTH} caracteres.")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Senha muito longa (máximo 72 bytes).")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode()


def _get_condominium(session: Session, slug: str) -> Condominium:
    condominium = session.exec(select(Condominium).where(Condominium.slug == slug)).first()
    if not condominium:
        raise ValueError(f"Condomínio '{slug}' não existe.")
    return condominium


def create_condominium(session: Session, slug: str, name: str, password: str) -> Condominium:
    if not SLUG_RE.match(slug):
        raise ValueError("Slug inválido: use letras minúsculas, números e hífens (ex.: barra-funda).")
    if session.exec(select(Condominium).where(Condominium.slug == slug)).first():
        raise ValueError(f"Já existe um condomínio com o slug '{slug}'.")
    condominium = Condominium(slug=slug, name=name, password_hash=_hash_password(password))
    session.add(condominium)
    session.commit()
    session.refresh(condominium)
    return condominium


def add_domain(session: Session, slug: str, host: str) -> Domain:
    if not host or "/" in host:
        raise ValueError("Informe só o host, sem https:// nem caminho (ex.: portal.exemplo.com.br).")
    host = normalize_host(host)
    condominium = _get_condominium(session, slug)
    if session.get(Domain, host):
        raise ValueError(f"O host '{host}' já está em uso.")
    domain = Domain(host=host, condominium_id=condominium.id)
    session.add(domain)
    session.commit()
    session.refresh(domain)
    return domain


def remove_domain(session: Session, host: str) -> None:
    domain = session.get(Domain, normalize_host(host))
    if not domain:
        raise ValueError(f"O host '{host}' não está cadastrado.")
    session.delete(domain)
    session.commit()


def set_password(session: Session, slug: str, password: str) -> None:
    condominium = _get_condominium(session, slug)
    condominium.password_hash = _hash_password(password)
    session.add(condominium)
    session.commit()


def ask_password() -> str:
    password = getpass.getpass("Senha: ")
    if getpass.getpass("Repita a senha: ") != password:
        raise ValueError("As senhas não conferem.")
    return password


def main() -> None:
    parser = argparse.ArgumentParser(description="Super-admin do Portal do Morador")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create-condominium", help="cadastra um condomínio")
    create.add_argument("slug")
    create.add_argument("name")

    add = sub.add_parser("add-domain", help="liga um host a um condomínio")
    add.add_argument("slug")
    add.add_argument("host")

    remove = sub.add_parser("remove-domain", help="desliga um host")
    remove.add_argument("host")

    password = sub.add_parser("set-password", help="define a senha do admin de um condomínio")
    password.add_argument("slug")

    sub.add_parser("list", help="lista condomínios e domínios")

    args = parser.parse_args()
    with Session(engine) as session:
        try:
            if args.command == "create-condominium":
                condominium = create_condominium(session, args.slug, args.name, ask_password())
                print(f"Condomínio '{condominium.slug}' criado (id {condominium.id}).")
            elif args.command == "add-domain":
                domain = add_domain(session, args.slug, args.host)
                print(f"'{domain.host}' agora abre o portal de '{args.slug}'.")
            elif args.command == "remove-domain":
                remove_domain(session, args.host)
                print(f"'{args.host}' removido.")
            elif args.command == "set-password":
                set_password(session, args.slug, ask_password())
                print(f"Senha de '{args.slug}' atualizada.")
            elif args.command == "list":
                for condominium in session.exec(select(Condominium).order_by(Condominium.slug)).all():
                    hosts = session.exec(
                        select(Domain.host).where(Domain.condominium_id == condominium.id)
                    ).all()
                    status = "" if condominium.active else " [inativo]"
                    print(f"{condominium.slug}{status}: {condominium.name}")
                    for host in hosts:
                        print(f"  - {host}")
        except ValueError as exc:
            print(f"Erro: {exc}")
            sys.exit(1)


if __name__ == "__main__":
    main()
