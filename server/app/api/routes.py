from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..db import get_session
from ..models import Command, Device, Metric
from ..schemas import CommandCreate, CommandOut, IngestRequest, IngestResponse
from ..services.command_service import enqueue_command
from ..services.ingest import process_ingest

router = APIRouter()


@router.get("/health")
def health():
    return {"ok": True, "time": datetime.now(timezone.utc).isoformat()}


@router.post("/v1/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, session: Session = Depends(get_session)):
    _, commands = process_ingest(session, payload)
    return IngestResponse(
        ok=True,
        server_time=datetime.now(timezone.utc),
        commands=[CommandOut(id=c.id, type=c.type, payload=c.payload) for c in commands],
    )


@router.get("/v1/devices")
def list_devices(session: Session = Depends(get_session)):
    devices = session.exec(select(Device)).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "is_active": d.is_active,
            "last_seen_at": d.last_seen_at,
            "created_at": d.created_at,
            "updated_at": d.updated_at,
        }
        for d in devices
    ]


@router.get("/v1/devices/{device_id}/latest")
def latest_metric(device_id: str, session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="device_not_found")
    metric = session.exec(
        select(Metric)
        .where(Metric.device_id == device_id)
        .order_by(Metric.received_at.desc())
    ).first()
    if not metric:
        raise HTTPException(status_code=404, detail="no_metrics")
    return metric


@router.post("/v1/devices/{device_id}/commands")
def create_command(
    device_id: str,
    body: CommandCreate,
    session: Session = Depends(get_session),
):
    try:
        cmd = enqueue_command(
            session,
            device_id=device_id,
            command_type=body.type,
            payload=body.payload,
            requested_by=body.requested_by,
        )
    except ValueError as e:
        if str(e) == "device_not_found":
            raise HTTPException(status_code=404, detail="device_not_found")
        raise
    return {
        "id": cmd.id,
        "device_id": cmd.device_id,
        "type": cmd.type,
        "status": cmd.status,
        "requested_at": cmd.requested_at,
    }


@router.get("/v1/devices/{device_id}/commands")
def list_commands(
    device_id: str,
    status: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
):
    if not session.get(Device, device_id):
        raise HTTPException(status_code=404, detail="device_not_found")
    stmt = select(Command).where(Command.device_id == device_id)
    if status:
        stmt = stmt.where(Command.status == status)
    stmt = stmt.order_by(Command.requested_at.desc())
    cmds = session.exec(stmt).all()
    return cmds
