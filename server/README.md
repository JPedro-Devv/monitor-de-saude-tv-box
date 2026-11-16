# Server (Monitor Central)

Servidor em **FastAPI + SQLModel (SQLite)** para receber métricas dos agentes, armazenar histórico, entregar comandos (ex.: reboot) e, futuramente, alertar offline via Telegram.

## Estrutura

```text
server/
├─ .env.example
├─ requirements.txt
├─ README.md
├─ scripts/
│  └─ seed_device.py         # cria/atualiza dispositivos e tokens
└─ app/
   ├─ main.py                # app FastAPI (startup: init DB)
   ├─ config.py              # configurações (.env)
   ├─ db.py                  # engine/sessão SQLite
   ├─ models.py              # tabelas: devices, metrics, commands, alerts
   ├─ schemas.py             # contratos de ingestão e comandos
   ├─ api/
   │  └─ routes.py           # endpoints HTTP
   ├─ services/
   │  ├─ ingest.py           # autentica, salva métricas, atualiza last_seen, retorna comandos
   │  ├─ command_service.py  # enfileira e marca comandos como enviados
   │  ├─ offline_checker.py  # lógica de offline/alerta (preparada)
   │  └─ telegram.py         # envio Telegram (stub/preparado)
   └─ jobs/
      └─ scheduler.py        # agendador do offline check (preparado)
```

## Configuração

```bash
cp .env.example .env
```

Variáveis principais:
- `DATABASE_URL` (padrão `sqlite:///./monitor.db`)
- `OFFLINE_TIMEOUT_HOURS` (padrão `5`) e `OFFLINE_CHECK_INTERVAL_MINUTES` (preparados)
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_ENABLED` (preparados para ativação futura)

## Execução

```bash
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A API ficará disponível em `http://<host>:8000/api`.

## Fluxo implementado (Opção B)

1. **Cadastro do dispositivo:** crie o device/token que o agente usará:
   ```bash
   python -m scripts.seed_device --id tvbox-001 --token 102030 --name "TVBox 001"
   ```
2. **Ingestão (agente → servidor):** `POST /api/v1/ingest`
   - Autentica `device_id` + `token`, salva histórico em `metrics` e atualiza `last_seen_at`.
   - Retorna comandos pendentes e os marca como `sent`.
3. **Reboot (comando remoto):** enfileire um comando para a TV Box:
   ```bash
   curl -X POST http://localhost:8000/api/v1/devices/tvbox-001/commands \
     -H "Content-Type: application/json" \
     -d '{"type":"reboot","requested_by":"tecnico"}'
   ```
   O agente receberá o comando na resposta do próximo ingest e executará conforme suas configs (`ALLOW_REBOOT`/`REBOOT_DRY_RUN`).

## Endpoints principais

- `GET  /api/health` — status do servidor
- `POST /api/v1/ingest` — recebe métricas e devolve comandos pendentes
- `GET  /api/v1/devices` — lista dispositivos
- `GET  /api/v1/devices/{id}/latest` — última métrica do dispositivo
- `POST /api/v1/devices/{id}/commands` — enfileira comando (ex.: `{"type":"reboot"}`)
- `GET  /api/v1/devices/{id}/commands` — lista comandos do dispositivo

## Telegram / Offline (preparado)

A lógica de verificação de offline e envio Telegram está preparada em `app/services/offline_checker.py` e `app/services/telegram.py`, mas o agendador não é iniciado nesta etapa. Para ativar futuramente:
1. Configurar `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` e `TELEGRAM_ENABLED=true` no `.env`.
2. Instalar `apscheduler` e habilitar `start_scheduler()` no `app/main.py`.

> Observação: no MVP o token do dispositivo é validado por comparação direta. O banco padrão é SQLite para facilitar execução local e migração futura.