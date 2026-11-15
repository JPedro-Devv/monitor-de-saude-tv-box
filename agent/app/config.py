import os
from dataclasses import dataclass, field
from typing import List, Tuple

from dotenv import load_dotenv

load_dotenv()


def _parse_watched_apps(raw: str) -> List[Tuple[str, str]]:
    """Converte 'chave=pacote,chave2=proc' em lista [(chave, identificador), ...].
    Preserva a ordem e permite múltiplos apps com a mesma chave ou identificadores distintos."""
    apps: List[Tuple[str, str]] = []
    for item in (raw or "").split(","):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            key, value = item.split("=", 1)
            apps.append((key.strip(), value.strip()))
        else:
            # Se não houver chave explícita, usa o próprio valor como chave
            apps.append((item, item))
    return apps


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Config:
    device_id: str = os.getenv("DEVICE_ID", "tvbox-001")
    device_token: str = os.getenv("DEVICE_TOKEN", "")
    server_url: str = os.getenv("SERVER_URL", "http://localhost:8000").rstrip("/")
    ingest_path: str = os.getenv("INGEST_PATH", "/api/v1/ingest")
    interval_seconds: int = int(os.getenv("INTERVAL_SECONDS", "300"))
    http_timeout_seconds: int = int(os.getenv("HTTP_TIMEOUT_SECONDS", "15"))
    watched_apps: List[Tuple[str, str]] = field(
        default_factory=lambda: _parse_watched_apps(os.getenv("WATCHED_APPS", ""))
    )
    allow_reboot: bool = _env_bool("ALLOW_REBOOT", False)
    reboot_dry_run: bool = _env_bool("REBOOT_DRY_RUN", True)

    @property
    def ingest_url(self) -> str:
        path = self.ingest_path if self.ingest_path.startswith("/") else f"/{self.ingest_path}"
        return f"{self.server_url}{path}"


config = Config()
