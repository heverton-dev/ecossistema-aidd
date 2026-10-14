# AIDD-Ops — Intake Web (Streamlit) · Anti-NIH #19

Frontend web do pipeline determinístico de infraestrutura (Intake → Curadoria → Sizing) do
**AIDD-Ops**, entregue como app Docker comum (deploy pelo motor único `compose-nativo`).

Reusa 100% a lógica das fases do CLI: `intake_core.py` delega a
`pipeline_ops.montar_plano_em_memoria` — a mesma fonte única que o
`python scripts/pipeline_ops.py plan` usa. O JSON baixado aqui é idêntico ao
`PLANO-INFRAESTRUTURA.json` do CLI. Zero LLM, zero lógica duplicada.

## Execução local (Python)

```bash
python -m pip install -r apps/intake/requirements.txt
python -m streamlit run apps/intake/app.py            # http://localhost:8501
```

## Execução local (Docker)

```bash
docker compose -f apps/intake/docker-compose.yml up --build   # depois: http://localhost:8501
```

## Deploy (motor único `compose-nativo`)

O Intake Web é um projeto Docker como qualquer outro: o `Dockerfile.intake` expõe `8501` com healthcheck real
(`/_stcore/health`) e o `docker-compose.yml` desta pasta sobe o serviço. Para implantar numa VPS use o mesmo
caminho dos apps gerados (o Coolify foi abolido):

```bash
python ecossistema.py ops plan "Intake Web" --pasta <projeto-com-docker-compose>
python ecossistema.py ops deploy <ambiente> --plano <PLANO-INFRAESTRUTURA.json> --host <ip-da-vps> --domain <fqdn> --real
```

O deploy copia o projeto (sem `.env`) por SSH e roda `docker compose up -d --build`; precisa de `VPS_HOST`,
`VPS_USER`, `SSH_KEY_PATH` (ou `VPS_PASSWORD`), `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ZONE_ID` no `.env`.

## Testes

```bash
python -m pytest modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/tests/test_intake_app.py modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/tests/test_compose_deploy.py -q
```

O encadeamento do deploy (`test_compose_deploy.py`) é provado com SSH e HTTP injetados; o isolamento da VPS
(portas privilegiadas só 80 e 443) é verificado sobre o compose do projeto.
