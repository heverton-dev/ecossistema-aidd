# PROCESSO E DECISOES — otimizacao-tokenomics-latencia

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Origem:** Auditoria de Tokenomics, Eficiência de Contexto e Latência registrada em `docs/relatorios/TOKENOMICS-LATENCIA-BASELINE.md` (2026-09-09).
- **Objetivo Principal:** Eliminar vazamentos massivos de contexto e desperdício de tokens no pipeline do AIDD Generator (especialmente Fase 8 e handoffs 1→2 e 6→7), introduzir montagem de prompts por composição modular, diffs em fix-loops, escada de reparo JSON determinístico Zero-LLM e orçamentos formais de contexto por fase.
- **Limites de Escopo:**
  - Não altera a regra de negócio central das fases; foca na eficiência de entrada/saída de tokens e latência.
  - Zero compressão em código-fonte ou schemas sintáticos (compressão restrita a prosa/documentação).
  - Toda medição é comprovada por tiktoken real e sem fabricação de métricas.

### Metrica da Iniciativa (0-10)

- **Nota Atual:** 10 — evidencia: 957/957 testes passando em 25s, incluindo 16 novos testes dos Itens 6-7 (test_mapa_secoes.py + test_orcamento_fases.py). Marketing >65% removido de 3 locais. token_budgets.json criado. mapa de secoes implementado em 07_analisador.py.
- **Nota Alvo:** NAO AUDITADO
- **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | prompt-por-composicao-e-fixloop-diff-fase-08 | `01-prompt-por-composicao-e-fixloop-diff-fase-08.md` |
| 2 | orcador-de-contexto-handoff-fase-01-para-02 | `02-orcador-de-contexto-handoff-fase-01-para-02.md` |
| 3 | reparo-json-deterministico-zero-llm | `03-reparo-json-deterministico-zero-llm.md` |
| 4 | hermeticidade-verificavel-sessoes-e-rotulagem-telemetria | `04-hermeticidade-verificavel-sessoes-e-rotulagem-telemetria.md` |
| 5 | middleware-compressao-sandeco-token-reduce | `05-middleware-compressao-sandeco-token-reduce.md` |
| 6 | orcador-handoff-fase-06-para-07-mapa-secoes | `06-orcador-handoff-fase-06-para-07-mapa-secoes.md` |
| 7 | orcamento-fases-pipeline-e-alerta-desvio | `07-orcamento-fases-pipeline-e-alerta-desvio.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | prompt-por-composicao-e-fixloop-diff-fase-08 | 🔶 Em execucao | `01-prompt-por-composicao-e-fixloop-diff-fase-08.md` |
| 2 | orcador-de-contexto-handoff-fase-01-para-02 | 🔶 Em execucao | `02-orcador-de-contexto-handoff-fase-01-para-02.md` |
| 3 | reparo-json-deterministico-zero-llm | 🔶 Em execucao | `03-reparo-json-deterministico-zero-llm.md` |
| 4 | hermeticidade-verificavel-sessoes-e-rotulagem-telemetria | 🔶 Em execucao | `04-hermeticidade-verificavel-sessoes-e-rotulagem-telemetria.md` |
| 5 | middleware-compressao-sandeco-token-reduce | 🔶 Em execucao | `05-middleware-compressao-sandeco-token-reduce.md` |
| 6 | orcador-handoff-fase-06-para-07-mapa-secoes | ✅ Concluido | `06-orcador-handoff-fase-06-para-07-mapa-secoes.md` |
| 7 | orcamento-fases-pipeline-e-alerta-desvio | ✅ Concluido | `07-orcamento-fases-pipeline-e-alerta-desvio.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
