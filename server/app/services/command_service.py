from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from ..models import Command, Device


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def enqueue_command(
    session: Session,
    device_id: str,
    command_type: str = "reboot",
    payload: Optional[dict] = None,
    requested_by: Optional[str] = None,
) -> Command:
    device = session.get(Device, device_id)
    if not device:
        raise ValueError("device_not_found")

    cmd = Command(
        device_id=device_id,
        type=command_type,
        status="pending",
        payload=payload or {},
        requested_by=requested_by,
        requested_at=utc_now(),
    )
    session.add(cmd)
    session.commit()
    session.refresh(cmd)
    return cmd


def fetch_and_mark_pending_commands(session: Session, device_id: str) -> list[Command]:
    stmt = (
        select(Command)
        .where(Command.device_id == device_id, Command.status == "pending")
        .order_by(Command.requested_at.asc())
    )
    commands = list(session.exec(stmt).all())
    if not commands:
        return []

    now = utc_now()
    for cmd in commands:
        cmd.status = "sent"
        cmd.sent_at = now
        session.add(cmd)
    session.commit()
    for cmd in commands:
        session.refresh(cmd)
    return commands
