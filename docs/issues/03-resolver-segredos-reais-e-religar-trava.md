---
id: ISSUE-0003
title: Resolver os alertas de segredo fora de teste e religar a trava
status: closed
closed_at: 2026-09-19
blocked_by: [ISSUE-0002]
created: 2026-09-19
source: open-decision sweep 2026-09-19
---

# ISSUE-0003 — Resolver os alertas de segredo fora de teste e religar a trava

**Deliver:** pushing a credential into the repo is automatically blocked again, on
every commit — or it is written down why it is not.

**Blocked by:** ISSUE-0002. With test noise cleared, the remaining alerts become readable.

## Verified this session

Non-test directory alerts individually inspected:

| Location | Factual Nature | Classification |
|---|---|---|
| `chaves/manifesto/ed25519_public.json:3` | Public key Ed25519 for CAPABILITIES.json manifest verification | False positive (public key is not a secret) |
| `componentes/compartilhado/src-core/database_adapter.py:405` | Documentation comment of connection string format (generic example in docstring) | False positive (explanatory comment) |
| `componentes/compartilhado/src-core/security.py:15` | Security sentinel constant asserting immediate abort if executed in production | False positive (local security sentinel) |
| `tools/aidd-bridge/aidd_bridge/cli.py:154` | DSN format example in CLI argument help string | False positive (help text) |
| `tools/aidd-master/CAPABILITIES.json:29` | SHA-256 hash of MCP security artifact for integrity | False positive (integrity checksum) |

Zero real secrets identified in source code. No external credential rotation required.

## Route Decision: ROUTE A (Re-enable Gate)

**Route A** successfully adopted:
- The `g-segredos` hook had `stages: [manual]` replaced by `always_run: true` in `.pre-commit-config.yaml`.
- Root cause of historical divergence (2026-09-08) resolved: `detect-secrets` requires `.secrets.baseline` to be staged when running in hook (`raise_exception_if_baseline_file_is_unstaged`) and the update scan to receive the full tree of tracked files so existing baselines are not pruned during merge.
- Execution of real hook both manual and re-enabled returned `exit 0` (`Passed`).

## Acceptance criteria

- [x] Each non-test alert classified false-positive or real-secret.
- [x] Every real secret removed from source **and the credential rotated** — (zero real secrets in repository; all proven false positives).
- [x] Real hook (`pre-commit run --hook-stage manual g-segredos --all-files`) exits 0.
- [x] Chosen route (A or B) recorded with justification in `.pre-commit-config.yaml` (Route A re-enabled).
- [x] Route A: a test commit proves the gate runs and produces no false positive inside the hook.
