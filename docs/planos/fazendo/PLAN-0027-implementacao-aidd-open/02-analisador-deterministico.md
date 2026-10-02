# Item 02: Fase 1 — Analisador Deterministico

## Escopo
Implementar `scripts/phases/01_analisador.py` que le o PLANO-INFRAESTRUTURA.json e extrai requisitos estruturados para o factory.

## Definicao de Pronto
- [ ] `01_analisador.py` implementado com 100% determinismo (zero LLM)
- [ ] Le PLANO-INFRAESTRUTURA.json via schema validado
- [ ] Extrai: nicho, ferramentas[], bancos_logicos[], vps_spec, blocos[]
- [ ] Cruza com `templates/infra/nichos/<nicho>.json` para mapear blocos
- [ ] Gera `factory_analysis.json` como output
- [ ] Valida output contra `schema_factory_analysis.json`
- [ ] Testes unitarios com fixture real (clinicas, delivery, farmacias)
- [ ] Gate G_FACTORY_ANALYSIS.py valida output

## Dependencias
- Item 01 (scaffold)

## Evidencia
- `PLANO-INFRAESTRUTURA.json` schema em `componentes/compartilhado/specs/plano-infraestrutura.schema.json`
- `nichos/*.json` tem blocos[] com caminho para templates
- `requisitos_recursos.json` tem banco_detectado por ferramenta
