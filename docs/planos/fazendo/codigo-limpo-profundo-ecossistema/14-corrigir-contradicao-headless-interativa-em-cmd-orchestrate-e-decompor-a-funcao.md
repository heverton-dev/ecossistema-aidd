# Item 14 — Corrigir contradicao headless-interativa em cmd_orchestrate e decompor a funcao

> **Escopo:** Corrigir a contradição em `ecossistema.py` onde o modo `--dangerously-force-headless` avisa que está em modo automático mas continua chamando `input()`, e decompor `cmd_orchestrate` (239 linhas) em partes menores com nomes claros. Não entra: `cmd_orchestrate` de outras ferramentas — este item é sobre `ecossistema.py` na raiz.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achados #19, #27 e #31, seção 2.2.

- `ecossistema.py:333–338` (e trecho seguinte): com a flag `--dangerously-force-headless`, o bloco de configuração interativa imprime `"[AVISO CRITICO] Modo headless forcado"` e **continua** chamando `input()` na sequência — um modo que se declara headless (sem interação) ainda pede resposta do usuário. **Nota de correção de registro do próprio relatório:** uma versão anterior do relatório havia classificado isso como "branch morto" (código inalcançável); a verificação das linhas 328–357 mostrou que o ramo **é alcançável** — o achado correto é a contradição de comportamento, não inalcançabilidade. Trate essa nota como parte do contexto: já foi verificado 2 vezes que o bug é real e alcançável.
- `ecossistema.py:318`: `import json` local dentro de uma função, usado 1 vez, quando deveria estar no topo do arquivo junto com os outros imports.
- `cmd_orchestrate` (`:189`, **239 linhas, 12 flags**): mistura roteamento de CLI, política de segurança (ambientes permitidos, a própria flag `--dangerously-force-headless`) e UI interativa (4 blocos `input()` com menus ASCII) no mesmo corpo — difícil de testar isoladamente.
- Nomes abreviados dentro dessa função exigem tradução mental (N7, achado #31): `harness_map_pars` (provável erro de grafia de "pairs"), `st`, `map_num`, `plan_obj` — dentro de um corpo de 239 linhas, tornando a leitura ainda mais difícil.

## Definicao de Pronto

1. O caso `--dangerously-force-headless` não chama mais `input()` em nenhum ponto do fluxo — se a flag está ativa, o comportamento é 100% não-interativo (falhar com erro claro se faltar informação, em vez de pedir input).
2. `import json` movido para o topo do arquivo.
3. `cmd_orchestrate` decomposto em pelo menos 3 funções distintas: roteamento de CLI, decisão de política de segurança, e fluxo interativo — cada uma testável isoladamente, sem precisar simular um terminal completo para testar a lógica de política.
4. Nomes abreviados (`harness_map_pars`, `st`, `map_num`, `plan_obj`) renomeados para nomes que não exigem tradução mental.
5. Testes reais cobrindo especificamente o cenário `--dangerously-force-headless` passam com exit 0, confirmando que nenhum `input()` é chamado nesse caminho.

## Criterio de saida

- Modo headless genuinamente não-interativo.
- `cmd_orchestrate` decomposto, nomes claros.
- Testes reais passando, incluindo o cenário headless.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 14: corrigir a contradicao em ecossistema.py onde
--dangerously-force-headless avisa modo automatico mas continua chamando input(), e
decompor cmd_orchestrate (239 linhas, 12 flags) com nomes claros (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achados #19, #27 e
#31, secao 2.2).

Fatos que voce precisa saber antes de comecar:
- ecossistema.py:333-338: com --dangerously-force-headless, imprime aviso critico de modo
  headless e SEGUE chamando input() na sequencia. JA FOI VERIFICADO 2 VEZES (inclusive uma
  correcao de registro dentro do proprio relatorio) que esse ramo e alcancavel de verdade,
  nao e codigo morto - nao repita o erro de assumir que e branch morto.
- ecossistema.py:318: import json local dentro de funcao, deveria estar no topo.
- cmd_orchestrate (:189, 239 linhas, 12 flags): mistura roteamento, politica de seguranca e
  UI interativa (4 blocos input() com menus ASCII) no mesmo corpo.
- Nomes abreviados dentro da funcao: harness_map_pars (provavel erro de grafia de "pairs"),
  st, map_num, plan_obj.

Regras obrigatorias:
1. O ponto central e comportamental, nao so estetico: apos a correcao, o modo headless
   forcado NUNCA pode chamar input() em nenhum caminho. Escreva um teste real que force esse
   cenario e confirme isso antes de considerar concluido - nao confie em leitura visual do
   codigo.
2. Ao decompor cmd_orchestrate, mantenha o comportamento observavel identico exceto pela
   correcao do item 1 acima - isto e refatoracao estrutural, nao mudanca de escopo.
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar o teste real do cenario
   headless.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 14: fix the contradiction in ecossistema.py where
--dangerously-force-headless warns about automatic mode but keeps calling input(), and
decompose cmd_orchestrate (239 lines, 12 flags) with clear names (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, findings #19, #27
and #31, section 2.2).

Facts you need before starting:
- ecossistema.py:333-338: with --dangerously-force-headless, it prints a critical headless
  warning and STILL calls input() next. This has ALREADY BEEN VERIFIED TWICE (including a
  correction note inside the report itself) that this branch is genuinely reachable, not
  dead code - do not repeat the mistake of assuming it's a dead branch.
- ecossistema.py:318: local import json inside a function, should be at the top.
- cmd_orchestrate (:189, 239 lines, 12 flags): mixes routing, security policy and
  interactive UI (4 input() blocks with ASCII menus) in the same body.
- Abbreviated names inside the function: harness_map_pars (likely misspelling of "pairs"),
  st, map_num, plan_obj.

Mandatory rules:
1. The core point is behavioral, not just cosmetic: after the fix, forced headless mode must
   NEVER call input() on any path. Write a real test that forces this scenario and confirms
   it before considering this done - do not rely on visual code review alone.
2. When decomposing cmd_orchestrate, keep observable behavior identical except for the fix
   in point 1 above - this is structural refactoring, not a scope change.
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real headless-scenario
   test.
5. Maintain monorepo governance rules (AGENTS.md).
```
