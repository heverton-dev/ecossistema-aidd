# Item 13 — Estreitar except Exception e except pass remanescentes em gates da raiz e src-core

> **Escopo:** Estreitar os `except Exception` genéricos remanescentes em `gates/*.py` (raiz) e os handlers `except: pass` silenciosos em `src/core/` de master/enterprise. Não entra: o narrowing já feito nos commits recentes (`fix(exceptions)` já concluídos) — este item cobre especificamente o que sobrou, verificado de novo nesta auditoria.
> **Status:** [EM EXECUCAO]

---

## Contexto ja investigado

Fonte: relatório de auditoria, achados #17 e #18, seções 2.3 e 5.4/6.

- **13× `except Exception`** nos gates da raiz (`gates/*.py`, contado por `grep -c`): `G_INFRA_COMPOSE` 6×, `G_COMPONENTE_AGNOSTICO` 2×, `G_HADOLINT` 2×, `G_ECOSSISTEMA_INTEGRIDADE` 1×, `G_SEGREDOS` 1×, `G_TESTES_REAIS` 1×.
- Caso concreto de risco real: `G_COMPONENTE_AGNOSTICO.py:54,73` — erro de parsing de configuração vira **retorno default silencioso**, ou seja, uma configuração corrompida pode fazer o gate **aprovar** em vez de falhar. Isso dilui o sinal de severidade (um erro de programação é tratado como se fosse um WARN de negócio).
- **17 handlers `except: pass` silenciosos** em `src/core/` de master e enterprise (confirmado por AST, não por grep de texto) — inclui `saga.py:28`, onde a falha de uma **compensação de saga é destruída sem log nem rethrow** (num padrão de saga, isso é particularmente grave: a compensação existe justamente para desfazer um efeito colateral já aplicado; se ela falhar em silêncio, o sistema fica em estado inconsistente sem ninguém saber). Outros pontos: `fleet_discovery.py:256`, `materializador.py` (8 pontos), `opentelemetry.py:45`, `subagent_engine.py:554`.

## Decisao Registrada (confirmada com o usuario em 2026-09-09)

- **saga.py:28:** falha de compensacao de saga NUNCA fica em silencio. Decisao: registrar a
  excecao real em log (com stack trace) e marcar o processo/saga como "precisa de atencao
  humana" (ex.: um status explicito de falha, nao so um log perdido em meio a outros) — em
  vez de so `except: pass`. Rethrow automatico nao e obrigatorio se houver um mecanismo de
  status/alerta equivalente; o que nao pode acontecer e a falha desaparecer sem rastro.
- **Demais 16 handlers `except: pass`** em `src/core/`: aplicar o mesmo principio (log da
  causa real, no minimo) caso a caso.
- **G_COMPONENTE_AGNOSTICO e os 13 `except Exception` dos gates da raiz:** seguir a
  Definicao de Pronto abaixo (erro de parsing de config deve falhar o gate, nao aprovar por
  padrao).

## Definicao de Pronto

1. Cada um dos 13 `except Exception` da raiz é avaliado individualmente: os que envolvem falha de sub-ferramenta externa legítima (ex.: `G_INFRA_COMPOSE` chamando ferramenta de infraestrutura) podem manter captura ampla, mas com log explícito da exceção real (não silenciar); os que hoje convertem erro de configuração em aprovação silenciosa (`G_COMPONENTE_AGNOSTICO:54,73`) são corrigidos para que erro de parsing faça o gate **falhar**, não aprovar por padrão.
2. Os 17 `except: pass` em `src/core/` são substituídos por tratamento que ao menos loga a exceção; `saga.py:28` especificamente precisa de correção prioritária — falha de compensação de saga não pode ser destruída sem rastro (a decisão de rethrow vs log-and-continue depende do design da saga e deve ser validada com quem entende esse fluxo).
3. Rodando novamente as contagens do relatório (`grep -c "except Exception"` nos gates da raiz e a busca AST por `except: pass` em `src/core/`), os números caem para os casos documentados como aceitáveis (com log), sem handlers silenciosos remanescentes fora dessa lista.
4. Testes reais dos gates da raiz e do fluxo de saga passam com exit 0, incluindo um teste que force o caso de configuração corrompida em `G_COMPONENTE_AGNOSTICO` e confirme que o gate agora falha (e não aprova) nesse cenário.

