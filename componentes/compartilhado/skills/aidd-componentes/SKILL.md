---
name: aidd-componentes
description: Creates, updates, and synchronizes agnostic components across all ecosystem harnesses.
---

# AIDD Componentes — Distribuição Agnóstica Multi-Harness

Esta skill gerencia a criação, atualização e sincronização de componentes agnósticos (skills, comandos, hooks, mcps) em todas as ferramentas e harnesses do ecossistema.

## Protocolo Obrigatório do Agente

1. **Materialização na Fonte Canônica Única:**
   Crie ou edite o componente exclusivamente dentro do diretório correspondente em `componentes/`:
   `componentes/<ferramenta ou compartilhado>/<tipo>/<nome>/...`
   seguindo a convenção de unidade e pasta estabelecida em `gates/manifesto_harnesses.json`:
   - `skill`: `componentes/<escopo>/skills/<nome>/SKILL.md`
   - `mcp`: `componentes/<escopo>/mcps/<nome>/server.py`
   - `spec`: `componentes/<escopo>/specs/<nome>.md`
   - `config`: `componentes/<escopo>/config/<nome>.json`
   - `command`: `componentes/<escopo>/comandos/<nome>.md`
   - `hook`: `componentes/<escopo>/hooks/<nome>/...`
   - `sub-agent`: `componentes/<escopo>/subagentes/<nome>.md`
   - `script`: `componentes/<escopo>/scripts/<nome>.py`

2. **Propagação Automática Determinística:**
   Execute o comando CLI oficial:
   ```bash
   python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>]
   ```

3. **Verificação de Integridade:**
   ```bash
   python ecossistema.py components verify --tipo <tipo> [--ferramenta <nome>]
   ```
