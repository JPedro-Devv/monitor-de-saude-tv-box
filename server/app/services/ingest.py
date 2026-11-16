from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session

from ..models import Device, Metric
from ..schemas import IngestRequest
from .command_service import fetch_and_mark_pending_commands


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_dict(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


def process_ingest(session: Session, payload: IngestRequest) -> tuple[Metric, list]:
    device = session.get(Device, payload.device_id)
    if not device or not device.is_active:
        raise HTTPException(status_code=401, detail="invalid_device")
    if device.token != payload.token:
        raise HTTPException(status_code=401, detail="invalid_token")

    now = utc_now()
    raw = payload.model_dump(mode="json")

    metric = Metric(
        device_id=device.id,
        reported_at=payload.reported_at,
        received_at=now,
        cpu_percent=payload.metrics.cpu_percent,
        memory_percent=payload.metrics.memory_percent,
        disk_percent=payload.metrics.disk_percent,
        temperature_c=payload.metrics.temperature_c,
        uptime_seconds=payload.metrics.uptime_seconds,
        ip_address=payload.network.ip_address,
        vpn_connected=payload.network.vpn_connected,
        network_interface=payload.network.interface,
        hdmi_connected=payload.display.hdmi_connected,
        display_info=_as_dict(payload.display),
        network_info=_as_dict(payload.network),
        apps_status=[_as_dict(a) for a in (payload.apps or [])],
        raw_payload=raw,
    )

    device.last_seen_at = now
    device.updated_at = now

    session.add(metric)
    session.add(device)
    session.commit()
    session.refresh(metric)

    commands = fetch_and_mark_pending_commands(session, device.id)
    return metric, commands
