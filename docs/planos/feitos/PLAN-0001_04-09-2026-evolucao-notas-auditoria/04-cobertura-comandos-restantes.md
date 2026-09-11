# Pacote 4 — Cobertura dos Comandos Restantes

> **Status:** ✅ CONCLUÍDO em 05/09/2026 — nota final 9.5/10 (ver Veredito ao final do documento).
> **Origem:** `docs/planos/PLANO-EVOLUCAO-NOTAS-AUDITORIA.md` §5 (Fase 4) — 7 comandos do CLI sem nenhuma cobertura de teste no nível de comando.
> **Contribui para:** dimensão Testabilidade/Cobertura Real (6→9/10, mesma dimensão que os Pacotes 1 e 2 já avançaram parcialmente).

---

## Verificação independente que já fiz (antes de aceitar o diagnóstico original às cegas)

O diagnóstico original é de antes dos Pacotes 1/2/7 — parte dele já pode estar resolvido. Reverifiquei:

1. **Confirmado via grep, ainda válido hoje:** nenhum dos 7 comandos (`audit`, `plan`, `apply`, `compose-orca`, `refine-module`, `bench`, `export-frontend`, `setup`) tem qualquer teste que referencie sua função (`cmd_audit`, `cmd_plan`, etc.) em `tools/aidd-master/tests/` **nem** em `tools/aidd-enterprise/tests/` — o gap existe nas 2 ferramentas, não só na auditada originalmente.
2. **Falso-positivo descartado:** grep por substring solta (`" audit"`, `" plan"`) encontrou ocorrências em `test_injector_core.py`/`test_scaffold_infra.py`, mas são a palavra "auditoria"/"planejamento" em texto de teste, não chamadas reais ao comando — confirmei lendo o contexto.
3. **Li a implementação real dos 7 comandos em `aidd-master/scripts/aidd.py` para confirmar que são testáveis de forma determinística, sem mock nem chamada de LLM:**
   - `cmd_audit`: roda 6-7 gates via `subprocess` contra um projeto composto, agrega PASS/FAIL, `sys.exit(1)` se algum falhar. 100% determinístico.
   - `cmd_plan`: confirmado — é casamento de palavras-chave contra uma lista fixa de ~24 domínios (`KNOWN_DOMAINS`), zero LLM. Gera `SPEC-ARQUITETURA.md` + `PLANO-EXECUCAO-ESTRUTURADO.json`.
   - `cmd_apply`: lê o `PLANO-EXECUCAO-ESTRUTURADO.json` gerado por `plan` e chama `compose_suite()` (já testado a fundo no Pacote 2) — o risco aqui é só a ponte JSON→compose, não a composição em si.
   - `cmd_compose_orca`: usa `SubagentEngine`/`ContextPurgeEngine` (`src/core/subagent_engine.py`) — confirmei que é geração determinística via `subprocess` por módulo (spec textual + template), **não** uma chamada real de LLM/agente. Testável sem mock.
   - `cmd_refine_module`: depende de `behave` — **confirmei que está instalado nesta máquina** (`behave` importável, binário em PATH), então o teste pode ser real, não só estrutural com `skipif` (diferente do padrão usado para `helm`/`terraform`, que genuinamente não estão instalados).
   - `cmd_bench`: benchmark local de concorrência SQLite WAL via `ThreadPoolExecutor`, sem dependência externa. 100% testável.
   - `cmd_export_frontend`: delega a `openapi_to_ts.export_frontend()` — geração determinística de TypeScript/Next.js a partir do `PLANO-EXECUCAO-ESTRUTURADO.json`.
   - `cmd_setup`: **atenção** — roda `pip install -r requirements.txt` de verdade (muta o ambiente real) e **nunca retorna exit code 1**, mesmo quando as etapas falham (só imprime `[WARN]`) — isso é um achado adicional (não estava no diagnóstico original): o comando nunca reporta falha via exit code, só via texto. Registrado como item a decidir na Definição de Pronto abaixo (não instalar dependências de verdade no teste; decidir se a ausência de exit code de falha é um bug de transparência a corrigir ou um comportamento "best effort" intencional).

---

## Definição de Pronto

**Regra geral, válida para todos os 7 comandos, nas 2 ferramentas (`aidd-master`, `aidd-enterprise`):** todo teste roda de verdade (subprocess ou chamada direta da função, nunca mock do comportamento central), confirma exit code real, e — onde aplicável — confirma o artefato físico gerado no disco (arquivo, linha em manifesto, etc.), não só "não lançou exceção".

