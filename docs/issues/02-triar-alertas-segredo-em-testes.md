---
id: ISSUE-0002
title: Triar os 26 alertas de segredo em arquivos de teste
status: closed
closed_at: 2026-09-19
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
31 alerts**. Of those, **26 sit in test/example files** — where a fake password is the
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
| other test/example files (`05_init_db.py`, `vsa/security.py`, `plano-implementacao.json`) | 5 |

### Individual Inspection of Alerts (1 line of reasoning each):
1. `tests/test_properties.py:81` (`Secret Keyword`): False positive — dummy secret in Hypothesis property test for JWT encode/decode.
2. `tests/test_properties.py:108` (`Secret Keyword`): False positive — synthetic key for JWT roundtrip test with mixed payloads.
3. `tests/test_properties.py:126` (`Secret Keyword`): False positive — dummy prefix for validating correct key in roundtrip.
4. `tests/test_properties.py:127` (`Secret Keyword`): False positive — dummy prefix to test deterministic rejection on wrong key.
5. `tests/unit/test_sandbox_runner.py:23` (`Secret Keyword`): False positive — mock API key variable to test sandbox sanitization.
6. `tests/unit/test_sandbox_runner.py:24` (`Secret Keyword`): False positive — mock DB password variable to test sandbox sanitization.
7. `tests/unit/test_sandbox_runner.py:25` (`Secret Keyword`): False positive — mock AWS credential to test sandbox removal.
8. `tools/aidd-bridge/tests/test_bridge.py:675` (`Secret Keyword`): False positive — dummy hash assert to test preservation of pre-hashed passwords during migration.
9. `tools/aidd-bridge/tests/test_bridge.py:844` (`Secret Keyword`): False positive — placeholder Cloudflare token in DNS teardown unit test.
10. `tools/aidd-bridge/tests/test_bridge.py:862` (`Secret Keyword`): False positive — placeholder SSH password in VPS teardown unit test.
11. `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/tests/unit/test_webhooks_studio.py:14` (`Secret Keyword`): False positive — dummy secret in webhook creation unit test.
12. `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/tests/unit/test_webhooks_studio.py:33` (`Secret Keyword`): False positive — dummy secret in webhook update unit test.
13. `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/tests/unit/test_webhooks_studio.py:73` (`Secret Keyword`): False positive — dummy HMAC secret in real webhook delivery test.
14. `tools/aidd-enterprise/materiais-extras/examples/logistica-hub-v4/tests/unit/test_webhooks_studio.py:14` (`Secret Keyword`): False positive — dummy secret in webhook creation unit test.
15. `tools/aidd-enterprise/materiais-extras/examples/logistica-hub-v4/tests/unit/test_webhooks_studio.py:33` (`Secret Keyword`): False positive — dummy secret in webhook update unit test.
16. `tools/aidd-enterprise/materiais-extras/examples/logistica-hub-v4/tests/unit/test_webhooks_studio.py:73` (`Secret Keyword`): False positive — dummy HMAC secret in real webhook delivery test.
17. `tools/aidd-enterprise/tests/unit/test_jwt_hardening.py:89` (`Secret Keyword`): False positive — sentinel insecure key asserting boot aborts in production.
18. `tools/aidd-enterprise/tests/unit/test_jwt_hardening.py:101` (`Secret Keyword`): False positive — dummy key validating successful boot in production.
19. `tools/aidd-master/tests/unit/test_jwt_hardening.py:89` (`Secret Keyword`): False positive — sentinel insecure key asserting boot aborts in production.
20. `tools/aidd-master/tests/unit/test_jwt_hardening.py:101` (`Secret Keyword`): False positive — dummy key validating successful boot in production.
21. `tools/aidd-ops/tests/test_deploy.py:188` (`Secret Keyword`): False positive — mock deploy token for orchestrator unit test.
22. `tools/aidd-factory/scripts/phases/05_init_db.py:39` (`Secret Keyword`): False positive — bash template with dynamic placeholder for example DB init.
23. `tools/aidd-factory/templates/vsa/security.py:29` (`Secret Keyword`): False positive — VSA template containing local environment sentinel.
24. `docs/melhorias/14-09-2026_melhoria-aidd-factory-plano-implementacao.json:474` (`Secret Keyword`): False positive — token count metric string.
25. `gates/dependencias_externas.json:9` (`Hex High Entropy String`): False positive — SHA-256 integrity hash for impeccable skill.
26. `gates/dependencias_externas.json:21` (`Hex High Entropy String`): False positive — SHA-256 integrity hash for code-review-graph skill.

## Acceptance criteria

- [x] All 26 inspected individually, each classified false-positive or real-secret, one line of reasoning each.
- [x] False positives added to `.secrets.baseline` via the tool's official procedure — never by hand-editing the file.
- [x] Any alert that turns out real gets promoted to ISSUE-0003 (zero real secrets found; all proven false positives).
- [x] Re-running the real hook shows all 26 cleared (non-test alerts remain; they are ISSUE-0003 scope).
