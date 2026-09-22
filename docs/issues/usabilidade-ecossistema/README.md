# `docs/issues/usabilidade-ecossistema/` — Work Tickets

Initiative: **Melhorias de Usabilidade do Ecossistema-AIDD**  
Source: `docs/melhorias/22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md` (A1–A9, developer-confirmed 22-09-2026).  
Spec: `docs/melhorias/22-09-2026_especificacao-tecnica-usabilidade-ecossistema.md`.

Target: Fix distribution and communication failures of the Triad delivery path (Fluxo 02 proven) without rewriting VSA engines.

## Language Rule (AGENTS.md Law #4)
- **Title and `title:` field — PT-BR:** Fast visual scanning by Brazilian developers.
- **Body — English, telegraphic imperative:** Token-efficient agent instruction.
- **Field names and values — English:** Machine-parseable by gates and scripts.

## Invariant Laws Enforced
- **Law #1 (Determinism First):** Path/sync/lock-in checks are deterministic (parser, regex, helper) — zero LLM calls.
- **Law #2 (Binary Quality):** Every ticket verified by real tests with binary exit code (0 or 1).
- **Law #3 (Structured Persistence):** Spec and diagnosis live in `docs/melhorias/`; tickets in this folder — not in chat memory.
- **Law #4 (Extreme Token Economy):** Lay outputs stay short; core stays compact English.
- **Law #6 (Agnostic Supremacy):** Language/profile fixes apply across Claude, Gemini, Codex, MiMoCode, OpenCode harness files.
- **Law #7 (Developer in Control):** Ambiguous layout and user-file deletions stop and ask. No silent defaults on ambiguity.
- **Law #8 (Label Honesty):** Never claim “1 command, 1 URL” when degradation requires 2 commands.
- **Law #10 (Quarteto Sine Qua Non):** Unchanged — `/api`, `/webhook`, `/mcp`, `/docs`. Distinct from Rule 10 (response format).
- **Law #13 (Gate Must Bite):** All new gates include automated tests asserting exit 1 on violation.

## New Gates in This Initiative
| Gate | Covers |
|---|---|
| `G_SYNC_CMD_ROT` | A1 |
| `G_LAYOUT_ENTREGA` | A4, A6 |
| `G_USER_FACING_PTBR` | A2 |
| `G_PACOTE_CORE` | A3 |
| `G_RESUMO_USUARIO` | A5, A9 |
| `G_ANT_LOCKIN_LEGADO` | A7 |