1. **`audit`:** compor um projeto de verdade (reaproveitar fixture/projeto já usado nos testes de `compose_suite`), rodar `cmd_audit`, confirmar exit 0. Quebrar algo de propósito (ex.: introduzir um `SyntaxError` num arquivo do projeto composto) e confirmar exit 1 com o gate certo reportado como FAIL. Repetir para `aidd-enterprise` (lista de gates pode divergir — confirmar qual é a lista real de cada ferramenta antes de escrever o teste, não assumir que são idênticas).
2. **`plan` / `apply`:** testar `cmd_plan` com 3 casos: (a) domínio conhecido (`"crie um crm"` → módulo `crm` detectado), (b) domínio desconhecido (fallback por palavras extraídas do prompt), (c) prompt vazio/sem substância (fallback para `["principal", "configuracao"]`). Confirmar que `SPEC-ARQUITETURA.md` e `PLANO-EXECUCAO-ESTRUTURADO.json` são gerados com o conteúdo esperado. Depois, testar `cmd_apply` lendo esse plano e confirmando que `compose_suite()` é chamada com os módulos certos (pode ser via projeto real pequeno, não precisa mockar `compose_suite` já que ele é rápido e determinístico).
3. **`compose-orca`:** confirmar que gera a mesma estrutura de arquivos por módulo que `compose`/`compose_suite` produz para os módulos padrão (mesmo padrão AIDD Modular Clean Architecture: `__init__.py`, `models.py`, `services.py`, `routes.py`, `mcp_tools.py`, teste unitário). Confirmar `COMPOSE-ORCA-MANIFEST.json` gerado e exit code correto (0 em sucesso, 1 se `summary["status"] == "REPROVADO"`).
4. **`refine-module`:** já que `behave` está instalado, teste real (não `skipif`): compor um módulo, rodar `refine-module`, confirmar que os cenários BDD executam de verdade. Manter também um teste estrutural independente de `behave` (confirma que o comando monta os argumentos certos para o `behave`), para o caso de rodar numa máquina sem `behave` no futuro.
5. **`bench`:** rodar contra um projeto composto de verdade (com `app.db` real), confirmar que retorna exit 0 sob concorrência normal e que os números reportados (sucessos/erros/RPS) batem com o que o teste consegue observar independentemente (não confiar só no print).
6. **`export-frontend`:** rodar contra um projeto composto (tem `PLANO-EXECUCAO-ESTRUTURADO.json` + contrato OpenAPI), confirmar que os arquivos `.ts`/`.tsx` gerados existem e são sintaticamente válidos (mesmo padrão já usado para validar YAML/Terraform gerado por `scaffold_infra` — usar parser real de TS se disponível no ambiente, ou heurística estrutural equivalente se não).
7. **`setup`:** testar só a parte de diagnóstico (detecção de Git, ORCA, Fleet Discovery) — **nunca** rodar a instalação real de `requirements.txt` dentro do teste (mutaria o ambiente de verdade). Isolar/mockar especificamente a chamada de `pip install` (única exceção à regra geral de "nunca mock do comportamento central", porque aqui o comportamento central É a mutação do ambiente, que não pode rodar em teste). Registrar como achado (não corrigir nesta fase, só documentar) que `cmd_setup` nunca retorna exit code de falha.

**Critério de saída (rodar e colar o output real de cada um):**
- Suíte completa de `aidd-master` e `aidd-enterprise` (`python -m pytest tests/ -q`) → sem regressão, com os novos testes incluídos na contagem.
- Cada um dos 7 comandos tem pelo menos 1 teste que roda o comando de verdade (subprocess ou chamada direta) e verifica exit code + artefato gerado — não apenas "não lançou exceção".
- Nenhum teste novo muta o ambiente real (nenhuma instalação de pacote de verdade, nenhuma escrita fora de `tmp_path`/diretório de teste).

---

## Ordem de execução recomendada (por risco real de uso, herdada do diagnóstico original)

1. `audit` — é o próprio mecanismo de garantia de qualidade; se ele não é testado, nada mais importa tanto.
2. `plan`/`apply` — maior superfície de confusão do usuário (fluxo de linguagem natural).
3. `compose-orca` — mecanismo agêntico mais complexo, nunca verificado.
4. `bench` — rápido, sem dependência externa, sem desculpa para não ter sido feito primeiro.
5. `export-frontend` — gera código para fora do próprio produto.
6. `refine-module` — depende de `behave`, mas já confirmado instalado.
7. `setup` — só a parte de diagnóstico, sem risco de mutar o ambiente.

---

## Nota sobre o tamanho deste pacote

7 comandos × 2 ferramentas (`aidd-master`, `aidd-enterprise`) é comparável em escopo ao Pacote 7. Recomendo dividir em **2 prompts sequenciais** para o agente executor, na mesma disciplina já usada: Prompt A = itens 1-4 (audit, plan/apply, compose-orca, bench — os de maior risco/uso real) e Prompt B = itens 5-7 (export-frontend, refine-module, setup), só depois do Prompt A auditado e aprovado.

**Aprovada pelo usuário em 05/09/2026.** Prompts de execução abaixo.

---

## Prompt A — audit, plan/apply, compose-orca, bench (maior risco/uso real)

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa. Rode isto primeiro; só depois de auditado e aprovado o Prompt B é enviado.

```
Você vai fechar um gap real de cobertura de testes no ecossistema-aidd
(monorepo em C:\Users\trcnologia\Desktop\ecossistema-aidd) — 4 comandos do
CLI (`audit`, `plan`, `apply`, `compose-orca`, `bench`) não têm NENHUM
teste que os exercite de verdade, em nenhuma das 2 ferramentas afetadas
(`tools/aidd-master`, `tools/aidd-enterprise`). Siga EXATAMENTE a
Definição de Pronto abaixo, não invente escopo adicional, e valide tudo
de verdade (execuções reais, exit codes reais, nunca mascarados por pipe).

CONTEXTO JÁ INVESTIGADO (não precisa redescobrir, mas DEVE confirmar você
mesmo antes de escrever cada teste — ver item de reverificação em cada fase):
- Confirmado via grep em `tools/aidd-master/tests/` e
  `tools/aidd-enterprise/tests/`: nenhum teste referencia `cmd_audit`,
  `cmd_plan`, `cmd_apply`, `cmd_compose_orca` ou `cmd_bench`.
- `cmd_audit` (`scripts/aidd.py`) roda uma bateria de gates via
  `subprocess` contra um projeto composto (`G_ESTRUTURA`, `G_QUALIDADE`,
  `G_TESTES`, `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, e
  opcionalmente `G_SEGURANCA` se o arquivo existir), agrega PASS/FAIL, e
  retorna exit 1 se qualquer gate falhar. 100% determinístico.
- `cmd_plan` (`scripts/aidd.py`) é casamento de palavras-chave contra uma
  lista fixa `KNOWN_DOMAINS` (~24 termos em português) — zero LLM. Gera
  `SPEC-ARQUITETURA.md` e `PLANO-EXECUCAO-ESTRUTURADO.json` no diretório
  alvo. Se nenhum domínio conhecido bater, tenta extrair palavras do
  prompt (excluindo stop-words); se ainda assim nada sobrar, usa
  `["principal", "configuracao"]` como fallback final.
