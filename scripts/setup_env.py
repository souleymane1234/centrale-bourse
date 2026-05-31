#!/usr/bin/env python3
"""Copie .env.example vers .env si .env est vide ou absent."""

import os
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(BASE, ".env")
EXAMPLE = os.path.join(BASE, ".env.example")


def main():
    if os.path.exists(ENV) and os.path.getsize(ENV) > 20:
        print(f"✅ {ENV} existe déjà — rien à faire.")
        return

    if not os.path.exists(EXAMPLE):
        print(f"❌ {EXAMPLE} introuvable.")
        raise SystemExit(1)

    shutil.copyfile(EXAMPLE, ENV)
    print(f"✅ Copié {EXAMPLE} → {ENV}")
    print("   Vérifiez MYSQL_HOST :")
    print("   - app lancée sur votre Mac → MYSQL_HOST=127.0.0.1")
    print("   - app dans un conteneur Docker → MYSQL_HOST=host.docker.internal")


if __name__ == "__main__":
    main()
