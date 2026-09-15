# Item 01: Scaffold do diretorio aidd-factory

## Escopo
Criar a estrutura base de `tools/aidd-factory/` seguindo o padrao das demais ferramentas do ecossistema.

## Definicao de Pronto
- [ ] Diretorio `tools/aidd-factory/` criado com estrutura completa
- [ ] `AGENTS.md` com diretrizes canonicas (padrao ecossistema)
- [ ] `scripts/pipeline_factory.py` — CLI Click basico com subcommands
- [ ] `scripts/contrato_factory.py` — validacao de input/output
- [ ] `src/core/__init__.py` e `src/core/result.py` (reutilizado de compartilhado)
- [ ] `schemas/schema_factory_input.json` — validacao do PLANO-INFRAESTRUTURA
- [ ] `schemas/schema_factory_output.json` — validacao do FACTORY_OUTPUT
- [ ] `tests/__init__.py`
- [ ] `py_compile` passa em todos os .py
- [ ] Gate G_FACTORY_MVP.py verifica estrutura

## Dependencias
- Nenhuma (primeiro item)

## Evidencia
- `tools/aidd-factory/` nao existe (audit explore-3)
- Padrao de estrutura: `tools/aidd-ops/`, `tools/aidd-generator/` como referencia
