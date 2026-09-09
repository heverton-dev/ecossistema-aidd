# Item 11 — Refatorar Fase 08 do generator (monolito, classificador por substring, excecoes copy-paste, estado global com sentinela dupla)

> **Escopo:** Decompor `scripts/phases/08_implementador.py` (1.527 linhas), corrigir o classificador de falhas por substring acoplado ao formato de saída do pytest, unificar os 7 handlers de exceção idênticos, e corrigir o estado global `_TOKENIZADOR_TIKTOKEN` com sentinela dupla confusa. Não entra: o parser `_extrair_json_manual` (Item 10, já tratado separadamente) nem a consolidação de Result monad genérica (Item 7).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achados #13, #14 e #22, seção 4.3 e 4.4.

- `scripts/phases/08_implementador.py`: **1.527 linhas** num arquivo só.
- `PostMortemAnalyzer._classificar_falha`: classifica erro de teste **procurando substring** (ex.: `'assertionerror' in saida_lower`) — acoplado ao formato de saída textual do `pytest`; quebra silenciosamente se o formatter do pytest mudar numa atualização futura.
- Auto-cura aninhada em **3 níveis**: `_implementar_script_com_verificacao` (85 linhas) chama `_auto_cura_microtasks` (70 linhas) — profundidade de aninhamento que dificulta seguir o fluxo de decisão.
- **7 ocorrências idênticas** do mesmo `except Exception as e: print(...)` (linhas `:98, 106, 1195` + 4 outras) — tratamento de exceção por cópia-colagem, sem abstração comum.
- **Contraste interno de padrão já existente na mesma ferramenta:** `materializador.py:93` usa `# noqa: BLE001` com justificativa explícita do porquê o `except Exception` genérico é aceitável ali; `utils_delegacao.py:137` usa `except Exception: pass` com comentário mas sem essa mesma disciplina — dois estilos para o mesmo problema dentro do próprio generator.
- **Estado global confuso (N7, achado #22):** `_TOKENIZADOR_TIKTOKEN` (`utils_delegacao.py:477–492`) pode valer `None` (ainda não carregado) ou `False` (carregamento falhou) — duas semânticas diferentes para dois estados de "não disponível", protegido por um `except Exception` que engole a causa real da falha de carregamento.

## Definicao de Pronto

1. `08_implementador.py` decomposto em módulos menores por responsabilidade (classificação de falha, auto-cura, orquestração de fase) — nenhum arquivo resultante deve concentrar de novo 1.500+ linhas.
2. `_classificar_falha` não depende mais de substring hardcoded no texto de saída do pytest — usa um mecanismo mais robusto (ex.: parsing estruturado do relatório do pytest, se disponível, ou um mapeamento explícito e testado de padrões conhecidos, documentado como tal).
3. Os 7 handlers `except Exception as e: print(...)` são substituídos por um mecanismo único de tratamento/log, aplicado nos 7 pontos.
4. `_TOKENIZADOR_TIKTOKEN` usa um sentinela único e não ambíguo para "não carregado" vs "falhou ao carregar" (ex.: enum ou 2 variáveis nomeadas em vez de `None`/`False` no mesmo slot), e o `except Exception` que hoje engole a causa passa a logar ou propagar a causa real.
5. Testes reais da Fase 08 (os testes já existentes do generator para essa fase) passam com exit 0 após a refatoração.

## Criterio de saida

- Fase 08 decomposta, sem arquivo monolítico de 1.500+ linhas.
- Classificador de falha e tratamento de exceção sem acoplamento frágil nem repetição copy-paste.
- Estado global com semântica clara.
- Testes reais passando.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 11: decompor scripts/phases/08_implementador.py (1.527 linhas),
corrigir o classificador de falhas por substring, unificar 7 handlers de excecao copy-paste,
e corrigir o estado global _TOKENIZADOR_TIKTOKEN com sentinela dupla confusa (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achados #13, #14 e
#22, secoes 4.3 e 4.4).

Fatos que voce precisa saber antes de comecar:
- 08_implementador.py: 1.527 linhas.
- PostMortemAnalyzer._classificar_falha classifica por substring ('assertionerror' in
  saida_lower) - acoplado ao formato de saida do pytest, fragil a mudanca de versao.
- Auto-cura aninhada 3 niveis: _implementar_script_com_verificacao (85L) chama
  _auto_cura_microtasks (70L).
- 7 ocorrencias identicas de except Exception as e: print(...) (linhas 98, 106, 1195 + 4
  outras).
- Contraste ja existente na mesma ferramenta: materializador.py:93 usa noqa BLE001 com
  justificativa explicita; utils_delegacao.py:137 usa except Exception: pass sem a mesma
  disciplina.
- _TOKENIZADOR_TIKTOKEN (utils_delegacao.py:477-492): None = nao carregado, False = falhou -
  duas semanticas no mesmo slot, protegido por except Exception que engole a causa real.

Regras obrigatorias:
1. Ao trocar o classificador por substring por algo mais robusto, verifique primeiro se ha
   uma forma estruturada de ler o resultado do pytest (nao so texto) antes de reimplementar
   outro parser fragil - se nao houver alternativa clara, documente a limitacao em vez de
   inventar uma solucao complexa demais para o problema.
2. Ao consertar o sentinela duplo do tokenizador, garanta que a causa real de falha de
   carregamento passe a ser logada, nao apenas silenciada de forma diferente.
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais da Fase 08.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 11: decompose scripts/phases/08_implementador.py (1,527
lines), fix the substring-based failure classifier, unify 7 copy-pasted exception handlers,
and fix the _TOKENIZADOR_TIKTOKEN global state with its confusing double sentinel (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, findings #13, #14
and #22, sections 4.3 and 4.4).

Facts you need before starting:
- 08_implementador.py: 1,527 lines.
- PostMortemAnalyzer._classificar_falha classifies by substring ('assertionerror' in
  saida_lower) - coupled to pytest's output format, fragile to version changes.
- 3-level nested self-healing: _implementar_script_com_verificacao (85L) calls
  _auto_cura_microtasks (70L).
- 7 identical occurrences of except Exception as e: print(...) (lines 98, 106, 1195 + 4
  more).
- Existing contrast in the same tool: materializador.py:93 uses noqa BLE001 with explicit
  justification; utils_delegacao.py:137 uses except Exception: pass without the same
  discipline.
- _TOKENIZADOR_TIKTOKEN (utils_delegacao.py:477-492): None = not loaded, False = failed to
  load - two semantics in the same slot, guarded by an except Exception that swallows the
  real cause.

Mandatory rules:
1. When replacing the substring classifier with something more robust, first check whether
   there is a structured way to read the pytest result (not just text) before reimplementing
   another fragile parser - if there is no clear alternative, document the limitation instead
   of inventing an overly complex solution for the problem.
2. When fixing the tokenizer's double sentinel, make sure the real cause of a load failure
   gets logged, not just silenced in a different way.
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real Phase 08 tests.
5. Maintain monorepo governance rules (AGENTS.md).
```
