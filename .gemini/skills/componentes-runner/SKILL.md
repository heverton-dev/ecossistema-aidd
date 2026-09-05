---
name: componentes-runner
description: Cria, atualiza e sincroniza componentes agnosticos (skills, mcps, specs, hooks, configs, commands, sub-agents, scripts) entre todos os harnesses do ecossistema AIDD.
---

# Componentes Runner — Distribuicao Agnostica Multi-Harness

Esta skill atende solicitacoes em linguagem natural para criacao ou atualizacao de componentes em qualquer ferramenta (`aidd-forge`, `aidd-generator`, `aidd-master`, `aidd-enterprise`) ou no escopo `compartilhado` do monorepo.

## Protocolo Obrigatorio do Agente

Quando o usuario solicitar a criacao ou atualizacao de qualquer componente:

1. **Materializacao na Fonte Canonica Unica:**
   Crie ou edite o componente exclusivamente dentro do diretorio correspondente em `componentes/`:
   `componentes/<ferramenta ou compartilhado>/<tipo>/<nome>/...`
   seguindo a convencao de unidade e pasta estabelecida em `gates/manifesto_harnesses.json`:
   - `skill`: `componentes/<escopo>/skills/<nome>/SKILL.md`
   - `mcp`: `componentes/<escopo>/mcps/<nome>/server.py`
   - `spec`: `componentes/<escopo>/specs/<nome>.md`
   - `config`: `componentes/<escopo>/config/<nome>.json`
   - `command`: `componentes/<escopo>/comandos/<nome>.md`
   - `hook`: `componentes/<escopo>/hooks/<nome>/...`
   - `sub-agent`: `componentes/<escopo>/subagentes/<nome>.md`
   - `script`: `componentes/<escopo>/scripts/<nome>.py`

2. **Propagacao Automatica Deterministica (ZERO sync logic no agente/skill):**
   Execute o comando CLI oficial:
   ```bash
   python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>]
   ```

3. **Relatorio Factual ao Usuario:**
   Apresente diretamente a saida gerada pelo proprio comando (`components sync`), evidenciando com transparencia e sem invencao de dados quais pastas de harness receberam o componente.

## Comandos CLI Equivalentes

```bash
# Sincronizar tipo especifico
python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>]

# Sincronizar todos os componentes
python ecossistema.py components sync --tipo todos

# Verificar conformidade estrita (leitura)
python ecossistema.py components verify --tipo <tipo|todos> [--ferramenta <nome>]
```