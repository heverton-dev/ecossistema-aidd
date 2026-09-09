# Item 1 — Trocar except Exception generico por excecoes especificas nas 5 ferramentas

> **Escopo:** Entra: analisar, ferramenta por ferramenta, os pontos onde `except Exception` (genérico demais) é usado para capturar um erro que na prática só pode ser de um tipo específico (ex.: `json.JSONDecodeError`, `FileNotFoundError`, `subprocess.CalledProcessError`), e trocar pelo tipo real — caso a caso, não substituição mecânica em massa. Não entra: resolver as ~288 ocorrências (197 enterprise + 196 master + 65 generator + 19 ops + 7 forge) numa única execução — o volume é grande demais pra uma passada só seguir com segurança; este item define a priorização e cobre a primeira fatia (arquivos de segurança/gates), deixando o resto registrado para fatias seguintes. Não entra mudar o comportamento observável em caso de erro (a exceção específica deve continuar sendo tratada do mesmo jeito, só deixando de mascarar erros que não eram esse).

> **Status:** 🔶 Segunda fatia concluída em 2026-09-08 — aidd-generator, aidd-ops e aidd-forge 100% revisados; aidd-enterprise/aidd-master com core/security.py, core/mcp_server.py, os 9 gates, materializador.py, events.py, subagent_engine.py, database.py (parcial), server.py (parcial) e scripts/aidd.py (parcial) feitos — resto de aidd-enterprise/aidd-master (webhooks.py, token_revocation.py, jobs.py, saga.py, outbox_worker.py, database_adapter.py, opentelemetry.py, result.py — todos já revisados e mantidos amplos por razão real — mais templates/core e templates/v2 nunca tocados) fica para uma fatia seguinte

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

**Pendências explícitas ao fim da primeira fatia** (resolvidas ou revisadas na segunda fatia abaixo, exceto onde indicado):
- Restante de `aidd-enterprise`/`aidd-master` fora do slice original: outros arquivos de `src/core/`, `scripts/` fora de `gates/`, `tests/`, e todo `templates/core/`/`templates/v2/`.
- `aidd-generator` (65 ocorrências), `aidd-ops` (19), `aidd-forge` (7).

## Execução — segunda fatia (2026-09-08, mesmo dia, sessão contínua a pedido do usuário "não pare até terminar")

### aidd-generator — 100% revisado (66 ocorrências reais, incluindo 1 em `utils_modelo.py` não contada no censo original)

Corrigidos com tipo real (verificado lendo o `try`): `05_criador.py` (7: `subprocess.SubprocessError`/`OSError` para git/G_SYNC_HARNESS, `sqlite3.Error` para schema, `OSError` para permissões), `06_documentador.py` (6: `OSError` para leitura HTML/MD, `(OSError, PdfReadError)` para validação de PDF — `PdfReadError` importado com placeholder inerte no topo do arquivo para não quebrar quando pypdf não está instalado, `(AttributeError, ValueError)` para `stdout.reconfigure`, `OSError` para Pandoc ×2), `08_implementador.py` (3 de 6: `subprocess.SubprocessError`/`OSError` para smoke-test e pytest, `ValueError` para parse de JSON — `extrair_json_resposta` só levanta `ValueError`/`json.JSONDecodeError`, ambas subclasses reais), `utils_delegacao.py` (7 de 11: `json.JSONDecodeError`, `ValueError` para pydantic/JSON, `OSError` para watchdog Observer ×2, `SchemaValidationError` para validação de schema, `ImportError` ×2 para detecção de modelo/harness), `utils_modelo.py` (1: `(OSError, json.JSONDecodeError)`), `web/config_manager.py` (3 de 4: `OSError` ×2, `(ImportError, OSError)` para dotenv), `web/app.py` (4: `OSError` ×2 para abrir pasta/Explorer, `(ValueError, TypeError, KeyError)` para status de projeto, `(OSError, json.JSONDecodeError)` para plano), `web/status_parser.py` (1: `(OSError, json.JSONDecodeError)`), `web/pipeline_runner.py` (2: `(OSError, subprocess.SubprocessError)`, `OSError`), `web_app.py` (1: `webbrowser.Error`), `scripts/core/repomix_runner.py` (4: `(AttributeError, ValueError)`, `OSError` ×2, `(subprocess.SubprocessError, OSError)`), `scripts/core/injector/injetor.py` (4: mesmo padrão de `sincronizar_componente` do aidd-forge — `(OSError, subprocess.SubprocessError)` e `(ImportError, OSError, json.JSONDecodeError, KeyError)` —, `OSError` ×2 para escrita canônica), `scripts/gates/AUDITAR_COMPARATIVO_HARNESS.py` (2: `(subprocess.SubprocessError, OSError)`, `OSError`), `01_pesquisador.py` (2 de 3: `(OSError, KeyError)` para GitHub e `OSError` para HuggingFace — **achado real de teste**: os testes simulam falha de rede com `ConnectionError` *builtin*, não `requests.exceptions.ConnectionError`; como só `OSError` é ancestral comum dos dois, usar `requests.exceptions.RequestException` sozinho quebrava 2 testes — corrigido para `OSError`, que cobre ambos), `03_designer.py` (2: `ValueError` para parse de JSON, `(RuntimeError, concurrent.futures.TimeoutError)` para resultado de subagente), `02_analisador.py` (1: `(KeyError, ValueError, TypeError)`).

