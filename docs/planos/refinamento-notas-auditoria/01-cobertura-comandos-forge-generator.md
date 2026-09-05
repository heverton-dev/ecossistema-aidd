# Item 1 — Cobertura de Comandos: aidd-forge e aidd-generator

> **Status:** ✅ CONCLUÍDO em 05/09/2026 — nota final 10/10 (ver Veredito ao final do documento).
> **Origem:** pergunta do usuário — "podemos superar o 10, sem fabricação?" — aplicada à dimensão Testabilidade/Cobertura Real (hoje 9/10).
> **Contribui para:** Testabilidade/Cobertura Real.

---

## As 4 perguntas de rigor, respondidas antes de propor qualquer trabalho

1. **É necessário?** — Parcialmente. Investiguei os dois tools e o achado real é bem mais estreito do que eu supunha inicialmente (ver abaixo).
2. **É possível?** — Sim, onde necessário: é o mesmo padrão mecânico já usado 2x nos Pacotes 2 e 4 da rodada 1 (subprocess/chamada direta, sucesso + falha, exit code real).
3. **É real?** — Sim: reproduzi a busca por testes eu mesmo, não assumi.
4. **Traz ganho real?** — Sim, no escopo estreito identificado — fecha exatamente o tipo de ponto cego que já causou um bug real (`add_module.py`) na rodada 1.

---

## Diagnóstico

### `aidd-forge` — achado: NÃO há gap real. Já está bem coberto.

`aidd-forge` só tem 2 subcomandos reais: `init` e `inject` (`aidd_forge/cli.py`). Investiguei os testes existentes e encontrei cobertura já sólida:
- `tests/unit/test_cli.py`: `init` testado com sucesso (exit 0, arquivos de governança criados), idempotência sem `--force`, e `inject` testado com sucesso, com `--conteudo-file`, **e com falha real (`exit_code == 1`)** quando o payload é inválido.
- `tests/integration/test_full_forge_pipeline.py`: cobertura ainda mais profunda — `init` provisiona a árvore inteira de governança, instala os 7 gates + hook de pre-commit, e **um projeto recém-bootstrapado passa em todos os gates de verdade** (`test_freshly_bootstrapped_project_passes_every_gate`). Tem até teste de falha real via git hook: **um commit com segredo é bloqueado de verdade** (`test_pre_commit_hook_blocks_a_real_commit_with_a_secret`), assim como um commit com erro de sintaxe.

**Conclusão:** não há ação a tomar aqui. Registrado como "já verificado, sem gap" — não vou inventar trabalho onde a auditoria não encontrou nada real.

### `aidd-generator` — achado real: `pipeline_completo.py`'s `main()` nunca foi testado como CLI

`aidd-generator` tem 4 pontos de entrada de CLI reais: `aidd_inject.py`, `pipeline_completo.py`, `preflight_llm.py`, `verificar_gates.py`.
- `aidd_inject.py`: já coberto extensivamente (`tests/test_aidd_inject_cli.py`, confirmado durante a auditoria do Pacote 5 da rodada 1).
- `preflight_llm.py`: coberto (`tests/test_preflight_llm.py`).
- `verificar_gates.py`: coberto (`tests/test_verificar_gates.py`).
- **`pipeline_completo.py`: `main()` — o comando principal do produto (`python scripts/pipeline_completo.py "<ideia>" --pasta <destino>`) — NUNCA é chamado como CLI em nenhum teste.** `tests/unit/test_phase_isolation.py` carrega o módulo via `importlib` só para testar funções internas isoladas, nunca invoca `main()` com argv real. Confirmei via grep: nenhum teste referencia `pipeline_completo` além desse carregamento de módulo.

Lendo o código de `main()` (linhas 296-352): tem lógica de exit code real e testável sem precisar rodar o pipeline de 8 fases de verdade (que já tem cobertura extensa via os testes de cada fase individualmente, 756+ testes):
1. Preflight de LLM (`verificar_llm_pronto()`) — se falhar, `sys.exit(1)` com mensagem específica.
2. `LLMNaoConfiguradoException` capturada explicitamente — `sys.exit(1)` com mensagem amigável.
3. Sucesso (`resultado['status'] == 'COMPLETO'`) → `sys.exit(0)`; falha de fase → `sys.exit(1)`.

