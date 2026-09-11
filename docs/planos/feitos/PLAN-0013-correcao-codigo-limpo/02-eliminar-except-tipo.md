# Item 2 — Eliminar except sem tipo (bare except) em aidd-enterprise, aidd-master e aidd-generator

> **Escopo:** Entra: trocar cada `except:` sem tipo (que captura literalmente tudo, inclusive `KeyboardInterrupt`/`SystemExit`) pelo tipo específico de erro esperado naquele ponto, nos arquivos listados abaixo. Não entra: aidd-forge e aidd-ops (0 ocorrências confirmadas — não precisam de mudança).

> **Status:** ✅ Concluído (auditado por reprodução real em 2026-09-08)

---

## Contexto já investigado

- Confirmado por varredura real (`grep`, 2026-09-08), 15 ocorrências em `aidd-enterprise` e 15 idênticas em `aidd-master` (mesmos arquivos/linhas, porque são cópias — ver iniciativa `correcao-arquitetura-limpa`):
  - `scripts/gates/G_SEGREDOS.py:53`
  - `src/core/fuzzing.py:221` e `:228`
  - `src/core/webhooks.py:81`
  - `templates/core/server.py:843`, `:977`, `:1014`, `:1041` (4 ocorrências só neste arquivo)
  - (mais 6 ocorrências não listadas em detalhe aqui — usar o mesmo comando de varredura para gerar a lista completa antes de começar)
- 7 ocorrências reais em `aidd-generator` (não são duplicata de skill materializada, são 7 pontos distintos do pipeline):
  - `scripts/phases/01_pesquisador.py:199`, `:407`, `:437`, `:464`, `:633` (5 ocorrências só neste arquivo)
  - `scripts/phases/02_analisador.py:148`
  - `scripts/phases/05_criador.py:292`
- `aidd-forge` e `aidd-ops`: 0 ocorrências confirmadas — nada a fazer nessas duas.

## Definição de Pronto

1. Lista completa e atualizada (`grep` rodado de novo no momento da execução, não confiar só nesta lista congelada) de todas as ocorrências nos 2 grupos de arquivos acima.
2. Cada `except:` substituído por um tipo específico, verificado lendo o que o bloco `try` faz (não suposição).
3. `scripts/gates/G_SEGREDOS.py` e `src/core/webhooks.py` (arquivos de segurança) tratados com prioridade e revisados com atenção redobrada, por serem `security_relevant` no `risk_index`.
4. `enterprise` e `master` corrigidos de forma equivalente (mesma mudança nos dois), para não quebrar o gate de drift que espera essas cópias idênticas.
5. Testes existentes cobrindo os arquivos alterados executados com exit 0 após a mudança.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Execução (2026-09-08)

Tipo de exceção definido caso a caso, lendo o corpo real de cada `try`, não suposição:

| Arquivo | Linha(s) | Tipo aplicado | Motivo |
|---|---|---|---|
| `scripts/gates/G_SEGREDOS.py` + `templates/gates/G_SEGREDOS.py` (enterprise+master, 4 cópias) | 53 | `OSError` | abre/lê arquivo do repo |
| `src/core/fuzzing.py` (enterprise+master) | 221, 228 | `json.JSONDecodeError` | parse de resposta HTTP fuzzed |
| `src/core/webhooks.py` + `templates/core` + `templates/v2` (enterprise+master, 6 cópias) | 81 | `(json.JSONDecodeError, AttributeError)` | parse de campo `eventos` que pode não ser JSON válido nem string |
| `templates/core/server.py` + `templates/v2/server.py` (enterprise+master, 4 cópias) | 843 | `json.JSONDecodeError` | parse de `payload_json` |
| idem | 977, 1014, 1041 | `(json.JSONDecodeError, UnicodeDecodeError)` | decode + parse do corpo da requisição HTTP |
| `aidd-generator/scripts/phases/01_pesquisador.py` | 199, 437 | `ValueError` | `datetime.fromisoformat` em data mal formada |
| idem | 407, 633 | `requests.exceptions.RequestException` | chamada de rede (`requests.head`) |
| idem | 464 | `TypeError` | `json.dumps` de objeto não serializável |
| `aidd-generator/scripts/phases/02_analisador.py` | 148 | `TypeError` | `in` sobre valor potencialmente não-dict |
| `aidd-generator/scripts/phases/05_criador.py` | 292 | `(UnicodeDecodeError, OSError)` | leitura de arquivo possivelmente binário |

- Reprodução real: `py_compile` em todos os arquivos tocados (sem erro de sintaxe); `pytest` nos testes existentes que cobrem os arquivos — `test_fuzzing.py` (enterprise e master, 21/21 cada), `test_add_module_server_wiring.py` (enterprise e master, 2/2 cada), `test_phase_01.py` + `test_phase_02.py` + `test_phase_05.py` (74/74) — todos passando sem regressão.
- `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` aprovado (100% OK) após as mudanças em enterprise/master.
- `aidd-forge` e `aidd-ops` confirmados sem ocorrências — nada alterado neles, como previsto.
- Fora de escopo (registrado, não corrigido): 1 ocorrência adicional em `aidd-generator/skills/project-spec-tracker/script.py:296` — é uma das 9 cópias materializadas do mesmo skill entre harnesses, cuja duplicação é tratada pela iniciativa `correcao-arquitetura-limpa` (itens 3/4), não por este item.
- **Veredito: Concluído.**

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 2: Eliminar except sem tipo (bare except) em aidd-enterprise, aidd-master e aidd-generator.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: Eliminar except sem tipo (bare except) em aidd-enterprise, aidd-master e aidd-generator.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
