# Plano de Evolução (Fase 2) - aidd-freedom

Este plano foi formulado para a ferramenta `aidd-freedom` e suas integrações canônicas a partir do Relatório de Auditoria Forense E2E (`RELATORIO-E2E-FLUXO-03.md`). Endereça os gaps de persistência de contrato, robustez de diretórios, conformidade de containers OCI e tolerância a esquemas declarativos de banco.

## Estratégia de Execução
Todos os tickets abaixo requerem ciclo TDD estrito e validação por Quality Gates dedicados.

### Ticket 1: Persistência do Contrato C5 no aidd-enterprise (TCK-FREEDOM-001)
- **Falha 15-D:** `D15. Output Consolidado e Handoff`
- **Artefato de Handoff:** `modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/application_enterprise/commands/verificar_drift.py`
- **Requisito TDD (Red):** Criar teste que executa `cmd_verificar_drift` em projeto alvo com drift verificado e asserta a existência e conformidade do arquivo `HANDOFF_ENTERPRISE_OPS.json` contra `handoff-enterprise-to-ops.schema.json`.
- **Implementação Técnica:**
  - Em `verificar_drift.py`, quando `res.sucesso` for verdadeiro, instanciar a estrutura do contrato C5:
    - `versao_schema`: "1.0.0"
    - `diretorio_projeto`: `target_dir`
    - `registry`: caminho e hash SHA-256 de `COMPONENT-REGISTRY.json` ou `CAPABILITIES.json`
    - `selo_sha256`: hash calculado dos componentes verificados
    - `drift`: `{"verificado": True, "exit_code": 0}`
    - `perfil_app`: lido de `PLANNER.json` ou padrão `{"tipo_runtime": "monolito_modular_docker", "portas_expostas": [8000], "banco": "postgresql"}`
  - Gravar `HANDOFF_ENTERPRISE_OPS.json` no `target_dir`.
- **Verificação (Green):** Teste asserta que `HANDOFF_ENTERPRISE_OPS.json` existe e valida contra o schema com exit 0.
- **Construtor Prompt (EN):**
  - In application_enterprise/commands/verificar_drift.py, after successful drift check, construct C5 dictionary adhering to handoff-enterprise-to-ops.schema.json.
  - Save to target_dir/HANDOFF_ENTERPRISE_OPS.json.
  - Assert schema validation passes and exit code 0.

### Ticket 2: Criação de Diretório Destino no BridgePipeline (TCK-FREEDOM-002)
- **Falha 15-D:** `D11. Tratamento de Exceções e Fallback`
- **Artefato de Handoff:** `modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom/aidd_freedom/pipeline_bridge.py`
- **Requisito TDD (Red):** Testar instanciar `BridgePipeline` com pasta de saída inexistente. Antes da correção, falha com `FileNotFoundError` ao tentar abrir `bridge-manifest.json`.
- **Implementação Técnica:**
  - Em `pipeline_bridge.py`, no método `run()`, invocar `os.makedirs(self.output_dir, exist_ok=True)` antes de escrever `bridge-manifest.json`.
- **Verificação (Green):** `BridgePipeline(origem, output_inexistente).run()` cria a pasta e executa sem `FileNotFoundError`.
- **Construtor Prompt (EN):**
  - In pipeline_bridge.py, ensure os.makedirs(self.output_dir, exist_ok=True) is called before opening manifest_path for writing.
  - Verify test with nonexistent output folder passes.

### Ticket 3: Multi-Stage Build no Template de Dockerfile do aidd-ops (TCK-FREEDOM-003)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `componentes/compartilhado/moldes/infra/Dockerfile`
- **Requisito TDD (Red):** O gate `G_BRIDGE_DOCKER_OCI.py` reprova com exit 1 quando executado em diretório contendo o `Dockerfile` gerado pelo molde do ops.
- **Implementação Técnica:**
  - Atualizar `componentes/compartilhado/moldes/infra/Dockerfile` para usar multi-stage build real com estágio `FROM ... AS builder` e estágio final limpo de runtime `AS runtime` executando como non-root `USER 10001:10001`.
- **Verificação (Green):** `python modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom/gates/G_BRIDGE_DOCKER_OCI.py <dir>` retorna exit 0.
- **Construtor Prompt (EN):**
  - Update componentes/compartilhado/moldes/infra/Dockerfile with explicit builder stage 'FROM python:3.12-slim AS builder' and runtime stage.
  - Verify G_BRIDGE_DOCKER_OCI passes with exit 0.

### Ticket 4: Reconhecimento de Migrações PostgreSQL no G_MIGRATION_ROT (TCK-FREEDOM-004)
- **Falha 15-D:** `D13. Quality Gates (Portões)`
- **Artefato de Handoff:** `modulos/02-triade-motores/fluxo-03-freedom/gates/G_MIGRATION_ROT.py`
- **Requisito TDD (Red):** `G_MIGRATION_ROT.py --target projetos/daily-tasks` falha com exit 1 por ausência de `alembic.ini`.
- **Implementação Técnica:**
  - Em `G_MIGRATION_ROT.py`, na função `auditar_migracoes_target()`, adicionar detecção de persistência SQL declarativa: se `init-db.sql` existir no diretório alvo, validar o script com `G_BRIDGE_POSTGRESQL` ou checagem de sintaxe e idempotência SQL pura, dispensando a exigência de `alembic.ini`.
- **Verificação (Green):** `G_MIGRATION_ROT.py --target projetos/daily-tasks` retorna exit 0.
- **Construtor Prompt (EN):**
  - In G_MIGRATION_ROT.py, check if init-db.sql exists when alembic.ini is absent. If valid, approve migration audit for PostgreSQL declarative scope.
  - Verify G_MIGRATION_ROT returns exit 0 on projects with init-db.sql.
