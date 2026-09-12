# Item 10 — Simplificar parser defensivo extrair_json_manual e corrigir comentario de numeracao mentiroso

> **Escopo:** Simplificar `_extrair_json_manual` (`scripts/phases/utils_delegacao.py`), que hoje é uma cascata de regexes de fallback sem teste unitário próprio, e corrigir o comentário de numeração de passos que não bate mais com o código. Não entra: a Fase 08 do generator como um todo (Item 11) — este item é específico do parser de `utils_delegacao.py`.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achados #12 e #24, seção 4.2.

- `scripts/phases/utils_delegacao.py:145` — `_extrair_json_manual`, **78 linhas**, com cascata de **5 estratégias** em sequência (JSON direto → fences markdown → sanitização de escapes → extração de campos `codigo`/`teste` → `json.loads` final para lançar erro).
- Exemplo de regex de "mini-gramática sem nome" citado no relatório (campo `codigo`, 3 padrões alternativos aninhados num único regex) — nenhuma dessas mini-gramáticas tem teste unitário próprio, só é exercitada indiretamente pelos testes que chamam a fase inteira.
- `_extrair_campos_codegen` (`:177`, 39 linhas) — mesma família de problema, parser de campos por regex sem teste isolado.
- **Comentário mentiroso (achado #24, N-relacionado):** cascata numerada "1. 2. 4. 5." dentro do código (`:176`) — o passo 3 foi removido em algum momento e a numeração não foi atualizada. Um comentário que descreve uma estrutura que não existe mais é pior que nenhum comentário, porque engana quem lê.

## Definicao de Pronto

1. `_extrair_json_manual` tem cada uma das 5 estratégias de parsing testada isoladamente (teste unitário da estratégia em si, não só do fluxo completo da fase) — ou as estratégias são reduzidas/simplificadas se alguma for redundante (ex.: se 2 das 5 nunca disparam na prática, confirmar por telemetria/teste real antes de remover, não por suposição).
2. Regexes hoje sem nome (ex.: o campo `codigo` com 3 padrões aninhados) recebem nome ou são decompostas em passos nomeados que descrevem o que cada um faz.
3. O comentário de numeração de passos é corrigido para bater com o código real (ou o passo removido é reintroduzido, se a remoção tiver sido um erro — a decidir durante a investigação, não assumido de antemão).
4. Testes reais de `utils_delegacao.py` passam com exit 0, cobrindo pelo menos um caso de entrada real para cada uma das 5 estratégias de fallback.

## Criterio de saida

- Parser com estratégias testadas isoladamente e nomeadas.
- Comentário de numeração corrigido, batendo com o código.
- Testes reais passando.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 10: simplificar _extrair_json_manual (scripts/phases/utils_delegacao.py)
e corrigir um comentario de numeracao de passos que nao bate mais com o codigo (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achados #12 e #24,
secao 4.2).

Fatos que voce precisa saber antes de comecar:
- utils_delegacao.py:145 - _extrair_json_manual, 78 linhas, 5 estrategias de fallback em
  cascata, nenhuma testada isoladamente.
- utils_delegacao.py:177 - _extrair_campos_codegen, 39 linhas, mesma familia de problema.
- utils_delegacao.py:176 - comentario "1. 2. 4. 5." (passo 3 foi removido, numeracao nao foi
  atualizada) - comentario mentiroso sobre a estrutura real do codigo.

Regras obrigatorias:
1. Antes de remover ou simplificar qualquer uma das 5 estrategias de fallback, confirme com
   teste real (nao suposicao) se ela ainda e exercitada na pratica - se houver duvida sobre
   se uma estrategia e realmente morta, PARE e pergunte antes de apagar codigo que pode
   estar protegendo contra um caso raro real.
2. Ao corrigir o comentario de numeracao, verifique se o passo 3 foi removido por engano
   (bug) ou de proposito (limpeza anterior) - documente qual dos dois casos encontrou.
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais cobrindo as 5
   estrategias.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 10: simplify _extrair_json_manual
(scripts/phases/utils_delegacao.py) and fix a step-numbering comment that no longer matches
the code (see docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html,
findings #12 and #24, section 4.2).

Facts you need before starting:
- utils_delegacao.py:145 - _extrair_json_manual, 78 lines, 5 cascading fallback strategies,
  none tested in isolation.
- utils_delegacao.py:177 - _extrair_campos_codegen, 39 lines, same problem family.
- utils_delegacao.py:176 - comment "1. 2. 4. 5." (step 3 was removed, numbering was never
  updated) - a comment that lies about the code's real structure.

Mandatory rules:
1. Before removing or simplifying any of the 5 fallback strategies, confirm with a real test
   (not assumption) whether it is still exercised in practice - if there is doubt about
   whether a strategy is truly dead, STOP and ask before deleting code that might be guarding
   against a real rare case.
2. When fixing the numbering comment, check whether step 3 was removed by mistake (bug) or
   on purpose (previous cleanup) - document which of the two you found.
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real tests covering all
   5 strategies.
5. Maintain monorepo governance rules (AGENTS.md).
```
