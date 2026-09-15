# Item 07: Integracao Full — Intake -> Factory -> Deploy

## Escopo
Encadear o pipeline completo: intake web -> PLANO-INFRAESTRUTURA -> factory -> deploy.

## Definicao de Pronto
- [ ] `pipeline_factory.py` aceita `--deploy` flag
- [ ] `--deploy` aciona `DeployOrchestrator` do aidd-ops automaticamente
- [ ] Intake web (Streamlit) ganha botao "Gerar Stack Completa"
- [ ] Botao aciona: gerar plano -> factory -> deploy em sequencia
- [ ] CLI unificada: `ecossistema.py factory --plano <arq> --pasta <dest> --deploy`
- [ ] `FACTORY_OUTPUT.json` inclui status de deploy
- [ ] Teste E2E: texto -> plano -> factory -> compose pronto -> deploy (dry-run)

## Dependencias
- Itens 01-06 (todas as fases do factory)

## Evidencia
- `DeployOrchestrator` em `pipeline_ops.py` ja tem etapa_5 para deploy
- `intake_core.py` ja tem `gerar_plano()` como wrapper
- v2 doc §4.3: "tudo pronto para o aidd-ops fazer deploy"