- `cmd_apply` lê o `PLANO-EXECUCAO-ESTRUTURADO.json` gerado por `cmd_plan`
  e chama `compose_suite(target_dir, suite_name, modulos)` — a função
  `compose_suite` já tem cobertura extensa (Pacote 2 da evolução de notas
  deste projeto); o risco aqui é só a ponte JSON → `compose_suite`, não a
  composição em si.
- `cmd_compose_orca` usa `SubagentEngine`/`ContextPurgeEngine`
  (`src/core/subagent_engine.py`) — CONFIRMADO que é geração determinística
  via `subprocess` por módulo (spec textual fixa + template), NÃO uma
  chamada real de LLM/agente. Testável sem mock. Gera os mesmos arquivos
  por módulo que `compose`/`compose_suite` (`__init__.py`, `models.py`,
  `services.py`, `routes.py`, `mcp_tools.py`, `tests/unit/test_{modulo}.py`)
  e salva `COMPOSE-ORCA-MANIFEST.json` no diretório alvo. Retorna exit 1
  se `summary["status"] == "REPROVADO"`.
- `cmd_bench` roda um benchmark de concorrência local no SQLite WAL via
  `ThreadPoolExecutor`, sem nenhuma dependência externa. Precisa de um
  `app.db` real acessível (via `src/core` do projeto composto, ou
  `templates/core`/`templates/v2` da própria ferramenta como fallback).
  Retorna exit 1 se qualquer operação concorrente falhar.
- Existe uma fixture reutilizável em
  `tools/aidd-master/tests/unit/test_compose_suite.py` (`suite_composta`,
  linha ~75) que já compõe uma suíte real com o módulo `produtos` — use
  o mesmo padrão em vez de inventar um novo utilitário de composição.

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. Todo teste roda o comando de verdade (subprocess ou chamada direta da
   função Python) — nunca mock do comportamento central. Confirma exit
   code real E o artefato físico gerado (arquivo no disco, entrada em
   manifesto JSON, etc.) — nunca só "não lançou exceção".
2. Os 4 comandos precisam de teste nas 2 ferramentas (`aidd-master` E
   `aidd-enterprise`) — NÃO assuma que o comportamento é idêntico nas
   duas; leia a implementação de cada uma antes de escrever o teste
   espelhado (ex.: a lista de gates de `cmd_audit` pode divergir entre
   as duas — confirme lendo o código de cada `scripts/aidd.py`, não
   copie a lista de uma ferramenta para a outra sem checar).
3. Nenhum teste novo pode mutar o ambiente real (nenhuma instalação de
   pacote de verdade, nenhuma escrita fora de `tmp_path`/diretório de
   teste temporário).

DEFINIÇÃO DE PRONTO — nesta ordem:

FASE 1 — `audit`
1.1. Reverifique você mesmo, lendo `scripts/aidd.py` de cada ferramenta,
     a lista exata de gates que `cmd_audit` executa (pode divergir entre
     `aidd-master` e `aidd-enterprise`).
1.2. Componha um projeto de teste real (reaproveite o padrão da fixture
     `suite_composta` citada acima, ou equivalente para `aidd-enterprise`
     se a fixture não existir lá — confirme antes de assumir).
1.3. Rode `cmd_audit` contra esse projeto composto e confirme exit 0 (com
     todos os gates reportando PASS).
1.4. Quebre algo de propósito no projeto composto (ex.: introduza um
     `SyntaxError` num arquivo do projeto, ou apague um arquivo que um
     gate específico exige) e confirme que `cmd_audit` retorna exit 1,
     com o gate certo (o que você quebrou) reportado como FAIL no
     relatório — não só "algum gate falhou", tem que ser o gate certo.
1.5. Repita 1.2-1.4 para `aidd-enterprise`.

FASE 2 — `plan` / `apply`
2.1. Teste `cmd_plan` com 3 casos, confirmando o conteúdo gerado (não só
     que os arquivos existem):
     a) Domínio conhecido: prompt tipo "crie um crm" → confirme que o
        módulo `crm` foi detectado e aparece em
        `PLANO-EXECUCAO-ESTRUTURADO.json` (`projeto.modulos`).
     b) Domínio desconhecido: prompt com palavras que não batem em
        `KNOWN_DOMAINS` → confirme o fallback de extração de palavras do
        prompt (excluindo stop-words).
     c) Prompt vazio ou sem substância → confirme o fallback final
        `["principal", "configuracao"]`.
     Para os 3 casos, confirme que `SPEC-ARQUITETURA.md` também foi
     gerado e contém o nome dos módulos detectados.
2.2. Teste `cmd_apply`: gere um `PLANO-EXECUCAO-ESTRUTURADO.json` (via
     `cmd_plan` ou escrito diretamente pelo teste, sua escolha) e confirme
     que `cmd_apply` lê os módulos certos dele e que `compose_suite` é
     chamada com esses módulos exatos (pode confirmar pelo resultado
     físico da composição — arquivos dos módulos aparecendo no projeto —
     não precisa mockar `compose_suite`, ela é rápida).
2.3. Repita 2.1-2.2 para `aidd-enterprise`.

FASE 3 — `compose-orca`
3.1. Rode `cmd_compose_orca` com 1-2 módulos de teste e confirme que cada
     módulo gera a mesma estrutura de arquivos que `compose`/`compose_suite`
     gera para módulos padrão (mesmos arquivos: `__init__.py`, `models.py`,
     `services.py`, `routes.py`, `mcp_tools.py`,
     `tests/unit/test_{modulo}.py`).
3.2. Confirme que `COMPOSE-ORCA-MANIFEST.json` é gerado no diretório alvo
     com a estrutura esperada (`total_modules`, `success`, `failed`,
     `errors`, `modules` por nome).
3.3. Teste o caminho de falha: force um módulo a falhar (ex.: nome de
     módulo inválido ou spec malformada, dependendo do que
     `SubagentEngine` aceitar) e confirme que o exit code é 1 quando
     `summary["status"] == "REPROVADO"`.
