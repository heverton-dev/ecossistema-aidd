# Remoção do esqueleto de app do aidd-enterprise (ciclo-03, Ticket 23)

Escrito antes da remoção, sobre `10a41f82`. Decisão do usuário (09/10/2026): o app de demonstração fica só no `aidd-master`, dono da construção (D1 de fronteiras-ferramentas); o `aidd-enterprise` só blinda. Nenhum gerador, CLI ou projeto gerado usava o app do enterprise: os projetos saem de `templates/` (medido com rastreio de leitura/import nas duas suítes, `aidd-logs/b9_13_rastreio_*.txt`).

Onde o conteúdo fica: o mesmo caminho em `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/`, com o mesmo blob do git (coluna da direita), e o histórico do git. Comando de prova: `python -m pytest -q -p no:cacheprovider tests/test_esqueleto_unico_enterprise_master.py tests/test_interfaces_fatias.py`.

Base: `modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/`.

## App de demonstração (esqueleto) (40)

| Arquivo (relativo à ferramenta) | Blob no enterprise | Blob no master |
|---|---|---|
| `alembic.ini` | `996a4951ad58` | `996a4951ad58` |
| `alembic/__init__.py` | `e69de29bb2d1` | `e69de29bb2d1` |
| `alembic/env.py` | `d4a0992bb5f1` | `d4a0992bb5f1` |
| `alembic/script.py.mako` | `958df8735364` | `958df8735364` |
| `alembic/versions/20260907_9cd894b8e0bf_initial_schema_system_tables_and_modulo1.py` | `e6a6eb4de5b4` | `e6a6eb4de5b4` |
| `alembic_models.py` | `c085720c4bc1` | `c085720c4bc1` |
| `src/__init__.py` | `e69de29bb2d1` | `e69de29bb2d1` |
| `src/modules/__init__.py` | `e69de29bb2d1` | `e69de29bb2d1` |
| `src/modules/modulo1/__init__.py` | `e69de29bb2d1` | `e69de29bb2d1` |
| `src/modules/modulo1/application/__init__.py` | `c8f90c1c53fc` | `c8f90c1c53fc` |
| `src/modules/modulo1/application/dtos.py` | `0403b19ea504` | `0403b19ea504` |
| `src/modules/modulo1/application/use_cases.py` | `e619b35fef9d` | `e619b35fef9d` |
| `src/modules/modulo1/domain/__init__.py` | `cd3452cd8110` | `cd3452cd8110` |
| `src/modules/modulo1/domain/entities.py` | `948274e19743` | `948274e19743` |
| `src/modules/modulo1/domain/events.py` | `9502f41698f8` | `9502f41698f8` |
| `src/modules/modulo1/domain/repositories.py` | `e8556cf43261` | `e8556cf43261` |
| `src/modules/modulo1/domain/value_objects.py` | `8cf2a1791555` | `8cf2a1791555` |
| `src/modules/modulo1/infrastructure/__init__.py` | `389229ec9522` | `389229ec9522` |
| `src/modules/modulo1/infrastructure/outbox.py` | `f8081961b59c` | `f8081961b59c` |
| `src/modules/modulo1/infrastructure/schema.py` | `75d131210c3a` | `75d131210c3a` |
| `src/modules/modulo1/infrastructure/sqlite_repository.py` | `48deaf53478d` | `48deaf53478d` |
| `src/modules/modulo1/interfaces/__init__.py` | `41f2a652273b` | `41f2a652273b` |
| `src/modules/modulo1/interfaces/routes.py` | `e9c3c8f5e6a5` | `e9c3c8f5e6a5` |
| `src/modules/modulo1/models.py` | `b249e53c1526` | `b249e53c1526` |
| `src/modules/modulo1/routes.py` | `db0e84993a64` | `db0e84993a64` |
| `src/modules/modulo1/services.py` | `daa646c2e535` | `daa646c2e535` |
| `src/server.py` | `d6919f60cf03` | `d6919f60cf03` |
| `src/shared/__init__.py` | `e69de29bb2d1` | `e69de29bb2d1` |
| `src/shared/ui/__init__.py` | `e69de29bb2d1` | `e69de29bb2d1` |
| `src/shared/ui/feedback.js` | `08ac44ee15b3` | `08ac44ee15b3` |
| `src/shared/ui/feedback.py` | `1e2d20d8b6a2` | `1e2d20d8b6a2` |
| `src/shared/ui/icons.py` | `9bd3493fede0` | `9bd3493fede0` |
| `src/shared/utils/__init__.py` | `e69de29bb2d1` | `e69de29bb2d1` |
| `src/shared/utils/crypto.py` | `cd632e2c49b7` | `cd632e2c49b7` |
| `src/shared/utils/formatters.py` | `bcbbe5162535` | `bcbbe5162535` |
| `src/shared/utils/validators.py` | `d504a0c99033` | `d504a0c99033` |
| `src/static/components/modulo1.html` | `98776e6159e9` | `98776e6159e9` |
| `src/static/index.html` | `dafce2517b4d` | `dafce2517b4d` |
| `src/static/input.css` | `b5c61c956711` | `b5c61c956711` |
| `src/static/output.css` | `7f0cb9123f86` | `7f0cb9123f86` |

Os 6 testes abaixo continuam rodando no master, no mesmo caminho (exceção aceita pelo usuário: a suíte do enterprise cai de 341 para 335 passando, sem perda de cobertura).

## Testes que só exercitam o app (2)

| Arquivo (relativo à ferramenta) | Blob no enterprise | Blob no master |
|---|---|---|
| `tests/integration/test_trace_id_audit_trail.py` | `1d8a6f658899` | `1d8a6f658899` |
| `tests/unit/test_modulo1.py` | `1af46affc55f` | `1af46affc55f` |

## Renomeado, não removido

- `application/` → `application_enterprise/` (pacote com nome único por fatia; os comandos do enterprise divergem dos do master).
- `core` segue com o mesmo nome nas duas ferramentas: é o núcleo vendorizado `src/core`, cópia proposital de `componentes/compartilhado/src-core` vigiada pelo `G_DRIFT_NUCLEO_COMPARTILHADO`; única entrada de `allowlist_pacotes_repetidos.json`, por decisão do usuário (09/10).

## Contratos ajustados

- `G_MIGRATION_ROT`: o enterprise saiu da lista de alvos (não tem mais `alembic.ini`); a entrada correspondente saiu de `allowlist_modulo_fronteira.json` e o teto baixou.
- `allowlist_pacotes_repetidos.json`: saíram `alembic`, `application`, `modules` e `shared`.
