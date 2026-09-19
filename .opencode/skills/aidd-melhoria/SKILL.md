---
name: aidd-melhoria
description: Deeply analyzes code improvements from natural language and produces structured evaluation reports.
---

# AIDD Melhoria — Análise Profunda Pré-Planejamento (/melhoria)

Contrato executável universal para análise profunda pré-planejamento de melhorias no ecossistema AIDD.

## Posição no Fluxo

| Etapa | Comando | Entra | Sai | Parada obrigatória no fim |
|---|---|---|---|---|
| 1 | `/melhoria <pedido>` | Pedido do usuário ou plano existente | Relatório em `docs/melhorias/` com Nota Atual e evidência | "Deseja que eu gere o plano a partir disto?" |
| 2 | `/plan <nome>` | Relatório da etapa 1 ou pedido direto | Pasta em `docs/planos/<nome>/` com todos os itens em rascunho | "Aprova este plano?" |
| 3 | `/orchestrate <plano>` | Plano aprovado | Execução real das frentes via worktrees | Escolha de ambiente + aprovação do Plano de Voo |

## Como Usar

No chat do assistente:
```text
/melhoria <sua sugestão de melhoria ou refatoração>
```

Via CLI Python:
```bash
python ecossistema.py melhoria init <nome> --pedido "<pedido>"
```
