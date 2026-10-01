# RELATORIO-CONSTRUTOR — aidd-bridge / ciclo-02 (Fase 3)

> Builder phase (audit pipeline 4F). TDD estrito Red-Green: testes novos falham primeiro (exit 1), implementação, testes aprovando (exit 0). Baseline `pytest tools/aidd-bridge/tests` = **64 passed** antes de qualquer edição. Nenhum `git commit` / `git push` / `git reset` executado (deferido ao orquestrador após o gate de fase).

| Ticket | Arquivo entregue | Comando de teste | Exit ANTES do fix | Exit DEPOIS do fix |
|--------|------------------|------------------|-------------------|--------------------|
| TICKET-01 | `tools/aidd-bridge/tests/test_gate_bites.py` | `python -m pytest tools/aidd-bridge/tests/test_gate_bites.py -q` | 1 (2 failed: `test_bite_docker_oci_user_root_no_dockerfile`, `test_bite_postgresql_extensao_proibida_pg_cron` — gates aprovavam violação) | 0 (4 passed) |
| TICKET-02 | `tools/aidd-bridge/aidd_bridge/pipeline_bridge.py` | `python -m pytest tools/aidd-bridge/tests/test_pipeline_hardening.py::test_pipeline_retorna_1_quando_import_de_gate_falha -q` | 1 (falhou: import de gate silenciado retornava 0) | 0 (passed) |
| TICKET-03 | `tools/aidd-bridge/aidd_bridge/pipeline_bridge.py` | `python -m pytest tools/aidd-bridge/tests/test_pipeline_hardening.py::test_manifest_registra_telemetria_por_fase -q` | 1 (falhou: `KeyError: 'pipeline_telemetry'`) | 0 (passed) |
| TICKET-04 | `tools/aidd-bridge/aidd_bridge/pipeline_bridge.py` | `python -m pytest tools/aidd-bridge/tests/test_pipeline_hardening.py -q` | 1 (3 failed: `FileNotFoundError: bridge-handoff.json`) | 0 (4 passed) |

**Suíte completa:** `python -m pytest tools/aidd-bridge/tests -q` → **exit 0, 72 passed** (64 baseline + 8 novos, zero regressão).

## O que foi implementado

- **TICKET-01 (D13 / Lei #13):** `test_gate_bites.py` com 1 bite case por gate (URL Supabase Cloud em `.tsx`; `USER root` no Dockerfile; `CREATE EXTENSION pg_cron` no `init-db.sql`; `quarteto_sine_qua_non/` sem `swagger_spec.json`). Dois gates não mordiam e foram corrigidos:
  - `gates/G_BRIDGE_DOCKER_OCI.py`: detecta `USER root` (regex multiline, case-insensitive) → exit 1.
  - `gates/G_BRIDGE_POSTGRESQL.py`: `EXTENSOES_PROIBIDAS = {"pg_cron"}` (indisponível no PostgreSQL vanilla da stack self-hosted; `uuid-ossp`/`pgcrypto` gerados pelo `DataBridge` continuam permitidos) → exit 1.
  - `G_BRIDGE_VENDOR_LOCKIN` e `G_BRIDGE_VSA_COMPAT` já mordiam; bites apenas fixaram a prova.
- **TICKET-02 (D11):** `pipeline_bridge.py` — o bloco `except Exception: print("[AVISO]...")` que engolia falha de import/gate e retornava 0 foi substituído por fail-fast: qualquer erro de import ou execução de gate grava handoff `failed` (`error_phase: "gates"`) e retorna **1** (Lei #1).
- **TICKET-03 (D12):** `bridge-manifest.json` reescrito ao fim com bloco `pipeline_telemetry` (`started_at`, `finished_at`, `total_duration_s`, `phase_timings` das 6 fases: `scan`, `db`, `frontend`, `devops`, `vsa`, `gates`), medido com `time.perf_counter()` e timestamps UTC.
- **TICKET-04 (D15):** `bridge-handoff.json` canônico emitido no `output_dir` — `tool`, `pipeline_id` (`bridge-<slug>-<ts>`), `status`, `output_dir`, `artifacts` (existentes em disco), `gate_results` (exit code dos 4 gates), `next_tool: "aidd-master"`, `pipeline_telemetry`; em falha: `status: "failed"` + `error_phase`.

## Notas

- **Novos artefatos de teste:** `tools/aidd-bridge/tests/test_gate_bites.py` (4 bites) e `tools/aidd-bridge/tests/test_pipeline_hardening.py` (4 testes D11/D12/D15) — `test_pipeline_hardening.py` reproduz o bug do import falho via stub em `sys.modules` e a falha de gate via `monkeypatch` do `audit_vendor_lockin`.
- **Registro em `G_PORTAO_PROVA_QUE_MORDE`:** não aplicável — esse meta-gate varre apenas `gates/` raiz (`GATES_DIR`), e os 4 gates da bridge vivem em `tools/aidd-bridge/gates/` com paridade de teste garantida pelo ecossistema via `test_gate_bites.py` (Lei #13 satisfeida no escopo da ferramenta).
- **Meta-gates raiz:** `G_PORTAO_PROVA_QUE_MORDE` → exit 1 com **6 violações pré-existentes** (`G_COMPONENTE_AGNOSTICO`, `G_HARNESS_COMPAT`, `G_NOVE_CAMADAS_MERCADO`, `G_SKILL_ROT`, `G_TEMPLATE_TANSTACK_OFFLINE`, `G_UNIVERSAL_HARNESS`) — causa comum: 84 destinos de distribuição `.codebuddy/skills/*` ausentes no worktree, nada a ver com `tools/aidd-bridge` (verificado rodando `G_COMPONENTE_AGNOSTICO` isoladamente antes/depois: mesmo falha).
- **Ticket 1 do plano (prompt `PROMPT-TICKET-01.txt`)** pedia `swagger.json`; o nome real do artefato é `swagger_spec.json` (contrato do `BridgeVSAExporter` e do gate `G_BRIDGE_VSA_COMPAT`) — implementado sobre o nome real.
- Próxima fase: Fase 4 (Retorno/Inspecionador) valida o `DOD` e roda `gate_final`.
