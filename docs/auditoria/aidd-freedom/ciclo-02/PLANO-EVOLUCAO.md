# Plano de Evolução (Fase 2) - aidd-bridge

Este plano foi gerado pelo Arquiteto (Fase 2) do Pipeline Linear de Auditoria 4F, com o objetivo de evoluir a ferramenta `aidd-bridge` a partir do Laudo 15-D do Ciclo 02 (`LAUDO-15D-INICIAL.md`, status ÍNTEGRO). A ferramenta passou em todas as 15 dimensões; os tickets abaixo endereçam gaps de hardening identificados pela análise do código-fonte real.

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito (Red-Green-Refactor) e isolamento em Git Worktree efêmera. Para cada requisito funcional, testes automatizados (exit 0 / exit 1) devem ser criados antes da implementação real. Toda alteração preserva os 64 testes existentes (`pytest tools/aidd-bridge/tests` continua com exit 0).

### Ticket 1: Gates Provam que Mordem — Bite Tests (Refere-se a D13 / DoD 6)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `tools/aidd-bridge/tests/test_gate_bites.py`
- **Requisito TDD (Red):** Atualmente existem apenas 1 bite test (assert == 1) vs 8 happy-path (assert == 0) em `test_bridge_pipeline_and_gates.py`. A Lei #13 exige que cada gate prove que barra sob violação real. Criar `test_gate_bites.py` antes de qualquer fix; antes da implementação todos os asserts de bite devem falhar (gate passa onde deveria reprovar).
- **Implementação Técnica:**
  - Criar `tools/aidd-bridge/tests/test_gate_bites.py` com ao menos um caso de violação deliberada para cada um dos 4 gates:
    - `G_BRIDGE_VENDOR_LOCKIN`: injetar URL `https://projeto.supabase.co` em arquivo `.tsx`; assert `audit_vendor_lockin(dir) == 1`.
    - `G_BRIDGE_DOCKER_OCI`: gerar `Dockerfile` com `USER root`; assert `audit_docker_oci(dir) == 1`.
    - `G_BRIDGE_POSTGRESQL`: escrever `init-db.sql` com cláusula `CREATE EXTENSION pg_cron` (extensão proibida); assert `audit_postgresql_script(dir) == 1`.
    - `G_BRIDGE_VSA_COMPAT`: omitir `swagger.json` do `quarteto_sine_qua_non/`; assert `audit_vsa_compat(dir) == 1`.
  - Registrar o gate novo em `gates/G_PORTAO_PROVA_QUE_MORDE.py` se ainda não coberto.
- **Verificação (Green):** `pytest tools/aidd-bridge/tests/test_gate_bites.py -v` retorna exit 0 com 4 testes de bite passando.
- **Construtor Prompt (EN):**
  - Create tools/aidd-bridge/tests/test_gate_bites.py.
  - Import audit_vendor_lockin from G_BRIDGE_VENDOR_LOCKIN. Write tmpdir with file containing URL https://proyecto.supabase.co. Assert audit_vendor_lockin(tmpdir) == 1.
  - Import audit_docker_oci from G_BRIDGE_DOCKER_OCI. Write Dockerfile with USER root. Assert audit_docker_oci(tmpdir) == 1.
  - Import audit_postgresql_script from G_BRIDGE_POSTGRESQL. Write init-db.sql with CREATE EXTENSION pg_cron. Assert audit_postgresql_script(tmpdir) == 1.
  - Import audit_vsa_compat from G_BRIDGE_VSA_COMPAT. Create quarteto_sine_qua_non/ without swagger.json. Assert audit_vsa_compat(tmpdir) == 1.
  - Run pytest tools/aidd-bridge/tests/test_gate_bites.py -v. Assert exit 0.
  - Run pytest tools/aidd-bridge/tests -q. Assert all 64 previous tests still pass.

### Ticket 2: Falha Silenciosa nos Gates do Pipeline (Refere-se a D11 / DoD 4)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `tools/aidd-bridge/aidd_bridge/pipeline_bridge.py`
- **Requisito TDD (Red):** Em `pipeline_bridge.py` linha ~151, o bloco `except Exception as e: print("[AVISO]...")` silencia falhas de importação dos gates e continua retornando exit 0 — violação direta da Lei #1 (Determinismo) e da semântica fail-fast documentada em D10. Criar teste que reproduza o bug: com gates movidos para caminho inexistente, `BridgePipeline.run()` deve retornar 1, mas atualmente retorna 0.
- **Implementação Técnica:**
  - Substituir o bloco `except Exception as e: print(AVISO)` por re-raise que propaga `SystemExit(1)` ao chamador.
  - Garantir que falha de importação de qualquer gate (`ImportError`) resulte em `return 1`, não em aviso silencioso.
  - Manter compatibilidade: o teste existente `test_bridge_pipeline_and_gates.py` deve continuar passando.
