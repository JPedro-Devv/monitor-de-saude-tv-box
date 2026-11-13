import socket
import subprocess
from typing import Any, Dict, Optional


def _run(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=5)
        return out.strip()
    except Exception:
        return ""


def get_ip_address() -> Optional[str]:
    # Método simples: abre socket UDP para descobrir IP de saída (não envia pacote)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return None


def collect_network_info() -> Dict[str, Any]:
    ip = get_ip_address()
    # Heurística simples de VPN: procura interfaces tun/tap/wg via `ip addr`
    ip_addr_out = _run(["ip", "-o", "addr", "show"]) or _run(["ifconfig"])
    vpn_connected = any(tok in ip_addr_out for tok in ("tun", "tap", "wg"))
    interface = None
    for marker in ("tun0", "tun1", "wg0", "tap0"):
        if marker in ip_addr_out:
            interface = marker
            break
    return {
        "ip_address": ip,
        "vpn_connected": vpn_connected,
        "interface": interface,
    }