**O que falta testar de verdade:** que o argparse aceita/rejeita os argumentos certos (`ideia` obrigatório, `--pasta` obrigatório, `--interativo`, `--implementar-codigo`), que o preflight bloqueia antes de gastar tempo/tokens quando LLM não está configurado, e que os 2 exit codes (0 sucesso / 1 falha) realmente saem certos — tudo isso **mockando só `executar_pipeline`** (a chamada cara, já testada em outro lugar), não escondendo o resto atrás de mock.

---

## Definição de Pronto

**Fase 1 — Testar `pipeline_completo.py`'s `main()` como CLI de verdade**
1.1. Teste real: rodar `main()`/`python scripts/pipeline_completo.py` sem `--pasta` (obrigatório) e confirmar que o argparse recusa com exit code de erro padrão do argparse (não 0), sem precisar mockar nada.
1.2. Teste real: mockar só `verificar_llm_pronto()` para retornar `(False, "motivo")`, confirmar que `main()` sai com `sys.exit(1)` e imprime a mensagem de preflight, **sem nunca chamar `executar_pipeline`** (confirmar isso explicitamente com um mock que levanta exceção se for chamado).
1.3. Teste real: mockar `executar_pipeline` para levantar `LLMNaoConfiguradoException`, confirmar `sys.exit(1)` com a mensagem amigável exibida (não o stack trace cru).
1.4. Teste real: mockar `executar_pipeline` para retornar `{'status': 'COMPLETO', 'score_final': 100, ...campos mínimos necessários...}`, confirmar `sys.exit(0)` e que a mensagem de sucesso é impressa com o score.
1.5. Teste real: mockar `executar_pipeline` para retornar `{'status': 'FALHOU', 'fase_que_falhou': 'phase_02', ...}`, confirmar `sys.exit(1)` e a mensagem de falha citando a fase certa.

**Critério de saída (rodar e colar o output real de cada um):**
- Suíte completa de `aidd-generator` (`python -m pytest tests/ -q`) → sem regressão, com os 5 testes novos incluídos.
- Nenhum teste novo chama `executar_pipeline` de verdade (todos mockam só essa função — confirmar isso é o que preserva "não gastar tempo/tokens reais" e "não é fabricação", já que o comportamento *interno* das 8 fases já tem prova própria em outro lugar).
- Confirme por comando (`git status`) que nenhum teste novo deixou arquivo fora de `tmp_path`/diretório de teste temporário.

---

## Ordem de execução

Item único, 1 fase, cabe em 1 prompt.

**Aprovado pelo usuário em 05/09/2026.** Prompt de execução abaixo.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai fechar um gap real de cobertura de teste no aidd-generator
(monorepo em C:\Users\trcnologia\Desktop\ecossistema-aidd, ferramenta em
tools/aidd-generator) — o comando principal do produto,
`python scripts/pipeline_completo.py "<ideia>" --pasta <destino>`, nunca
foi testado como CLI de verdade (argparse, preflight, exit codes). Só as
funções internas das fases isoladas já são testadas (700+ testes). Siga
EXATAMENTE a Definição de Pronto abaixo, não invente escopo adicional, e
valide tudo de verdade (execuções reais, exit codes reais, nunca
mascarados por pipe).

IMPORTANTE — o que este prompt NÃO pede: não rode o pipeline de 8 fases
de verdade (isso chama um LLM real, é caro e lento, e já tem cobertura
própria extensa). O objetivo é testar a CASCA da CLI — argparse,
preflight, exit codes, tratamento de exceção — mockando só a função
`executar_pipeline` (a chamada cara), nunca mais que isso.

CONTEXTO JÁ INVESTIGADO (não precisa redescobrir, mas confirme lendo o
código antes de escrever cada teste):
- `tools/aidd-generator/scripts/pipeline_completo.py`'s `main()` (por
  volta da linha 296): monta um `argparse.ArgumentParser` com `ideia`
  (posicional, obrigatório), `--pasta` (obrigatório), `--interativo` e
  `--implementar-codigo` (flags booleanas). Chama
  `verificar_llm_pronto()` (importado de `preflight_llm.py`) ANTES de
  qualquer coisa cara — se falhar, `sys.exit(1)` com uma mensagem
  específica, sem nunca chamar `executar_pipeline`. Se o preflight
  passar, chama `executar_pipeline(args.ideia, Path(args.pasta),
  nao_interativo=not args.interativo, implementar_codigo=args.implementar_codigo)`
  dentro de um `try`/`except LLMNaoConfiguradoException` — se essa
  exceção for levantada, `sys.exit(1)` com a mensagem amigável (nunca o
  stack trace cru). Se `executar_pipeline` retornar
  `resultado['status'] == 'COMPLETO'`, imprime o score final e
  `sys.exit(0)`; caso contrário, imprime `resultado['fase_que_falhou']`
  e `sys.exit(1)`.
