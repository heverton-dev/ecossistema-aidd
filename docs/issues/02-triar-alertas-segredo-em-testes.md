---
id: ISSUE-0002
title: Triar os 26 alertas de segredo em arquivos de teste
status: ready-for-agent
blocked_by: []
created: 2026-09-19
source: open-decision sweep 2026-09-19
---

# ISSUE-0002 — Triar os 26 alertas de segredo em arquivos de teste

**Deliver:** most of the secret-scanner noise disappears. Every alert caused by a
fake test password is recorded as a known false positive, with a reason, and stops
resurfacing.

**Blocked by:** nothing. Start now.

## Verified this session

The gate scans for credentials hardcoded in source. Ran the real hook: **exit 1,
31 alerts**. Of those, **26 sit in test files** — where a fake password is the
expected pattern, written so the test has something to assert against.

| File | Alerts |
|---|---|
| `tests/test_properties.py` | 4 |
| `tools/aidd-enterprise/materiais-extras/examples/logistica-hub-v4/.../test_webhooks_studio.py` | 3 |
| `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/.../test_webhooks_studio.py` | 3 |
| `tools/aidd-bridge/tests/test_bridge.py` | 3 |
| `tests/unit/test_sandbox_runner.py` | 3 |
| `tools/aidd-master/tests/unit/test_jwt_hardening.py` | 2 |
| `tools/aidd-enterprise/tests/unit/test_jwt_hardening.py` | 2 |
| `tools/aidd-ops/tests/test_deploy.py` | 1 |
| other test/example files | 5 |

**Do not bulk-accept.** Project rule is real proof, not presumption. Living in a
test file makes an alert *probable* false positive, not *certain*. Inspect each one
before it enters the allowlist.

## Acceptance criteria

- [ ] All 26 inspected individually, each classified false-positive or real-secret, one line of reasoning each.
- [ ] False positives added to `.secrets.baseline` via the tool's official procedure — never by hand-editing the file.
- [ ] Any alert that turns out real gets promoted to ISSUE-0003.
- [ ] Re-running the real hook shows all 26 cleared (non-test alerts remain; they are ISSUE-0003 scope).
