"""Agendador do job de verificação offline (Telegram/alertas)."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session

from ..config import settings
from ..db import engine
from ..services.offline_checker import check_offline_devices

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _run_check() -> None:
    try:
        with Session(engine) as session:
            created = check_offline_devices(session)
            if created:
                logger.info("[offline-check] alertas gerados: %s", created)
    except Exception:
        logger.exception("[offline-check] erro ao verificar dispositivos offline")


def start_scheduler() -> BackgroundScheduler | None:
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        _run_check,
        "interval",
        minutes=max(1, int(settings.offline_check_interval_minutes)),
        id="offline_check",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "[offline-check] scheduler iniciado (intervalo=%s min, timeout=%s h)",
        settings.offline_check_interval_minutes,
        settings.offline_timeout_hours,
    )
    return _scheduler