- `tests/unit/test_phase_isolation.py` (mesmo diretório de testes) já
  tem uma fixture `pipeline_mod` que carrega `pipeline_completo.py` via
  `importlib.util.spec_from_file_location` — reaproveite exatamente esse
  padrão de carregamento (ou crie uma fixture equivalente no arquivo
  novo), não invente outra forma de importar o módulo.
- Nenhum teste hoje chama `main()` com argv real — confirmado via grep
  (nenhuma ocorrência de `pipeline_completo` fora desse carregamento de
  módulo para testar funções internas).

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. Nunca chame `executar_pipeline` de verdade em nenhum teste novo — ela
   dispara um pipeline real de LLM. Mock sempre, via
   `monkeypatch.setattr(pipeline_mod, 'executar_pipeline', fake_fn)` (ou
   equivalente).
2. `verificar_llm_pronto` também deve ser mockada quando o teste precisa
   controlar o resultado do preflight (para os casos de falha) — mas
   pelo menos 1 teste deve confirmar que, quando o preflight mockado
   falha, `executar_pipeline` NUNCA é chamada (use um mock que levanta
   `AssertionError`/`Exception` se for invocado, para provar isso, não
   só assumir).
3. Testes de sucesso e falha usam `resultado` (dict) mínimo mas
   realista — não precisa reproduzir todas as chaves de
   `executar_pipeline` de verdade, só as que `main()` realmente lê
   (`status`, `score_final`, `fleet`, `context_purge`, `duracao_segundos`,
   `fase_que_falhou`).

DEFINIÇÃO DE PRONTO — nesta ordem:

FASE 1 — Testar `pipeline_completo.py`'s `main()` como CLI de verdade
1.1. Teste real: chame `main()` (via `sys.argv` mockado com
     `monkeypatch.setattr(sys, 'argv', [...])`, sem `--pasta`) e confirme
     que o argparse recusa (levanta `SystemExit` com código != 0,
     comportamento padrão do argparse para argumento obrigatório
     ausente) — sem precisar mockar mais nada.
1.2. Teste real: mock `verificar_llm_pronto` para retornar
     `(False, "motivo de teste")`; mock `executar_pipeline` com uma
     função que levanta exceção se for chamada (prova que não é
     invocada). Rode `main()` com argv válido, confirme `SystemExit`
     com código 1 e a mensagem de preflight na saída capturada
     (`capsys`).
1.3. Teste real: mock `verificar_llm_pronto` para retornar
     `(True, "ok")`; mock `executar_pipeline` para levantar
     `LLMNaoConfiguradoException("mensagem amigável de teste", "detalhe tecnico")`.
     Confirme `SystemExit` código 1 e que a saída mostra a mensagem
     amigável, não um stack trace.
1.4. Teste real: mock `executar_pipeline` para retornar
     `{'status': 'COMPLETO', 'score_final': 92, 'fleet': {'modo': 'x', 'total_detectados': 1},
     'context_purge': {}, 'duracao_segundos': 1.0}`. Confirme
     `SystemExit` código 0 e que a saída mostra o score (92).
1.5. Teste real: mock `executar_pipeline` para retornar
     `{'status': 'FALHOU', 'fase_que_falhou': 'phase_02_analysis',
     'fleet': {}, 'context_purge': {}, 'duracao_segundos': 1.0}`.
     Confirme `SystemExit` código 1 e que a saída cita
     "phase_02_analysis".

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- Suíte completa de `aidd-generator` (`python -m pytest tests/ -q`) →
  sem regressão, com os 5 testes novos incluídos na contagem.
- Confirme explicitamente (no output do teste 1.2) que
  `executar_pipeline` nunca foi chamada quando o preflight falha.
