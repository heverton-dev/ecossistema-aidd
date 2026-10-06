# Traefik com TLS Let's Encrypt

## O que é

Contêiner Traefik v3 que atua como **reverse proxy e terminação TLS automática** via Let's Encrypt. Todos os demais serviços da stack AIDD-Ops são expostos publicamente apenas através deste bloco.

## Como funciona

- **TLS Automático:** Certificados Let's Encrypt gerados via TLS-ALPN-01 challenge (sem dependência de DNS).
- **Proxy automático:** Containers Docker com labels `traefik.enable=true` são descobertos automaticamente via socket Docker.
- **Redirect HTTP→HTTPS:** Todas as rotas HTTP são redirecionadas para HTTPS automaticamente.

## Uso

```bash
# 1. Copiar e configurar o .env
cp .env.example .env

# 2. Editar .env (obrigatório: ACME_EMAIL)
# ACME_EMAIL=seu@email.com

# 3. Subir
docker compose up -d

# 4. Verificar status
docker compose ps
docker compose logs traefik | grep "ACME"
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `ACME_EMAIL` | Sim | E-mail para registro Let's Encrypt |
| `CF_DNS_API_TOKEN` | Não | Token DNS Cloudflare (só para DNS challenge) |
| `TRAEFIK_HTTP_PORT` | Não | Porta HTTP no host (default: 80) |
| `TRAEFIK_HTTPS_PORT` | Não | Porta HTTPS no host (default: 443) |
| `TRAEFIK_DASHBOARD_HOST` | Não | Host do dashboard (default: traefik.localhost) |
| `TRAEFIK_LOG_LEVEL` | Não | Nível de log (default: INFO) |
| `TRAEFIK_MAX_RAM` | Não | Limite de memória (default: 256m) |

## Como expor um serviço

Adicione labels ao seu `docker-compose.yml`:

```yaml
services:
  meu_servico:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.meu_servico.rule=Host(`meu.dominio.com`)"
      - "traefik.http.routers.meu_servico.entrypoints=websecure"
      - "traefik.http.routers.meu_servico.tls.certresolver=letsencrypt"
      - "traefik.http.services.meu_servico.loadbalancer.server.port=3000"
```

## Portas expostas

| Porta | Serviço | Nota |
|---|---|---|
| 80 | HTTP | Redireciona para HTTPS |
| 443 | HTTPS | Terminação TLS |

## Imagem

- **Oficial:** `traefik:v3.3` (Docker Hub — Traefik Labs)
- **Sem Dockerfile próprio** — imagem oficial cobre 100% do caso de uso.
