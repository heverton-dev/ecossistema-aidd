# Reconciliação tools/ → modulos/ — ciclo-03, Ticket 3

> Gerado em 06/10/2026 a partir de `scripts/reconciliar_copias_vsa.py` (só arquivos versionados, sem CRLF, sem cache).
> Decisão A: `modulos/` é a cópia canônica. O lado `tools/` sai no Ticket 5.

## Divergências decididas

Em todas as 28, o lado de `modulos/` é o de `tools/` com a descoberta da raiz do repo adaptada ao layout VSA
(procura `ecossistema.py` subindo pastas, em vez de `parents[3]` ou `../aidd-<x>`). As linhas que só existem em
`tools/` são esses caminhos antigos; nenhuma lógica exclusiva de `tools/` se perde.

| Arquivo | Lado | Motivo | Hash final |
|---|---|---|---|
| aidd-pure/scripts/core/pecas_catalogo.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 99ae92712d6310dc |
| aidd-pure/tests/conftest.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | ff6b955b1b567271 |
| aidd-pure/tests/test_fronteira_generator.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 1d40df136194e854 |
| aidd-open/scripts/phases/01_analisador.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 2b24e92af1b328e9 |
| aidd-open/scripts/phases/04_compose.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 9d2babebf53661db |
| aidd-open/scripts/phases/06_env.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 14f2c1d26164bd5b |
| aidd-open/src/core/result.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 0c3844c0ff6b0b59 |
| aidd-open/tests/test_fronteira_factory.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | c042d7b68df27844 |
| aidd-open/tests/test_pipeline_factory.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | e48d203ab7157370 |
| aidd-freedom/tests/test_fronteira_bridge.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 7832f6ed0357e436 |
| aidd-enterprise/application/commands/delegacao.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 0435ff80ab3b19fd |
| aidd-enterprise/application/pecas_catalogo.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | fcbac59f74da2bda |
| aidd-enterprise/scripts/compose_suite.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 2706f587611cfe75 |
| aidd-enterprise/scripts/moldes_catalogo.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 2f5953465555700a |
| aidd-enterprise/scripts/scaffold_infra.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 3a33b754568c8342 |
| aidd-enterprise/tests/test_fronteira_enterprise.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | b836813b7fbe786a |
| aidd-enterprise/tests/unit/test_g_inject_gate.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 8c42e37dee0c3815 |
| aidd-enterprise/tests/unit/test_g_seguranca_gate.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | e579800c06c72a9a |
| aidd-master/application/pecas_catalogo.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | b26a9c80d1ea8598 |
| aidd-master/scripts/compose_suite.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 5551a2d3583ed029 |
| aidd-master/scripts/moldes_catalogo.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 03cb1c2be0627d53 |
| aidd-master/scripts/scaffold_infra.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 3a33b754568c8342 |
| aidd-ops/scripts/contrato_plano.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | aae196261bdd692c |
| aidd-ops/scripts/infra_perfil.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | b756aa4844d34742 |
| aidd-ops/scripts/pipeline_ops.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 1de7045969dd41a9 |
| aidd-ops/tests/test_contrato_infraestrutura.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | 4b3fb398d7e28fea |
| aidd-ops/tests/test_fronteira_ops_infra_generica.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | e8b1fb17d7e9847a |
| aidd-ops/tests/test_mcps.py | modulos | caminho da raiz adaptado ao layout VSA; tools/ só tem caminho antigo | acdb30e4bfcd79ab |

### Ajustes feitos no Ticket 3 para as suítes rodarem de modulos/

O planner (cópia nova) e 3 arquivos do master ainda calculavam a raiz pela profundidade antiga de `tools/`.

| Arquivo | Lado | Motivo | Hash final |
|---|---|---|---|
| aidd-planner/aidd_planner/core/planner_engine.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | 95d29ebe8bedda58 |
| aidd-planner/aidd_planner/core/planta.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | 73115e8a4a062938 |
| aidd-planner/src/core/design_system.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | 814763e7d82ae058 |
| aidd-planner/src/core/mobbin_client.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | 4f2a2b1e9c36b4de |
| aidd-planner/src/core/planner_engine.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | 1a739dbd89a69c07 |
| aidd-planner/src/core/planta.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | 73115e8a4a062938 |
| aidd-planner/tests/test_planner.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | a8f4fbdfb7f7612b |
| aidd-planner/tests/test_planta_tickets_roteados.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | 84741ec06946611d |
| aidd-planner/tests/test_vsa_compiler.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | 8223e86064e00b49 |
| aidd-master/scripts/attach_vsa_infra.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | bd6e0f00a20d8d20 |
| aidd-master/tests/unit/test_drift_gate_blind_spot.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | cd6e6131353dd639 |
| aidd-master/tests/unit/test_g_seguranca_gate.py | modulos | ajustado no Ticket 3 para achar a raiz do repo pelo ecossistema.py (suíte verde rodando de modulos/) | bef8f02b1a02c41b |

### Removidos no Ticket 3 (Lei #7: para onde foi o conteúdo)

- `modulos/01-governanca-e-qualidade/core/__init__.py`, `modulos/02-triade-motores/fluxo-01-pure/core/__init__.py`, `fluxo-02-open/core/__init__.py` e `fluxo-03-freedom/core/__init__.py`: arquivos de 0 byte, sem conteúdo. Transformavam a pasta da fatia num pacote `core` que escondia o `core` real das ferramentas (`ModuleNotFoundError: core.result` ao planner chamar o `pipeline_ops` do ops).

### Prova

