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

### Inspeção Individual dos Alertas (1 linha de raciocínio cada):
1. `tests/test_properties.py:81` (`Secret Keyword`): Falso positivo — variável de segredo fictício em teste de propriedade Hypothesis para encode/decode JWT.
2. `tests/test_properties.py:108` (`Secret Keyword`): Falso positivo — chave sintética para teste de roundtrip JWT com payloads mistos.
3. `tests/test_properties.py:126` (`Secret Keyword`): Falso positivo — prefixo dummy para validação de chave correta em roundtrip.
4. `tests/test_properties.py:127` (`Secret Keyword`): Falso positivo — prefixo dummy para testar rejeição determinística com chave incorreta.
5. `tests/unit/test_sandbox_runner.py:23` (`Secret Keyword`): Falso positivo — mock de variável de API key para testar sanitização de sandbox.
6. `tests/unit/test_sandbox_runner.py:24` (`Secret Keyword`): Falso positivo — mock de variável de senha de banco para testar sanitização de sandbox.
7. `tests/unit/test_sandbox_runner.py:25` (`Secret Keyword`): Falso positivo — mock de credencial AWS para testar remoção em sandbox.
8. `tools/aidd-bridge/tests/test_bridge.py:675` (`Secret Keyword`): Falso positivo — assert de hash dummy para testar preservação de senhas já hasheadas na migração.
9. `tools/aidd-bridge/tests/test_bridge.py:844` (`Secret Keyword`): Falso positivo — token Cloudflare placeholder em teste unitário de teardown de DNS.
10. `tools/aidd-bridge/tests/test_bridge.py:862` (`Secret Keyword`): Falso positivo — senha SSH placeholder em teste unitário de teardown de VPS.
11. `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/tests/unit/test_webhooks_studio.py:14` (`Secret Keyword`): Falso positivo — segredo fictício em teste unitário de criação de webhook.
12. `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/tests/unit/test_webhooks_studio.py:33` (`Secret Keyword`): Falso positivo — segredo fictício em teste unitário de atualização de webhook.
13. `tools/aidd-enterprise/materiais-extras/examples/enterprise-suite-v4/tests/unit/test_webhooks_studio.py:73` (`Secret Keyword`): Falso positivo — segredo HMAC dummy em teste de entrega real de webhook.
14. `tools/aidd-enterprise/materiais-extras/examples/logistica-hub-v4/tests/unit/test_webhooks_studio.py:14` (`Secret Keyword`): Falso positivo — segredo fictício em teste unitário de criação de webhook.
15. `tools/aidd-enterprise/materiais-extras/examples/logistica-hub-v4/tests/unit/test_webhooks_studio.py:33` (`Secret Keyword`): Falso positivo — segredo fictício em teste unitário de atualização de webhook.
16. `tools/aidd-enterprise/materiais-extras/examples/logistica-hub-v4/tests/unit/test_webhooks_studio.py:73` (`Secret Keyword`): Falso positivo — segredo HMAC dummy em teste de entrega real de webhook.
17. `tools/aidd-enterprise/tests/unit/test_jwt_hardening.py:89` (`Secret Keyword`): Falso positivo — chave insegura sentinela para testar que o boot aborta em produção.
18. `tools/aidd-enterprise/tests/unit/test_jwt_hardening.py:101` (`Secret Keyword`): Falso positivo — chave dummy para validar sucesso de boot em produção.
19. `tools/aidd-master/tests/unit/test_jwt_hardening.py:89` (`Secret Keyword`): Falso positivo — chave insegura sentinela para testar que o boot aborta em produção.
20. `tools/aidd-master/tests/unit/test_jwt_hardening.py:101` (`Secret Keyword`): Falso positivo — chave dummy para validar sucesso de boot em produção.
21. `tools/aidd-ops/tests/test_deploy.py:188` (`Secret Keyword`): Falso positivo — mock de token de deploy para teste unitário do orquestrador.
22. `tools/aidd-factory/scripts/phases/05_init_db.py:39` (`Secret Keyword`): Falso positivo — template bash com placeholder dinâmico para inicialização de bancos de exemplo.
23. `tools/aidd-factory/templates/vsa/security.py:29` (`Secret Keyword`): Falso positivo — template VSA contendo a constante sentinela de ambiente local.
24. `docs/melhorias/14-09-2026_melhoria-aidd-factory-plano-implementacao.json:474` (`Secret Keyword`): Falso positivo — string de métrica de contagem de tokens.
25. `gates/dependencias_externas.json:9` (`Hex High Entropy String`): Falso positivo — hash SHA-256 de integridade da skill impecável.
26. `gates/dependencias_externas.json:21` (`Hex High Entropy String`): Falso positivo — hash SHA-256 de integridade da skill code-review-graph.

## Acceptance criteria

- [x] All 26 inspected individually, each classified false-positive or real-secret, one line of reasoning each.
- [x] False positives added to `.secrets.baseline` via the tool's official procedure — never by hand-editing the file.
- [x] Any alert that turns out real gets promoted to ISSUE-0003 (nenhum segredo real encontrado; todos são falsos positivos comprovados).
- [x] Re-running the real hook shows all 26 cleared (non-test alerts remain; they are ISSUE-0003 scope).
