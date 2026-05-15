"""Configuração de logging para a aplicação e audit log de ações admin."""
import logging
import sys


def setup_logging() -> None:
    """Configura logging para console em formato legível."""
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(logging.INFO)


# Logger dedicado para auditoria — facilita filtrar em produção.
audit_logger = logging.getLogger("audit")


def audit(action: str, **fields: object) -> None:
    """Registra uma ação de admin.

    Exemplo: audit("login_success", ip="1.2.3.4")
    """
    parts = " ".join(f"{k}={v!r}" for k, v in fields.items())
    audit_logger.info(f"action={action} {parts}".rstrip())
