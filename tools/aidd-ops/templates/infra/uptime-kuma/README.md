# AIDD-Ops ? Template: Uptime Kuma (Observabilidade & Healthchecks Reais)

> **Substitui??o Anti-NIH #14:** Substitui o dashboard anterior (`dashboard_server.py`) que fabricava resultados hardcoded de preflight/portas por uma solu??o open-source madura, auto-hospedada e funcional de monitoramento cont?nuo.

---

## 1. Vis?o Geral

- **Imagem:** `louislam/uptime-kuma:1` (Docker Hub oficial).
- **Porta padr?o do host:** `3005` (evita qualquer colis?o com portas de outros servi?os como 3000 ou 3001).
- **Porta interna do container:** `3001`.
- **Roteamento Traefik:** Host configur?vel via `UPTIME_KUMA_HOST` (default: `status.localhost`).
- **Persist?ncia:** Volume `uptime_kuma_data` mapeado para `/app/data` (banco SQLite do Uptime Kuma mantido em disco).
- **Zero Dados Hardcoded:** Todos os status e healthchecks s?o checados em tempo real contra as inst?ncias ativas da infraestrutura.

---

## 2. Healthchecks Reais Integrados

O Uptime Kuma monitora ativamente:
- **Traefik Ping:** `http://aidd_traefik:80/ping` (ou rota exposta)
- **Twenty CRM:** `http://aidd_twenty_server:3000/healthz`
- **Cal.com:** `http://aidd_calcom_server:3000/api/health`
- **Chatwoot:** `http://aidd_chatwoot_web:3000/health_check`
- **PostgreSQL / Redis:** Ping TCP na rede interna `aidd_internal`

---

## 3. Comandos ?teis

```bash
# Validar sintaxe com vari?veis default
docker compose config

# Iniciar Uptime Kuma
docker compose up -d

# Visualizar logs
docker compose logs -f uptime-kuma
```
