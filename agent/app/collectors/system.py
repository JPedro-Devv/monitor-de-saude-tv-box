import os
import shutil
import subprocess
import time
from typing import Any, Dict, Optional


def _read_first_line(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.readline().strip()
    except Exception:
        return None


def get_uptime_seconds() -> Optional[int]:
    # /proc/uptime: "<segundos_ativo> <segundos_idle>"
    line = _read_first_line("/proc/uptime")
    if line:
        try:
            return int(float(line.split()[0]))
        except Exception:
            pass
    return None


def get_memory_percent() -> Optional[float]:
    # Lê /proc/meminfo (funciona bem em ambientes Linux/Android)
    try:
        meminfo: Dict[str, int] = {}
        with open("/proc/meminfo", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if ":" not in line:
                    continue
                key, rest = line.split(":", 1)
                parts = rest.strip().split()
                if not parts:
                    continue
                # valores em kB
                meminfo[key] = int(parts[0])
        total = meminfo.get("MemTotal")
        available = meminfo.get("MemAvailable")
        if total and available is not None and total > 0:
            used = total - available
            return round((used / total) * 100, 2)
    except Exception:
        return None
    return None


def get_disk_percent(path: str = "/") -> Optional[float]:
    try:
        usage = shutil.disk_usage(path)
        if usage.total == 0:
            return None
        used = usage.total - usage.free
        return round((used / usage.total) * 100, 2)
    except Exception:
        return None


def get_cpu_percent(sample_interval: float = 0.3) -> Optional[float]:
    """Calcula uso de CPU por amostragem de /proc/stat (sem dependências externas)."""

    def read_stat():
        line = _read_first_line("/proc/stat")
        if not line or not line.startswith("cpu "):
            return None
        parts = [int(x) for x in line.split()[1:]]
        if len(parts) < 4:
            return None
        idle = parts[3] + (parts[4] if len(parts) > 4 else 0)  # idle + iowait
        total = sum(parts)
        return total, idle

    first = read_stat()
    if not first:
        return None
    time.sleep(sample_interval)
    second = read_stat()
    if not second:
        return None

    total_delta = second[0] - first[0]
    idle_delta = second[1] - first[1]
    if total_delta <= 0:
        return None
    usage = (total_delta - idle_delta) / total_delta * 100
    return round(max(0.0, min(usage, 100.0)), 2)


def collect_system_metrics() -> Dict[str, Any]:
    return {
        "cpu_percent": get_cpu_percent(),
        "memory_percent": get_memory_percent(),
        "disk_percent": get_disk_percent("/"),
        "uptime_seconds": get_uptime_seconds(),
        # temperature_c pode vir de collector específico; mantido aqui como visão geral
    }
