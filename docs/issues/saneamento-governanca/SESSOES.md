# Sessões de execução — ordem obrigatória

Um bloco por sessão, **na ordem em que devem rodar**. Copie o prompt, abra conversa
nova, cole. Marque a caixa ao fechar.

A ordem não é por número de ticket — é por dependência real. Cada bloco declara o que
ele toca, para você enxergar por que ele está nesse lugar da fila.

**Dois arquivos concentram o risco de conflito:**

- `.pre-commit-config.yaml` — mexido pelas sessões 5, 6 e 7. Uma de cada vez.
- `AGENTS.md` — mexido pelas sessões 5, 10 a 15. A sessão 15 **reestrutura** o arquivo,
por isso é a última: rodar antes faria todo mundo editar algo prestes a mudar de forma.

---

## Fase 0 — concluída

- [x] **Session 1 — ISSUE-0011 parte 1** · regra "prove que morde" + 8 portões sem teste
- [x] **Session 2 — ISSUE-0011 parte 2** · auditoria dos 18 testes + meta-gate
- [x] **Session 3 — ISSUE-0010** · inventário das leis + `G_LEI_DECLARA_PORTAO`

---

## Fase 1 — consertar o cobrador antes de tudo

> Todo portão escrito daqui pra frente herda a rigidez definida aqui. Rodar qualquer
> sessão da Fase 5 antes desta produz portões frouxos que terão de ser refeitos.

- [x] **Session 4 — ISSUE-0019**

Toca: `gates/G_PORTAO_PROVA_QUE_MORDE.py` · Requer: nada

```bash
Execute docs/issues/saneamento-governanca/19-endurecer-cobrador-da-lei-13.md.

gates/G_PORTAO_PROVA_QUE_MORDE.py enforces Law #13 statically: it checks a test file exists, has test functions, and its text matches one of eleven regex patterns asserting exit 1. It never runs the tests. Then it prints "100% dos 26 Quality Gates provam que mordem".

Two defects: text inspection standing in for behaviour verification, and a coverage claim exceeding what was measured (Law #8).

Make it execute each gate's test suite and require the failing-path test to actually pass. Rewrite the output to claim only what is measured.

Rules:
- A test that pattern-matches but errors on execution must cause exit 1.
- Where deterministic verification of "the failing scenario touches the real invariant" is not achievable, write the limit into the gate output rather than implying it away.
- Its own failing-path test must EXECUTE, not pattern-match.
- Stop and ask before any commit.
```

- [x] **Session 5 — ISSUE-0009**

Toca: `gates/G_ZERO_HEADLESS.py`, hooks do harness · Requer: sessão 4

```bash
Execute docs/issues/saneamento-governanca/09-barreira-agentes-paralelos.md.

G_ZERO_HEADLESS is a facade: it checks that the string "interactive: bool = True" appears in one file and "--dangerously-force-headless" in another, never launches an agent, then prints "[OK] Zero risco de subagentes ocultos em concorrencia silenciosa".

Implement the real hook that intercepts concurrent subagent launches and blocks or demands explicit confirmation. Rewrite the gate to exercise that hook instead of grepping, and strip the unearned "zero risco" claim.

Rules:
- Real reproduction: attempt two parallel launches without confirmation, assert the block appears in output. Hook code existing does not count.
- Reproduce the legitimate path too: an explicitly requested launch passes.
- Known limit, state it explicitly: the recorded incident involved an external tool outside this repo, which no hook here can constrain. Claim no coverage that was not tested.
- Failing-path test must EXECUTE, per the strict Law #13 reading from session 4.
- Stop and ask before any commit.
```

---

## Fase 2 — risco aberto, sem conflito de arquivo

> Entra aqui porque é o único ticket com promessa de conformidade legal sem
> implementação, e não disputa arquivo com ninguém.

- [x] **Session 6 — ISSUE-0006**

Toca: `src/core/opentelemetry.py`, templates, doc de arquitetura · Requer: nada

