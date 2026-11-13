import subprocess
from typing import Any, Dict

from ..config import config
from .base import make_result


def execute_reboot(command: Dict[str, Any]) -> Dict[str, Any]:
    """Executa reboot do dispositivo.
    IMPORTANTE: requer root no dispositivo. Por segurança, o esqueleto respeita
    ALLOW_REBOOT e REBOOT_DRY_RUN definidos no .env.
    """
    cmd_id = command.get("id")

    if config.reboot_dry_run or not config.allow_reboot:
        reason = []
        if not config.allow_reboot:
            reason.append("ALLOW_REBOOT=false")
        if config.reboot_dry_run:
            reason.append("REBOOT_DRY_RUN=true")
        msg = f"reboot simulado (não executado): {', '.join(reason) or 'bloqueado'}"
        print(f"[executor:reboot] cmd={cmd_id} {msg}")
        return make_result(False, msg, simulated=True)

    # Comandos comuns em Android/Termux com root (podem variar por dispositivo)
    candidates = [
        ["su", "-c", "reboot"],
        ["su", "-c", "svc power reboot"],
        ["reboot"],
    ]

    print(f"[executor:reboot] cmd={cmd_id} iniciando reboot do dispositivo...")
    for cmd in candidates:
        try:
            # Popen: não esperamos conclusão, pois o sistema deve reiniciar
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return make_result(True, f"comando de reboot disparado: {' '.join(cmd)}", command=cmd)
        except Exception as exc:
            last_error = str(exc)

    return make_result(False, f"falha ao disparar reboot: {last_error if 'last_error' in locals() else 'desconhecido'}")