- Confirme por comando (`git status`) que nenhum teste novo deixou
  arquivo fora de `tmp_path`/diretório de teste temporário, e que
  nenhuma chamada real de LLM foi feita durante os testes (sem
  `.aidd/cache/_llm_request_*.json` novo no repositório).

REGRAS DE ESCOPO — NÃO FAÇA:
- Não rode `executar_pipeline` de verdade em nenhum teste — é sempre
  mockada.
- Não toque em `aidd-forge` — a auditoria já confirmou que os comandos
  `init`/`inject` dessa ferramenta já têm cobertura sólida (sucesso e
  falha real, inclusive via git hook), não há trabalho a fazer lá.
- Não toque em `aidd_inject.py`, `preflight_llm.py` nem
  `verificar_gates.py` do aidd-generator — já cobertos, fora de escopo
  deste item.
- Não faça `git commit` nem `git push`.
- Não altere
  `docs/planos/refinamento-notas-auditoria/01-cobertura-comandos-forge-generator.md`.

ENTREGÁVEL: lista exata de arquivos criados/alterados; comando + output
real que comprova cada um dos 5 testes; qualquer desvio necessário,
reportado explicitamente em vez de decidido sozinho.
```

---

## Veredito — Auditoria

**Auditoria independente realizada — não me baseei no relatório do agente executor.** Entregável real: um único arquivo novo, `tools/aidd-generator/tests/unit/test_pipeline_completo_cli.py` (5 testes), confirmado por `git status` no repo inteiro — nada mais foi tocado (aidd-forge intocado, documento deste item não alterado, sem commit/push feito).

**Suíte completa reproduzida por mim:** `python -m pytest tests/ -q` → **770 passed**, exit code real 0 (765 pré-existentes + 5 novos, sem regressão). Os 5 testes novos isolados (`pytest tests/unit/test_pipeline_completo_cli.py -v`) → 5 passed, exit 0.

**Reproduções independentes fora do arquivo do executor** (não confiei só em rodar o arquivo dele):
- **1.1 (argparse sem `--pasta`):** rodei o CLI real via subprocess, zero mock — `python scripts/pipeline_completo.py "ideia sem pasta"` → argparse recusa com `exit code 2` (padrão do argparse para argumento obrigatório ausente), confirma a asserção `!= 0` sem depender de nenhum teste.
- **1.2 (preflight falho nunca chama `executar_pipeline`):** escrevi do zero um script de auditoria separado (não importei o arquivo de teste do executor), com um "espião" que levanta `RuntimeError` se `executar_pipeline` for chamada. Resultado real: `executar_pipeline foi chamada? False`, `codigo de saida: 1`, mensagem `❌ PREFLIGHT FALHOU — auditoria independente - motivo fake` no stdout — prova concreta e própria de que a garantia de segurança (nunca gastar tempo/tokens de LLM quando o preflight reprova) é real, não apenas afirmada pelo executor.
- **1.3 (`LLMNaoConfiguradoException` sem stack trace):** escrevi um segundo script independente, com um módulo carregado do zero (nova instância, não reaproveitando a do caso 1.2), que levanta `LLMNaoConfiguradoException("mensagem amigavel de auditoria independente", "DETALHE TECNICO SIGILOSO QUE NAO PODE VAZAR")` — texto próprio, nunca usado pelo executor. Resultado real: `exit 1`, a mensagem amigável aparece na saída, e nem `"Traceback"` nem o detalhe técnico sigiloso aparecem — confirma que o comportamento de não vazar stack trace é do produto, não um acaso do teste do executor.
- **1.4 (sucesso):** mesmo script, mockando `executar_pipeline` para devolver um resultado com `score_final: 77` (valor deliberadamente diferente do `92` usado pelo executor, para eliminar qualquer chance de coincidência de string). Resultado real: `exit 0`, saída mostra `PIPELINE COMPLETO — score final: 77/100`.
- **1.5 (falha de fase):** mesmo script, mockando `executar_pipeline` para devolver `fase_que_falhou: 'phase_07_autocritica'` (também deliberadamente diferente do `phase_02_analysis` do executor). Resultado real: `exit 1`, saída mostra `PIPELINE FALHOU na phase_07_autocritica`.

Os 5 casos (1.1 a 1.5) foram, portanto, **todos** reproduzidos por mim do zero, fora do arquivo de teste do executor — 3 deles (1.3/1.4/1.5) usando valores deliberadamente diferentes dos escolhidos pelo executor, o que descarta qualquer hipótese de que os testes originais só "combinam por acaso" com o comportamento real.

**Zero chamada real de LLM confirmada empiricamente (não só por ausência no `git status`):** `scripts/.aidd/cache/` está no `.gitignore` inteiro, então `git status` nunca mostraria arquivo novo lá de qualquer forma. Contornei isso contando os arquivos do diretório antes/depois de rodar SÓ os 5 testes novos, isolados: **126 → 126, delta zero.** (A suíte completa de 770 testes escreve nesse cache como comportamento pré-existente de outros testes, não relacionado a este item — confirmado pelo mesmo delta-zero ao isolar só o arquivo novo.)

**Notável:** fechou de primeira, sem nenhuma correção necessária — mesmo padrão do Pacote 4 (rodada 1).

### Nota Final — Item 1 (Cobertura de Comandos): 10/10

**Por que 10:**
- Todos os critérios de saída definidos na Definição de Pronto foram cumpridos e verificados com reprodução real — os 5 casos (1.1 a 1.5) foram reproduzidos por mim inteiramente do zero, fora do arquivo de teste do executor, 3 deles com valores deliberadamente diferentes dos do executor (score `77` vs `92`, fase `phase_07_autocritica` vs `phase_02_analysis`, mensagens de exceção próprias) para descartar qualquer coincidência de string.
- Escopo 100% respeitado: nenhum arquivo fora do combinado foi tocado, nenhuma chamada real de LLM (confirmado empiricamente, delta zero no cache), nenhuma regressão (770 passed, exit 0 real), nenhum arquivo órfão no repositório em nenhuma das reproduções.
- Fechou de primeira, sem nenhuma correção necessária no código do executor.
- **Efeito na dimensão Testabilidade/Cobertura Real:** o único gap real identificado no diagnóstico (`pipeline_completo.py`'s `main()` nunca testado como CLI) está fechado com evidência genuína e integralmente reproduzida por mim — argparse, preflight, tratamento de exceção e os 2 exit codes finais agora têm teste real, mockando só a chamada cara. Combinado com o achado de que `aidd-forge` já não tinha gap nenhum (verificado no diagnóstico, não neste veredito), a dimensão **sobe de 9 para 10/10**.

## Prompt de Execução — English version

```
You are going to close a real test-coverage gap in aidd-generator
(monorepo at C:\Users\trcnologia\Desktop\ecossistema-aidd, tool at
tools/aidd-generator) — the product's main command,
`python scripts/pipeline_completo.py "<idea>" --pasta <destination>`,
has never been tested as a real CLI (argparse, preflight, exit codes).
Only the isolated internal phase functions are already tested (700+
tests). Follow the Definition of Done below EXACTLY, do not invent
additional scope, and validate everything for real (real runs, real
exit codes, never masked by a pipe).

