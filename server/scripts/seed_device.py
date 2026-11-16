"""Cria ou atualiza um dispositivo (uso no MVP).

Exemplos:
  python -m scripts.seed_device --id tvbox-001 --token 102030 --name "TVBox 001"
  python -m scripts.seed_device --id tvbox-001 --token 102030
"""

import argparse
import os
import sys

# permite executar como módulo a partir da pasta server/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sqlmodel import Session, select  # noqa: E402

from app.db import engine, init_db  # noqa: E402
from app.models import Device  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="ID do dispositivo (ex.: tvbox-001)")
    parser.add_argument("--token", required=True, help="Token do dispositivo")
    parser.add_argument("--name", default=None, help="Nome amigável (opcional)")
    args = parser.parse_args()

    init_db()
    with Session(engine) as session:
        device = session.get(Device, args.id)
        if device:
            device.token = args.token
            if args.name is not None:
                device.name = args.name
            device.is_active = True
            session.add(device)
            action = "atualizado"
        else:
            device = Device(id=args.id, token=args.token, name=args.name, is_active=True)
            session.add(device)
            action = "criado"
        session.commit()
        print(f"Dispositivo {action}: {device.id} (active={device.is_active})")


if __name__ == "__main__":
    main()
