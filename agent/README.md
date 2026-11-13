# Agent (TV Box / Termux)

Esqueleto do agente que roda na TV Box para **coletar métricas**, **enviar ao servidor** a cada intervalo e **executar comandos remotos** (ex.: reboot) recebidos na resposta.

## Estrutura

```text
agent/
├─ .env.example
├─ requirements.txt
├─ README.md
└─ app/
   ├─ main.py              # loop principal (coleta → envia → processa comandos)
   ├─ config.py            # configurações via variáveis de ambiente (.env)
   ├─ sender.py            # envio HTTP do payload para o servidor
   ├─ collectors/
   │  ├─ system.py         # CPU, RAM, disco, uptime
   │  ├─ network.py        # IP e heurística de VPN/interface
   │  ├─ temperature.py    # temperatura (thermal zones / dumpsys battery)
   │  ├─ apps.py           # status dos apps/processos monitorados
   │  └─ display.py        # estado da tela/saída de vídeo (registro no MVP)
   └─ executors/
      ├─ __init__.py       # despacho de comandos por tipo
      ├─ base.py
      └─ reboot.py         # reboot do dispositivo (com proteções de segurança)
```

## Como funciona (fluxo)

1. **Loop periódico** (`main.py`): executa um ciclo a cada `INTERVAL_SECONDS` (padrão: 300s / 5 min).
2. **Coleta**: os coletores em `app/collectors/` reúnem métricas de sistema, rede, temperatura, estado do display e apps monitorados (`WATCHED_APPS`).
3. **Montagem do payload** (`build_payload`): gera um JSON com `device_id`, `token`, timestamp, métricas, rede, display e apps.
4. **Envio** (`sender.py`): faz `POST` para `SERVER_URL + INGEST_PATH` (ex.: `/api/v1/ingest`).
5. **Comandos na resposta**: se o servidor responder com `commands` pendentes, o agente despacha para os executores em `app/executors/`.
   - `reboot`: executa (ou simula) o reinício do dispositivo.
6. **Resiliência**: erros de coleta/envio são logados e o loop continua no próximo ciclo.

## Payload (exemplo)

```json
{
  "device_id": "tvbox-001",
  "token": "...",
  "reported_at": "2026-11-13T10:05:00-03:00",
  "interval_seconds": 300,
  "metrics": {
    "cpu_percent": 23.4,
    "memory_percent": 61.0,
    "disk_percent": 72.5,
    "uptime_seconds": 86420,
    "temperature_c": 54.1
  },
  "network": { "ip_address": "10.8.0.15", "vpn_connected": true, "interface": "tun0" },
  "display": { "screen_on": true, "awake": "Awake", "output_connected": true },
  "apps": [ { "key": "critico", "identifier": "com.app.anuncios", "running": true } ]
}
```

Resposta esperada do servidor (quando houver comandos):

```json
{ "ok": true, "commands": [ { "id": "cmd-123", "type": "reboot", "payload": {} } ] }
```

## Configuração

1. Copie o exemplo e ajuste:
   ```bash
   cp .env.example .env
   ```
2. Principais variáveis:
   - `DEVICE_ID`, `DEVICE_TOKEN`: identificação/autenticação do dispositivo no servidor.
   - `SERVER_URL`, `INGEST_PATH`: endereço da API do servidor.
   - `INTERVAL_SECONDS`: intervalo de coleta/envio (padrão 300).
   - `WATCHED_APPS`: lista `chave=identificador` separada por vírgula (pacote ou nome de processo). Ex.: `critico=com.app.anuncios`.
   - `ALLOW_REBOOT` / `REBOOT_DRY_RUN`: controles de segurança para o executor de reboot.

## Execução (desenvolvimento / Termux)

> Requisitos: Python 3.10+ e acesso de rede ao servidor (VPN). Algumas coletas e o reboot podem exigir **root** no dispositivo.

```bash
pip install -r requirements.txt
python -m app.main
```

Para rodar em segundo plano no Termux, você pode usar `nohup`, `tmux`, ou serviços (`termux-services`/`runit`) conforme seu ambiente.

## Reboot remoto (MVP)

- O comando é entregue na **resposta do `/ingest`** (modelo pull-via-resposta), evitando conexão direta do servidor à TV Box.
- **Latência:** até ~1 ciclo (`INTERVAL_SECONDS`) para o agente receber o comando (evolução futura: polling mais frequente).
- **Segurança:** `ALLOW_REBOOT=false` e `REBOOT_DRY_RUN=true` por padrão no `.env.example` para evitar reinícios acidentais durante testes.
- **Confirmação de sucesso:** como o reboot derruba o dispositivo, o sucesso real costuma ser confirmado quando o device volta a reportar (uptime menor / novo contato).

## Observações e limitações (esqueleto)

- Coletas de **temperatura** e **display** são *best-effort* e variam por modelo/versão do Android; o código tenta múltiplas fontes (`/sys`, `dumpsys`, DRM) com fallback.
- O campo `apps` verifica processo/pacote de forma simples; a identificação exata do “app crítico” (pacote, activity em foreground etc.) deve ser ajustada quando você definir qual é.
- O envio ainda não possui fila local persistente para períodos sem rede (pode ser adicionado depois).
- O resultado do comando (ack) não é reenviado em endpoint dedicado neste esqueleto — evolução natural: reportar status no próximo `ingest` ou em `POST /commands/{id}/ack`.
