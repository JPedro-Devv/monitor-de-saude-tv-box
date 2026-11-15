import subprocess
from typing import Any, Dict, Optional


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=5)
    except Exception:
        return ""


def _parse_connection_state(value: str) -> Optional[bool]:
    v = value.strip().lower()
    if not v:
        return None
    # exemplos: "HDMI=1", "HDMI=0", "1", "connected"
    if "=" in v:
        v = v.split("=", 1)[1].strip()
    if v in {"1", "connected", "on", "plugged"}:
        return True
    if v in {"0", "disconnected", "off", "unplugged"}:
        return False
    return None


def collect_display_status() -> Dict[str, Any]:
    """Coleta status de conexão HDMI/saída de vídeo via sysfs (sem dumpsys/su)."""
    result: Dict[str, Any] = {
        "output_connected": None,
        "notes": [],
    }

    # 1) DRM (quando disponível) pode indicar conexão física de saída
    drm = _run(["sh", "-c", "cat /sys/class/drm/*/status 2>/dev/null || true"])
    if drm:
        statuses = [s.strip().lower() for s in drm.splitlines() if s.strip()]
        if statuses:
            result["notes"].append("drm_status=" + ",".join(statuses))
            if any(s == "connected" for s in statuses):
                result["output_connected"] = True
            elif all(s != "connected" for s in statuses):
                result["output_connected"] = False

    # 2) HDMI/switch/extcon (device-específico). Ex.: "HDMI=1"/"HDMI=0"
    hdmi_raw = _run(
        [
            "sh",
            "-c",
            "cat /sys/class/switch/hdmi/state /sys/devices/virtual/switch/hdmi/state "
            "/sys/class/extcon/*hdmi*/state /sys/class/extcon/hdmi/state "
            "/sys/class/hdmi/hdmi/state 2>/dev/null || true",
        ]
    )
    hdmi_vals = [v.strip().lower() for v in hdmi_raw.splitlines() if v.strip()]
    if hdmi_vals:
        result["notes"].append("hdmi_state=" + ",".join(hdmi_vals))
        states = [_parse_connection_state(v) for v in hdmi_vals]
        known = [s for s in states if s is not None]
        # HDMI explícito tem prioridade como sinal de conexão do monitor
        if any(s is True for s in known):
            result["output_connected"] = True
        elif known and all(s is False for s in known):
            result["output_connected"] = False

    if not result["notes"]:
        result.pop("notes", None)
    return result
