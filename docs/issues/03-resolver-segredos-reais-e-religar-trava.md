---
id: ISSUE-0003
title: Resolver os alertas de segredo fora de teste e religar a trava
status: ready-for-agent
blocked_by: [ISSUE-0002]
created: 2026-09-19
source: open-decision sweep 2026-09-19
---

# ISSUE-0003 — Resolver os alertas de segredo fora de teste e religar a trava

**Deliver:** pushing a credential into the repo is automatically blocked again, on
every commit — or it is written down why it is not.

**Blocked by:** ISSUE-0002. With test noise cleared, the remaining alerts become readable.

## Verified this session

**5 alerts sit outside test files**, each a different kind of thing:

| Location | Apparent nature (confirm) |
|---|---|
| `chaves/manifesto/ed25519_public.json` | **public** key — public by definition, likely false positive |
| `componentes/compartilhado/src-core/security.py` | suspicious keyword in shared code — most serious of the list |
| `componentes/compartilhado/src-core/database_adapter.py` | DB credential in user:pass form |
| `tools/aidd-factory/templates/vsa/security.py` | project template — a secret here replicates into every new project |
| `tools/aidd-factory/scripts/phases/05_init_db.py` | DB init |
| `gates/dependencias_externas.json`, `tools/aidd-master/CAPABILITIES.json` | 3 alerts in config files |

**The real decision:** this gate was disabled on 2026-09-08 because it failed inside
the hook and passed outside, root cause never found. Two routes:

- **Route A — re-enable.** After clearing alerts, drop `stages: [manual]` and prove
  by test commit that the inside/outside mismatch does not return.
- **Route B — stay manual.** Only if the mismatch reappears. Then record the root
  cause found and define when the manual run is mandatory (e.g. before every push),
  so it does not decay into never.

Route B without an identified root cause is not acceptable — that is exactly how
this hole stayed open for 11 days.

## Acceptance criteria

- [ ] Each non-test alert classified false-positive or real-secret.
- [ ] Every real secret removed from source **and the credential rotated** — removal alone is insufficient, git history keeps it.
- [ ] Real hook (`pre-commit run --hook-stage manual g-segredos --all-files`) exits 0.
- [ ] Chosen route (A or B) recorded with justification in `.pre-commit-config.yaml`.
- [ ] Route A: a test commit proves the gate runs and produces no false positive inside the hook.
