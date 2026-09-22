---
id: ISSUE-USA-0008
title: Varredura anti-lock-in completa em legado (A7)
status: open
blocked_by: []
created: 2026-09-22
source: 22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md (A7)
---

# ISSUE-USA-0008 — Varredura anti-lock-in completa em legado (A7)

**Deliver:** Any flow that touches an existing project ends with a deterministic lock-in sweep. Supabase / `.lovable/` / firebase residues cannot ship silently.

**Blocked by:** nothing. Start now.

## Scope

1. End-of-flow deterministic checklist (regex/AST only — Law #1):
   ```bash
   grep -rniE 'lovable|supabase|firebase' <raiz_entrega> --include='*.{json,ts,tsx,js,py,toml,yml,yaml,md}'
   ```
   Also flag residual dirs: `.lovable/`, `supabase/`.
2. Gate `gates/G_ANT_LOCKIN_LEGADO.py`: exit 1 when residues remain in delivery tree.
3. Bite test `gates/test_g_ant_lockin_legado.py`: fixture with `supabase` ref + `.lovable/` dir asserts exit 1.
4. Removal of user-project residues requires explicit human confirm (Law #7) — list files, never auto-delete.
5. If intentional (e.g. self-hosted Supabase), require explicit allowlist entry + note in `RESUMO-USUARIO.md` (Law #8 honesty).
6. Wire checklist into Fluxo 02 (open) and Fluxo 03 (freedom/bridge) closers.

## Acceptance criteria

- [ ] Sweep runs on every flow that touches a pre-existing project.
- [ ] `G_ANT_LOCKIN_LEGADO` exit 1 on residue fixture; exit 0 on clean tree.
- [ ] No auto-delete of user files without confirm.
- [ ] Allowlist path documented for intentional vendors.
- [ ] `python ecossistema.py audit` exit 0.