IMPORTANT — what this prompt does NOT ask for: do not actually run the
8-phase pipeline (that calls a real LLM, is expensive and slow, and
already has its own extensive coverage). The goal is to test the CLI's
shell — argparse, preflight, exit codes, exception handling — mocking
only the `executar_pipeline` function (the expensive call), never more
than that.

ALREADY-INVESTIGATED CONTEXT (no need to rediscover, but confirm by
reading the code before writing each test):
- `tools/aidd-generator/scripts/pipeline_completo.py`'s `main()` (around
  line 296): builds an `argparse.ArgumentParser` with `ideia`
  (positional, required), `--pasta` (required), `--interativo` and
  `--implementar-codigo` (boolean flags). Calls `verificar_llm_pronto()`
  (imported from `preflight_llm.py`) BEFORE anything expensive — if it
  fails, `sys.exit(1)` with a specific message, never calling
  `executar_pipeline`. If preflight passes, calls
  `executar_pipeline(args.ideia, Path(args.pasta),
  nao_interativo=not args.interativo, implementar_codigo=args.implementar_codigo)`
  inside a `try`/`except LLMNaoConfiguradoException` — if that exception
  is raised, `sys.exit(1)` with the friendly message (never the raw
  stack trace). If `executar_pipeline` returns
  `resultado['status'] == 'COMPLETO'`, it prints the final score and
  `sys.exit(0)`; otherwise it prints `resultado['fase_que_falhou']` and
  `sys.exit(1)`.