3.4. Repita 3.1-3.3 para `aidd-enterprise` (confirme antes se
     `compose-orca` existe de forma idêntica lá, ou se diverge).

FASE 4 — `bench`
4.1. Componha um projeto real (mesma fixture da Fase 1) para ter um
     `app.db` real acessível.
4.2. Rode `cmd_bench` contra esse projeto e confirme exit 0 sob
     concorrência normal (sem lock contention).
4.3. Confirme os números reportados (sucessos, erros, RPS) de forma
     independente do print do comando — ex.: capture a saída e valide
     que "Falhas (FAIL)" é 0 quando o exit code é 0, e que o total de
     operações bate com o `--n` passado.
4.4. Repita 4.1-4.3 para `aidd-enterprise`.

CRITÉRIO DE SAÍDA DESTE PROMPT (rode e cole o output real de cada um):
- Suíte completa de `aidd-master` (`python -m pytest tests/ -q`) → sem
  regressão, com os novos testes incluídos na contagem.
- Suíte completa de `aidd-enterprise` (`python -m pytest tests/ -q`) →
  sem regressão, com os novos testes incluídos na contagem.
- Para cada um dos 4 comandos, confirme por output real: o teste de
  sucesso (exit 0 + artefato certo) E o teste de falha/fallback
  correspondente (exit 1, ou fallback certo no caso de `plan`).
- Confirme por comando (`git status`) que nenhum teste novo deixou
  arquivo fora de `tmp_path`/diretório de teste temporário no
  repositório.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não implemente ainda os testes de `export-frontend`, `refine-module`
  nem `setup` — isso é o Prompt B, só roda depois deste ser auditado.
- Não corrija nenhum bug de comportamento que encontrar nos comandos
  (ex.: se achar algo estranho em `cmd_plan`/`cmd_apply`/`cmd_compose_orca`/
  `cmd_bench` além do já documentado aqui) — apenas RELATE no seu
  entregável, não decida consertar sozinho.
- Não faça `git commit` nem `git push`.
- Não altere
  `docs/planos/evolucao-notas-auditoria/04-cobertura-comandos-restantes.md`.

ENTREGÁVEL: lista exata de arquivos de teste criados/alterados; para cada
fase e cada ferramenta, comando + output real que comprova (sucesso E
falha/fallback); qualquer divergência encontrada entre `aidd-master` e
`aidd-enterprise` que exigiu tratamento diferente (relatada, não decidida
em silêncio); qualquer comportamento estranho/inesperado encontrado nos 4
comandos (relatado, não corrigido).
```

## Prompt A — English version

```
You are going to close a real test-coverage gap in the ecossistema-aidd
monorepo (C:\Users\trcnologia\Desktop\ecossistema-aidd) — 4 CLI commands
(`audit`, `plan`, `apply`, `compose-orca`, `bench`) have NO test that
exercises them for real, in either of the 2 affected tools
(`tools/aidd-master`, `tools/aidd-enterprise`). Follow the Definition of
Done below EXACTLY, do not invent additional scope, and validate
everything for real (real runs, real exit codes, never masked by a pipe).

ALREADY-INVESTIGATED CONTEXT (no need to rediscover, but you MUST confirm
it yourself before writing each test — see the re-verification step in
each phase):
- Confirmed via grep in `tools/aidd-master/tests/` and
  `tools/aidd-enterprise/tests/`: no test references `cmd_audit`,
  `cmd_plan`, `cmd_apply`, `cmd_compose_orca`, or `cmd_bench`.
- `cmd_audit` (`scripts/aidd.py`) runs a gate battery via `subprocess`
  against a composed project (`G_ESTRUTURA`, `G_QUALIDADE`, `G_TESTES`,
  `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`, and optionally
  `G_SEGURANCA` if that file exists), aggregates PASS/FAIL, and returns
  exit 1 if any gate fails. 100% deterministic.
- `cmd_plan` (`scripts/aidd.py`) is keyword matching against a fixed
  `KNOWN_DOMAINS` list (~24 Portuguese terms) — zero LLM. It generates
  `SPEC-ARQUITETURA.md` and `PLANO-EXECUCAO-ESTRUTURADO.json` in the
  target directory. If no known domain matches, it tries extracting
  words from the prompt (excluding stop-words); if nothing is left, it
  falls back to `["principal", "configuracao"]`.