```bash
Execute docs/issues/saneamento-governanca/06-trilha-de-auditoria-trace-id.md.

This ticket carries a route decision (A: implement, B: remove and correct the docs). Do NOT choose it yourself. Open by presenting both sides with the cost of each, then wait for the user's call.

Context already verified, do not re-derive: TraceContextMiddleware is built by a factory nothing calls; it extends Starlette BaseHTTPMiddleware while the generated server uses stdlib http.server, so it could never be mounted; occurrences of "trace" in the generated server template is zero. The architecture doc sells this as LGPD/GDPR compliance.

Rules:
- Route A requires a real end-to-end test: request enters carrying X-Trace-Id, same value returns in the response and appears in the log. The piece existing does not count.
- Route B requires correcting the architecture doc and book, removing the compliance claim.
- Either route leaves no dead piece in src/core/opentelemetry.py nor in the template and componentes/compartilhado mirrors.
- Stop and ask before any commit.
```

---

## Fase 3 — fila do `.pre-commit-config.yaml`

> As três sessões abaixo religam travas no mesmo arquivo. **Uma de cada vez**, nunca
> em paralelo, ou uma sobrescreve a outra.

- [x] **Session 7 — ISSUE-0001**

Toca: `.pre-commit-config.yaml`, `AGENTS.md` (Lei #10), livro · Requer: nada

```bash
Execute docs/issues/saneamento-governanca/01-faxina-registros-desatualizados.md.

Three records describe a reality that no longer exists:
1. The label-honesty gate sits in stages: [manual] pending a decision whose cause is gone — verified passing: exit 0, 68 files, zero banned terms. Re-enable it.
2. AGENTS.md Law #10 cites /swagger; every generated server serves /docs. Fix it.
3. PLAN-0025 item 10 lists CircuitBreaker as dead code. It is used in the server-generating template, has a state endpoint and tests. The src/core copy is byte-identical to templates/core. Record it as a mirror, not an orphan.

Rules:
- Remove the .pre-commit-config.yaml comments claiming a pending human decision for that gate.
- Book Appendix E stops listing it as open.
- A test commit confirms the re-enabled gate blocks nothing legitimate.
- Commit e push.
```

- [x] **Session 8 — ISSUE-0002 → ISSUE-0003**

Toca: `.secrets.baseline`, `.pre-commit-config.yaml` · Requer: sessão 7

```bash
Execute docs/issues/saneamento-governanca/02-triar-alertas-segredo-em-testes.md, then docs/issues/saneamento-governanca/03-resolver-segredos-reais-e-religar-trava.md.

31 alerts total: 26 in test files, 5 outside.

ISSUE-0002: inspect all 26 individually. Living in a test file makes an alert probable false positive, not certain. One line of reasoning each. False positives enter .secrets.baseline through the tool's official procedure, never by hand-editing the file.

ISSUE-0003: handle the 5 outside tests. Any real secret gets removed AND the credential rotated — removal alone is insufficient, git history keeps it. Then decide route A (re-enable the gate) or route B (stay manual). Route B is only acceptable with an identified root cause for the inside-hook / outside-hook mismatch that disabled it on 2026-09-08.

Rules:
- No bulk acceptance of any alert group.
- Verify with the real hook: pre-commit run --hook-stage manual g-segredos --all-files.
- Stop and ask before any commit.
```

- [x] **Session 9 — ISSUE-0004**

Toca: `src/core/` (master+enterprise), `.pre-commit-config.yaml` · Requer: sessão 8

```bash
Execute docs/issues/saneamento-governanca/04-zerar-violacoes-arquitetura-e-religar-trava.md.

18 SQL-outside-infrastructure violations in four files, two mirrored pairs across master and enterprise: transaction_log.py (7 each) and mcp_server.py (2 each). Move the DB calls into the infrastructure layer on both sides.

Mandatory FIRST: reconcile the 18 measured against the 212 PLAN-0023 predicted. If 194 template violations exist that the gate cannot see, the defect is gate coverage, not backlog. Settle which, in writing, before fixing anything.

Rules:
- Master/enterprise drift gate must keep approving.
- Verify with the real hook, then remove the gate from stages: [manual].
- Update PLAN-0023 item 1 with the real number and outcome.
- Stop and ask before any commit.
```

---

## Fase 4 — análise e decisões, sem construir nada

- [x] **Session 10 — ISSUE-0018**

Toca: doc de melhorias de ROT · Requer: nada

```bash
Execute docs/issues/saneamento-governanca/18-reconciliar-taxonomia-rot.md.

Analysis session, no gate construction.

The source document docs/melhorias/19-09-2026_melhoria-taxonomia-prevencao-rot-ecossistema.md proposes 10 gates. Six duplicate existing gates or open tickets. For each of the six, decide: deepen the existing gate, fold into the open ticket, or genuinely new. Default is NOT "new gate".

Also correct four false statements verified against the repo:
- "Lei #9 (Execução Limpa em Máquina Nova)" — Law #9 is Tool Testing Discipline. No law by that name exists.
- Architecture Rot mapped to Law #6 — Law #6 is Agnostic Supremacy (vendor lock-in), unrelated to slice boundaries.
- "combate via sandeco-token-reduce" — proven inert: nothing calls it, its availability check always fails.
- Docs Rot homologated and Law #13 exists — both correct, leave them.

Rules:
- Every decision carries its evidence: which existing gate covers the category, verified by reading it.
- Change the document status to reflect what was accepted and what was rejected, with reasons.
- Stop and ask before any commit.
```

- [x] **Session 11 — ISSUE-0007 e ISSUE-0008**

Toca: `src/core/`, skill `sandeco`, PLAN-0015, PLAN-0018 · Requer: nada

```bash
Execute docs/issues/saneamento-governanca/07-saga-orchestrator-ligar-ou-remover.md, then docs/issues/saneamento-governanca/08-compressor-sandeco-ligar-ou-remover.md.

Both carry route decisions. Do NOT choose them yourself. Present each trade-off to the user and wait.

Context already verified, do not re-derive:
- SagaOrchestrator: only its own test instantiates it; absent from the server template; byte-identical across src/core and templates/core. No broken documentation promise attached.
- sandeco compressor: nothing calls it; its availability check runs against the main Python where llmlingua is not installed, while the skill carries its own environment holding llmlingua 0.2.2 and anthropic 1.5.0, which the code never looks at. So it always falls back to truncation. PLAN-0015 item 5 records a saving that is not happening.

Rules:
- ISSUE-0008 route A requires measured before/after numbers at a real pipeline point, plus a test that fails if compression silently falls back. No estimates.
- ISSUE-0008 outcome closes the PLAN-0018 version-pinning item either way.
- Stop and ask before any commit.
```

---

## Fase 5 — portões novos

> Só entram depois da Fase 1. Cada um declara seu portão no `AGENTS.md`, então rodam
> em sequência, não em paralelo.

- [x] **Session 12 — ISSUE-0014 (Contract Rot)**

Toca: `gates/`, `AGENTS.md` · Requer: sessão 4

```bash
Execute docs/issues/saneamento-governanca/14-contract-rot-gate.md.

Build a gate that enumerates routes and response shapes as the generated server actually exposes them, and diffs them against the committed openapi.json. Exit 1 on any divergence, naming the diverging route.

Known trap, already measured: AGENTS.md Law #10 cited /swagger while every generated server serves /docs. Build against the real served paths, not the documented ones.

Rules:
- Enumerate from the running server, not from source comments.
- Failing-path test must EXECUTE, per the strict Law #13 reading: mutate one route's status code, run the gate, assert exit 1.
- Output claims only what it checks. No coverage language beyond the diff performed.
- Declare the gate against its law in AGENTS.md, per the ISSUE-0010 convention.
- Stop and ask before any commit.
```

- [x] **Session 13 — ISSUE-0015 (Env Rot)**

Toca: `gates/`, `AGENTS.md` · Requer: sessão 12

```bash
Execute docs/issues/saneamento-governanca/15-env-rot-gate.md.

Build a gate that AST-scans for os.getenv(...), os.environ[...] and process.env.*, and requires every key found to appear in .env.example. Exit 1 on any missing key, naming key and file. Also report orphan keys present in .env.example that no code reads.

The source document maps this to "Lei #9 (Execução Limpa em Máquina Nova)". That law does not exist — Law #9 is Tool Testing Discipline. Map it correctly before declaring.

Rules:
- AST, not regex, so dynamically constructed keys are detected or explicitly reported as undecidable.
- Failing-path test must EXECUTE: add an os.getenv call for an undocumented key, run the gate, assert exit 1.
- Declare the gate against its law in AGENTS.md, per the ISSUE-0010 convention.
- Stop and ask before any commit.
```

- [x] **Session 14 — ISSUE-0016 (Skill Rot)**

Toca: `gates/`, `AGENTS.md` · Requer: sessão 13

```bash
Execute docs/issues/saneamento-governanca/16-skill-rot-gate.md.

Build a gate that statically resolves every path, script reference and CLI command written inside SKILL.md bodies. Exit 1 on any reference that does not resolve.

Regression fixture: the sandeco-token-reduce case, where the middleware checks for llmlingua in the main interpreter while the library lives in the skill's own isolated environment. If the gate does not flag that case, the gate is insufficient.

Scope decision to make FIRST: skills are replicated across .claude/, .cursor/, .gemini/, .opencode/, .mimocode/, .agents/ and componentes/compartilhado/skills/. Decide whether the shared copy is source of truth and the rest are mirrors, or each is validated independently. Getting this wrong produces six duplicate failures per real defect.

Rules:
- Run against the current repo and triage the resulting list individually. No bulk suppression.
- Failing-path test must EXECUTE: rename a referenced script, run the gate, assert exit 1.
- Declare the gate against its law in AGENTS.md, per the ISSUE-0010 convention.
- Stop and ask before any commit.
```

- [x] **Session 15 — ISSUE-0017 (Migration Rot)**

Toca: `gates/`, `AGENTS.md` · Requer: sessão 14

```bash
Execute docs/issues/saneamento-governanca/17-migration-rot-gate.md.

Build a gate that applies every migration up then down against an ephemeral in-memory database per run, asserts convergence to the declared final schema, and proves re-application is idempotent. Exit 1 on divergence, missing rollback, or non-idempotent re-application.

Scope decision to make FIRST: the ecosystem targets both SQLite WAL and PostgreSQL. Decide whether the gate exercises both engines or only the default, and state the limit rather than implying both are covered.

Law at stake: #3, Structured Persistence.

Rules:
- No real database is touched. Ephemeral only.
- Idempotency is proven by re-application, never assumed.
- Failing-path test must EXECUTE: remove a rollback, run the gate, assert exit 1.
- Declare the gate against Law #3 in AGENTS.md, per the ISSUE-0010 convention.
- Stop and ask before any commit.
```

---

## Fase- Update [README.md](http://README.md) to reflect changes in the project's architecture.

- Fix Traefik configuration to ensure proper routing.

- Do not expose database ports in the production environment.

 6 — disciplina de saída

- [x] **Session 16 — ISSUE-0012 (gate de idioma)**

Toca: `gates/`, `AGENTS.md` · Requer: sessão 15

```bash
Execute docs/issues/saneamento-governanca/12-gate-de-idioma-lei-4.md.

Build the language gate for Law #4. Deterministic detection, zero LLM. Copy the shape of G_HONESTIDADE_ROTULO.

Define the path scope list FIRST and get it agreed — which paths must be English (ticket bodies, SKILL.md, prompt templates, gate output strings, AGENTS.md core), which stay PT-BR (title fields, INDEX.md, docs/ explanatory material, book, reports). That is the hard part, not the detector.

Detection: PT-BR marker density above a threshold — accented-character ratio plus a small closed list of structural words.

Measured justification: the 9 tickets first written in PT-BR prose cost 6,730 tokens; rewritten in telegraphic English, 4,826 — 28.3% cheaper. In a 100k budget that is 133 tickets versus 186.

Rules:
- Failing-path test must EXECUTE: feed PT-BR prose into a must-be-English path, assert exit 1.
- False-positive check against a PT-BR path that must NOT trigger, e.g. INDEX.md.
- Run against the current repo and triage violations individually. No bulk suppression.
- Declare the gate against Law #4 in AGENTS.md, per the ISSUE-0010 convention.
- Stop and ask before any commit.
```

- [x] **Session 17 — ISSUE-0013 (formato de resposta)**

Toca: `AGENTS.md`, hooks de todos os harnesses · Requer: sessão 16

```bash
Execute docs/issues/saneamento-governanca/13-formato-de-resposta-agnostico.md.

Encode the mandatory answer shape into AGENTS.md next to Rule 10, in compact English per Law #4:
1. One top sentence stating what to do or what happened. No preamble.
2. Short bulleted body. Facts, numbers, findings. No narration of steps taken.
3. One closing suggestion block, separated from the body.
Forbidden: introductions, restating the request, recapping what was just said, listing options without a recommendation.

Then extend .claude/hooks/regra10_check.py to check shape, not only jargon — deterministic, zero LLM — and replicate the hook into every harness that supports hooks: Cursor, Gemini, opencode, mimocode, qoder, codebuddy.

Rules:
- Harnesses without hook support get the rule in their pointer file AND an explicit entry in docs/protocolos/BACKLOG-LEIS-SEM-GATE.md saying enforcement is unavailable there. Never silently assume coverage.
- Failing-path test must EXECUTE: feed the hook a prolix answer, assert it blocks.
- Declare the hook against Law #4 in AGENTS.md, per the ISSUE-0010 convention.
- Stop and ask before any commit.
```

---

## Fase 7 — por último, porque reestrutura o arquivo

> A sessão 18 parte o `AGENTS.md` em dois. Todas as sessões acima escrevem nele.
> Rodar antes obrigaria a refazer cada declaração de portão no formato novo.

- [x] **Session 18 — ISSUE-0005**

Toca: `AGENTS.md` e todos os arquivos-ponteiro · Requer: sessões 7, 12 a 17

```bash
Execute docs/issues/saneamento-governanca/05-dividir-agents-md.md.

PLAN-0022 item 2 exists but its file is an unfilled template. The split is not designed yet. This is a design task before it is an execution task.

Decide and record: what stays core (inviolable laws, canonical flow, commit rules) versus what becomes on-demand (per-tool reference detail, decision history, long tables).

Rules:
- Core keeps every inviolable law and every gate declaration added by earlier sessions. No governance rule becomes on-demand.
- A real on-demand loading mechanism must exist. A file cut in half that nobody knows how to fetch does not count.
- Measure core size reduction in numbers, before and after.
- Pointer files for the other assistants (CLAUDE.md, GEMINI.md, QODER.md, CODEBUDDY.md) must still resolve.
- Stop and ask before any commit.
```

---

## Fase 8 — new gates for laws still marked "no gate"

> All six sessions below touch `AGENTS.md` and `.pre-commit-config.yaml` — same
> collision risk as Fase 5. Run one at a time in this checkout, in this order.
> To parallelize safely, isolate each session in its own `git worktree`
> (`git worktree add ../sessao-XX -b sessao-XX`), run each interactively in its
> own confirmed session (never headless/unattended — Law #7), then merge
> branches back to `main` **one at a time**, re-running the full gate suite
> after each merge. Sessions 21-23 correct a stale premise: `BACKLOG-LEIS-SEM-GATE.md`
> still lists Laws #3, #9 and #10 as "no gate", but Sessions 12-15 already gave
> them one. Add a second `Portão:` line under the existing one — never overwrite it.

- [x] **Session 19 — ISSUE-0020 (Law #1 determinism gate)**

Toca: `gates/`, `AGENTS.md`, `.pre-commit-config.yaml` · Requer: sessão 18

```bash
Execute docs/issues/saneamento-governanca/20-gate-determinismo-lei-1.md.

Law #1 (Determinism First) is convention-only today. Build a static check blocking
known LLM SDK imports/calls (anthropic, openai, google.generativeai, ...) inside
gates/*.py or any file a manifest tags deterministic-only.

Known limit, state it in the gate's own output: no static analyzer classifies
"mechanical" vs "cognitive" LLM usage in general. This gate covers only the known
SDK subset. Full coverage stays human-review territory.

Rules:
- Reuse detection logic already built for G_LLM_PROMPT_SHIELD.py where possible.
- Exceptions only via a documented, version-controlled list, never a silent skip.
- Failing-path test must EXECUTE: inject a synthetic file importing an LLM SDK into gates/, assert exit 1.
- False-positive check: a normal deterministic gate file passes (exit 0).
- Law #1 in AGENTS.md changes from "sem-gate" to name this gate, per ISSUE-0010.
- BACKLOG-LEIS-SEM-GATE.md row for Lei #1 updated to reflect coverage and its stated limit.
- Stop and ask before any commit.
```

- [x] **Session 20 — ISSUE-0021 (Law #2 binary-exit gate)**

Toca: `gates/`, `AGENTS.md`, `.pre-commit-config.yaml` · Requer: sessão 19

```bash
Execute docs/issues/saneamento-governanca/21-gate-saida-binaria-lei-2.md.

Law #2 (Binary Quality) is convention-only today. Build a gate auditing every
gates/*.py file: its only exit points must be sys.exit(0) or sys.exit(1) — no bare
return, no other numeric code, no unguarded exception falling through to Python's
implicit exit 0.

Rules:
- AST walk each gate file: find sys.exit call sites, flag any argument that is not literal 0 or 1.
- Flag any gate whose __main__ block can fall through without an explicit sys.exit call.
- Failing-path test must EXECUTE: synthetic gate file with sys.exit(2), assert exit 1.
- False-positive check: an existing compliant gate (e.g. G_HONESTIDADE_ROTULO.py) passes.
- Run against the current gates/ directory; triage violations individually, no bulk suppression.
- Law #2 in AGENTS.md changes from "sem-gate" to name this gate.
- BACKLOG-LEIS-SEM-GATE.md row for Lei #2 updated.
- Stop and ask before any commit.
```

- [x] **Session 21 — ISSUE-0022 (Law #3 second gate — orchestrator state persistence)**

Toca: `gates/`, `AGENTS.md`, `.pre-commit-config.yaml`, `docs/protocolos/BACKLOG-LEIS-SEM-GATE.md` · Requer: sessão 20

```bash
Execute docs/issues/saneamento-governanca/22-gate-persistencia-estruturada-lei-3.md.

Correction before starting: Law #3 already has a proven gate (gates/G_MIGRATION_ROT.py,
declared in AGENTS.md from Session 15). That gate covers generated-app database
migrations. This ticket covers a different surface: the orchestration tools' own
state files (flight_plan.json, .jsonl logs). Add a second Portão line under Law #3
in AGENTS.md — do not replace the existing one, do not claim the law was "sem-gate".

Known limit, state it in the gate's own output: cannot prove a negative ("no script
anywhere keeps state only in a variable") in general. Scope narrows to tools that
already claim structured persistence — verify the claim, do not invent global coverage.

Rules:
- Inventory tools claiming JSON/SQLite persistence, starting from flight_plan.json's schema and existing .jsonl writers. Keep the inventory list explicit in the gate; additions require a deliberate edit.
- Failing-path test must EXECUTE: run a tool with its persistence write disabled/corrupted, assert exit 1.
- False-positive check: a tool with valid persisted state passes.
- BACKLOG-LEIS-SEM-GATE.md row for Lei #3 updated to list both gates, not replace one with the other.
- Stop and ask before any commit.
```

- [x] **Session 22 — ISSUE-0023 (Law #9 third gate — tool-test-report freshness)**

Toca: `gates/`, `AGENTS.md`, `.pre-commit-config.yaml`, `docs/protocolos/BACKLOG-LEIS-SEM-GATE.md` · Requer: sessão 21

```bash
Execute docs/issues/saneamento-governanca/23-gate-disciplina-teste-ferramenta-lei-9.md.

Correction before starting: Law #9 already has two proven gates (G_ENV_ROT.py,
G_SKILL_ROT.py, from Sessions 13-14). Neither checks the 5-step test-and-report
cycle from PROTOCOLO-TESTES-FERRAMENTAS.md. Add a third Portão line under Law #9
in AGENTS.md — do not replace the existing two.

Rules:
- Define "touches a tool" as: the change set includes files under a tools/<name>/ path.
- Gate requires a report file under docs/teste-end-to-end/ whose git-log timestamp is not older than the change touching the tool; block if missing or stale.
- Wire into the same pre-commit path as the other gates.
- Failing-path test must EXECUTE: synthetic change touching a tool folder with a stale/missing report, assert exit 1.
- False-positive check: a change with a same-day updated report passes.
- BACKLOG-LEIS-SEM-GATE.md row for Lei #9 updated to list all three gates.
- Stop and ask before any commit.
```

- [x] **Session 23 — ISSUE-0024 (Law #10 second gate — root Quarteto Sine Qua Non)**

Toca: `gates/`, `AGENTS.md`, `.pre-commit-config.yaml`, `docs/protocolos/BACKLOG-LEIS-SEM-GATE.md`, `tools/aidd-planner/` · Requer: sessão 22

```bash
Execute docs/issues/saneamento-governanca/24-gate-quarteto-sine-qua-non-lei-10.md.

Correction before starting: Law #10 already has a proven gate (gates/G_CONTRACT_ROT.py,
from Session 12), which checks a running server's routes against the committed
openapi.json. This ticket is different: audit a generated deliverable for the 4
mandatory pillars (/docs, /webhooks, /mcp, /docs/guia) actually being present. Add a
second Portão line under Law #10 in AGENTS.md — do not replace the existing one.

Rules:
- Read tools/aidd-planner/scripts/gates/G_PLANNER_SINE_QUA_NON.py in full first; decide promote-in-place vs. wrap from root, record the decision and why.
- Gate takes a generated project path and asserts all 4 route groups resolve, via OpenAPI spec or live route registry.
- Run it against real fixture output from each of the 3 canonical flows (pure, open, factory-derived), not only the planner's own test fixture.
- Failing-path test must EXECUTE: fixture project missing one pillar (e.g. no /mcp), assert exit 1.
- False-positive check: a complete fixture with all 4 pillars passes.
- BACKLOG-LEIS-SEM-GATE.md row for Lei #10 updated to list both gates.
- Stop and ask before any commit.
```

- [x] **Session 24 — ISSUE-0025 (Law #11 stack gate)**

Toca: `gates/`, `AGENTS.md`, `.pre-commit-config.yaml`, `docs/protocolos/BACKLOG-LEIS-SEM-GATE.md` · Requer: sessão 23

```bash
Execute docs/issues/saneamento-governanca/25-gate-stack-padrao-ouro-lei-11.md.

Law #11 (Padrão-Ouro de Stack) is convention-only today. Build a gate rejecting a
generated project whose frontend is not Next.js + TypeScript + Tailwind, or whose
backend is not Python + SQLite WAL + OpenAPI 3.1 — unless the plan/prompt explicitly
authorized a different stack for that layer.

Rules:
- Parse the generated package.json / tsconfig.json / tailwind.config.* for Next.js, React, TypeScript and Tailwind CSS as declared deps.
- Pair with a backend check: SQLite journal_mode=WAL in generated DB init code, OpenAPI spec declares version 3.1.x.
- Honor the explicit-override clause in Law #11 (AGENTS.md §2.11): pass when the plan/prompt recorded an explicit different-stack decision for that layer; fail only on silent drift.
- Failing-path test must EXECUTE: fixture package.json without Tailwind, assert exit 1.
- False-positive check: fixture with an explicit recorded override for that layer passes.
- Run against proj_ctt's real generated output (the reference case named in Law #11); confirm it passes.
- Law #11 in AGENTS.md changes from "sem-gate" to name this gate.
- BACKLOG-LEIS-SEM-GATE.md row for Lei #11 updated.
- Stop and ask before any commit.
```

