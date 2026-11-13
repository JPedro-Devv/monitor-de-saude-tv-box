# Contexto do Projeto — TV Box Monitor

> Documento de handoff para preservar o contexto das decisões e do estado atual do projeto.
> Última atualização: 2026-11-13

## 1. Visão geral
Projeto para **monitorar a saúde de TV Boxes** conectadas via **VPN**, com agente rodando em **Termux (root, em segundo plano)** enviando métricas periodicamente a um **servidor central**. O servidor armazena histórico e envia **alertas via Telegram** quando um dispositivo fica sem contato além de um tempo limite. Funcionalidade-chave: **reboot remoto** do dispositivo para recuperar o funcionamento.

## 2. Requisitos e decisões (definidos até agora)

### Monitoramento
- **Métricas:** CPU, RAM, temperatura, espaço em disco, uptime, IP/rede (VPN), apps/serviços específicos e estado do monitor/tela.
- **Intervalo de envio (agente → servidor):** a cada **5 minutos** (300s).
- **Timeout/offline:** alerta se ficar **> 5 horas** sem enviar dados (tolerância a quedas longas de Wi-Fi).
- **Histórico:** armazenar medições ao longo do tempo.

### Alertas e controle
- **Canal de alerta:** Telegram (Bot API) para o técnico.
- **Reboot remoto:** funcionalidade essencial (reboot corrige o estado na prática). Solicitação via dashboard/outro cliente → servidor enfileira comando → agente recebe e executa.
- **Monitor/tela:** coletar e **registrar** estado no MVP; **alerta automático de monitor** fica no backlog (detecção de "monitor queimado" é ambígua — usar sinais como tela desligada/sem saída de vídeo).

### Ambiente e escala
- **Agente:** TV Box com acesso root, Termux em segundo plano, conectada à VPN.
- **Servidor:** iniciar em um **computador do trabalho**; migrar futuramente para **VPS**.
- **Escala:** piloto com poucas caixas; possibilidade de crescer para ~100–150 dispositivos.
- **Stack escolhida:** **Python** no agente e no servidor (maior familiaridade). Java fica para depois.

### Apps monitorados
- Haverá pelo menos **um app crítico** (exibe informações/anúncios na tela) a ser monitorado; identificador (pacote/processo) será definido posteriormente. Configurável via `WATCHED_APPS`.

## 3. Arquitetura proposta

### Fluxo de métricas (push)
1. Agente coleta métricas a cada 5 min.
2. Agente envia `POST /api/v1/ingest` com payload (device_id, token, métricas, rede, display, apps).
3. Servidor autentica, salva histórico em `metrics` e atualiza `devices.last_seen_at`.
4. Job periódico no servidor verifica dispositivos com `now - last_seen_at > 5h` e dispara alerta Telegram (registrando em `alerts` para evitar spam).

### Fluxo de comandos / reboot (controle)
- Modelo **pull-via-resposta** (compatível com agente atrás de VPN/NAT sem porta exposta):
  1. Comando de reboot é enfileirado no servidor (`commands`, status `pending`).
  2. Na resposta do `/ingest`, servidor devolve comandos pendentes e marca como `sent`.
  3. Agente executa o comando (com root) e futuramente reporta ack/resultado.
- **Latência:** até ~1 ciclo (5 min) no MVP; pode evoluir para polling dedicado mais frequente.
- **Sucesso do reboot:** como o device reinicia, confirmação real tende a ser inferida pelo retorno (novo contato / uptime menor).

## 4. Estrutura do repositório (proposta)

```text
tvbox-monitor/
├─ README.md
├─ docs/
│  ├─ CONTEXTO.md
│  ├─ arquitetura.md
│  ├─ modelo-dados.md
│  └─ backlog.md
├─ agent/                  # (esqueleto criado)
│  └─ app/ (collectors, executors, sender, config, main)
├─ server/                 # (a criar)
│  └─ app/ (api, models, services, jobs, db)
└─ scripts/
```

## 5. Modelo de dados proposto (servidor)

