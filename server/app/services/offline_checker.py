"""Verificação de dispositivos offline e disparo de alertas.

Preparado para o MVP: implementação completa (job/scheduler + integração Telegram)
será ativada quando o bot estiver configurado. Este módulo concentra a lógica
para facilitar a evolução.
"""

from datetime import datetime, timedelta, timezone

from sqlmodel import Session, select

from ..config import settings
from ..models import Alert, Device
from .telegram import send_message


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_last_contact(dt: datetime | None) -> str:
    if not dt:
        return "nunca"
    # converte para o fuso local do servidor e remove frações de segundo/offset na exibição
    local_dt = dt.astimezone().replace(microsecond=0)
    return local_dt.strftime("%d/%m/%Y às %H:%M:%S")


def _format_limit(hours: float) -> str:
    total_seconds = int(round(hours * 3600))
    if total_seconds < 60:
        return f"{total_seconds}s"
    total_minutes = total_seconds / 60
    if total_minutes < 60:
        if abs(total_minutes - round(total_minutes)) < 1e-9:
            return f"{int(round(total_minutes))} min"
        return f"{total_minutes:.1f} min".replace(".", ",")
    if abs(hours - round(hours)) < 1e-9:
        h = int(round(hours))
        return f"{h}h" if h != 1 else "1h"
    return f"{hours:.2f}h".replace(".", ",")


def check_offline_devices(session: Session) -> int:
    """Retorna quantidade de alertas gerados nesta execução."""
    threshold = utc_now() - timedelta(hours=settings.offline_timeout_hours)
    stmt = select(Device).where(Device.is_active == True)  # noqa: E712
    devices = list(session.exec(stmt).all())
    created = 0

    for device in devices:
        if device.last_seen_at and device.last_seen_at >= threshold:
            # voltou/está ok: resolve alerta ativo, se houver (sem notificar por enquanto)
            active = session.exec(
                select(Alert).where(
                    Alert.device_id == device.id,
                    Alert.type == "offline_timeout",
                    Alert.status == "active",
                )
            ).first()
            if active:
                active.status = "resolved"
                active.resolved_at = utc_now()
                session.add(active)
            continue

        # offline (nunca visto ou último contato antigo)
        existing_active = session.exec(
            select(Alert).where(
                Alert.device_id == device.id,
                Alert.type == "offline_timeout",
                Alert.status == "active",
            )
        ).first()
        if existing_active:
            continue

        last = _format_last_contact(device.last_seen_at)
        msg = (
            f"⚠️ Dispositivo offline: {device.id}\n"
            f"Último contato: {last}\n"
            f"Limite: {_format_limit(settings.offline_timeout_hours)}"
        )
        sent = send_message(msg)
        alert = Alert(
            device_id=device.id,
            type="offline_timeout",
            status="active",
            message=msg,
        )
        session.add(alert)
        created += 1
        _ = sent  # envio real depende de TELEGRAM_ENABLED/configuração

    session.commit()
    return created
