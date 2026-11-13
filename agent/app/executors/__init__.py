from typing import Any, Callable, Dict, List

from .reboot import execute_reboot

Handler = Callable[[Dict[str, Any]], Dict[str, Any]]

HANDLERS: Dict[str, Handler] = {
    "reboot": execute_reboot,
}


def process_commands(commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Executa comandos recebidos do servidor e retorna resultados locais."""
    results: List[Dict[str, Any]] = []
    for cmd in commands or []:
        cmd_type = cmd.get("type")
        handler = HANDLERS.get(cmd_type)
        if not handler:
            print(f"[executor] comando desconhecido/ignorado: {cmd}")
            results.append({"id": cmd.get("id"), "success": False, "message": "tipo desconhecido"})
            continue
        try:
            res = handler(cmd)
        except Exception as exc:
            res = {"success": False, "message": f"erro ao executar: {exc}"}
        res["id"] = cmd.get("id")
        res["type"] = cmd_type
        results.append(res)
    return results