Revisados e **mantidos amplos** (razão real documentada, não indecisão): `scripts/core/injector/materializador.py` (1, já tinha `# noqa: BLE001` do autor original — staging/rollback de I/O), `08_implementador.py` (3 de 6: `Result.map`/`flat_map` — monad que precisa capturar qualquer exceção de função arbitrária do chamador —, e a chamada a `solicitar_llm`), `utils_delegacao.py` (4 de 11: fallback do `instructor`, carregamento do `tiktoken` — docstring do autor já diz "qualquer falha... vira retorno None permanente" —, fallback para Modo Headless, e a chamada direta a `litellm.completion` — próxima linha já chama `_traduzir_erro_litellm(e, modelo)`, cuja função é interpretar qualquer tipo de exceção), `utils_subagente_ephemero.py` (3: callback de validador arbitrário, chamada a `solicitar_llm`, dispatcher de thread pool), `01_pesquisador.py` (1 de 3: dispatcher de thread pool, todos os 3 workers comprovadamente não levantam mais nada), `web/config_manager.py` (1 de 4: chamada direta a `litellm.completion` para validar API key), `pipeline_prefect.py` (1: fallback de import do Prefect, autor já tipou a variável como `Exception` genérica de propósito), `scripts/verificar_gates.py` (1: dispatcher genérico de gates arbitrários).

Testes: `pytest tools/aidd-generator/tests/` → 863/863 passando antes e depois de cada arquivo.

### aidd-ops — 100% revisado (19 ocorrências)

Corrigidos: `src/core/preflight.py` (4, todas `OSError` — DNS/SSL/HTTP via `socket`/`ssl`/`urllib`, todas subclasses reais de `OSError`, confirmado empiricamente), `src/core/coolify.py` (2: `urllib.error.URLError`, `json.JSONDecodeError`), `src/core/uptime_kuma.py` (2 de 3: `OSError` para gravação de export, `urllib.error.URLError` para dashboard — 1 deixado sem tipo real alcançável, ver abaixo), `scripts/pipeline_ops_deploy.py` (2: `(OSError, json.JSONDecodeError)`, `(ValueError, OSError, subprocess.SubprocessError)`), `mcps/docker-mcp/server.py` (1: `(OSError, subprocess.SubprocessError)` — corrigido também em `componentes/aidd-ops/mcps/docker-mcp/server.py`, cópia que os testes realmente carregam via `REPO_ROOT`), `mcps/cloudflare-mcp/server.py` (1: `json.JSONDecodeError`, mesma duplicação corrigida em `componentes/`).

Mantidos amplos (revisados): `src/core/result.py` (3: monad Result, mesmo padrão do aidd-generator/aidd-forge), `src/core/ssh_runner.py` (2 — **achado real de teste**: os testes fazem `@patch("...ssh_runner.paramiko")` substituindo o módulo inteiro por `MagicMock`; referenciar `paramiko.SSHException` no `except` quebra com `TypeError: catching classes that do not inherit from BaseException` porque `paramiko` deixa de ser o módulo real — revertido para `except Exception`, comentário explicando o motivo adicionado no código), `src/core/uptime_kuma.py` (1: bloco de parsing de porta em docker-compose.yml onde nenhuma linha do `try` pode realisticamente levantar — sem tipo real, não inventado), `scripts/pipeline_ops.py` (1: fronteira de comando CLI Click, `[ERRO INESPERADO]`, deve sempre reportar e sair com código, nunca travar).

