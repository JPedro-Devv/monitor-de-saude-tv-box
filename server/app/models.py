from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Device(SQLModel, table=True):
    __tablename__ = "devices"

    id: str = Field(primary_key=True, index=True)
    name: Optional[str] = None
    token: str
    is_active: bool = Field(default=True, index=True)
    last_seen_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Metric(SQLModel, table=True):
    __tablename__ = "metrics"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(foreign_key="devices.id", index=True)

    reported_at: Optional[datetime] = None
    received_at: datetime = Field(default_factory=utc_now, index=True)

    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    temperature_c: Optional[float] = None
    uptime_seconds: Optional[int] = None

    ip_address: Optional[str] = None
    vpn_connected: Optional[bool] = None
    network_interface: Optional[str] = None

    hdmi_connected: Optional[bool] = None
    display_info: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    network_info: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    apps_status: Optional[list[dict[str, Any]]] = Field(
        default=None, sa_column=Column(JSON)
    )
    raw_payload: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))


class Command(SQLModel, table=True):
    __tablename__ = "commands"

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    device_id: str = Field(foreign_key="devices.id", index=True)
    type: str = Field(index=True)  # ex.: reboot
    status: str = Field(default="pending", index=True)  # pending|sent|ack|succeeded|failed|expired
    payload: Optional[dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    requested_at: datetime = Field(default_factory=utc_now)
    sent_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    result_message: Optional[str] = None
    requested_by: Optional[str] = None


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"

    id: Optional[int] = Field(default=None, primary_key=True)
    device_id: str = Field(foreign_key="devices.id", index=True)
    type: str = Field(index=True)  # ex.: offline_timeout
    status: str = Field(default="active", index=True)  # active|resolved
    message: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: Optional[datetime] = None
