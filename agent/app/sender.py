from typing import Any, Dict, Optional

import requests

from .config import config


def send_payload(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Envia o payload para o servidor e retorna a resposta JSON (ou None em falha)."""
    try:
        resp = requests.post(
            config.ingest_url,
            json=payload,
            timeout=config.http_timeout_seconds,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        if resp.content:
            return resp.json()
        return {"ok": True}
    except requests.RequestException as exc:
        print(f"[sender] falha ao enviar métricas: {exc}")
        return None
    except ValueError:
        # resposta não-JSON
        return {"ok": True}
