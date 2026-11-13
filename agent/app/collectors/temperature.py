import glob
import subprocess
from typing import Optional


def _read_float(path: str) -> Optional[float]:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read().strip()
        if not raw:
            return None
        val = float(raw)
        # Muitos kernels expõem miligraus Celsius
        if val > 1000:
            val = val / 1000.0
        return round(val, 2)
    except Exception:
        return None


def get_temperature_c() -> Optional[float]:
    # 1) Tenta zonas térmicas comuns do Linux/Android
    candidates = sorted(glob.glob("/sys/class/thermal/thermal_zone*/temp"))
    for path in candidates:
        temp = _read_float(path)
        if temp is not None and 0 < temp < 120:
            return temp

    # 2) Fallback: algumas builds expõem via `dumpsys battery` (não é CPU, mas útil)
    try:
        out = subprocess.check_output(
            ["dumpsys", "battery"], stderr=subprocess.STDOUT, text=True, timeout=5
        )
        for line in out.splitlines():
            if "temperature" in line:
                # geralmente em décimos de grau Celsius (ex.: 345 => 34.5)
                digits = "".join(ch for ch in line if ch.isdigit())
                if digits:
                    val = float(digits)
                    if val > 100:
                        val = val / 10.0
                    if 0 < val < 120:
                        return round(val, 2)
    except Exception:
        pass

    return None
