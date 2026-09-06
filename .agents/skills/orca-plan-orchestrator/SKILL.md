---
name: orca-plan-orchestrator
description: Orquestrador multi-agente determinístico ORCA ADE para execução paralela de planos fatiados com git worktrees efêmeras, hooks reativos e gates locais.
---

# ORCA ADE — Plan Orchestrator

Esta skill orquestra a execução automatizada de planos fatiados (`00-PROCESSO-E-DECISOES.md` + `NN-*.md`) em qualquer projeto ou repositório.

## Capacidades

- **Parser Determinístico de Planos:** interpreta pastas de planos com frentes paralelas.
- **Ciclo de Vida Efêmero de Worktree:** isolamento estrito via `git worktree` e branches efêmeras.
- **Hooks Reativos (Zero Polling):** sinalização por eventos push e sincronismo de estado.
- **Auditoria de Gates Locais:** validação estrita (exit 0) antes de qualquer merge.
- **Circuit Breaker Anti-Loop:** proteção ativa contra travamento ou excesso de tempo/inatividade.
- **CLI e Plano de Voo Interativo:** compilação de comandos de harness, detecção de binários instalados e seleção interativa.

## Protocolo Interativo do Agente (/orchestrate)

Quando o comando `/orchestrate [plano]` for invocado:

1. **Inspeção do Plano:**
   Valide se o caminho informado possui `00-PROCESSO-E-DECISOES.md` e arquivos `NN-*.md`.
2. **Configuração Interativa (Perguntas Estruturadas ao Usuário):**
   Antes de disparar a execução, pergunte interativamente ao usuário:
   - **Modo de Operação:**
     - `1) Automatizado (Headless):` execução autônoma com streaming de logs em tempo real.
     - `2) Interativo (Recomendado):` você assume o controle direto no terminal da worktree de cada frente.
   - **Atribuição de Harnesses Executores:**
     - `1) Global:` um único harness executor para todas as frentes (`claude`, `agy`, `mimo`, `opencode`).
     - `2) Personalizado (Miscelânea Multi-Harness):` o usuário define qual harness executa cada frente específica do plano.
3. **Compilação e Apresentação do Plano de Voo:**
   Gere e apresente o Plano de Voo (`--dry-run`) exibindo frentes, branches efêmeras, harness atribuído por frente e modo da sessão.
4. **Confirmação e Disparo:**
   Aguarde a aprovação explícita do usuário para iniciar o motor executivo via CLI.

## Uso via CLI

```bash
# Modo Interativo Automático (pergunta modo interativo/headless e harness por frente)
python ecossistema.py orchestrate [plano]

# Modo Interativo direto
python ecossistema.py orchestrate [plano] --interactive

# Miscelânea por frente via CLI
python ecossistema.py orchestrate [plano] --interactive --harness-map frente1=claude,frente2=agy

# Visualizar plano de voo sem executar (Zero LLM / Zero Token)
python ecossistema.py orchestrate [plano] --dry-run
```
