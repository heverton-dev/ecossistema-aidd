# Item 14 — Remover ou ligar código morto de resiliência no enterprise

> **Escopo:** Entra: decidir, pra cada classe achada sem chamador (`CircuitBreaker`, `SagaOrchestrator`, `TraceContextMiddleware` em `tools/aidd-enterprise/src/core/` e espelhos em `templates/`), entre (a) remover — se é scaffolding nunca finalizado, ou (b) ligar de verdade — se é feature real que só não foi conectada ainda. Não entra: os outros 737 símbolos mortos do levantamento (a maioria é cópia esperada de exemplo/template — este item cobre só os 3 de `core/`, que são o caso mais grave por serem "missão crítica").
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (decisão de escopo: remover vs. terminar a feature)

---

## Contexto já investigado

- Achado em 2026-09-07 rodando `code-review-graph dead-code` de verdade: 740 símbolos sem nenhum chamador no ecossistema inteiro. A maioria é cópia esperada (exemplos em `materiais-extras/`, espelhos multi-harness de `.claude/`, `.gemini/` etc. da mesma skill).
- **3 casos graves, isolados dos demais:** `CircuitBreaker` (`tools/aidd-enterprise/src/core/circuit_breaker.py:9`), `SagaOrchestrator` (`tools/aidd-enterprise/src/core/saga.py:11`), `TraceContextMiddleware` (`tools/aidd-enterprise/src/core/opentelemetry.py:166`) — três padrões de resiliência/observabilidade de missão crítica, presentes no código do `aidd-enterprise` (a ferramenta que se vende como "Missão Crítica"), mas **nenhum tem um único chamador** confirmado pelo grafo. Mesmos 3 espelhados em `templates/core/` e `templates/v2/`.
- Contradiz a Regra de Ouro #5 (Zero Stubs / Zero Mocks Falsos em Produção) se for scaffolding abandonado — ou é uma feature real que falta só o fio de ligação, caso em que o achado é "termine, não remova".

## Definição de Pronto

1. Pra cada um dos 3 símbolos, reproduzir a checagem (`code-review-graph query --pattern callers_of --target <símbolo>` ou equivalente) confirmando de novo que não há chamador — não confiar cegamente no scan anterior sem reproduzir.
2. Decisão registrada aqui (remover vs. ligar) com justificativa, antes de qualquer código ser tocado.
3. Se remover: também remover dos 3 espelhos em `templates/`. Se ligar: pelo menos 1 teste real cobrindo o caminho que agora chama o símbolo.
4. Rodar `code-review-graph update` + `dead-code` de novo depois da mudança e confirmar que os 3 não aparecem mais na lista (removidos) ou aparecem com chamador real (ligados).
5. Suíte de testes do `aidd-enterprise` continua verde.

## Critério de saída

- Os 3 símbolos resolvidos (removidos ou ligados), reproduzido via `code-review-graph dead-code`.
- Nenhuma regressão nos testes.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item 14: Remover ou ligar código morto de resiliência no enterprise.
Siga rigorosamente a Definição de Pronto acima.
Não invente aprovações e mantenha as regras do monorepo.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 14: Remover ou ligar código morto de resiliência no enterprise.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
