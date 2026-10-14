# AIDD-Ops

> Resumo e fronteiras canônicas: [README.md](README.md). Regras para agentes: [AGENTS.md](AGENTS.md).

**AIDD-Ops** é o Meta-Orquestrador Agêntico de Infraestrutura e Stacks Open Source do Ecossistema AIDD. A ferramenta estende o ecossistema para além da geração de código, permitindo receber requisitos de negócio em linguagem natural e orquestrar o provisionamento completo de stacks self-hosted (Traefik, Authentik, Next.js, PostgreSQL, microsserviços Docker) em VPS própria — como alternativa soberana e white-label ao GoHighLevel, sem limites artificiais de contatos ou sobretaxas de envio.

**Status atual:** Governança reconhecida desde o Pacote 2 da integração; implementação funcional do MVP (Fases 1-3 do pipeline — Intake, Curadoria, Sizing) chega no Pacote 3.

**Documentos de referência:**
- Plano arquitetural original: `docs/features/06-09-2026_feature-arquitetura-aidd-ops.md`
- Processo de integração: `docs/planos/integracao-aidd-ops/00-PROCESSO-E-DECISOES.md`
- Plano geral de integração: `docs/planos/integracao-aidd-ops/PLANO-INTEGRACAO-AIDD-OPS.md`

## Observabilidade e Monitoramento Ativo (Anti-NIH #14)

Substitui qualquer fabricação de dados ou dashboards estáticos por **Uptime Kuma** oficial:
- Template canônico: `templates/infra/uptime-kuma/docker-compose.yml`
- Módulo core: `src/core/uptime_kuma.py` (UptimeKumaManager)
- Suporte CLI: `python scripts/pipeline_ops.py monitor export|check`
- Healthchecks ativos reais (HTTP, portas, ping) sem dados hardcoded.


## Hardening de VPS (NIH #15: Ansible + devsec.hardening)