- `cmd_apply` reads the `PLANO-EXECUCAO-ESTRUTURADO.json` generated by
  `cmd_plan` and calls `compose_suite(target_dir, suite_name, modulos)`
  — `compose_suite` already has extensive coverage (Package 2 of this
  project's note-evolution effort); the risk here is only the JSON →
  `compose_suite` bridge, not the composition itself.
- `cmd_compose_orca` uses `SubagentEngine`/`ContextPurgeEngine`
  (`src/core/subagent_engine.py`) — CONFIRMED to be deterministic
  generation via `subprocess` per module (fixed textual spec + template),
  NOT a real LLM/agent call. Testable without mocking. It produces the
  same per-module files as `compose`/`compose_suite`
  (`__init__.py`, `models.py`, `services.py`, `routes.py`,
  `mcp_tools.py`, `tests/unit/test_{modulo}.py`) and saves
  `COMPOSE-ORCA-MANIFEST.json` in the target directory. Returns exit 1
  if `summary["status"] == "REPROVADO"`.
- `cmd_bench` runs a local SQLite WAL concurrency benchmark via
  `ThreadPoolExecutor`, with no external dependency. It needs a real
  `app.db` reachable (via the composed project's `src/core`, or the
  tool's own `templates/core`/`templates/v2` as fallback). Returns exit 1
  if any concurrent operation fails.
- There is a reusable fixture in
  `tools/aidd-master/tests/unit/test_compose_suite.py` (`suite_composta`,
  around line 75) that already composes a real suite with the `produtos`
  module — reuse that pattern instead of inventing a new composition
  utility.

DECISIONS ALREADY MADE (do not reopen these):
1. Every test runs the real command (subprocess or a direct Python
   function call) — never mock the core behavior. It confirms the real
   exit code AND the physical artifact generated (a file on disk, an
   entry in a JSON manifest, etc.) — never just "didn't raise an
   exception".
2. All 4 commands need tests in BOTH tools (`aidd-master` AND
   `aidd-enterprise`) — do NOT assume behavior is identical between the
   two; read each implementation before writing the mirrored test (e.g.
   `cmd_audit`'s gate list may diverge between the two — confirm by
   reading each `scripts/aidd.py`, don't copy one tool's list onto the
   other without checking).
3. No new test may mutate the real environment (no real package
   installs, no writes outside `tmp_path`/a temporary test directory).

DEFINITION OF DONE — in this order:

PHASE 1 — `audit`
1.1. Re-verify yourself, by reading each tool's `scripts/aidd.py`, the
     exact list of gates `cmd_audit` runs (may diverge between
     `aidd-master` and `aidd-enterprise`).
1.2. Compose a real test project (reuse the `suite_composta` fixture
     pattern mentioned above, or an equivalent for `aidd-enterprise` if
     that fixture doesn't exist there — confirm before assuming).
1.3. Run `cmd_audit` against that composed project and confirm exit 0
     (with every gate reporting PASS).
1.4. Deliberately break something in the composed project (e.g.
     introduce a `SyntaxError` in a project file, or delete a file a
     specific gate requires) and confirm `cmd_audit` returns exit 1, with
     the SPECIFIC gate you broke reported as FAIL in the report — not
     just "some gate failed", it must be the right one.
1.5. Repeat 1.2-1.4 for `aidd-enterprise`.

PHASE 2 — `plan` / `apply`
2.1. Test `cmd_plan` with 3 cases, confirming the generated content (not
     just that the files exist):
     a) Known domain: a prompt like "crie um crm" → confirm the `crm`
        module was detected and appears in
        `PLANO-EXECUCAO-ESTRUTURADO.json` (`projeto.modulos`).
     b) Unknown domain: a prompt with words that don't match
        `KNOWN_DOMAINS` → confirm the word-extraction fallback from the
        prompt (excluding stop-words).
     c) Empty or substance-less prompt → confirm the final fallback
        `["principal", "configuracao"]`.
     For all 3 cases, confirm `SPEC-ARQUITETURA.md` was also generated
     and contains the detected module names.
2.2. Test `cmd_apply`: generate a `PLANO-EXECUCAO-ESTRUTURADO.json`
     (either via `cmd_plan` or written directly by the test, your
     choice) and confirm `cmd_apply` reads the right modules from it and
     that `compose_suite` is called with those exact modules (you can
     confirm this via the physical composition result — module files
     appearing in the project — no need to mock `compose_suite`, it's
     fast).
2.3. Repeat 2.1-2.2 for `aidd-enterprise`.

PHASE 3 — `compose-orca`
3.1. Run `cmd_compose_orca` with 1-2 test modules and confirm each module
     produces the same file structure that `compose`/`compose_suite`
     produces for standard modules (same files: `__init__.py`,
     `models.py`, `services.py`, `routes.py`, `mcp_tools.py`,
     `tests/unit/test_{modulo}.py`).
3.2. Confirm `COMPOSE-ORCA-MANIFEST.json` is generated in the target
     directory with the expected structure (`total_modules`, `success`,
     `failed`, `errors`, `modules` by name).
3.3. Test the failure path: force one module to fail (e.g. an invalid
     module name or malformed spec, depending on what `SubagentEngine`
     accepts) and confirm the exit code is 1 when
     `summary["status"] == "REPROVADO"`.
3.4. Repeat 3.1-3.3 for `aidd-enterprise` (confirm first whether
     `compose-orca` exists identically there, or diverges).

PHASE 4 — `bench`
4.1. Compose a real project (same fixture as Phase 1) to have a real
     `app.db` reachable.
4.2. Run `cmd_bench` against it and confirm exit 0 under normal
     concurrency (no lock contention).
4.3. Confirm the reported numbers (successes, errors, RPS) independently
     of the command's print output — e.g. capture the output and verify
     "Falhas (FAIL)" is 0 when exit code is 0, and that the total
     operation count matches the `--n` passed.
4.4. Repeat 4.1-4.3 for `aidd-enterprise`.

EXIT CRITERIA FOR THIS PROMPT (run and paste the real output of each):
- Full `aidd-master` suite (`python -m pytest tests/ -q`) → no
  regression, with the new tests included in the count.
- Full `aidd-enterprise` suite (`python -m pytest tests/ -q`) → no
  regression, with the new tests included in the count.
