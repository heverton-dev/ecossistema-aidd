# Item 1 — Trocar except Exception generico por excecoes especificas nas 5 ferramentas

> **Escopo:** Entra: analisar, ferramenta por ferramenta, os pontos onde `except Exception` (genérico demais) é usado para capturar um erro que na prática só pode ser de um tipo específico (ex.: `json.JSONDecodeError`, `FileNotFoundError`, `subprocess.CalledProcessError`), e trocar pelo tipo real — caso a caso, não substituição mecânica em massa. Não entra: resolver as ~288 ocorrências (197 enterprise + 196 master + 65 generator + 19 ops + 7 forge) numa única execução — o volume é grande demais pra uma passada só seguir com segurança; este item define a priorização e cobre a primeira fatia (arquivos de segurança/gates), deixando o resto registrado para fatias seguintes. Não entra mudar o comportamento observável em caso de erro (a exceção específica deve continuar sendo tratada do mesmo jeito, só deixando de mascarar erros que não eram esse).

> **Status:** ⏳ Rascunho gerado, aguardando aprovação

---

## Contexto já investigado

- Contagem real (`grep` por `^\s*except\s+Exception\b`, 2026-09-08, excluindo pastas de exemplo/gerado e skills materializadas): aidd-enterprise = 198, aidd-master = 196, aidd-generator = 65, aidd-ops = 19, aidd-forge = 7.
- Risco de fazer isso errado: capturar `Exception` genérico às vezes é intencional (ex.: um laço que não pode parar por um item ruim, ou um ponto de entrada de CLI que precisa sempre retornar um código de saída). Trocar sem entender o que o bloco `try` realmente faz por dentro pode fazer o programa quebrar em vez de logar e continuar — por isso este item não é mecânico, precisa de leitura caso a caso.
- Priorização sugerida (não é decisão fabricada, é proposta pro humano aprovar): começar pelos arquivos que o próprio grafo marca como `security_relevant=1` em `risk_index` (ex.: `core/security.py`, `core/mcp_server.py`, os arquivos `G_*.py` de gates) — são os que mais importam se um erro real for mascarado.

## Definição de Pronto

1. Inventário produzido (arquivo + linha + o que o `try` faz) para os arquivos de maior prioridade (gates de segurança e `core/security.py`/`core/mcp_server.py` nas 5 ferramentas) antes de qualquer troca.
2. Para cada ocorrência trocada, o tipo de exceção substituído é o que realmente pode ocorrer ali (verificado lendo o código dentro do `try`, não suposição).
3. Comportamento observável (mensagem de log, código de saída, resultado do gate) idêntico ao anterior para os casos de erro que o tipo específico ainda cobre — reproduzido rodando o gate/teste antes e depois.
4. Ocorrências não cobertas nesta primeira fatia listadas explicitamente neste documento como pendência, não escondidas.

## Execução — primeira fatia (2026-09-08)

Escopo: `core/security.py`, `core/mcp_server.py` e os 9 arquivos `G_*.py` de gates de `aidd-enterprise` e `aidd-master` (`scripts/gates/`), mais os 4 arquivos de `templates/gates/` cuja paridade com `scripts/gates/` é exigida por `G_DRIFT_NUCLEO_COMPARTILHADO.py`, mais `templates/gates/G_QUALIDADE.py` e `G_SEGURANCA.py` (versões reduzidas, sem paridade obrigatória, mas com o mesmo bug real). Cada tipo de exceção foi escolhido lendo o corpo do `try` (import dinâmico → `ImportError`; leitura de arquivo → `OSError`; parse de JSON → `json.JSONDecodeError`; parse de AST → `SyntaxError`; SQL via `sqlite3` → `sqlite3.Error`; `subprocess` com `check=True` → `subprocess.CalledProcessError`), nunca por suposição.

