# Item 5 — Unificar reconhecimento de dominio (KNOWN_DOMAINS vs IntentRouter)

> **Escopo:** Unificar os dois mecanismos paralelos de reconhecimento de domínio dentro de master/enterprise: a lista fixa `KNOWN_DOMAINS` usada em `cmd_plan` e o `IntentRouter` (`src/core/intent_router.py`). Não entra: a decomposição estrutural de `cmd_plan` em si (Item 4) — este item é sobre o vocabulário duplicado, não sobre o tamanho da função.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achado #6 e seção 5.2.

- `scripts/aidd.py:850` (master) / `:650` (enterprise): `KNOWN_DOMAINS`, uma lista fixa de **24 termos em PT-BR** (ex.: "crm", "helpdesk", "faturamento"), com mapeamento manual de sinônimos dentro de `cmd_plan` (ex.: `slug = "crm" if d in ["lead", "leads"] else ...`).
- `src/core/intent_router.py`: **330 linhas, 15 padrões** de reconhecimento de intenção — o mesmo tipo de tarefa (reconhecer que tipo de módulo o usuário quer), só que por um mecanismo totalmente diferente.
- Evidência de que os dois vocabulários já divergiram: `grep "helpdesk\|faturamento"` dentro de `intent_router.py` retorna **zero resultados** — dois termos que `KNOWN_DOMAINS` reconhece não existem no `IntentRouter`.
- Isto é classificado no relatório como a "pior forma de DRY": não é duplicação de código, é **duplicação de conhecimento** — adicionar um domínio novo ao produto exige lembrar de tocar os dois lugares, e nada no código avisa que o segundo lugar existe.

## Decisao Registrada (confirmada com o usuario em 2026-09-09)

- **Decisao:** `IntentRouter` (`src/core/intent_router.py`) vira a fonte unica de
  reconhecimento de dominio, por ja ser o mecanismo mais sofisticado (padroes, nao lista
  fixa). Os 24 termos de `KNOWN_DOMAINS` sao incorporados como padroes/sinonimos dentro do
  `IntentRouter`. `cmd_plan` passa a chamar o `IntentRouter` diretamente em vez de manter
  `KNOWN_DOMAINS` e o mapeamento manual de sinonimos separado.

## Definicao de Pronto

1. Decisão registrada (humana) sobre qual mecanismo é a fonte de verdade — `KNOWN_DOMAINS` alimenta o `IntentRouter`, o `IntentRouter` substitui `KNOWN_DOMAINS`, ou os dois se fundem numa estrutura de dados única consumida pelos dois pontos de uso.
2. Após a unificação, rodando `grep` pelos 24 termos de `KNOWN_DOMAINS` dentro do mecanismo escolhido como fonte única, todos aparecem — 0 termos órfãos.
3. Adicionar um novo domínio de teste (ex.: um termo fictício) exige tocar exatamente **um lugar** no código, não dois.
4. Testes reais de `cmd_plan` (master e enterprise) passam com exit 0, cobrindo pelo menos os 24 termos originais de `KNOWN_DOMAINS`.

## Criterio de saida

- Um único mecanismo de reconhecimento de domínio, sem vocabulário duplicado.
- Nenhuma regressão nos 24 termos de domínio que `cmd_plan` já reconhecia.
- Testes reais passando.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 5: unificar os dois mecanismos paralelos de reconhecimento de
dominio em master/enterprise - a lista fixa KNOWN_DOMAINS usada em cmd_plan e o IntentRouter
(ver docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achado #6 e
secao 5.2, para evidencia completa).

Fatos que voce precisa saber antes de comecar:
- KNOWN_DOMAINS: aidd.py:850 (master) / :650 (enterprise) - 24 termos PT-BR com mapeamento
  manual de sinonimos.
- IntentRouter: src/core/intent_router.py, 330 linhas, 15 padroes.
- grep "helpdesk|faturamento" dentro do intent_router.py: ZERO resultados - os dois
  vocabularios ja divergiram de verdade.
- Isso e duplicacao de conhecimento, nao so de codigo: adicionar dominio novo hoje exige
  lembrar de tocar os 2 lugares.

Regras obrigatorias:
1. JA FOI DECIDIDO (ver secao "Decisao Registrada" acima): IntentRouter vira a fonte unica,
   KNOWN_DOMAINS e incorporado a ele e removido de cmd_plan.
2. Siga rigorosamente a Definicao de Pronto acima.
3. Nao invente aprovacoes. So marque como concluido apos confirmar por grep que os 24 termos
   originais existem na fonte unica escolhida e apos rodar os testes reais.
4. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 5: unify the two parallel domain-recognition mechanisms in
master/enterprise - the fixed KNOWN_DOMAINS list used in cmd_plan and the IntentRouter (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, finding #6 and
section 5.2, for full evidence).

Facts you need before starting:
- KNOWN_DOMAINS: aidd.py:850 (master) / :650 (enterprise) - 24 PT-BR terms with manual
  synonym mapping.
- IntentRouter: src/core/intent_router.py, 330 lines, 15 patterns.
- grep "helpdesk|faturamento" inside intent_router.py: ZERO results - the two vocabularies
  have already really diverged.
- This is duplication of knowledge, not just code: adding a new domain today requires
  remembering to touch both places.

Mandatory rules:
1. This has ALREADY BEEN DECIDED (see "Decisao Registrada" section above): IntentRouter
   becomes the single source, KNOWN_DOMAINS is folded into it and removed from cmd_plan.
2. Strictly follow the Definition of Done above.
3. Do not fabricate approvals. Only mark this done after confirming by grep that the 24
   original terms exist in the chosen single source, and after running the real tests.
4. Maintain monorepo governance rules (AGENTS.md).
```
