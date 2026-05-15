"""Gera um hash bcrypt para a senha do admin.

Uso:
    python scripts/generate_password_hash.py <senha>

Copie o hash gerado para a variável ADMIN_PASSWORD_HASH do .env.
"""
import sys
import bcrypt


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python scripts/generate_password_hash.py <senha>")
        sys.exit(1)

    password = sys.argv[1].encode("utf-8")
    if len(password) > 72:
        print("Senha muito longa (máximo 72 bytes).")
        sys.exit(1)

    hashed = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12)).decode()
    print(hashed)


if __name__ == "__main__":
    main()