- **`devices`**: `id`, `name`, `token`/`token_hash`, `is_active`, `last_seen_at`, timestamps.
- **`metrics`** (histórico): `id`, `device_id` (FK), `reported_at`, `received_at`, `cpu_percent`, `memory_percent`, `disk_percent`, `temperature_c`, `uptime_seconds`, `ip_address`, `network_info`, `display_status`, `apps_status`, `raw_payload` (opcional).
- **`alerts`**: `id`, `device_id`, `type` (ex.: `offline_timeout`), `status`, `message`, `created_at`, `resolved_at` (controle de spam/reincidência).
- **`commands`** (fila/auditoria): `id`, `device_id`, `type` (ex.: `reboot`), `status` (`pending/sent/acknowledged/succeeded/failed/expired`), `payload`, `requested_at`, `sent_at`, `ack_at`, `executed_at`, `result_message`, `requested_by`.

Banco inicial sugerido: **SQLite** (PC do trabalho), com migração futura para **PostgreSQL**.

## 6. Contrato de payload (agente → servidor) — rascunho

```json
{
  "device_id": "tvbox-001",
  "token": "SEGREDO_DO_DISPOSITIVO",
  "reported_at": "2026-11-13T10:05:00-03:00",
  "interval_seconds": 300,
  "metrics": { "cpu_percent": 0, "memory_percent": 0, "disk_percent": 0, "temperature_c": null, "uptime_seconds": 0 },
  "network": { "ip_address": "10.8.0.15", "vpn_connected": true, "interface": "tun0" },
  "display": { "screen_on": true, "output_connected": true },
  "apps": [ { "key": "critico", "identifier": "com.app.anuncios", "running": true } ]
}
```

**Resposta do servidor (com comandos):**
```json
{ "ok": true, "server_time": "...", "commands": [ { "id": "cmd-123", "type": "reboot", "payload": {} } ] }
```

## 7. Estado atual (implementado)

- [x] **Esqueleto do agente (`agent/`)** criado:
  - Loop a cada 5 min, montagem de payload e envio HTTP (`POST /api/v1/ingest`).
  - Coletores: `system`, `network`, `temperature`, `apps`, `display` (best-effort, com fallbacks para Android/Termux).
  - Executor de comandos com suporte a `reboot` (protegido por `ALLOW_REBOOT`/`REBOOT_DRY_RUN`, padrão seguro/simulado).
  - Configuração via `.env` (`.env.example` incluso), `requirements.txt` e `README.md` do agente.
- [ ] Servidor (FastAPI + DB + ingest + fila de comandos + offline checker + Telegram) — **não iniciado**.
- [ ] Repositório git inicializado e commitado — **neste passo**.

## 8. Backlog / próximos passos
- [ ] Definir identificador do **app crítico** (pacote/processo) e ajustar `WATCHED_APPS`/coleta.
- [ ] Implementar **esqueleto do servidor**: FastAPI, modelos/tabelas, endpoint `/api/v1/ingest` (salvar métricas + retornar comandos), CRUD básico de devices/commands.
- [ ] Implementar **job de offline** (> 5h) e integração **Telegram**.
- [ ] Reportar **ack/resultado de comandos** (no próximo ingest ou endpoint dedicado).
- [ ] **Alerta automático de monitor** (ex.: tela/saída inativa por tempo configurável) — registrar já existe, alertar depois.
- [ ] Notificação de recuperação (device voltou), alertas por limiar (temp/disco/app parado).
- [ ] Fila local/retry persistente no agente para falhas de rede.
- [ ] Dashboard web (visualização, histórico, solicitação de reboot com confirmação).
- [ ] Migração SQLite → PostgreSQL e deploy em VPS; endurecer autenticação/rotação de tokens.

## 9. Observações para retomar no PC do trabalho
- O agente é *best-effort*: temperatura/display variam por modelo Android; validar coletores no dispositivo real.
- O reboot exige root e deve ser testado com cautela (começar com `REBOOT_DRY_RUN=true`).
- Servidor e agente se comunicarão pela **VPN**; configurar `SERVER_URL` do agente para o IP acessível do servidor.
- Próxima decisão sugerida: iniciar pelo **esqueleto do servidor** para fechar o fluxo ponta a ponta com o agente já criado.
