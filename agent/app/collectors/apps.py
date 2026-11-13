import subprocess
from typing import Any, Dict, List


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True, timeout=5)
    except Exception:
        return ""


def _is_process_running(identifier: str) -> bool:
    # Tenta `pidof` (comum) e fallback para `ps`
    if not identifier:
        return False
    out = _run(["pidof", identifier]).strip()
    if out:
        return True
    out = _run(["sh", "-c", "ps -A 2>/dev/null || ps"])
    return identifier.lower() in out.lower()


def collect_apps_status(watched_apps: Dict[str, str]) -> List[Dict[str, Any]]:
    """Retorna status dos apps monitorados.
    watched_apps: {chave_logica: pacote_ou_nome_do_processo}
    """
    results: List[Dict[str, Any]] = []
    for key, identifier in (watched_apps or {}).items():
        running = _is_process_running(identifier)
        results.append(
            {
                "key": key,
                "identifier": identifier,
                "running": running,
            }
        )
    return results