**Corrigido e verificado por reprodução real** (testes existentes antes/depois idênticos + reprodução manual dos caminhos de erro sem teste dedicado; `pytest tools/aidd-enterprise/tests/` → 259/259 passando, `pytest tools/aidd-master/tests/` → 285/285 passando; `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` → 100% OK; `python scripts/gates/G_SEGURANCA.py` rodado de fim a fim nas duas ferramentas, mesmo score 88.9% A+ nas duas):
- `src/core/security.py` (2 ocorrências, ambas as ferramentas): `ValueError` (cobre `json.JSONDecodeError`/`UnicodeDecodeError`/erro de `split()`, todos subclasses reais de `ValueError`).
- `src/core/mcp_server.py` (5 de 8, ambas as ferramentas): os 5 handlers CRUD genéricos (`_generic_listar/obter/criar/atualizar/deletar`) → `sqlite3.Error`. Os outros 3 (`execute_tool`, `handle_json_rpc`, `run_stdio_server`) foram revisados e **mantidos propositalmente amplos** — são fronteiras de despacho (plugin arbitrário / loop de servidor STDIO) que precisam sobreviver a qualquer erro do handler chamado, exatamente o caso que a Definição de Pronto do item avisa para não mexer.
- `scripts/gates/G_ARQUITETURA.py` (1): `OSError`.
- `scripts/gates/G_CHAOS.py` (1): `urllib.error.URLError`.
- `scripts/gates/G_HARNESS_COMPAT.py` (1): `json.JSONDecodeError`.
- `scripts/gates/G_INJECT.py` (2, só aidd-enterprise — aidd-master já não tinha `except Exception` neste arquivo): `(ImportError, AttributeError)` e `json.JSONDecodeError`.
- `scripts/gates/G_ESTRUTURA.py` (2): `(json.JSONDecodeError, TypeError)` e `(SyntaxError, OSError)`.
- `scripts/gates/G_CONTRACTS.py` (4): `(ImportError, OSError)`, `OSError`, `(OSError, NameError)` (o `NameError` cobre um acoplamento real e pré-existente entre a seção 1 e a seção 3 da função — se o import da seção 1 falha, `modules_dir`/`modulos` nunca são definidos e a seção 3 já dependia disso ser engolido hoje; comportamento preservado, não corrigido — fora de escopo deste item), `OSError`.
- `scripts/gates/G_PERFORMANCE.py` (3): `(ImportError, OSError)` × 2, `(AttributeError, OSError)`.
- `scripts/gates/G_QUALIDADE.py` (2 de 4): `(SyntaxError, OSError)` e `(OSError, subprocess.SubprocessError)`. Os outros 2 (linhas do fuzzing contínuo, que chamam `executar_fuzzing_continuo`) foram revisados e **mantidos amplos** — a função chamada já engole toda exceção internamente e retorna dict, então não há um tipo real e alcançável para restringir sem supor.
- `scripts/gates/G_SEGURANCA.py` (6): `ImportError` × 3 (camadas 1, 2, 7), `(ImportError, sqlite3.Error, OSError)` (camada 6), `(subprocess.CalledProcessError, OSError)` e `OSError` (camada 8).
- `templates/gates/G_CHAOS.py`, `G_CONTRACTS.py`, `G_ESTRUTURA.py`, `G_HARNESS_COMPAT.py`: espelhados byte-a-byte a partir da versão já corrigida de `scripts/gates/` (eram idênticos antes da mudança; `G_DRIFT_NUCLEO_COMPARTILHADO.py` exige essa paridade).
- `templates/gates/G_QUALIDADE.py` (1) e `G_SEGURANCA.py` (4): revisados de forma independente (arquivos menores, sem a Camada 8 e sem fuzzing/mutmut) e corrigidos com os mesmos tipos das seções equivalentes em `scripts/gates/`.

**Pendências explícitas** (não escondidas, ficam para a próxima fatia):
- Restante de `aidd-enterprise`/`aidd-master` fora deste slice: outros arquivos de `src/core/` (ex.: `database.py`, `openapi.py`, `webhooks.py`, `fuzzing.py` — este último com 2 `except Exception` genuinamente intencionais, mesma razão do mcp_server), `src/modules/`, `scripts/` fora de `gates/`, `tests/`, e todo `templates/core/` e `templates/v2/` (13 arquivos cada, nunca tocados nesta fatia — não exigidos pelo gate de drift, mas ainda têm o mesmo bug real).
- `aidd-generator` (65 ocorrências), `aidd-ops` (19), `aidd-forge` (7) — nenhuma tocada ainda.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Trocar except Exception generico por excecoes especificas nas 5 ferramentas.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Trocar except Exception generico por excecoes especificas nas 5 ferramentas.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
