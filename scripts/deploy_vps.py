"""Bootstrap do deploy na VPS (Oracle Cloud / Ubuntu 22.04, x86 ou ARM).

Roda DENTRO da VM, como root (sudo). Idempotente — pode rodar de novo
pra atualizar config sem quebrar nada existente.

Uso típico:
    # No seu Mac, mande o script pra VM:
    scp scripts/deploy_vps.py ubuntu@SEU_IP:/tmp/

    # Na VM:
    sudo REPO_URL=https://github.com/USER/site-barra-funda.git \\
         ADMIN_PASSWORD='senha-forte' \\
         python3 /tmp/deploy_vps.py

Variáveis suportadas (env ou flags --repo-url etc.):
    REPO_URL          (obrigatório)  URL git pública do repo
    ADMIN_PASSWORD    (obrigatório na 1ª execução) senha do admin em texto plano
    APP_DIR           default: /opt/barra-funda
    APP_USER          default: ubuntu
    SERVICE_NAME      default: barra-funda
    PUBLIC_HOST       default: _ (qualquer host); pode setar o IP/dominio

Pré-condições:
    - Ubuntu 22.04 LTS com acesso à internet
    - Regra de Ingress TCP/80 liberada na Security List da VCN (console Oracle)
"""
from __future__ import annotations

import argparse
import os
import secrets
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