O bootstrap/hardening remoto (`src/core/ssh_runner.py`) não roda mais comandos
shell manuais via Paramiko: a política de hardening vive em
`ansible/playbooks/hardening.yml`, que aplica a coleção testada
[`devsec.hardening`](https://github.com/dev-sec/ansible-collection-hardening)
(`os_hardening`, `ssh_hardening`) mais tasks locais idempotentes (Docker,
firewall UFW, fail2ban, swap). Paramiko é mantido apenas como camada de
execução/transporte: pré-voo de conectividade (`SSHRunner.testar_conexao`) e
`ansible_connection=paramiko` no inventário efêmero gerado para cada run.

Setup do control node (requer Linux/WSL/CI — `ansible-core` não roda nativo
no Windows):

```bash
pip install -r requirements.txt
ansible-galaxy collection install -r ansible/requirements.yml -p ansible/collections
```

Tags fechadas disponíveis (ver `TAGS_PERMITIDAS` em `ssh_runner.py`):
`atualizar_pacotes`, `docker`, `firewall`, `fail2ban`, `os_hardening`,
`ssh_hardening`, `swap`.

## Deploy `compose-nativo`, Isolamento VPS e DNS (Anti-NIH #21)

Único motor de deploy (o Coolify foi abolido em 13/10/2026), para todos os fluxos:
- **Deploy (`src/core_ops/compose_deploy.py` — `ComposeDeployer`):** valida o nome do ambiente, empacota o projeto gerado pelo aidd-master **sem segredos** (`.env`, `.env.*`, chaves), `.git`, `node_modules` e builds, envia por SSH para `/opt/aidd/<ambiente>`, roda `docker compose up -d --build` e confere `docker compose ps`: todo serviço precisa estar `running` e sem `unhealthy`. As variáveis de runtime do projeto (`.env`) não sobem; o operador as cria na VPS.
- **Isolamento em VPS compartilhada (NIH #21):** `verificar_isolamento_compose()` reprova serviço que publica porta privilegiada (< 1024) do host além de 80 e 443.
- **DNS da borda (`src/core_ops/cloudflare_dns.py`):** registro A idempotente do subdomínio do app (cria, atualiza se o IP mudou, não mexe se está certo), com `CLOUDFLARE_API_TOKEN` e `CLOUDFLARE_ZONE_ID`; o token nunca aparece em saída ou erro.
- **Pipeline de Deploy:** `DeployOrchestrator` em `scripts/pipeline_ops.py`: `python scripts/pipeline_ops.py deploy <ambiente> --plano <PLANO-INFRAESTRUTURA.json> --host <ip> --domain <fqdn> [--real]` (padrão é simulação; o plano precisa vir de `ops plan --dir-projeto`).
- **Limite conhecido:** o transporte SSH real (`TransporteParamiko`) e a API real da Cloudflare não foram exercitados contra uma VPS e uma zona de verdade; o encadeamento está provado com SSH e HTTP injetados.

## Cofre de Credenciais (NIH #18/#29: sops + age)

Cofre local de segredos sem serviço externo — credenciais saem do `docker-compose.yml`/`.env` versionados e passam a viver cifradas.

**Por que sops + age (decisão 2026-09-07, vs Vaultwarden):** para o caso de uso do pipeline automatizado (deploy via SSH/Ansible em VPS), um cofre cliente-servidor traria um serviço + banco a manter, expor por rede e autenticar — sem ganho sobre uma cifragem assimétrica local não envolvendo rede. Detalhes e comparativo em `docs/planos/a-fazer/03-evolucao-aidd-ops-fase-completa/02-cofre-local-e-coleta-segura-de-credenciais.md`.

**Fluxo:**
1. **Gerar o cofre** — cria par de chaves age e o `.sops.yaml` com o `path_regex` agnóstico a separador de diretório (`templates[\\/]infra[\\/].*\.env$`, mirando o `.env` **de entrada**, não o `.env.enc`):
   ```bash
   python scripts/pipeline_ops.py cofre init \
     --chave "$HOME/.config/aidd/age-key.txt" \
     --sops-config "PATH_TO/modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/templates/infra/.sops.yaml"
   ```
2. **Cifrar** o `.env` de trabalho → `.env.enc` versionável (sem chave explícita usa o `.sops.yaml` descoberto a partir do diretório do `.env` ou do cwd; com `--chave-publica` usa uma config temporária catch-all via `--config`, nunca vazando para o repo):
   ```bash
   python scripts/pipeline_ops.py cofre encrypt \
     --env "templates/infra/calcom/.env" --saida "templates/infra/calcom/.env.enc"
   ```
3. **Subir serviço** — decifra o `.env.enc` no momento do `docker compose up`, sem deixar segredo em disco:
   ```bash
   python scripts/pipeline_ops.py cofre up --servico "templates/infra/calcom" --chave-privada "$HOME/.config/aidd/age-key.txt"
   ```

**Regras de ouro:**
- A chave **privada** age NUNCA entra no repositório (fica fora, ex.: `$HOME/.config/aidd/`). A chave **pública** (no `.sops.yaml` e no `.env.enc`) é pública por definição e é segura de versionar.
- `docker-compose.yml` referencia segredos apenas por interpolação `${VAR:?Defina ... no .env}` — o valor real viverá no cofre.
- A cifragem é explicitamente amarrada a uma config (`--config`), eliminando a dependência do cwd na descoberta de regras do sops.
- Cobertura real (17 testes em `tests/test_cofre_credenciais.py`, com os binários reais `sops`/`age-keygen`), incluindo a regressão do smoke CLI: `no matching creation rules found` em Windows + `.sops.yaml` não correspondente.

## Helm Chart e Testes de Integração (Item 10)

- **Chart canônico:** `charts/aidd-ops/` — instala infraestrutura base (PostgreSQL centralizado + Traefik) e serviços de aplicação (`services.apps.<slug>`), com resources por serviço injetáveis via `values.yaml`.
- **Testes de validação binária real:** `tests/test_helm_integration.py` executa `helm lint` e `helm template -f <values>` sobre o chart e afirma que os resources calculados pelo sizing real (Fase 3, `scripts/phases/03_sizing.py`) aparecem exatamente nos manifests renderizados (Deployments e PVCs).
- **Dependência externa:** requer o binário `helm` (>= v3) no PATH ou em `HELM_BIN`. Se ausente, a suíte pula honestamente (skip) — não simula aprovação.

## Notas para agentes (detalhe das regras 7 e 8 do AGENTS.md)

- **Nicho Dinâmico (Fluxo 02, fora do catálogo fixo):** `01_intake.reconhecer_nicho_dinamico` + `02_curadoria.curar_stack_dinamico` (`pipeline_ops.montar_plano_em_memoria(..., ferramentas_planejadas=[...])`, CLI `plan --ferramentas-json <arquivo>`) let a caller with an already-curated OSS tool list (e.g. `aidd-planner`'s PRÉ-PLANO) skip the 5-niche keyword match in `data/catalogo_nichos.json` entirely. Discriminador: `nicho_slug` prefixed `dinamico_` (`01_intake.DINAMICO_PREFIXO_SLUG`/`eh_nicho_dinamico`) — mirrors the existing `monolito_customizado` bypass for Fluxo 01. Sizing (`03_sizing.dimensionar`) needed no change — it was already 100% tool-name-driven and gracefully skips unknown tools.
- **Infra pelo perfil do app (Ticket 16, C2):** `plan ... --pasta <projeto>` with the planner's `HANDOFF_PLANNER_ENGINE.json` in that folder reads the `aidd-ops` tickets + `perfil_app` (`scripts/infra_perfil.py`, validated against the C2 schema) and writes `Dockerfile`, `docker-compose.yml`, `deploy.sh`, `nginx/` from the `moldes/infra/*` catalog pieces via `obter_peca`. Services follow the profile (`app`+`nginx`; `web` only with `frontend/Dockerfile`; `db` for PostgreSQL; `fila` when queues exist). Discriminador: `nicho_slug` prefixed `perfil_`. Niche is an optional shortcut: `--nicho`/`--dir-projeto`/`--ferramentas-json` take precedence; without a plant the old niche match is unchanged.
