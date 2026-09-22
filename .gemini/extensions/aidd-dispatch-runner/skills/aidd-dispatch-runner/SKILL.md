---
name: aidd-dispatch-runner
description: Despacha fatias verticais VSA em Git Worktrees efêmeras com isolamento estrito, verificação de Quality Gates e convergência master.
---

# AIDD-Dispatch Runner — Despacho Topológico de Fatias VSA em Git Worktrees

Esta skill executa o pipeline de meso-camada da Tríade Canônica, despachando fatias verticais (Vertical Slice Architecture) em Git Worktrees efêmeras com isolamento de código, verificação em lote topológico (DAG) e convergência segura no Monólito Modular (`aidd-master`).

## Triggers
- `/dispatch`
- `dispatch`
- `/aidd-dispatch`
- `python ecossistema.py dispatch`

## Invariantes e Leis Auditadas

1. **Determinismo Topológico (Lei #1):** O plano compilado (`vsa_dispatch.json`) ordena a execução das fatias via algoritmo de Kahn. Fatias independentes rodam no mesmo lote; dependentes aguardam a convergência anterior.
2. **Saída Binária (Lei #2):** Cada fatia e a convergência master passam por Quality Gates com saída estrita (`exit 0` = aprovação, `exit 1` = bloqueio).
3. **Isolamento em Worktree (Lei #7):** Cada fatia executa em `.worktrees/<slice_id>` em branch dedicada `slice/<slice_id>`. O cleanup é garantido ao término.
4. **Fronteira Estrita de Arquivos (Lei #5):** Nenhuma fatia pode modificar arquivos fora dos diretórios atribuídos explicitamente em `arquivos_permitidos`. Violações abortam o merge imediatamente.
5. **Quarteto Sine Qua Non Dinâmico (Lei #10):** Toda fatia provê rotas e contratos para `/docs`, `/webhooks`, `/mcp` e `/docs/guia`.

## Como Usar

### 1. Despacho Direto via PLANNER.json
Compila automaticamente o grafo topológico e despacha as fatias:
```bash
python ecossistema.py dispatch --planner <caminho/para/PLANNER.json>
```

### 2. Despacho via Manifesto Pré-Compilado
Executa diretamente um plano topológico `vsa_dispatch.json` validado contra `G_DISPATCH_PIPELINE_VSA`:
```bash
python ecossistema.py dispatch --dispatch <caminho/para/vsa_dispatch.json>
```

### 3. Simulação Determinística (Dry-Run)
Valida todo o grafo, contratos e isolamento sem tocar no Git ou no disco:
```bash
python ecossistema.py dispatch --planner <caminho/para/PLANNER.json> --dry-run
```

### 4. Controle de Paralelismo
Limita a quantidade de Git Worktrees simultâneas:
```bash
python ecossistema.py dispatch --planner <caminho/para/PLANNER.json> --workers 2
```

## Encadeamento Canônico de Intake
```text
/aidd-grill ➔ /aidd-spec ➔ /aidd-planner ➔ /aidd-dispatch-runner ➔ aidd-master ➔ aidd-enterprise
```
