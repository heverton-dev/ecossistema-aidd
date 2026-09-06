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
2. **Seleção Interativa de Harnesses (Pergunta Explícita ao Usuário):**
   Antes de disparar a execução, realize uma pergunta interativa estruturada ao usuário:
   - **Harness Executor:** Qual harness executará as etapas de código? (`claude`, `agy`, `mimo`, `opencode`).
   - **Harness Auditor:** Qual harness ou processo auditará os Quality Gates locais antes do merge? (Padrão determinístico: Quality Gates locais / auditoria do próprio agente coordenador).
3. **Compilação e Apresentação do Plano de Voo:**
   Gere e apresente o Plano de Voo (`--dry-run`) exibindo frentes, branches efêmeras e comandos mapeados.
4. **Confirmação e Disparo:**
   Aguarde a aprovação explícita do usuário para iniciar o motor executivo.

## Uso via CLI

```bash
# Modo Interativo Automático (detecta harnesses instalados no sistema e pergunta ao usuário)
python ecossistema.py orchestrate [plano]

# Visualizar plano de voo sem executar (Zero LLM / Zero Token)
python ecossistema.py orchestrate [plano] --dry-run

# Executar direto com harness específico (modo não-interativo)
python ecossistema.py orchestrate [plano] --harness claude --yes
```
