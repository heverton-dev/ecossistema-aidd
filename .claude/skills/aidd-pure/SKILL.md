---
name: aidd-pure
description: Runs Triad Flow 01 (build from scratch) end to end - forge, planner, the aidd-pure engine with strict TDD Red-Green, then master, enterprise and ops; also runs only the 8-phase engine that turns an idea into tested software. Use when the user wants a brand-new project from zero or an app from an idea, or types "/pure", "pure", "pure-motor", "/generate", "generate", "criar projeto do zero", "projeto do zero puro", "novo projeto com TDD", "gerar app a partir da ideia".
---

# aidd-pure (Flow 01, build from scratch)

Pipeline: `[FORGE -> PLANNER -> MASTER -> DISPATCH] -> {ENGINE nas Worktrees} -> [BARREIRA (Rebase Sync) -> ENTERPRISE -> OPS -> 54 GATES]`

| Stage | Tool | Output |
|---|---|---|
| 1. Fundação | `aidd-forge` | blindagem agentica e hooks git |
| 2. Planejamento | `aidd-planner` | contratos BDD/SDD, Quarteto Sine Qua Non, hash SHA-256 |
| 3. Fatiamento VSA | `aidd-master` | fatiamento vertical e contratos de fatias |
| 4. Despacho & Worktrees | `aidd-dispatch` | isolamento em git worktrees com micro-gates |
| 5. Motor | `aidd-pure` (`tools/aidd-pure`) | execução TDD Red-Green estrito em Clean Architecture |
| 6. Barreira & Rebase | `aidd-master` | rebase determinístico e merge das fatias |
| 7. Blindagem | `aidd-enterprise` | auditoria SHA-256 e blindagem corporativa |
| 8. Infraestrutura | `aidd-ops` | Dockerfile, Nginx SSL, compose |
| 9. Qualidade Global | `54 Gates` | auditoria determinística final |

## Steps

1. Collect or confirm name, slug, domain and destination folder with the user. Done when all four are known (slug and domain have defaults).
2. Simulate first:
   ```bash
   python ecossistema.py pure "My Project" gestao --dry-run
   ```
3. Run:
   ```bash
   python ecossistema.py pure "My Project" gestao
   # explicit flags
   python ecossistema.py pure --nome "My Project" --slug my-project --dominio gestao --pasta ./projetos/my-project
   # same engine
   python ecossistema.py run-fluxo --fluxo pure --nome "My Project" --slug my-project --dominio gestao --pasta ./projetos/my-project
   ```
   Positional form: `<name> [domain]`. Done when the command exits 0.
4. Confirm the delivery honors the Quarteto Sine Qua Non defined in `AGENTS.md` section 3 and a Next.js frontend.

## Engine invariants (`run-fluxo`)

- Synchronous: no stage starts before the previous one exits 0.
- Handoffs validated by JSON Schema (`componentes/compartilhado/specs/handoff-*.schema.json`).
- Fail-fast: any gate break stops the pipeline.
- Writes `ORQUESTRACAO_EXECUCAO.json` in the target folder.

## Engine only (`pure-motor`)

Runs just the 8-phase engine of `tools/aidd-pure`, without the other stages:
research and requirements, analysis and decomposition, architecture and design, technical decisions, artifacts and schemas (Draft 2020-12), full documentation, self-critique and gate audit, working implementation with automated tests.

```bash
python ecossistema.py pure-motor "<idea>"
```

Old name `generate` (and `/generate`) still works for one cycle and prints an "old name" warning (table in `componentes/compartilhado/specs/NOMES-ANTIGOS.json`).
Done when: the command exits 0 and the phase 8 tests pass.

## Negative Guardrails

- NEVER configure an LLM API key or set `AIDD_MODO=headless` to unblock a phase: the model is always the running harness, answering the delegated protocol in `<pasta>/.aidd/cache/` (`_llm_request_<id>.json` -> `_llm_response_<id>.json`).
- NEVER treat `pure ... --dry-run` exit 0 as proof: in dry-run the orchestrator skips every command and logs "contrato ... não conferido" for C1-C5.
- NEVER declare Flow 01 done without a red-then-green test: phase 8 (`--implementar-codigo`) must show the failing test first, then the passing run.
- NEVER point `--pasta` at an existing project or at the ecosystem root: stage 1 runs `git init` and `forge init <pasta> --force` there.
- NEVER hand-write `HANDOFF_*.json` or `ORQUESTRACAO_EXECUCAO.json` to skip a failed stage; each tool writes its own contract.

## Failure Modes & Fallback

- **"<tool> não gravou HANDOFF_...: o bastão não passa":** the named stage failed upstream; rerun that tool alone (`python ecossistema.py planner validate <pasta>/PLANNER.json`, `master`, `enterprise`) and restart `pure` only after it exits 0.
- **Phase waits on `_llm_request_<id>.json`:** you are the model. Read the request, write the JSON answer as `_llm_response_<id>.json` in the same folder; on timeout, rerun `python ecossistema.py pure-motor "<idea>" --pasta <dest> --resume` to skip finished phases.
- **`pure-motor` exits with "Missing option '--pasta'":** the engine requires `--pasta <dest>`; add it (the short form in "Engine only" omits it).
- **`python tools/aidd-pure/scripts/preflight_llm.py` reports "PRÉ-VOO FALHOU":** confirm you are inside a harness session (delegated mode); never fix it with a key.

## Stopping Checklist

- [ ] `python ecossistema.py pure --nome "<Name>" --slug <slug> --dominio <domain> --pasta <dest> > pure.log 2>&1; echo $? > pure.rc` and `pure.rc` holds `0`.
- [ ] `<dest>/ORQUESTRACAO_EXECUCAO.json` exists and `contratos_lidos` lists C1-C5 with sha256.
- [ ] `python gates/G_QUARTETO_SINE_QUA_NON.py --target <dest> > q-pure.log 2>&1; echo $? > q-pure.rc` holds `0` and `<dest>` has the Next.js frontend from step 4.
- [ ] `python -m pytest <dest> > t.log 2>&1; echo $? > t.rc` holds `0`, and a red run of the same test was observed before the green one.
- [ ] No API key was added to `.env`, the shell or any config during the run.
