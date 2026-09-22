# Sessões de Execução — Ordem Obrigatória

Iniciativa: **Melhorias de Usabilidade do Ecossistema-AIDD**  
Lei #7: uma sessão por ticket, execução estritamente sequencial e interativa. Zero subagentes headless invisíveis.

Copy the prompt block, open a new conversation/session, paste and execute. Mark the checkbox upon completion.

---

## Sessão 1 — ISSUE-USA-0001: Alias de sincronização e docs canônicos (A1)

**Touches:** `ecossistema.py`, `scripts/gestor_componentes.py`, `gates/G_SYNC_CMD_ROT.py`, `gates/test_g_sync_cmd_rot.py`, `MEMORY.md`, `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`, `docs/livros/**` · **Blocked by:** nothing

- [x] Concluída

```bash
Execute docs/issues/usabilidade-ecossistema/01-alias-sync-docs-canonicos.md.

Implement CLI aliases and fix canonical docs for component sync.
Must enforce:
- Canonical form: python ecossistema.py components sync --tipo todos.
- Accept: sync alias, --tipos synonym, missing --tipo defaults to 'todos' + 1-line warning.
- Unknown-command error prints the canonical copy-pasteable line and exits 1.
- Fix MEMORY.md:33, AGENTS-REFERENCIA-COMPLETA.md:181, docs/livros/** wrong forms.
- Gate gates/G_SYNC_CMD_ROT.py + bite test asserting exit 1 on dirty fixture (Law #13).
- Run: python ecossistema.py audit. Stop and ask before commit.
```

---

## Sessão 2 — ISSUE-USA-0002: Helper determinístico de posicionamento (A6)

**Touches:** `core/` (resolve_pasta_entrega), triad flow entrypoints, `gates/G_LAYOUT_ENTREGA.py`, `gates/test_g_layout_entrega.py`, `docs/livros/partes/02-fluxos.md` · **Blocked by:** Sessão 1

- [ ] Concluída

```bash
Execute docs/issues/usabilidade-ecossistema/02-helper-posicionamento-entrega.md.

Implement resolve_pasta_entrega(cwd, nome_projeto, pasta_arg=None) used by ALL triad flows.
Must enforce:
- Explicit --pasta wins; legacy sibling => workspace root (NEVER <clone>/projetos/).
- Ecosystem-only CWD => <clone>/projetos/<slug>.
- Ambiguity => structured PT-BR error with 2 options, zero disk writes (Law #7).
- Gate G_LAYOUT_ENTREGA + bite test exit 1 on nested-with-legacy fixture (Law #13).
- Document "cloned inside existing project" case in mini-livro.
- Run: python ecossistema.py audit. Stop and ask before commit.
```

---

## Sessão 3 — ISSUE-USA-0003: Entrega fora do clone e achatada (A4)

**Touches:** generator/factory/bridge path writers, delivery-card emitter, `git init` wiring · **Blocked by:** Sessão 2

- [ ] Concluída

```bash
Execute docs/issues/usabilidade-ecossistema/03-entrega-fora-clone-achatada.md.

Land generated project flat at resolve_pasta_entrega() result.
Must enforce:
- Layout: <pasta_entrega>/<app>/{src,frontend,tests,docker}. Kill proj_ prefix and double nesting.
- Delivery card (=== SEU APP ESTÁ PRONTO ===) with absolute path, one up-command, main URL, guide path.
- git init at delivery root or one manual command printed.
- E2E fixture: legacy sibling => delivery at workspace root, not projetos/.
- Run: python ecossistema.py audit. Stop and ask before commit.
```

---

## Sessão 4 — ISSUE-USA-0004: Perfil de linguagem leigo e GEMINI.md (A2)

**Touches:** `AGENTS.md`, `GEMINI.md`, `CODEX.md`, `MIMOCODE.md`, `OPENCODE.md`, `ecossistema.py` (preflight), `gates/G_USER_FACING_PTBR.py`, `docs/glossario/` · **Blocked by:** Sessão 1

- [ ] Concluída

```bash
Execute docs/issues/usabilidade-ecossistema/04-perfil-linguagem-leigo.md.

Make lay-facing surfaces simple PT-BR; unambiguous Rule 10 vs Law #10.
Must enforce:
- Labels: Rule 10 (Formato de Resposta) / Lei #10 (Quarteto) / Lei #4 (Idioma).
- GEMINI.md answer-shape rewritten in simple PT-BR (no English Mandatory Answer Shape).
- preflight-host --perfil leigo|tecnico with banned-jargon contract (spec §2.6).
- Rule 10 covers README, --help, gate messages, session reports.
- Gate G_USER_FACING_PTBR + bite test exit 1 on jargon fixture (Law #13).
- Generated /docs includes glossario (term -> everyday phrase).
- Run: python ecossistema.py audit. Stop and ask before commit.
```

---

## Sessão 5 — ISSUE-USA-0005: Ponto de entrada único da entrega (A5)

**Touches:** flow closers, `README-USUARIO.md` template, `docker-compose.yml`/`make run` umbrella, E2E golden path · **Blocked by:** Sessão 3

- [ ] Concluída

