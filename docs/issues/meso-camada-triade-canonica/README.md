# Meso-Camada da Tríade Canônica: aidd-dispatch-pipeline

> **Iniciativa:** Implementação da Meso-Camada da Tríade Canônica (Aplicações Completas)  
> **Ciclo:** `[FORGE] ➔ [PRÉ-PLANO (Grill + Spec)] ➔ [PLANNER] ➔ [DISPATCH-PIPELINE] ➔ [ENGINE (Pure/Open/Freedom)] ➔ [MASTER CONVERGENCE]`  
> **Status do Backlog:** `ready-for-agent`

---

## 🎯 Objetivo

Implementar a camada intermediária determinística do ecossistema que:
1. Traduz o manifesto polimórfico `PLANNER.json` gerado pelo `aidd-planner` em um **Grafo Acíclico Dirigido (DAG)** de fatias verticais VSA.
2. Executa fatias independentes em **Git Worktrees paralelos**, acionando a engine correta da Tríade:
   - **Fluxo 01 (`pure`):** `aidd-generator` com ciclo TDD Red-Green.
   - **Fluxo 02 (`open`):** `aidd-factory` com curadoria open-source e fatias de integração.
   - **Fluxo 03 (`freedom`):** `aidd-bridge` com desacoplamento low-code.
3. Submete cada fatia a uma **Barreira de Validação** com Quality Gates locais antes de efetuar o merge.
4. Harmoniza todas as fatias validadas no núcleo Monólito Modular VSA do **`aidd-master`**, dando sequência natural para `aidd-enterprise` (SHA-256) e `aidd-ops` (VPS Docker).

---

## 🛡️ Leis Invioláveis Aplicadas

- **Lei #1 (Determinismo First):** DAG e ordenação topológica mecânicos via AST/NetworkX/Algoritmo de Kahn, sem deliberação de LLM.
- **Lei #2 (Saída Binária):** Gates por fatia retornando estritamente exit 0 (pass) ou exit 1 (block).
- **Lei #5 (Zero Stubs):** Proibição de stubs em contratos de fatias, rotas e casos de teste.
- **Lei #7 (Developer in Control):** Execuções sequenciais/paralelas determinísticas com join barrier e inspeção auditável.
- **Lei #10 (Quarteto Sine Qua Non):** Injeção obrigatória e dinâmica de Swagger, Webhooks, MCP e Guia em 100% das fatias.
- **Lei #11 (Padrão-Ouro de Stack):** Next.js + TypeScript + Tailwind no Frontend; Python puro + SQLite WAL (ou Postgres) no Backend; OpenAPI 3.1.
- **Lei #13 (Todo Portão Deve Provar que Morde):** `G_DISPATCH_PIPELINE_VSA.py` acompanhado de testes reais que comprovam reprovação sob violação sintética.

---

## 📂 Estrutura de Execução

Consulte `SESSOES.md` para os prompts executáveis em ordem estrita de dependência.