- `python scripts/reconciliar_copias_vsa.py --exigir-zero`: exit 0.
- Suítes rodadas de dentro de cada pasta em `modulos/`: forge 310, planner 48, pure 1016, open 21, freedom 75, enterprise 341, master 414, ops 198 passando; todas com exit 0 (2423 no total).

## Conteúdo que só existia em tools/ (copiado para modulos/)

| Arquivo | Destino |
|---|---|
| aidd-planner/AGENTS.md | modulos/01-governanca-e-qualidade/core/aidd-planner/AGENTS.md |
| aidd-planner/README.md | modulos/01-governanca-e-qualidade/core/aidd-planner/README.md |
| aidd-planner/aidd_planner/__init__.py | modulos/01-governanca-e-qualidade/core/aidd-planner/aidd_planner/__init__.py |
| aidd-planner/aidd_planner/cli.py | modulos/01-governanca-e-qualidade/core/aidd-planner/aidd_planner/cli.py |
| aidd-planner/aidd_planner/core/__init__.py | modulos/01-governanca-e-qualidade/core/aidd-planner/aidd_planner/core/__init__.py |
| aidd-planner/aidd_planner/core/design_system.py | modulos/01-governanca-e-qualidade/core/aidd-planner/aidd_planner/core/design_system.py |
| aidd-planner/aidd_planner/core/mobbin_client.py | modulos/01-governanca-e-qualidade/core/aidd-planner/aidd_planner/core/mobbin_client.py |
| aidd-planner/aidd_planner/core/planner_engine.py | modulos/01-governanca-e-qualidade/core/aidd-planner/aidd_planner/core/planner_engine.py |
| aidd-planner/aidd_planner/core/planta.py | modulos/01-governanca-e-qualidade/core/aidd-planner/aidd_planner/core/planta.py |
| aidd-planner/aidd_planner/core/ui_reference_resolver.py | modulos/01-governanca-e-qualidade/core/aidd-planner/aidd_planner/core/ui_reference_resolver.py |
| aidd-planner/gates/G_PLANNER_COERENCIA_FLUXO.py | modulos/01-governanca-e-qualidade/core/aidd-planner/gates/G_PLANNER_COERENCIA_FLUXO.py |
| aidd-planner/gates/G_PLANNER_SCHEMA.py | modulos/01-governanca-e-qualidade/core/aidd-planner/gates/G_PLANNER_SCHEMA.py |
| aidd-planner/gates/G_PLANNER_SINE_QUA_NON.py | modulos/01-governanca-e-qualidade/core/aidd-planner/gates/G_PLANNER_SINE_QUA_NON.py |
| aidd-planner/schemas/planner_schema.json | modulos/01-governanca-e-qualidade/core/aidd-planner/schemas/planner_schema.json |
| aidd-planner/setup.py | modulos/01-governanca-e-qualidade/core/aidd-planner/setup.py |
| aidd-planner/src/__init__.py | modulos/01-governanca-e-qualidade/core/aidd-planner/src/__init__.py |
| aidd-planner/src/cli.py | modulos/01-governanca-e-qualidade/core/aidd-planner/src/cli.py |
| aidd-planner/src/core/__init__.py | modulos/01-governanca-e-qualidade/core/aidd-planner/src/core/__init__.py |
| aidd-planner/src/core/design_system.py | modulos/01-governanca-e-qualidade/core/aidd-planner/src/core/design_system.py |
| aidd-planner/src/core/mobbin_client.py | modulos/01-governanca-e-qualidade/core/aidd-planner/src/core/mobbin_client.py |
| aidd-planner/src/core/planner_engine.py | modulos/01-governanca-e-qualidade/core/aidd-planner/src/core/planner_engine.py |
| aidd-planner/src/core/planta.py | modulos/01-governanca-e-qualidade/core/aidd-planner/src/core/planta.py |
| aidd-planner/src/core/ui_reference_resolver.py | modulos/01-governanca-e-qualidade/core/aidd-planner/src/core/ui_reference_resolver.py |
| aidd-planner/tests/test_planner.py | modulos/01-governanca-e-qualidade/core/aidd-planner/tests/test_planner.py |
| aidd-planner/tests/test_planta_tickets_roteados.py | modulos/01-governanca-e-qualidade/core/aidd-planner/tests/test_planta_tickets_roteados.py |
| aidd-planner/tests/test_vsa_compiler.py | modulos/01-governanca-e-qualidade/core/aidd-planner/tests/test_vsa_compiler.py |
| aidd-enterprise/materiais-extras/examples/catalogo-digital-v3/.cursorrules | modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/materiais-extras/examples/catalogo-digital-v3/.cursorrules |
| aidd-enterprise/materiais-extras/examples/catalogo-digital-whatsapp/.cursorrules | modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/materiais-extras/examples/catalogo-digital-whatsapp/.cursorrules |
| aidd-enterprise/materiais-extras/examples/plataforma-de-membros/.cursorrules | modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/materiais-extras/examples/plataforma-de-membros/.cursorrules |
| aidd-enterprise/materiais-extras/examples/plataforma-membros-v3/.cursorrules | modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/materiais-extras/examples/plataforma-membros-v3/.cursorrules |
| aidd-enterprise/materiais-extras/examples/plataforma-modular-assinaturas/.cursorrules | modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/materiais-extras/examples/plataforma-modular-assinaturas/.cursorrules |

## Não migrado (lixo)

- `__pycache__/`, `.pytest_cache/`, `node_modules/`, `*.pyc`, `*.db-wal`, `*.db-shm`: ignorados na comparação e não copiados.
- Os 5 `.cursorrules` de `aidd-enterprise/materiais-extras/examples/` foram copiados só para zerar órfãos; `materiais-extras/examples` sai do repo no Ticket 6 (arquivado fora).
