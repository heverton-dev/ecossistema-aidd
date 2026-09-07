# Item 11 — Corrigir deploy Docker do modulo gerado (pip install ausente, nginx/ inexistente, secret em texto plano)

> **Escopo:** Entra: template Dockerfile/docker-compose.yml do aidd-master (núcleo compartilhado com enterprise) — adicionar `pip install` de runtime, parar de referenciar `nginx/` inexistente (ou gerar a pasta), tirar `JWT_SECRET_KEY` de texto plano do compose. Não entra: mudar orquestração de containers em si (isso é aidd-ops).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Modelo sugerido:** Claude Sonnet · Antigravity Gemini 3.7 · MiMo mimo-v2.5-pro (3 correções coordenadas em template compartilhado)

---

## Contexto ja investigado

- Confirmado por fork rodando o projeto gerado: `Dockerfile:22-35` faz `ENTRYPOINT ["python","src/server.py"]` sem nenhum `pip install`; `requirements.txt` do projeto gerado só lista `pytest`/`requests`/`locust` (dependências de teste, zero dependência de runtime como fastapi/uvicorn) — build falharia com `ModuleNotFoundError`.
- `docker-compose.yml:32-33` monta `./nginx/nginx.conf` e `./nginx/ssl` como volumes obrigatórios do serviço nginx; a pasta `nginx/` não é gerada em nenhum lugar do template — `docker-compose up` falharia na criação do container nginx.
- `docker-compose.yml:11` tem `JWT_SECRET_KEY=aidd_enterprise_production_jwt_secret_scale_2026_super_secure` hardcoded em texto plano, rotulado "production" — fora do escopo do `gates/G_SEGREDOS.py` (que varre só o repo do framework, não o projeto gerado).
- Aplicação em si roda perfeitamente via `uvicorn` direto — o problema é isolado ao caminho de deploy via Docker.

## Definicao de Pronto

1. Gerar um novo módulo, rodar `docker compose build && docker compose up` (ou equivalente) de ponta a ponta sem editar nada manualmente — o serviço da aplicação sobe sem erro de dependência faltando.
2. Nenhum volume do compose referencia pasta inexistente no projeto gerado (ou a pasta passa a ser gerada junto).
3. Nenhum secret aparece em texto plano no `docker-compose.yml` gerado — vem de `.env`/gerado por instância no momento da criação do projeto.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 11: Corrigir deploy Docker do modulo gerado (pip install ausente, nginx/ inexistente, secret em texto plano).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 11: Corrigir deploy Docker do modulo gerado (pip install ausente, nginx/ inexistente, secret em texto plano).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