- `tests/unit/test_phase_isolation.py` (same test directory) already has
  a `pipeline_mod` fixture that loads `pipeline_completo.py` via
  `importlib.util.spec_from_file_location` — reuse that exact loading
  pattern (or create an equivalent fixture in the new file), don't
  invent another way to import the module.
- No test today calls `main()` with real argv — confirmed via grep (no
  occurrence of `pipeline_completo` outside that module-loading pattern
  used to test internal functions).

DECISIONS ALREADY MADE (do not reopen these):
1. Never call `executar_pipeline` for real in any new test — it
   triggers a real LLM pipeline. Always mock it, via
   `monkeypatch.setattr(pipeline_mod, 'executar_pipeline', fake_fn)` (or
   equivalent).
2. `verificar_llm_pronto` should also be mocked when the test needs to
   control the preflight outcome (for failure cases) — but at least 1
   test must confirm that, when the mocked preflight fails,
   `executar_pipeline` is NEVER called (use a mock that raises an
   `AssertionError`/`Exception` if invoked, to prove this, not just
   assume it).
3. Success and failure tests use a minimal but realistic `resultado`
   dict — no need to reproduce every key `executar_pipeline` actually
   returns, just the ones `main()` actually reads (`status`,
   `score_final`, `fleet`, `context_purge`, `duracao_segundos`,
   `fase_que_falhou`).

DEFINITION OF DONE — in this order:

PHASE 1 — Test `pipeline_completo.py`'s `main()` as a real CLI
1.1. Real test: call `main()` (via `sys.argv` mocked with
     `monkeypatch.setattr(sys, 'argv', [...])`, without `--pasta`) and
     confirm argparse rejects it (raises `SystemExit` with a non-zero
     code, argparse's default behavior for a missing required
     argument) — no need to mock anything else.
1.2. Real test: mock `verificar_llm_pronto` to return
     `(False, "test reason")`; mock `executar_pipeline` with a function
     that raises if called (proving it's not invoked). Run `main()`
     with valid argv, confirm `SystemExit` with code 1 and the
     preflight message in the captured output (`capsys`).
1.3. Real test: mock `verificar_llm_pronto` to return `(True, "ok")`;
     mock `executar_pipeline` to raise
     `LLMNaoConfiguradoException("test friendly message", "technical detail")`.
     Confirm `SystemExit` code 1 and that the output shows the friendly
     message, not a raw stack trace.
1.4. Real test: mock `executar_pipeline` to return
     `{'status': 'COMPLETO', 'score_final': 92, 'fleet': {'modo': 'x', 'total_detectados': 1},
     'context_purge': {}, 'duracao_segundos': 1.0}`. Confirm
     `SystemExit` code 0 and that the output shows the score (92).
1.5. Real test: mock `executar_pipeline` to return
     `{'status': 'FALHOU', 'fase_que_falhou': 'phase_02_analysis',
     'fleet': {}, 'context_purge': {}, 'duracao_segundos': 1.0}`.
     Confirm `SystemExit` code 1 and that the output mentions
     "phase_02_analysis".

EXIT CRITERIA (run and paste the real output of each):
- Full `aidd-generator` suite (`python -m pytest tests/ -q`) → no
  regression, with the 5 new tests included in the count.
- Explicitly confirm (in test 1.2's output) that `executar_pipeline` was
  never called when preflight fails.
- Confirm via command (`git status`) that no new test left a file
  outside `tmp_path`/a temporary test directory, and that no real LLM
  call was made during the tests (no new
  `.aidd/cache/_llm_request_*.json` in the repository).

SCOPE RULES — DO NOT:
- Do not run `executar_pipeline` for real in any test — always mock it.
- Do not touch `aidd-forge` — the audit already confirmed that its
  `init`/`inject` commands already have solid coverage (real success and
  failure, including via a git hook), there is no work to do there.
- Do not touch `aidd_inject.py`, `preflight_llm.py`, or
  `verificar_gates.py` in aidd-generator — already covered, out of scope
  for this item.
- Do not `git commit` or `git push`.
- Do not modify
  `docs/planos/refinamento-notas-auditoria/01-cobertura-comandos-forge-generator.md`.

DELIVERABLE: exact list of files created/changed; command + real output
proving each of the 5 tests; any necessary deviation, explicitly
reported instead of decided by yourself.
```
