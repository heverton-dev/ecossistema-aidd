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

### Ajustes do Ticket 4 (reapontar para modulos/)

Arquivos que o Ticket 4 editou só em `modulos/` (caminhos). Linha mais nova vale sobre a anterior do mesmo arquivo.

| Arquivo | Lado | Motivo | Hash final |
|---|---|---|---|
| aidd-forge/aidd_forge/cli.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 4ca3fcfa6d01aa8a |
| aidd-forge/aidd_forge/core/almoxarifado.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 345cdb5ae0ee026a |
| aidd-forge/aidd_forge/templates/gates/G_QUARTETO_SINE_QUA_NON.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | b26b0ac812117340 |
| aidd-forge/tests/test_almoxarifado.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | d16d4a94eff530a6 |
| aidd-forge/tests/unit/test_injector_profiles.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 31919734c5079190 |
| aidd-planner/AGENTS.md | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 4e3414ce1fde1227 |
| aidd-pure/scripts/core/pecas_catalogo.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 0a16b8ba433deb66 |
| aidd-pure/scripts/core/pipeline_state.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | a7a4857c6909597b |
| aidd-pure/scripts/phases/01_pesquisador.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 7dd5836b18f150f2 |
| aidd-pure/scripts/phases/02_analisador.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 7a2adb8651fde6b9 |
| aidd-pure/scripts/phases/03_designer.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 4923cc7bde4aeee9 |
| aidd-pure/scripts/phases/04_decisor.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 8cdaff1f5b38faeb |
| aidd-pure/scripts/phases/05_criador.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 1d8f7030dd808a6d |
| aidd-pure/scripts/phases/06_documentador.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | adf8664c95cb60bc |
| aidd-pure/scripts/phases/07_analisador.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | f70a3902cfb7abc4 |
| aidd-pure/scripts/phases/08_implementador.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | d4f5993d08fd3cab |
| aidd-pure/scripts/phases/utils_delegacao.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | b0b392fc6cb8b690 |
| aidd-pure/scripts/phases/utils_fleet_discovery.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | accd78d2f7f1e14d |
| aidd-pure/scripts/phases/utils_subagente_ephemero.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 3f3ba18f96942d28 |
| aidd-pure/scripts/pipeline_completo.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 2ef812cec0e61973 |
| aidd-pure/tests/conftest.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 290bc3791c11e6fe |
| aidd-pure/tests/test_fronteira_generator.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 335d79f4f81fda0e |
| aidd-pure/tests/test_injector_core.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 3502267d44c73066 |
| aidd-pure/tmp_junit.xml | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | e1f441932321335e |
| aidd-open/scripts/contrato_factory.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | f0fcd732cfd0f237 |
| aidd-open/scripts/phases/01_analisador.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | bc52c3e9345354de |
| aidd-open/scripts/phases/04_compose.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 6f7ebd9c5829e33a |
| aidd-open/scripts/phases/05_init_db.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | fb9ea60c156900c2 |
| aidd-open/scripts/phases/06_env.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | ceb27e7a51a9a998 |
| aidd-open/scripts/phases/09_integracao.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 32e6addf6f58f555 |
| aidd-open/scripts/pipeline_factory.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | ce5a360fa7216c6b |
| aidd-open/src/core/escritor_atomico.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 6c28a822a56a400f |
| aidd-open/src/core/frontend_generator.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 5aee5a00d7f1529d |
| aidd-open/src/core/gateway_generator.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 6e851ed8041ac65a |
| aidd-open/src/core/swagger_generator.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | a3224daeab15ed0e |
| aidd-open/src/core/vsa_generator.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 7d1f9fe0f7836354 |
| aidd-open/tests/test_fronteira_factory.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | f1c5db3cb16ef691 |
| aidd-enterprise/RELATORIO-AUDITORIA.json | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 4dc81002034926ba |
| aidd-enterprise/application/commands/delegacao.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 720e0bf5424f493f |
| aidd-enterprise/scripts/compose_suite.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | b945deb51ae3ccd5 |
| aidd-enterprise/src/core/assinatura_manifesto.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 8c9acb7cf459c378 |
| aidd-enterprise/src/core/escritor_atomico.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 09b9b20feaa7f3bf |
| aidd-enterprise/src/core/materializador.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 1788cc0de093143e |
| aidd-enterprise/src/core/nextjs_exporter.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 45e8dd5f6c747344 |
| aidd-enterprise/tests/test_fronteira_enterprise.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 98e082ed23fc8ff2 |
| aidd-master/scripts/compose_suite.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | acfabe8b77c89b6e |
| aidd-master/scripts/dispatch_pipeline.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 8855dd03e247b8a5 |
| aidd-master/scripts/engine_router.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | ab62609fb17cd317 |
| aidd-master/scripts/moldes_catalogo.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 7e661f6dcc6297fc |
| aidd-master/scripts/orchestrator_pipeline.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 33d1d55ca9e03358 |
| aidd-master/src/core/assinatura_manifesto.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 8c9acb7cf459c378 |
| aidd-master/src/core/escritor_atomico.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 09b9b20feaa7f3bf |
| aidd-master/src/core/materializador.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 1788cc0de093143e |
| aidd-master/src/core/nextjs_exporter.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 45e8dd5f6c747344 |
| aidd-master/tests/test_fronteira_master.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 8bf60c34bce131f0 |
| aidd-master/tests/unit/test_alembic_migrations.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 2de9e45630313ccf |
| aidd-master/tests/unit/test_provision_project.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 24da6b28a0259c69 |
| aidd-ops/.dockerignore | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 724646f5b2ae95ee |
| aidd-ops/Dockerfile.intake | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 8fe2a1efb9e7eefc |
| aidd-ops/README.md | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 162ba7083e6cd2b4 |
| aidd-ops/ansible/requirements.yml | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | e0222a459d8b793f |
| aidd-ops/apps/intake/README.md | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 6c9c508519765b2c |
| aidd-ops/apps/intake/docker-compose.yml | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | c8fe08e6f224d01e |
| aidd-ops/gates/G_OPS_MVP.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | b97a3411d67ed3cc |
| aidd-ops/gates/G_OPS_SSH.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 2703353249ddf789 |
| aidd-ops/mcps/cloudflare-mcp/server.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 7b3412bac459898d |
| aidd-ops/scripts/infra_perfil.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 8c9cdaff5ce025d2 |
| aidd-ops/scripts/phases/01_intake.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | fca3b2b68175c38a |
| aidd-ops/scripts/pipeline_ops.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | d9655d7e1566e4af |
| aidd-ops/scripts/rotate_secrets.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 2a4c354c89ee815b |
| aidd-ops/src/core/cofre_credenciais.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 1774f4404b95c180 |
| aidd-ops/src/core/coolify.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 581f63fc656116c1 |
| aidd-ops/src/core/result.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 9f5cee36356ebf9f |
| aidd-ops/templates/infra/nichos/b2b_industrial.json | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 71902f5fdf18cb0a |
| aidd-ops/templates/infra/nichos/clinicas.json | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 4cc8d14ae9ed5826 |
| aidd-ops/templates/infra/nichos/delivery.json | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | ed60ce5c9fa830d3 |
| aidd-ops/templates/infra/nichos/energia_solar.json | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 8a718fc721267c34 |
| aidd-ops/templates/infra/nichos/farmacias.json | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | ededc1b08b84d0e1 |
| aidd-ops/tests/test_coolify.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 279e87e36bd18e76 |
| aidd-ops/tests/test_helm_integration.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | a8d5a4f979ce5bca |
| aidd-ops/tests/test_intake_app.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | aae74fe3378550eb |
| aidd-ops/tests/test_mcps.py | modulos | Ticket 4: só troca de caminho tools/ -> modulos/ (descoberta da raiz ou pasta do mapa) | 21e3d41ce39b8544 |

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
