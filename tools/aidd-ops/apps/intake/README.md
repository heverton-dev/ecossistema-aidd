# AIDD-Ops — Intake Web (Streamlit) · Anti-NIH #19

Frontend web do pipeline determinístico de infraestrutura (Intake → Curadoria → Sizing) do
**AIDD-Ops**, decretado na decisão de infraestrutura como **app gerenciado no Coolify**.

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

## Deploy como app gerenciado no Coolify

Pré-requisitos no painel Coolify: um **projeto** (nome opcional) e um **servidor** registrado.

1. **Commitar e publicar** o repositório (o Coolify constrói a partir do git público/registrado).
2. Configuração do app (tela *Public Repository* do Coolify):
   - Build Pack: `Dockerfile`
   - Base Directory: `tools/aidd-ops`
   - Dockerfile Location: `Dockerfile.intake`
   - Ports Exposes: `8501`
   - Branch: `main` (ou a desejada)
3. Opcional: definir domínio público no campo *Domains* (ex.: `intake.seusite.com.br`).
4. **Deploy**.

O Dockerfile já expõe `8501` com healthcheck real (`/_stcore/health`) e a CLI deste
monorepo permite automatizar os passos 2-4 sem tocar na UI:

```bash
# 1) Conferir a instância (dispensa token)
export COOLIFY_BASE_URL=https://seu-coolify.interno
export COOLIFY_API_TOKEN=seu_token

# 2) Descobrir o UUID do servidor e do projeto (somente leitura)
python tools/aidd-ops/scripts/pipeline_ops.py coolify servers
python tools/aidd-ops/scripts/pipeline_ops.py coolify apps

# 3) Registrar o app (dry-run por padrão — adicione --real para aplicar)
python tools/aidd-ops/scripts/pipeline_ops.py coolify create \
  --project-uuid <projeto> --server-uuid <servidor> \
  --repo https://github.com/<org>/<repo>.git --real

# 4) Variáveis de ambiente + deploy
python tools/aidd-ops/scripts/pipeline_ops.py coolify setenv --app <uuid-do-app> STREAMLIT_SERVER_HEADLESS=true --real
python tools/aidd-ops/scripts/pipeline_ops.py coolify deploy --app <uuid-do-app> --real
```

> Credenciais só entram por ambiente (`COOLIFY_BASE_URL`/`COOLIFY_API_TOKEN`) ou por flag
> `--url`/`--token` — nunca hardcoded. Leitura (`health`, `version`, `servers`, `apps`,
> `status`) roda sempre; escrita (`create`, `setenv`, `deploy`) exige `--real`.

## Testes

```bash
python -m pytest tools/aidd-ops/tests/test_intake_app.py tools/aidd-ops/tests/test_coolify.py -q
```

O contrato HTTP do Coolify em `test_coolify.py` é validado contra um servidor HTTP real
local que implementa o contrato da API v1 (nada de mocks). O `CoolifyManager` (contrato
de `scripts/pipeline_ops.py` (DeployOrchestrator) também é coberto: orquestração de stack,
isolamento VPS (portas internas ≥ 1024) e AppShell white-label seguem em dry-run
determinístico por padrão.