## Criterio de saida

- `except Exception`/`except: pass` remanescentes revisados individualmente, com log ou narrowing conforme o caso.
- `G_COMPONENTE_AGNOSTICO` não aprova mais com config corrompida.
- Falha de compensação de saga não é mais destruída em silêncio.
- Testes reais passando.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 13: estreitar os except Exception genericos remanescentes em
gates/*.py (raiz) e os except: pass silenciosos em src/core/ de master/enterprise (ver
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, achados #17 e #18,
secoes 2.3 e 5.4/6). Este item e uma continuacao do trabalho de narrowing ja feito em
commits anteriores (fix(exceptions)) - cobre o que sobrou, verificado de novo nesta
auditoria.

Fatos que voce precisa saber antes de comecar:
- 13x except Exception nos gates da raiz: G_INFRA_COMPOSE 6x, G_COMPONENTE_AGNOSTICO 2x,
  G_HADOLINT 2x, G_ECOSSISTEMA_INTEGRIDADE 1x, G_SEGREDOS 1x, G_TESTES_REAIS 1x.
- G_COMPONENTE_AGNOSTICO.py:54,73: erro de parsing vira retorno default SILENCIOSO - config
  corrompida pode aprovar o gate.
- 17 handlers except: pass em src/core/ (master e enterprise), incluindo saga.py:28 - falha
  de compensacao de saga destruida sem log nem rethrow.
- Outros pontos: fleet_discovery.py:256, materializador.py (8 pontos), opentelemetry.py:45,
  subagent_engine.py:554.

Regras obrigatorias:
1. saga.py:28 JA FOI DECIDIDO (ver secao "Decisao Registrada" acima): nunca silenciar -
   registrar a excecao real em log com stack trace e marcar o processo como "precisa de
   atencao humana". Implemente exatamente isso.
2. Para G_COMPONENTE_AGNOSTICO, a mudanca de "aprovar por padrao" para "falhar em erro de
   parsing" muda o comportamento observavel do gate - escreva um teste real que force esse
   cenario antes de considerar concluido.
3. Siga rigorosamente a Definicao de Pronto acima.
4. Nao invente aprovacoes. So marque como concluido apos rodar os testes reais e confirmar
   as contagens do relatorio de novo.
5. Mantenha as regras de governanca do monorepo (AGENTS.md).
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 13: narrow the remaining generic except Exception in
gates/*.py (root) and the silent except: pass in src/core/ of master/enterprise (see
docs/relatorios/relatorio-auditoria-codigo-limpo-ecossistema-aidd.html, findings #17 and
#18, sections 2.3 and 5.4/6). This item continues the narrowing work already done in
previous commits (fix(exceptions)) - it covers what remains, re-verified in this audit.

Facts you need before starting:
- 13x except Exception in root gates: G_INFRA_COMPOSE 6x, G_COMPONENTE_AGNOSTICO 2x,
  G_HADOLINT 2x, G_ECOSSISTEMA_INTEGRIDADE 1x, G_SEGREDOS 1x, G_TESTES_REAIS 1x.
- G_COMPONENTE_AGNOSTICO.py:54,73: a parsing error becomes a SILENT default return -
  corrupted config can make the gate pass.
- 17 except: pass handlers in src/core/ (master and enterprise), including saga.py:28 -
  saga compensation failure destroyed with no log or rethrow.
- Other points: fleet_discovery.py:256, materializador.py (8 spots), opentelemetry.py:45,
  subagent_engine.py:554.

Mandatory rules:
1. saga.py:28 has ALREADY BEEN DECIDED (see "Decisao Registrada" section above): never
   silence it - log the real exception with stack trace and mark the process as "needs
   human attention". Implement exactly that.
2. For G_COMPONENTE_AGNOSTICO, changing from "pass by default" to "fail on parsing error"
   changes the gate's observable behavior - write a real test forcing that scenario before
   considering it done.
3. Strictly follow the Definition of Done above.
4. Do not fabricate approvals. Only mark this done after running the real tests and
   re-confirming the report's counts.
5. Maintain monorepo governance rules (AGENTS.md).
```