def run(cmd: list[str] | str, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    print(f"$ {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    return subprocess.run(
        cmd,
        shell=isinstance(cmd, str),
        check=check,
        text=True,
        capture_output=capture,
    )


def require_root() -> None:
    if os.geteuid() != 0:
        sys.exit("Rode como root: sudo python3 deploy_vps.py ...")


def apt_install(packages: list[str]) -> None:
    env = {**os.environ, "DEBIAN_FRONTEND": "noninteractive"}
    subprocess.run(["apt-get", "update", "-qq"], check=True, env=env)
    subprocess.run(["apt-get", "install", "-y", "-qq", *packages], check=True, env=env)


def open_port_80() -> None:
    # Oracle Ubuntu vem com iptables bloqueando tudo fora 22. Insere regra
    # antes do REJECT genérico e persiste com netfilter-persistent.
    result = subprocess.run(
        ["iptables", "-C", "INPUT", "-p", "tcp", "--dport", "80", "-j", "ACCEPT"],
        capture_output=True,
    )
    if result.returncode != 0:
        run(["iptables", "-I", "INPUT", "6", "-m", "state", "--state", "NEW",
             "-p", "tcp", "--dport", "80", "-j", "ACCEPT"])
    if shutil.which("netfilter-persistent"):
        run(["netfilter-persistent", "save"], check=False)


def ensure_repo(app_dir: Path, app_user: str, repo_url: str) -> None:
    app_dir.mkdir(parents=True, exist_ok=True)
    run(["chown", f"{app_user}:{app_user}", str(app_dir)])
    if not (app_dir / ".git").exists():
        run(["sudo", "-u", app_user, "git", "clone", repo_url, str(app_dir)])
    else:
        run(["sudo", "-u", app_user, "git", "-C", str(app_dir), "pull", "--ff-only"])


def ensure_venv(app_dir: Path, app_user: str) -> Path:
    venv = app_dir / ".venv"
    if not venv.exists():
        run(["sudo", "-u", app_user, "python3", "-m", "venv", str(venv)])
    pip = venv / "bin" / "pip"
    run(["sudo", "-u", app_user, str(pip), "install", "-q", "-U", "pip"])
    run(["sudo", "-u", app_user, str(pip), "install", "-q", "-r",
         str(app_dir / "requirements.txt")])
    return venv


def bcrypt_hash(venv: Path, app_user: str, password: str) -> str:
    py = venv / "bin" / "python"
    result = subprocess.run(
        ["sudo", "-u", app_user, str(py), "-c",
         "import bcrypt,sys; pw=sys.stdin.read().rstrip('\\n').encode(); "
         "print(bcrypt.hashpw(pw, bcrypt.gensalt(rounds=12)).decode())"],
        input=password,
        text=True,
        check=True,
        capture_output=True,
    )
    return result.stdout.strip()


def write_env_file(app_dir: Path, app_user: str, password: str | None, public_host: str) -> None:
    env_path = app_dir / ".env"
    existing: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                existing[k.strip()] = v.strip()

    if "SECRET_KEY" not in existing or not existing["SECRET_KEY"]:
        existing["SECRET_KEY"] = secrets.token_urlsafe(48)

    if password:
        venv = app_dir / ".venv"
        existing["ADMIN_PASSWORD_HASH"] = bcrypt_hash(venv, app_user, password)
    elif "ADMIN_PASSWORD_HASH" not in existing:
        sys.exit("ADMIN_PASSWORD precisa ser fornecido na primeira execução.")

    origin = "http://" + (public_host if public_host != "_" else "localhost")
    existing.setdefault("ALLOWED_ORIGINS", origin)

    lines = [f"{k}={v}" for k, v in existing.items()]
    env_path.write_text("\n".join(lines) + "\n")
    os.chmod(env_path, 0o600)
    shutil.chown(env_path, user=app_user, group=app_user)


def write_systemd_unit(service_name: str, app_dir: Path, app_user: str) -> None:
    unit = dedent(f"""\
        [Unit]
        Description=Portal do Morador (FastAPI)
        After=network.target

        [Service]
        User={app_user}
        WorkingDirectory={app_dir}
        EnvironmentFile={app_dir}/.env
        ExecStart={app_dir}/.venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
        Restart=always
        RestartSec=3

        [Install]
        WantedBy=multi-user.target
    """)
    Path(f"/etc/systemd/system/{service_name}.service").write_text(unit)
    run(["systemctl", "daemon-reload"])
    run(["systemctl", "enable", service_name])
    run(["systemctl", "restart", service_name])


def write_nginx_conf(service_name: str, app_dir: Path, public_host: str) -> None:
    conf = dedent(f"""\
        server {{
            listen 80 default_server;
            server_name {public_host};
            client_max_body_size 10M;

            location /static/ {{
                alias {app_dir}/static/;
                expires 7d;
            }}

            location / {{
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }}
        }}
    """)
    available = Path(f"/etc/nginx/sites-available/{service_name}")
    enabled = Path(f"/etc/nginx/sites-enabled/{service_name}")
    default_link = Path("/etc/nginx/sites-enabled/default")
    available.write_text(conf)
    if not enabled.exists():
        enabled.symlink_to(available)
    if default_link.exists():
        default_link.unlink()
    run(["nginx", "-t"])
    run(["systemctl", "reload", "nginx"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy do site na VPS")
    parser.add_argument("--repo-url", default=os.getenv("REPO_URL"))
    parser.add_argument("--admin-password", default=os.getenv("ADMIN_PASSWORD"))
    parser.add_argument("--app-dir", default=os.getenv("APP_DIR", "/opt/barra-funda"))
    parser.add_argument("--app-user", default=os.getenv("APP_USER", "ubuntu"))
    parser.add_argument("--service-name", default=os.getenv("SERVICE_NAME", "barra-funda"))
    parser.add_argument("--public-host", default=os.getenv("PUBLIC_HOST", "_"))
    args = parser.parse_args()

    if not args.repo_url:
        sys.exit("REPO_URL é obrigatório (env ou --repo-url).")

    require_root()
    app_dir = Path(args.app_dir)

    print("→ Instalando pacotes do sistema")
    apt_install(["python3-venv", "python3-pip", "git", "nginx", "iptables-persistent"])

    print("→ Liberando porta 80 no firewall do OS")
    open_port_80()

    print("→ Clonando/atualizando repositório")
    ensure_repo(app_dir, args.app_user, args.repo_url)

    print("→ Criando venv e instalando dependências")
    ensure_venv(app_dir, args.app_user)

    print("→ Escrevendo .env (gera SECRET_KEY/hash se necessário)")
    write_env_file(app_dir, args.app_user, args.admin_password, args.public_host)

    print("→ Configurando systemd")
    write_systemd_unit(args.service_name, app_dir, args.app_user)

    print("→ Configurando Nginx")
    write_nginx_conf(args.service_name, app_dir, args.public_host)

    print()
    print(f"Pronto. Verifique: systemctl status {args.service_name}")
    print(f"Logs:           journalctl -u {args.service_name} -f")
    print(f"Acesse:         http://{args.public_host if args.public_host != '_' else '<IP-PUBLICO>'}/")


if __name__ == "__main__":
    main()
