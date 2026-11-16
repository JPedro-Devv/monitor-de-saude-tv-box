from fastapi import FastAPI

from .api.routes import router
from .db import init_db

app = FastAPI(title="TV Box Monitor Server", version="0.1.0")


@app.on_event("startup")
def on_startup():
    init_db()
    # Inicia verificação offline/alertas (envio Telegram depende de TELEGRAM_ENABLED + token/chat)
    try:
        from .jobs.scheduler import start_scheduler

        start_scheduler()
    except Exception:
        # Não impede o servidor de subir caso o agendador não esteja disponível
        pass


app.include_router(router, prefix="/api")