```bash
Execute docs/issues/usabilidade-ecossistema/05-ponto-entrada-unico.md.

One command brings the whole delivery up from the workspace root.
Must enforce:
- README-USUARIO.md ≤30 lines, zero acronym: install / one up-command / one main URL / other URLs.
- Umbrella compose or make run wiring legacy + connector + infra.
- Golden path from delivery root reaches HTTP 200 on main URL.
- Degradation: if Docker/ports down, print 2 commands + URLs; never lie "1 command" (Law #8).
- Run: python ecossistema.py audit. Stop and ask before commit.
```

---

## Sessão 6 — ISSUE-USA-0006: Pacote core enxuto (A3)

**Touches:** `.gitattributes`, `.gitignore`, `ecossistema.py` (package), `gates/G_PACOTE_CORE.py`, `gates/test_g_pacote_core.py`, README · **Blocked by:** Sessão 1

- [ ] Concluída

```bash
Execute docs/issues/usabilidade-ecossistema/06-pacote-core-enxuto.md.

Ship only functional core to end users. Kill 221MB/8186-file inflation.
Must enforce:
- .gitattributes export-ignore for tests/, *.db, requirements-dev*, caches, executor plans.
- .gitignore + remove committed residue (*.db, __pycache__, .worktrees, .ade_tmp).
- python ecossistema.py package --perfil usuario (or documented git archive/sparse recipe).
- INCLUDE core only; EXCLUDE docs/relatorios, docs/reports, docs/livros PDF/images.
- Gate G_PACOTE_CORE + bite test exit 1 on dirty release fixture (Law #13).
- Run: python ecossistema.py audit. Stop and ask before commit.
```

---

## Sessão 7 — ISSUE-USA-0007: Template duplo de encerramento (A9)

**Touches:** flow closers, `RESUMO-USUARIO.md` / `RELATORIO-TECNICO.md` templates, `gates/G_RESUMO_USUARIO.py`, `gates/test_g_resumo_usuario.py` · **Blocked by:** Sessão 1

- [ ] Concluída

```bash
Execute docs/issues/usabilidade-ecossistema/07-template-duplo-encerramento.md.

Every flow ends with lay summary AND technical report.
Must enforce:
- RESUMO-USUARIO.md ≤20 lines, zero acronym, 3 answers: o que mudou / como abro / como verifico.
- RELATORIO-TECNICO.md keeps full telemetry.
- Both at delivery root next to README-USUARIO.md.
- Gate G_RESUMO_USUARIO + bite test exit 1 on missing/overlong/wrong-shape fixture (Law #13).
- Run: python ecossistema.py audit. Stop and ask before commit.
```

---

## Sessão 8 — ISSUE-USA-0008: Varredura anti-lock-in (A7)

**Touches:** fluxo closers (open + freedom), `gates/G_ANT_LOCKIN_LEGADO.py`, `gates/test_g_ant_lockin_legado.py` · **Blocked by:** Sessão 1

- [ ] Concluída

```bash
Execute docs/issues/usabilidade-ecossistema/08-varredura-anti-lockin.md.

Deterministic lock-in sweep on any flow touching an existing project.
Must enforce:
- grep -rniE 'lovable|supabase|firebase' + residual dirs .lovable/, supabase/.
- Gate G_ANT_LOCKIN_LEGADO + bite test exit 1 on residue fixture (Law #13).
- Never auto-delete user files; list and ask (Law #7).
- Allowlist + note in RESUMO-USUARIO.md for intentional vendors (Law #8).
- Run: python ecossistema.py audit. Stop and ask before commit.
```

---

## Sessão 9 — ISSUE-USA-0009: Topologia Git padrão (A8)

**Touches:** delivery-root `git init`, nested-repo guard, mini-livro topology note, E2E usabilidade · **Blocked by:** Sessão 3

- [ ] Concluída

```bash
Execute docs/issues/usabilidade-ecossistema/09-topologia-git-padrao.md.

Standard Git boundaries: delivery root versionable; tool history never pollutes product repo.
Must enforce:
- Topology: <workspace>/.git (product), legacy subtree or declared own repo, tool outside.
- No silent triple-repo nesting (ecossistema-aidd + projetos/* + proj_*).
- Mini-livro 5-line topology standard.
- E2E: exactly one product .git at delivery root.
- Run: python ecossistema.py audit. Stop and ask before commit.
```

---

## Sessão 10 — Fechamento da iniciativa

**Touches:** `docs/issues/usabilidade-ecossistema/INDEX.md` · **Blocked by:** Sessões 1–9

- [ ] Concluída

```bash
Close initiative docs/issues/usabilidade-ecossistema/ after all 9 tickets.

Must enforce:
- Reproduce golden path from a clean clone of the tool: clone -> preflight-host -> fluxo -> 1 command -> 1 URL.
- Assert delivery at workspace root, card + README-USUARIO + RESUMO-USUARIO + RELATORIO-TECNICO present.
- Assert package --perfil usuario free of dev-only artifacts.
- python ecossistema.py audit exit 0.
- Flip ticket status to done in INDEX.md with evidence (Law #8, #12). Stop and ask before commit.
```
