# Requisitos e Status do Projeto

> Resumo rápido para retomada. Detalhes de arquitetura, modelo de dados e contratos: ver `docs/CONTEXTO.md`.

## 1. Objetivo
Monitorar a saúde de TV Boxes (via VPN) com agente em Termux/root enviando métricas a um servidor central, armazenando histórico, alertando offline no Telegram e permitindo reboot remoto.

## 2. Requisitos do MVP

### 2.1 Concluídos (Agente)
- [x] Coleta periódica configurável (padrão 5 min): CPU, memória, disco, uptime, temperatura, IP/rede (VPN), apps monitorados e conexão HDMI.
- [x] Monitoramento de múltiplos apps via `WATCHED_APPS` (chave=identificador), com status de execução.
- [x] Detecção de conexão/link HDMI via sysfs (`hdmi_connected`), com limitação conhecida: não indica monitor ligado/exibindo imagem.
- [x] Montagem e envio de payload JSON para `POST /api/v1/ingest` (com token do dispositivo), tolerando falhas de rede.
- [x] Recebimento e execução de comandos na resposta do ingest (executor de `reboot` com proteções `ALLOW_REBOOT`/`REBOOT_DRY_RUN`).
- [x] Empacotamento/release do agente automatizados via GitHub Actions (tags `agent-v*`, release `agent-v0.1.1` publicada).

### 2.2 Pendentes para concluir o MVP (Servidor e integração)
- [ ] **API/ingestão:** endpoint `POST /api/v1/ingest` para autenticar dispositivo (id/token), persistir métricas/histórico e atualizar `last_seen_at`.
- [ ] **Persistência/modelo de dados:** cadastro de dispositivos e armazenamento de histórico (`devices`, `metrics`) e registro de alertas/comandos (`alerts`, `commands`) — ex.: SQLite no início.
- [ ] **Fila de comandos (reboot):** enfileirar comando, devolver comandos pendentes na resposta do ingest e registrar estado/resultado (auditoria).
- [ ] **Detecção de offline:** job periódico que identifica ausência de contato > 5h (configurável) e dispara alerta.
- [ ] **Integração Telegram:** envio de alertas ao técnico, com controle para evitar notificações repetidas enquanto offline.
- [ ] **Gestão básica de dispositivos:** forma de cadastrar/ativar device e token para os agentes.
- [ ] **Validação ponta a ponta:** agente ↔ servidor (na rede/VPN acessível), incluindo entrega de comando de reboot.

### 2.3 Fora do escopo do MVP (infra/ambiente)
- Configuração dos **servidores/clientes VPN** e conectividade entre dispositivos e servidor (pré-requisito de rede, tratado à parte).

## 3. Requisitos futuros (backlog)
- [ ] Alertas automáticos de monitor/HDMI (ex.: desconectado por tempo configurável) — registro já existe; inferir “monitor queimado” não é garantido pelo sinal atual.
- [ ] Notificação de recuperação (dispositivo voltou a enviar).
- [ ] Alertas por limiar (temperatura alta, disco cheio, app crítico parado).
- [ ] Dashboard web (visualização, histórico, solicitação de reboot com confirmação).
- [ ] Ack/resultado de comandos dedicado (além da inferência por retorno de contato/uptime).
- [ ] Fila local/retry persistente no agente para períodos sem rede.
- [ ] Migração SQLite → PostgreSQL, deploy em VPS e endurecimento de autenticação/rotação de tokens.

## 4. Observações importantes
- `display.hdmi_connected` = detecção de link/cabo HDMI (hotplug), não garante monitor ligado/exibindo imagem.
- Identificadores dos apps críticos devem ser confirmados no dispositivo e configurados em `WATCHED_APPS`.
- Contratos e detalhes técnicos: `docs/CONTEXTO.md`.
