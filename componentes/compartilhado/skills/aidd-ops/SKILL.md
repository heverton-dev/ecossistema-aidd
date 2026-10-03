---
name: aidd-ops
description: Runs the aidd-ops agentic infrastructure pipeline (VPS sizing, SSH hardening, Docker, Cloudflare, deploy). Use when the user wants to provision or deploy infrastructure, or says "ops", "/ops", "infraestrutura", "subir na VPS", "provisionar".
---

# aidd-ops

Agentic infrastructure meta-orchestrator of the ecosystem: provisioning pipeline, SSH runner, Docker and Cloudflare MCPs. Its infrastructure plan feeds `aidd-open`.

## Run

```bash
python ecossistema.py ops "<requirement>" --pasta <destination>
```

Slash command: `/ops <requirement>`.

Done when: the pipeline exits 0.

## Negative Guardrails

- NEVER run `ops bootstrap <host> --real` or `ops deploy <env> --real` before the same command passed in its default dry-run and the user named the real host: `--real` applies `tools/aidd-ops/ansible/playbooks/hardening.yml` (SSH hardening, UFW, fail2ban) and a wrong `--user`/`--key` locks you out of the VPS.
- NEVER call the legacy form `ops "<requirement>"` without `--pasta` (`_cmd_legado` raises a UsageError), and never run `ops plan` without `--pasta`: the default is a temp folder, so `aidd-open` never finds `PLANO-INFRAESTRUTURA.json`.
- NEVER hand-edit `PLANO-INFRAESTRUTURA.json` to clear a `[ERRO] <codigo>`: rerun `ops plan` with `--nicho`, `--dir-projeto` or `--ferramentas-json`; `validar_plano_contrato` and `tools/aidd-ops/gates/G_OPS_MVP.py --dir` reject a patched plan.
- NEVER leave a plain `.env` in a service folder or commit it: `ops cofre encrypt` it to `.env.enc` and keep the age private key from `ops cofre init --chave` outside the repo; rotate with `tools/aidd-ops/scripts/rotate_secrets.py`.
- NEVER read a failed `ops deploy` as rolled back: it only prints `rollback_recomendado` (containers, temporary DNS records, credentials); undo each item and tell the user before any re-run.

## Failure Modes & Fallback

- **`ops deploy` stops at an `etapa_com_falha`** (`validacao_plano`, `bootstrap_vps`, `configuracao_dns`, `validacao_infra`, `deploy_docker`, `preflight_e2e`): fix that stage only, rerun with `--dry-run`, then `--real`; never skip stages.
- **SSH unreachable or refused in `bootstrap`:** run `ops preflight <env> --host <host> --json`; if the port or key changed after hardening, stop and ask the user for console access instead of retrying.
- **`[ERRO] INFRA_NAO_GERADA`** (plan with `HANDOFF_PLANNER_ENGINE.json` in `--pasta`): the `moldes/infra/*` pieces were not written; check the planner handoff `perfil_app`, then rerun `ops plan --pasta <project>`.
- **Coolify path:** `ops coolify health` first; on `[ERRO]` from `ops coolify deploy <app> --real` read `ops coolify status <app>` and report, without forcing `--force`.

## Stopping Checklist

Prove each item with the exit code read from a file (`> x.log 2>&1; echo $? > x.rc`, read `x.rc`), never through a pipe.

- [ ] `python ecossistema.py ops plan "<requirement>" --pasta <dest>` exit 0 and `<dest>/PLANO-INFRAESTRUTURA.json` exists.
- [ ] `python tools/aidd-ops/gates/G_OPS_MVP.py --dir <dest>` exit 0.
- [ ] Every `--real` command ran only after its dry-run exit 0 and an explicit user OK for that host.
- [ ] `python ecossistema.py ops preflight <env> --host <host> --json` exit 0 after a real deploy.
- [ ] `git status --short` shows no `.env` or age key from this run.

## References

- Integration plan: `docs/planos/feitos/PLAN-0004-integracao-aidd-ops/00-PROCESSO-E-DECISOES.md`
- Architecture: `docs/features/06-09-2026_feature-arquitetura-aidd-ops.md`
