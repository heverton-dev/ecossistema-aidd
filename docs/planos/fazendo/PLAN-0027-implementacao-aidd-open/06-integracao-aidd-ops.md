# Item 06: Integracao com aidd-ops

## Escopo
Conectar o factory ao pipeline existente do aidd-ops via PLANO-INFRAESTRUTURA.json e CLI unificada.

## Definicao de Pronto
- [ ] `ecossistema.py factory "<texto>" --pasta <dest>` funcional
- [ ] Chama `montar_plano_em_memoria()` do aidd-ops programaticamente
- [ ] Alimenta o factory_analysis.json como input
- [ ] Diretorio de saida contem todos os artefatos gerados
- [ ] `FACTORY_OUTPUT.json` lista todos os artefatos com status
- [ ] Intake web (Streamlit) tem botao "Gerar Stack Completa" que aciona factory
- [ ] Teste E2E: texto livre -> PLANO-INFRAESTRUTURA -> factory_output -> compose pronto
- [ ] Gate G_FACTORY_INTEGRATION.py valida cadeia completa

## Dependencias
- Itens 01-05 (todos os anteriores)

## Evidencia
- `montar_plano_em_memoria()` em `pipeline_ops.py:131`
- `contrato_plano.py` valida PLANO-INFRAESTRUTURA.json
- `intake_core.py` ja tem `gerar_plano()` como wrapper
- `DeployOrchestrator` em pipeline_ops.py ja tem etapa_5 para deploy
