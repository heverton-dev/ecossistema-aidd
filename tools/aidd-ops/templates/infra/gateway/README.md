# Gateway FastAPI Mínimo

## O que é

Gateway leve baseado em **FastAPI + Uvicorn** que atua como ponto de entrada único para orquestrar chamadas entre microserviços da stack AIDD-Ops. Este template inclui apenas a infraestrutura Docker — o código Python da aplicação (`app/main.py`) deve ser criado conforme a necessidade do nicho.

## Por que um gateway próprio?

O gateway permite:
- **Agregação de APIs:** endpoint único que orquestra chamadas a múltiplos serviços (Twenty, Chatwoot, Cal.com, etc.).
- **Rate limiting e auth centralizada:** camada de segurança antes de atingir os serviços internos.
- **Transformação de dados:** formatação/validação de payloads entre sistemas.

Para reverse proxy público com TLS, use o bloco `traefik/` em vez deste.

## Uso

```bash
# 1. Criar o diretório da aplicação
mkdir -p app

# 2. Criar um main.py mínimo dentro de app/
# cat > app/main.py << 'EOF'
# from fastapi import FastAPI
# app = FastAPI(title="AIDD Gateway")
# @app.get("/health")
# def health(): return {"status": "ok"}
# EOF

# 3. Copiar e configurar o .env
cp .env.example .env

# 4. Subir
docker compose up -d

# 5. Verificar status
docker compose ps
docker compose logs gateway | grep "Started"
```

## Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `GATEWAY_ENV` | Não | Ambiente: production, staging, development |
| `GATEWAY_WORKERS` | Não | Workers Uvicorn (default: 2) |
| `GATEWAY_LOG_LEVEL` | Não | Nível de log (default: info) |
| `GATEWAY_PORT` | Não | Porta exposta (default: 8000) |
| `GATEWAY_MAX_RAM` | Não | Limite de memória (default: 256m) |

## Integração com outros blocos

- **Traefik:** para expor publicamente, adicione labels Traefik ao container `gateway`.
- **Todos os serviços:** o gateway conecta-se via rede `aidd_internal` a todos os demais blocos.
- **Nichos delivery/b2b_industrial:** ponto de entrada para APIs customizadas (Odoo, Listmonk, ERPNext, etc.).

## Portas expostas

| Porta | Serviço | Nota |
|---|---|---|
| 8000 | FastAPI Gateway | API Gateway interno |

## Imagens

- **FastAPI/Uvicorn:** `fastapi/uvicorn:latest` (Docker Hub — Tiangolo)
- **Dockerfile:** necessário para copiar `app/main.py` — incluído via volume bind-mount (`./app:/app/app:ro`).
- **Nota:** a imagem oficial `fastapi/uvicorn` já inclui FastAPI e Uvicorn. O código da aplicação é fornecido via volume.