- **Verificação (Green):** Com `G_BRIDGE_VENDOR_LOCKIN` renomeado temporariamente, `BridgePipeline.run()` retorna 1.
- **Construtor Prompt (EN):**
  - Open tools/aidd-bridge/aidd_bridge/pipeline_bridge.py.
  - Find the except block around gates import in run(). Replace bare except with specific handling: on ImportError or any gate error, print error and return 1. Never swallow gate failures.
  - Write test: monkeypatch sys.path so gate import fails. Call BridgePipeline.run(). Assert return value == 1.
  - Run pytest tools/aidd-bridge/tests -q. Assert all tests pass exit 0.

### Ticket 3: Observabilidade por Fase no bridge-manifest.json (Refere-se a D12 / DoD 5)
- **Falha 15-D:** `D12. Observabilidade e Frugalidade`
- **Artefato de Handoff:** `tools/aidd-bridge/aidd_bridge/pipeline_bridge.py`
- **Requisito TDD (Red):** O `bridge-manifest.json` gerado em disco não registra `started_at`, `finished_at` nem duração por fase. Criar teste que carrega o JSON após `BridgePipeline.run()` e falha (`KeyError`) na ausência de `pipeline_telemetry`.
- **Implementação Técnica:**
  - Ao iniciar `run()`, capturar `datetime.utcnow().isoformat()` em `started_at`.
  - Ao fim de cada fase (Scan, DB, Frontend, DevOps, VSA, Gates), registrar `phase_timings[fase] = duration_s`.
  - Ao concluir, adicionar ao JSON final um bloco `pipeline_telemetry` com `started_at`, `finished_at`, `total_duration_s` e `phase_timings`.
  - Reescrever `bridge-manifest.json` com o bloco de telemetria no fim.
- **Verificação (Green):** `bridge-manifest.json` contém `pipeline_telemetry` com todas as chaves; `pytest tools/aidd-bridge/tests -q` retorna exit 0.
- **Construtor Prompt (EN):**
  - Open tools/aidd-bridge/aidd_bridge/pipeline_bridge.py.
  - At start of run() record started_at = datetime.utcnow().isoformat(). Use time.perf_counter() for per-phase durations.
  - After each of the 6 pipeline phases record phase name and elapsed seconds in phase_timings dict.
  - After phase 6 compute finished_at and total_duration_s. Add pipeline_telemetry block to manifest dict.
  - Write updated manifest JSON to bridge-manifest.json at output_dir.
  - Write test: run BridgePipeline on fixture project. Load bridge-manifest.json. Assert pipeline_telemetry key present. Assert started_at and phase_timings keys present. Assert exit 0.
  - Run pytest tools/aidd-bridge/tests -q. Assert all pass.

### Ticket 4: Handoff Canônico bridge-handoff.json (Refere-se a D15 / DoD 8)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `tools/aidd-bridge/aidd_bridge/pipeline_bridge.py`
- **Requisito TDD (Red):** O pipeline não emite `bridge-handoff.json` estruturado para o orquestrador `aidd-master`. O `bridge-manifest.json` é um inventário do projeto de origem, não um handoff canônico de pipeline. Criar teste que falha (`FileNotFoundError`) na ausência de `bridge-handoff.json` após `BridgePipeline.run()`.
- **Implementação Técnica:**
  - Ao concluir com exit 0, gravar `bridge-handoff.json` no `output_dir` com os campos:
    - `tool`: `"aidd-bridge"`
    - `pipeline_id`: `f"bridge-{project_slug}-{timestamp}"`
    - `status`: `"succeeded"`
    - `output_dir`: caminho absoluto do diretório de saída
    - `artifacts`: lista dos arquivos-chave gerados (`init-db.sql`, `.env.production`, `Dockerfile`, `docker-compose.yml`, `quarteto_sine_qua_non/swagger.json`, ...)
    - `gate_results`: dict com exit code de cada um dos 4 gates
    - `next_tool`: `"aidd-master"`
    - `pipeline_telemetry`: referência ao bloco gerado pelo Ticket 3
  - Em caso de falha (exit 1), gravar `bridge-handoff.json` com `"status": "failed"` e `"error_phase"` indicando a fase que falhou.
- **Verificação (Green):** `bridge-handoff.json` existe, é JSON válido e contém todos os campos; `pytest tools/aidd-bridge/tests -q` retorna exit 0.
- **Construtor Prompt (EN):**
  - Open tools/aidd-bridge/aidd_bridge/pipeline_bridge.py.
  - At end of run() on success: build handoff dict with fields tool, pipeline_id, status=succeeded, output_dir, artifacts list, gate_results dict, next_tool=aidd-master, pipeline_telemetry reference.
  - On failure (before return 1): write bridge-handoff.json with status=failed and error_phase field.
  - Write to output_dir/bridge-handoff.json using json.dump with indent=2.
  - Write test: run BridgePipeline on fixture. Assert bridge-handoff.json exists. Load JSON. Assert status == succeeded. Assert next_tool == aidd-master. Assert artifacts list non-empty.
  - Write second test: simulate gate failure (monkeypatch audit to return 1). Assert bridge-handoff.json status == failed. Assert error_phase key present.
  - Run pytest tools/aidd-bridge/tests -q. Assert all pass.
