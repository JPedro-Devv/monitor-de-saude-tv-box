import subprocess
from typing import Any, Dict, Optional


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=7)
    except Exception:
        return ""


def _parse_bool(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    v = value.strip().lower()
    if v in {"true", "1", "on", "yes"}:
        return True
    if v in {"false", "0", "off", "no"}:
        return False
    return None


def collect_display_status() -> Dict[str, Any]:
    """Coleta sinais do estado de tela/display (best-effort, varia por dispositivo Android).
    No MVP os dados são apenas registrados no servidor.
    """
    result: Dict[str, Any] = {
        "screen_on": None,
        "awake": None,
        "output_connected": None,
        "notes": [],
    }

    # 1) dumpsys power/display (requer permissões adequadas; em root/Termux costuma funcionar)
    power = _run(["dumpsys", "power"])
    if power:
        for line in power.splitlines():
            line_stripped = line.strip()
            if "mWakefulness=" in line_stripped:
                # Awake / Asleep / Dozing
                val = line_stripped.split("mWakefulness=", 1)[1].split()[0]
                result["awake"] = val
                result["screen_on"] = val.lower() == "awake"
            if "Display Power: state=" in line_stripped:
                state = line_stripped.split("state=", 1)[1].split()[0]
                result["notes"].append(f"display_power_state={state}")
                if result["screen_on"] is None:
                    result["screen_on"] = state.upper() == "ON"

    display = _run(["dumpsys", "display"])
    if display:
        lowered = display.lower()
        # heurísticas simples; podem ser refinadas por modelo de device
        if "mstate=on" in lowered or "state=on" in lowered:
            result["screen_on"] = True if result["screen_on"] is None else result["screen_on"]
        if "connected" in lowered:
            result["output_connected"] = True
        elif "disconnected" in lowered and result["output_connected"] is None:
            result["output_connected"] = False

    # 2) DRM (quando disponível) pode indicar conexão física de saída
    drm = _run(["sh", "-c", "cat /sys/class/drm/*/status 2>/dev/null || true"])
    if drm:
        statuses = [s.strip().lower() for s in drm.splitlines() if s.strip()]
        if any(s == "connected" for s in statuses):
            result["output_connected"] = True
        elif statuses and all(s != "connected" for s in statuses) and result["output_connected"] is None:
            result["output_connected"] = False
        if statuses:
            result["notes"].append("drm_status=" + ",".join(statuses))

    if not result["notes"]:
        result.pop("notes", None)
    return result