Testes: `pytest tools/aidd-ops/tests/` → 144/144 passando antes e depois.

### aidd-forge — 100% revisado (7 ocorrências)

Corrigidos: `aidd_forge/core/injector_profiles.py` (2: mesmo padrão `sincronizar_componente` de aidd-generator), `aidd_forge/core/materializador.py` (3: `OSError` ×3), `aidd_forge/core/universal_injector.py` (1: `(ConteudoStubError, DestinoExistenteError, MaterializacaoError)` — as 3 exceções reais que `Materializador.materializar()` pode levantar, importadas explicitamente no topo do arquivo).

Mantido amplo: `aidd_forge/core/subagent_purger.py` (1, já tinha `# noqa: BLE001` do autor original).

Testes: `pytest tools/aidd-forge/` → 197/197 passando (1 skip, igual ao baseline) antes e depois.

### aidd-enterprise / aidd-master — arquivos adicionais de `src/core/` e `scripts/`

Corrigidos em ambas as ferramentas (arquivos idênticos entre si, confirmado por diff antes de copiar): `src/core/materializador.py` (7 de 8: mesmo padrão `sincronizar_componente`, mais rollback de I/O em `OSError`, mais leitura/escrita de `mcp.json` em `(OSError, json.JSONDecodeError)`), `src/core/events.py` (3 de 5: `redis.exceptions.ResponseError` para `xgroup_create` — precisou de `import redis` local dentro do método, já que o `import redis` do `__init__` não persiste como nome no módulo —, `(json.JSONDecodeError, KeyError, redis.exceptions.RedisError)` e `redis.exceptions.RedisError` no loop de consumo), `src/core/subagent_engine.py` (3: `OSError` para o bloco de scaffold de arquivos, `(OSError, subprocess.SubprocessError)` para execução do subagente, `(OSError, json.JSONDecodeError)` para leitura do manifesto de resultado), `src/core/database.py` (1 de 2: `sqlglot.errors.SqlglotError` para parse de SQL).

Corrigidos independentemente em cada ferramenta (arquivos com divergência documentada pelo gate de drift, não copiados um do outro): `src/server.py` (1 de 4 em cada: `ValueError` para parse do corpo da requisição POST), `scripts/aidd.py` (2 de 5 em cada: `(subprocess.CalledProcessError, OSError)` para auto-instalação de dependências, `ImportError` para Fleet Discovery).

Revisados e mantidos amplos (razão real): `src/core/webhooks.py` (5), `src/core/token_revocation.py` (4), `src/core/jobs.py` (3), `src/core/opentelemetry.py` (3), `src/core/saga.py` (2), `src/core/outbox_worker.py` (2), `src/core/database_adapter.py` (2), `src/core/database.py` (1 de 2), `src/core/result.py` (3), `src/server.py` (3 de 4: dispatcher de rota HTTP ×2, fluxo OIDC multi-etapa com PyJWT opcional), `scripts/aidd.py` (3 de 5: fronteira de comando CLI ×2, dispatcher de worker de benchmark) — a maioria desses usa a fachada `core/database.py` (`Database`), que suporta SQLite **e** PostgreSQL (via `psycopg2`, de fato instalado neste ambiente) sem normalizar as exceções nativas de cada driver; fixar um tipo aqui exigiria import condicional de `psycopg2` replicado em dezenas de arquivos com risco real de quebrar instalações só-SQLite se malfeito — deixado para uma fatia dedicada a essa decisão de arquitetura, não decidido por este item.

Testes: `pytest tools/aidd-enterprise/tests/` → 259/259 (4 skips) e `pytest tools/aidd-master/tests/` → 285/285 (4 skips), idênticos ao baseline em cada arquivo alterado. `python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py` → 100% OK após cada mudança copiada entre as ferramentas.

**Pendências explícitas para a próxima fatia:**
- `aidd-enterprise`/`aidd-master`: `templates/core/` e `templates/v2/` (13 arquivos cada, nunca tocados — não exigidos por nenhum gate de drift, mas têm o mesmo bug real), `src/modules/`, `tests/` (poucas ocorrências, não auditadas), e uma decisão de arquitetura sobre como tratar exceções de `core/database.py` multi-backend (SQLite/Postgres) de forma específica sem risco de quebrar instalações só-SQLite.
- Todas as 5 ferramentas: nenhuma ocorrência restante é "não revisada" — toda ocorrência que ainda diz `except Exception` neste ponto foi lida e mantida deliberadamente ampla, com razão registrada acima.

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
