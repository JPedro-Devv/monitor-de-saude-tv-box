from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class MetricsPayload(BaseModel):
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    disk_percent: Optional[float] = None
    uptime_seconds: Optional[int] = None
    temperature_c: Optional[float] = None


class NetworkPayload(BaseModel):
    ip_address: Optional[str] = None
    vpn_connected: Optional[bool] = None
    interface: Optional[str] = None


class DisplayPayload(BaseModel):
    hdmi_connected: Optional[bool] = None
    notes: Optional[list[str] | str] = None


class AppStatusPayload(BaseModel):
    key: Optional[str] = None
    identifier: Optional[str] = None
    running: Optional[bool] = None


class IngestRequest(BaseModel):
    device_id: str
    token: str
    reported_at: Optional[datetime] = None
    interval_seconds: Optional[int] = None
    metrics: MetricsPayload = Field(default_factory=MetricsPayload)
    network: NetworkPayload = Field(default_factory=NetworkPayload)
    display: DisplayPayload = Field(default_factory=DisplayPayload)
    apps: list[AppStatusPayload] = Field(default_factory=list)


class CommandOut(BaseModel):
    id: str
    type: str
    payload: Optional[dict[str, Any]] = None


class IngestResponse(BaseModel):
    ok: bool = True
    server_time: datetime
    commands: list[CommandOut] = Field(default_factory=list)


class CommandCreate(BaseModel):
    type: str = "reboot"
    payload: Optional[dict[str, Any]] = None
    requested_by: Optional[str] = None
