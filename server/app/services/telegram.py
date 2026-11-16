import logging
from typing import Optional

import requests

from ..config import settings

logger = logging.getLogger(__name__)


def send_message(text: str, chat_id: Optional[str] = None) -> bool:
    """Envia mensagem via Telegram Bot API.
    Stub/preparado: retorna False se não estiver configurado/habilitado.
    """
    token = settings.telegram_bot_token
    target_chat = chat_id or settings.telegram_chat_id

    if not settings.telegram_enabled:
        logger.info("[telegram] desabilitado (TELEGRAM_ENABLED=false). Mensagem: %s", text)
        return False
    if not token or not target_chat:
        logger.warning("[telegram] não configurado (token/chat_id ausente).")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": target_chat, "text": text}, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as exc:
        logger.error("[telegram] falha ao enviar mensagem: %s", exc)
        return False