- For each of the 4 commands, confirm via real output: the success test
  (exit 0 + correct artifact) AND the corresponding failure/fallback test
  (exit 1, or the correct fallback in `plan`'s case).
- Confirm via command (`git status`) that no new test left a file outside
  `tmp_path`/a temporary test directory in the repository.

SCOPE RULES — DO NOT:
- Do not implement tests for `export-frontend`, `refine-module`, or
  `setup` yet — that's Prompt B, only runs after this one has been
  audited.
- Do not fix any behavioral bug you find in these commands (e.g. if you
  find something odd in `cmd_plan`/`cmd_apply`/`cmd_compose_orca`/
  `cmd_bench` beyond what's already documented here) — only REPORT it in
  your deliverable, do not decide to fix it yourself.
- Do not `git commit` or `git push`.
- Do not modify
  `docs/planos/evolucao-notas-auditoria/04-cobertura-comandos-restantes.md`.

DELIVERABLE: exact list of test files created/changed; for each phase and
each tool, the command + real output that proves it (success AND
failure/fallback); any divergence found between `aidd-master` and
`aidd-enterprise` that required different handling (reported, not
silently decided); any odd/unexpected behavior found in the 4 commands
(reported, not fixed).
```

---

## Prompt B — export-frontend, refine-module, setup — só rodar depois do Prompt A auditado

> Copie o bloco abaixo integralmente para o agente executor, depois que o resultado do Prompt A tiver sido auditado e aprovado. Autocontido.

```
Você vai concluir a cobertura de testes dos comandos restantes do
ecossistema-aidd (monorepo em C:\Users\trcnologia\Desktop\ecossistema-aidd).
Um trabalho anterior (Prompt A, já auditado e aprovado) cobriu `audit`,
`plan`, `apply`, `compose-orca` e `bench` nas 2 ferramentas
(`tools/aidd-master`, `tools/aidd-enterprise`). Este prompt cobre os 3
comandos restantes: `export-frontend`, `refine-module`, `setup`.

Siga EXATAMENTE a Definição de Pronto abaixo, não invente escopo
adicional, valide tudo de verdade (execuções reais, exit codes reais,
nunca mascarados por pipe).

CONTEXTO JÁ INVESTIGADO:
- `cmd_export_frontend` (`scripts/aidd.py`) lê
  `PLANO-EXECUCAO-ESTRUTURADO.json` do diretório alvo (para o nome da
  suíte) e delega para `openapi_to_ts.export_frontend(target_dir,
  suite_name, stack=...)` — geração determinística de um frontend
  Next.js/TypeScript a partir do contrato OpenAPI do projeto composto.
- `cmd_refine_module` roda a suíte BDD (`behave`) de um módulo até 100%
  dos cenários passarem. **CONFIRMADO que `behave` está instalado nesta
  máquina** (binário disponível no PATH, pacote Python importável) — o
  teste deve ser REAL (rodar `behave` de verdade), não só estrutural com
  `skipif`. Ainda assim, mantenha também 1 teste estrutural independente
  de `behave` estar instalado (confirma que o comando monta os argumentos
  certos para invocar `behave`), para o caso de rodar no futuro numa
  máquina sem `behave`.
- `cmd_setup` roda diagnóstico de ambiente (versão do Python, Git CLI,
  ORCA ADE, Fleet Discovery de agentes de IA) e **também roda
  `pip install -r requirements.txt` de verdade** — isso MUTA o ambiente
  real e NÃO PODE rodar dentro do teste. Achado adicional já confirmado:
  `cmd_setup` nunca retorna exit code de falha (só imprime `[WARN]`),
  mesmo quando uma etapa falha — isto é um comportamento existente, não é
  para você corrigir agora, só para você respeitar ao escrever o teste
  (não espere um exit 1 que o comando nunca produz).

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. Mesma regra do Prompt A: todo teste roda o comportamento real
   (subprocess ou chamada direta), confirma exit code E artefato físico,
   nunca mock do comportamento central — EXCETO a instalação de pacotes
   dentro de `cmd_setup` (ver Fase 3 abaixo), que é a única exceção
   explícita a esta regra, porque o comportamento central ali É a
   mutação do ambiente, que não pode rodar em teste.
2. Os 3 comandos precisam de teste nas 2 ferramentas (`aidd-master` E
   `aidd-enterprise`) — confirme você mesmo se o comportamento diverge
   antes de espelhar um teste de uma ferramenta para a outra.
3. Nenhum teste novo pode mutar o ambiente real.

DEFINIÇÃO DE PRONTO — nesta ordem:

FASE 5 — `export-frontend`
5.1. Componha um projeto de teste real com um contrato OpenAPI válido
     (reaproveite a mesma fixture de composição usada no Prompt A).
5.2. Rode `cmd_export_frontend` contra esse projeto e confirme que os
     arquivos `.ts`/`.tsx` esperados são gerados no disco.
5.3. Valide que o TypeScript gerado é sintaticamente válido — use um
     parser/compilador TypeScript real se disponível no ambiente (ex.:
     `tsc --noEmit` via `npx` ou binário já instalado); se genuinamente
     não houver nenhuma ferramenta TypeScript disponível nesta máquina,
     use uma validação estrutural equivalente à já usada para YAML/
     Terraform gerado por `scaffold_infra` (documente explicitamente qual
     caminho você seguiu e por quê).
5.4. Repita 5.1-5.3 para `aidd-enterprise`.

FASE 6 — `refine-module`
6.1. Componha um módulo de teste real (reaproveite a fixture de
     composição).
6.2. Rode `cmd_refine_module` contra esse módulo e confirme que os
     cenários BDD (`behave`) executam de verdade — capture a saída real
     do `behave` e confirme que reporta os cenários esperados.
6.3. Escreva também 1 teste estrutural (não depende de `behave` estar
     instalado) que confirma que `cmd_refine_module` monta os argumentos
     corretos para invocar `behave` (ex.: caminho certo das features,
     diretório certo do módulo).
6.4. Repita 6.1-6.3 para `aidd-enterprise`.

FASE 7 — `setup`
7.1. Teste SOMENTE a parte de diagnóstico de `cmd_setup`: detecção de
     Git CLI, detecção de ORCA ADE, Fleet Discovery de agentes de IA.
     Isole/mocke especificamente a chamada de `pip install` (via
     `subprocess.run` ou equivalente) — esta é a única exceção à regra
     geral de nunca mockar o comportamento central, porque rodar a
     instalação de verdade mutaria o ambiente real de forma irreversível
     dentro de um teste automatizado.
7.2. Confirme que o teste NÃO espera um exit code de falha do comando
     (`cmd_setup` nunca retorna 1, conforme já confirmado) — o teste deve
     validar o conteúdo do output (texto impresso confirmando cada etapa
     de diagnóstico), não o exit code, para este comando especificamente.
7.3. Repita 7.1-7.2 para `aidd-enterprise`.

CRITÉRIO DE SAÍDA FINAL (rode e cole o output real de cada um):
- Suíte completa de `aidd-master` (`python -m pytest tests/ -q`) → sem
  regressão, com os novos testes incluídos na contagem.
- Suíte completa de `aidd-enterprise` (`python -m pytest tests/ -q`) →
  sem regressão, com os novos testes incluídos na contagem.
- Para cada um dos 3 comandos, confirme por output real que o teste
  cobre o comportamento real (não mockado, exceto a exceção explícita da
  Fase 7).
- Confirme por comando (`git status`) que nenhum teste novo deixou
  arquivo fora de `tmp_path`/diretório de teste temporário, e que nenhum
  pacote foi instalado de verdade no ambiente durante os testes de
  `setup`.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não toque em nada já implementado e auditado no Prompt A além do
  necessário para integrar com ele.
- Não corrija o comportamento de `cmd_setup` nunca retornar exit code de
  falha — apenas respeite esse comportamento existente ao escrever o
  teste, e relate o achado no seu entregável.
- Não faça `git commit` nem `git push`.
- Não altere
  `docs/planos/evolucao-notas-auditoria/04-cobertura-comandos-restantes.md`.

ENTREGÁVEL: lista exata de arquivos de teste criados/alterados; para cada
fase e cada ferramenta, comando + output real que comprova; qualquer
divergência encontrada entre `aidd-master` e `aidd-enterprise`; qual
caminho de validação de TypeScript você seguiu na Fase 5 e por quê;
qualquer desvio necessário, reportado explicitamente em vez de decidido
sozinho.
```

## Prompt B — English version

```
You are going to complete test coverage for the remaining commands of
ecossistema-aidd (monorepo at C:\Users\trcnologia\Desktop\ecossistema-aidd).
Prior work (Prompt A, already audited and approved) covered `audit`,
`plan`, `apply`, `compose-orca`, and `bench` across both tools
(`tools/aidd-master`, `tools/aidd-enterprise`). This prompt covers the 3
remaining commands: `export-frontend`, `refine-module`, `setup`.

Follow the Definition of Done below EXACTLY, do not invent additional
scope, validate everything for real (real runs, real exit codes, never
masked by a pipe).

ALREADY-INVESTIGATED CONTEXT:
- `cmd_export_frontend` (`scripts/aidd.py`) reads
  `PLANO-EXECUCAO-ESTRUTURADO.json` from the target directory (for the
  suite name) and delegates to `openapi_to_ts.export_frontend(target_dir,
  suite_name, stack=...)` — deterministic generation of a Next.js/
  TypeScript frontend from the composed project's OpenAPI contract.
- `cmd_refine_module` runs a module's BDD suite (`behave`) until 100% of
  scenarios pass. **CONFIRMED that `behave` is installed on this
  machine** (binary available on PATH, Python package importable) — the
  test must be REAL (actually run `behave`), not just structural with
  `skipif`. Still, also keep 1 structural test independent of `behave`
  being installed (confirms the command builds the right arguments to
  invoke `behave`), in case this runs in the future on a machine without
  `behave`.
- `cmd_setup` runs environment diagnostics (Python version, Git CLI, ORCA
  ADE, AI-agent Fleet Discovery) and **also runs
  `pip install -r requirements.txt` for real** — this MUTATES the real
  environment and CANNOT run inside the test. Already-confirmed
  additional finding: `cmd_setup` never returns a failure exit code
  (only prints `[WARN]`), even when a step fails — this is existing
  behavior, not something for you to fix now, just something to respect
  when writing the test (don't expect an exit 1 the command never
  produces).

DECISIONS ALREADY MADE (do not reopen these):
1. Same rule as Prompt A: every test runs the real behavior (subprocess
   or direct call), confirms exit code AND physical artifact, never
   mocks the core behavior — EXCEPT the package install inside
   `cmd_setup` (see Phase 3 below), which is the one explicit exception
   to this rule, because the core behavior there IS the environment
   mutation, which cannot run in a test.
2. All 3 commands need tests in BOTH tools (`aidd-master` AND
   `aidd-enterprise`) — confirm yourself whether behavior diverges before
   mirroring a test from one tool to the other.
3. No new test may mutate the real environment.

DEFINITION OF DONE — in this order:

PHASE 5 — `export-frontend`
5.1. Compose a real test project with a valid OpenAPI contract (reuse the
     same composition fixture used in Prompt A).
5.2. Run `cmd_export_frontend` against it and confirm the expected
     `.ts`/`.tsx` files are generated on disk.
5.3. Validate the generated TypeScript is syntactically valid — use a
     real TypeScript parser/compiler if available in the environment
     (e.g. `tsc --noEmit` via `npx` or an already-installed binary); if
     genuinely no TypeScript tooling is available on this machine, use a
     structural validation equivalent to the one already used for the
     YAML/Terraform generated by `scaffold_infra` (explicitly document
     which path you took and why).
5.4. Repeat 5.1-5.3 for `aidd-enterprise`.

PHASE 6 — `refine-module`
6.1. Compose a real test module (reuse the composition fixture).
6.2. Run `cmd_refine_module` against it and confirm the BDD (`behave`)
     scenarios actually execute — capture `behave`'s real output and
     confirm it reports the expected scenarios.
6.3. Also write 1 structural test (not dependent on `behave` being
     installed) that confirms `cmd_refine_module` builds the correct
     arguments to invoke `behave` (e.g. correct features path, correct
     module directory).
6.4. Repeat 6.1-6.3 for `aidd-enterprise`.

PHASE 7 — `setup`
7.1. Test ONLY the diagnostic part of `cmd_setup`: Git CLI detection,
     ORCA ADE detection, AI-agent Fleet Discovery. Isolate/mock
     specifically the `pip install` call (via `subprocess.run` or
     equivalent) — this is the one exception to the general rule of never
     mocking core behavior, because actually running the install would
     irreversibly mutate the real environment inside an automated test.
7.2. Confirm the test does NOT expect a failure exit code from the
     command (`cmd_setup` never returns 1, as already confirmed) — the
     test should validate the output content (printed text confirming
     each diagnostic step), not the exit code, for this specific command.
7.3. Repeat 7.1-7.2 for `aidd-enterprise`.

FINAL EXIT CRITERIA (run and paste the real output of each):
- Full `aidd-master` suite (`python -m pytest tests/ -q`) → no
  regression, with the new tests included in the count.
- Full `aidd-enterprise` suite (`python -m pytest tests/ -q`) → no
  regression, with the new tests included in the count.
- For each of the 3 commands, confirm via real output that the test
  covers the real behavior (not mocked, except the explicit Phase 7
  exception).
- Confirm via command (`git status`) that no new test left a file
  outside `tmp_path`/a temporary test directory, and that no package was
  actually installed in the environment during the `setup` tests.

SCOPE RULES — DO NOT:
- Do not touch anything already implemented and audited in Prompt A
  beyond what's needed to integrate with it.
- Do not fix `cmd_setup`'s behavior of never returning a failure exit
  code — only respect this existing behavior when writing the test, and
  report the finding in your deliverable.
- Do not `git commit` or `git push`.
- Do not modify
  `docs/planos/evolucao-notas-auditoria/04-cobertura-comandos-restantes.md`.

DELIVERABLE: exact list of test files created/changed; for each phase and
each tool, the command + real output that proves it; any divergence found
between `aidd-master` and `aidd-enterprise`; which TypeScript validation
path you took in Phase 5 and why; any necessary deviation, explicitly
reported instead of decided by yourself.
```

---

## Veredito — Auditoria dos Prompts A e B

**Auditoria independente realizada nos dois prompts — não me baseei no relatório do agente executor em nenhum dos dois.**

**Prompt A (audit, plan/apply, compose-orca, bench) — aprovado sem ressalvas.** Reproduzi ao vivo, fora do arquivo de teste do executor: compus um projeto independente e rodei `cmd_audit` (exit 0, 7 gates — 6 + `G_SEGURANCA`); rodei `cmd_compose_orca` com nome de módulo malformado (`inv"alid`) e confirmei exit 1 real (minha primeira tentativa com um nome "malicioso" diferente não quebrou nada — só confirma que o nome específico do executor foi escolhido com cuidado, não por acaso). Confirmei via `diff` que `cmd_plan`, `cmd_apply`, `cmd_compose_orca` e `cmd_bench` são byte-idênticos entre `aidd-master` e `aidd-enterprise` — por isso os testes quase idênticos nas duas ferramentas são reaproveitamento legítimo, não cópia cega sem verificação. Sem regressão (aidd-master 195→206, aidd-enterprise 199→210), sem poluição de repositório (`git status` limpo após rodar as suítes 2x), `ecossistema.py audit` 6/6 gates.

**Prompt B (export-frontend, refine-module, setup) — aprovado sem ressalvas.** Reproduzi ao vivo, de forma independente: compus meu próprio projeto e escrevi meus próprios cenários BDD para `refine-module`, confirmando sucesso real (`behave` executa de verdade, "1 feature passed") e falha real (exit 1 com cenário quebrado de propósito). Confirmei que `tsc` real não está disponível nesta máquina (só `npx` sem cache local, precisaria buscar da rede) — a validação estrutural de TypeScript (balanceamento de delimitadores via lexer que ignora strings/comentários) é uma escolha justificada, não um atalho preguiçoso. O teste de `setup` isola corretamente só a chamada de `pip install` (mock por padrão de comando), deixando o diagnóstico real (Git/ORCA/Fleet Discovery) rodar de verdade, e respeita o comportamento documentado de `cmd_setup` nunca retornar exit code de falha. Confirmei via `diff` que `cmd_export_frontend`, `cmd_refine_module`, `cmd_setup` e `openapi_to_ts.py` também são praticamente idênticos entre as duas ferramentas. Sem regressão (aidd-master 206→215, aidd-enterprise 210→219), sem poluição, `ecossistema.py audit` 6/6 gates.

**Notável:** as duas rodadas foram aprovadas **sem nenhuma correção necessária** — diferente do Pacote 7, que precisou de 3 rodadas corretivas para achados reais. Isso é o primeiro pacote desta série de evolução de notas a fechar de primeira em ambas as fases.

### Nota Final — Pacote 4 (Cobertura dos Comandos Restantes): 9.5/10

**Por que 9.5, não 10:**
- Os 7 comandos (`audit`, `plan`, `apply`, `compose-orca`, `refine-module`, `bench`, `export-frontend`, `setup`) agora têm teste real (subprocess ou chamada direta, nunca mock do comportamento central, exceto a única exceção explícita e justificada de `pip install` em `setup`) nas 2 ferramentas afetadas — cobrindo tanto o caminho de sucesso quanto o de falha/fallback para cada um.
- Reproduzi eu mesmo, de forma independente e fora dos arquivos de teste do executor, os casos de maior risco (`audit`, `compose-orca`, `refine-module` — sucesso e falha) e confirmei que são genuínos, não coincidências nem testes fracos.
- Zero regressão em 2 rodadas, zero poluição de repositório, zero desvio de escopo.
- **0.5 de desconto:** não reproduzi manualmente cada um dos 20 cenários de teste (verifiquei uma amostra representativa de alto risco + rodei as suítes completas, que já são subprocess-based, não mockadas); e o achado documentado (`cmd_setup` nunca retorna exit code de falha) continua sem correção — decisão deliberada e correta de escopo, mas é uma lacuna de transparência que permanece real no produto, não neste pacote de testes.
- **Efeito na dimensão Testabilidade/Cobertura Real:** esta dimensão já havia sido marcada 6→9/10 (alvo atingido) pelo Pacote 2, mas a Fase 4 do plano original de evolução (este pacote) fazia parte do mesmo gap de cobertura ("8 de 17 comandos sem teste"). Este pacote fecha definitivamente essa lacuna remanescente — a nota da dimensão permanece 9/10 (era o teto já perseguido, não havia meta de 10/10 registrada para ela), agora com evidência completa em vez de parcial.
