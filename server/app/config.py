import os

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./monitor.db")

    offline_timeout_hours: float = float(os.getenv("OFFLINE_TIMEOUT_HOURS", "5"))
    offline_check_interval_minutes: int = int(
        os.getenv("OFFLINE_CHECK_INTERVAL_MINUTES", "5")
    )

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    telegram_enabled: bool = _env_bool("TELEGRAM_ENABLED", False)


settings = Settings()
