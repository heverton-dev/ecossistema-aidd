# Pacote 2 — Testabilidade + Determinismo

> **Status:** Diagnóstico concluído — Definição de Pronto abaixo aguardando sua aprovação antes de qualquer implementação.
> **Gap original coberto:** cobertura real de `add_module.py` (mesma classe de risco do `compose_suite.py`, já corrigida no ciclo de auditoria anterior).

---

## Diagnóstico

O plano original (`PLANO-EVOLUCAO-NOTAS-AUDITORIA.md`, Fase 2) partiu de uma suspeita: `add_module.py` tem o mesmo ponto cego de teste que `compose_suite.py` tinha antes de eu achar o `SyntaxError` real nele — um teste existe (`test_modulo1.py`), mas testa um módulo **já gerado e commitado**, nunca chama `add_module.py` de verdade. O plano presumia que, uma vez com um teste real, tudo funcionaria — e listava como um dos critérios a confirmar: *"Rotas do módulo novo aparecem em `src/server.py` automaticamente"*.

Investiguei isso com um teste real, não uma leitura de código:

1. **Confirmado**: `tools/aidd-master/scripts/add_module.py` e `tools/aidd-enterprise/scripts/add_module.py` são byte-a-byte idênticos (600 linhas) — mesmo risco, mesma correção serve para os dois.
2. **Confirmado**: `add_module.py` compila sem `SyntaxError` (`ast.parse` limpo) — não é o mesmo bug do `compose_suite.py`.
3. **Confirmado, e mais grave do que o plano supunha**: regenerei `modulo1` (o módulo fixture commitado que `test_modulo1.py` testa) com o `add_module.py` atual e comparei com o que está commitado — `models.py` diverge (mesmo comportamento, código reordenado). Isso prova, com evidência concreta, exatamente a suspeita do plano: **o teste existente nunca roda o gerador atual, testa uma foto congelada de uma versão antiga dele.**
4. **Achado novo, não previsto pelo plano original**: montei um projeto real do zero (`aidd-master compose ... crm`), rodei `add_module.py faturamento` dentro dele, subi o servidor gerado (`python src/server.py`) e testei as duas rotas com `curl`:
   - `GET /api/crm` (módulo composto na criação) → **200 OK**
   - `GET /api/faturamento` (módulo adicionado depois via `add_module.py`) → **404 Not Found**

   Causa raiz: `add_module.py` **nunca toca em `src/server.py`**. Confirmei isso lendo o arquivo inteiro (600 linhas) e via `grep` — zero menção a `server.py`. `server.py` não faz descoberta dinâmica de módulos (`templates/core/server.py`/`templates/v2/server.py` idênticos entre as duas ferramentas, sem `importlib`/`scandir` de `modules/`) — ele é gerado **estaticamente**, uma única vez, no momento do `compose`, pela função `generate_modular_server_code(suite_name, module_slugs, db_engine)` em `compose_suite.py`, iterando sobre a lista de módulos **daquele momento**. Qualquer módulo adicionado depois via `add_module.py` fica com código real, testes próprios passando isoladamente, e até uma entrada "implementado" no manifesto — mas é **inalcançável via HTTP**. O manifesto, inclusive, mente sobre isso: marca `"status": "implementado"` para um módulo que não está de fato servido.

   Isso significa que a funcionalidade mais anunciada do produto ("Suíte Modular com Fatias Verticais" — adicionar um módulo depois de já ter uma suíte rodando) **não entrega o que promete**, hoje, para os dois tools. Não é um problema de falta de teste — é um bug funcional real, só que meu **primeiro instinto de diagnóstico (regex/leitura) não o revelou; só apareceu ao rodar o fluxo completo de ponta a ponta com um servidor real e uma requisição HTTP real**, exatamente o tipo de coisa que "parece certo" mas não é.

5. **Verifiquei a viabilidade do conserto antes de propor a Definição de Pronto** (para não travar um DoD que se prove inviável na implementação, como quase aconteceu no Pacote 1): `generate_modular_server_code()` já é uma função top-level, testada e usada há muito, que recebe `suite_name`, `module_slugs` (lista completa) e `db_engine`, e devolve o texto completo do `server.py`. `add_module.py` pode reconstruir a lista completa de módulos lendo `PLANO-EXECUCAO-ESTRUTURADO.json["modulos"]` (confirmei que essa lista já contém corretamente os módulos compostos na criação, não só os adicionados depois) e somando o novo slug. **Mas `db_engine` não é persistido em lugar nenhum do manifesto** — se eu simplesmente regenerar `server.py` chamando essa função com o default `"sqlite"`, uma suíte composta com `--db postgres` teria seu `server.py` silenciosamente revertido para sqlite na primeira vez que alguém rodasse `add_module.py`. Confirmado via `grep` em `compose_suite.py`: `db_engine` só existe como parâmetro de função em tempo de composição, nunca é escrito no `PLANO-EXECUCAO-ESTRUTURADO.json`.

---

## Definição de Pronto

1. **Persistir `db_engine` no manifesto**: `compose_suite.py` passa a gravar `plano_dict["projeto"]["db_engine"] = db_engine` no momento da composição, nas duas ferramentas (`aidd-master`, `aidd-enterprise` — arquivos idênticos, mesma mudança nos dois).

2. **`add_module.py` passa a regenerar `src/server.py` de verdade**, reutilizando `generate_modular_server_code()` (não texto duplicado, não patch frágil por regex): lê `PLANO-EXECUCAO-ESTRUTURADO.json` para obter `suite_name` (`projeto.nome`), `db_engine` (`projeto.db_engine`, com fallback `"sqlite"` só para manifestos antigos que ainda não tinham o campo) e a lista de módulos já existentes (`modulos[].slug`), soma o slug novo, chama `generate_modular_server_code(...)` com a lista completa, e sobrescreve `src/server.py`. Aplicado nas duas ferramentas.

3. **Teste real de ponta a ponta, não leitura de código** — mesmo padrão do `test_compose_suite.py`: compor uma suíte de verdade (`compose` com 1 módulo inicial), chamar `add_module.py` para adicionar um segundo módulo, subir `src/server.py` via subprocess, e confirmar via requisição HTTP real que **ambos** os módulos (o inicial e o adicionado depois) respondem 200 em suas rotas. Este teste precisa **falhar no estado atual do código** (antes da correção) e **passar depois** — reprodução real da regressão, igual ao que foi feito no Pacote 1.

4. **Teste de regressão do `db_engine`**: compor uma suíte com `--db postgres`, chamar `add_module.py`, e confirmar que o `server.py` regenerado ainda referencia postgres (não reverteu para sqlite silenciosamente).

5. **`test_modulo1.py` deixa de testar uma fixture congelada**: substituir (ou complementar) por um teste que gera o módulo dinamicamente via `add_module.py` em um diretório temporário, igual ao padrão novo do item 3 — para que qualquer edição futura em `add_module.py` seja imediatamente pega por teste, e não só na próxima vez que alguém notar a divergência manualmente (como eu fiz nesta investigação).

6. **Replicar tudo nas duas ferramentas** (`aidd-master`, `aidd-enterprise`) — mesmo padrão de risco compartilhado, mesma correção, confirmado que os arquivos-fonte (`add_module.py`, `compose_suite.py`, `templates/core/server.py`, `templates/v2/server.py`) são hoje byte-a-byte idênticos entre as duas.

7. **Zero regressão**: suítes completas das 4 ferramentas + os 5 gates da raiz continuam 100% verdes depois da mudança.

8. **Nota — só sobe com verificação genuína**: "Testabilidade / Cobertura Real" (6→9 alvo) e "Determinismo Primeiro" (9→9.5 alvo) só avançam na medida do que for realmente comprovado pelos testes acima — nenhuma inflação antecipada nesta Definição de Pronto.

---

## Observação sobre o escopo real deste pacote

O plano original estimava este pacote como "escrever o teste que faltava". A investigação real mudou isso: o teste que faltava, ao ser escrito de verdade (rodando o fluxo completo, não só lendo código), revelou que a funcionalidade em si tem um bug — não é mais "só" testabilidade, é testabilidade **e** um bug funcional real na Fatia Vertical adicionada por `add_module.py`. Isso segue o mesmo padrão já visto no `compose_suite.py`: o teste ausente escondia o bug, não o contrário. A Definição de Pronto acima já reflete esse escopo corrigido — inclui o conserto, não só o teste.

---

## Prompt de Implementação (para o agente executor)

> Copie o bloco abaixo integralmente para o agente que vai executar. Ele é autocontido — não pressupõe que o agente executor tenha visto esta conversa.

```
Você vai corrigir um bug real e comprovado no ecossistema-aidd (monorepo em
C:\Users\trcnologia\Desktop\ecossistema-aidd), nas ferramentas aidd-master e
aidd-enterprise. Este é um pacote de trabalho dentro de um processo maior de
evolução de qualidade do projeto — siga EXATAMENTE a Definição de Pronto
abaixo, não invente escopo adicional, e valide tudo de verdade (execuções
reais, exit codes reais — nunca mascarados por pipe) antes de reportar
qualquer item como concluído.

CONTEXTO DO BUG (já investigado e comprovado, não precisa redescobrir):

`add_module.py` (idêntico, byte-a-byte, em
tools/aidd-master/scripts/add_module.py e
tools/aidd-enterprise/scripts/add_module.py) gera uma "fatia vertical"
completa (models.py, services.py, routes.py, teste, componente UI) para um
módulo novo dentro de um projeto já composto — mas NUNCA atualiza
`src/server.py` do projeto gerado. `src/server.py` é gerado de forma
ESTÁTICA, uma única vez, no momento do `compose`, pela função
`generate_modular_server_code(suite_name, module_slugs, db_engine)` definida
em `scripts/compose_suite.py` (idêntica nas duas ferramentas) — ele NÃO faz
descoberta dinâmica de módulos em tempo de execução.

Prova reproduzível do bug (faça isso primeiro, para confirmar o estado atual
antes de corrigir):
1. `cd tools/aidd-master && python scripts/aidd.py compose <dir_temp> "Teste" crm`
2. `cd <dir_temp> && python scripts/add_module.py faturamento`
3. Suba o servidor gerado: `python src/server.py` (porta default 3000,
   tenta 3000-3025 se ocupada — leia o output pra saber a porta real)
4. `curl http://localhost:<porta>/api/crm` → deve responder 200
5. `curl http://localhost:<porta>/api/faturamento` → hoje responde 404
   (bug). Depois da sua correção, deve responder 200 também.

Além disso, `db_engine` (sqlite/postgres, escolhido no momento do `compose`)
NUNCA é persistido no manifesto `PLANO-EXECUCAO-ESTRUTURADO.json` — só existe
como parâmetro de função em tempo de composição. Isso importa porque a
correção abaixo precisa regenerar `server.py`, e sem saber o `db_engine`
original ela reverteria silenciosamente uma suíte Postgres para SQLite.

DEFINIÇÃO DE PRONTO — implemente cada item, nesta ordem, nas DUAS
ferramentas (tools/aidd-master e tools/aidd-enterprise — os arquivos-fonte
relevantes são hoje idênticos entre as duas, então a mesma mudança se aplica
igual nas duas, sem acoplamento de runtime entre elas):

1. Em `scripts/compose_suite.py`, na função `compose_suite()`, ao montar
   `plano_dict`, adicione `plano_dict["projeto"]["db_engine"] = db_engine`
   (grava o motor de persistência escolhido no manifesto).

2. Em `scripts/add_module.py`, na função `criar_modulo()`, DEPOIS de
   atualizar `plano["modulos"]` com o módulo novo, regenere
   `src/server.py`:
   - Importe `generate_modular_server_code` de `compose_suite.py` (mesmo
     diretório — use import relativo/absoluto conforme o padrão já usado
     no arquivo para importar outras funções entre scripts irmãos).
   - Leia `suite_name` de `plano["projeto"]["nome"]`.
   - Leia `db_engine` de `plano["projeto"].get("db_engine", "sqlite")`
     (fallback só para manifestos antigos que ainda não tinham o campo).
   - Monte a lista completa de slugs de módulos a partir de
     `plano["modulos"]` (que já inclui os módulos compostos na criação E os
     adicionados depois — confirme isso lendo o manifesto de um projeto
     testado) SOMANDO o slug do módulo que acabou de ser criado nesta
     chamada (ele só é adicionado à lista do manifesto durante esta mesma
     execução — garanta que o slug novo entre na lista antes de chamar
     `generate_modular_server_code`).
   - Chame `generate_modular_server_code(suite_name, lista_completa_slugs,
     db_engine=db_engine)` e sobrescreva `src/server.py` com o resultado.
   - Isso só deve rodar quando `add_module.py` está sendo chamado dentro de
     um projeto JÁ COMPOSTO (ou seja, quando o manifesto e `src/server.py`
     já existem) — não quebre o uso de `add_module.py` chamado internamente
     por `compose_suite()` durante a composição inicial (aquele já gera o
     `server.py` completo depois, no próprio `compose_suite`; regenerar de
     novo ali não deveria causar erro, mas evite trabalho duplicado
     desnecessário se der pra distinguir os dois casos com uma checagem
     simples, tipo "já existe src/server.py no destino").

3. Escreva um teste de ponta a ponta REAL (não mock, não leitura de
   código) — sugestão de nome:
   `tools/aidd-master/tests/integration/test_add_module_server_wiring.py`
   (e o equivalente em aidd-enterprise). O teste deve, usando `tmp_path` e
   `subprocess`:
   a. Compor uma suíte real com 1 módulo inicial.
   b. Chamar `add_module.py` para adicionar um segundo módulo.
   c. Subir `src/server.py` via `subprocess.Popen` (mesmo padrão usado em
      `tests/unit/test_compose_suite.py`, que já sobe um servidor gerado
      via subprocess e bate num endpoint real — siga esse padrão).
   d. Fazer requisição HTTP real (biblioteca `requests` ou
      `urllib.request`) contra a rota do módulo INICIAL e contra a rota do
      módulo ADICIONADO DEPOIS. Ambas precisam responder 200.
   e. Encerrar o processo do servidor ao final (sempre, mesmo se o teste
      falhar — use try/finally ou fixture com yield).

   ANTES de aplicar a correção do item 2, rode este teste novo e confirme
   que ele FALHA (a rota do módulo adicionado depois responde 404 ou dá
   erro de conexão) — isso prova que o teste realmente pega o bug. DEPOIS
   de aplicar a correção, rode de novo e confirme que passa. Reporte os
   dois resultados (falha antes / sucesso depois) como evidência, com o
   output real do pytest.

4. Escreva um teste de regressão para o `db_engine`: compor uma suíte com
   `db_engine="postgres"`, chamar `add_module.py`, e confirmar (lendo o
   `src/server.py` regenerado, ex. via grep/assert em string) que ele ainda
   referencia postgres, não sqlite.

5. `tools/aidd-master/tests/unit/test_modulo1.py` (e o equivalente em
   aidd-enterprise) hoje testa uma fixture `src/modules/modulo1/` commitada
   estaticamente, gerada por uma versão ANTIGA de `add_module.py` (já
   diverge do que o gerador produz hoje — reordenação de código em
   `models.py`, comportamento equivalente mas prova que o teste não
   exercita o gerador atual). Substitua por (ou complemente com) um teste
   que gera o módulo dinamicamente chamando `add_module.py` num diretório
   temporário, para que qualquer edição futura no gerador seja pega
   automaticamente.

6. Rode e cole o resultado real (não resuma, não trunque exit codes) de:
   - `cd tools/aidd-master && python -m pytest tests/ -q`
   - `cd tools/aidd-enterprise && python -m pytest tests/ -q`
   - `cd tools/aidd-generator && python -m pytest tests/ -q`
   - `cd tools/aidd-forge && python -m pytest tests/ -q`
   - `python ecossistema.py audit` (na raiz do monorepo)
   Todos precisam passar (exit code 0) — nenhuma regressão é aceitável.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não toque em nenhum outro arquivo além dos listados acima.
- Não invente abstrações além do necessário (ex.: não crie um sistema de
  plugins genérico — a correção é regenerar server.py reaproveitando
  `generate_modular_server_code`, que já existe e já é testado).
- Não faça `git commit` nem `git push` — isso fica para depois da auditoria.
- Não altere `docs/planos/evolucao-notas-auditoria/02-testabilidade-e-determinismo.md`
  (quem preenche o Veredito final é quem audita depois).

ENTREGÁVEL ESPERADO (seu relatório final, em texto):
- Lista exata de arquivos modificados/criados.
- Para cada item da Definição de Pronto acima: o que foi feito, e o
  comando + output real que comprova (não "deveria funcionar" — output de
  verdade, incluindo o teste falhando ANTES da correção do item 2 e
  passando DEPOIS).
- Resultado das 4 suítes completas + `ecossistema.py audit` (item 6),
  colado integralmente, não resumido.
- Qualquer desvio da Definição de Pronto que você precisou fazer, e por quê
  (se encontrar motivo para desviar, PARE e relate em vez de decidir
  sozinho por uma mudança de escopo maior).
```

### English version (same prompt, for executor agents that work better in English)

```
You are going to fix a real, already-confirmed bug in the ecossistema-aidd
monorepo (C:\Users\trcnologia\Desktop\ecossistema-aidd), in the aidd-master
and aidd-enterprise tools. This is one work package inside a larger quality
evolution process for this project — follow the Definition of Done below
EXACTLY, do not invent additional scope, and validate everything for real
(real command runs, real exit codes — never masked by a pipe) before
reporting any item as complete.

CONFIRMED BUG CONTEXT (already investigated and proven, no need to
rediscover it):

`add_module.py` (byte-for-byte identical in
tools/aidd-master/scripts/add_module.py and
tools/aidd-enterprise/scripts/add_module.py) generates a complete "vertical
slice" (models.py, services.py, routes.py, test file, UI component) for a
new module inside an already-composed project — but it NEVER updates the
generated project's `src/server.py`. `src/server.py` is generated
STATICALLY, once, at `compose` time, by the function
`generate_modular_server_code(suite_name, module_slugs, db_engine)` defined
in `scripts/compose_suite.py` (identical in both tools) — it does NOT do
any dynamic module discovery at runtime.

Reproducible proof of the bug (do this first, to confirm the current state
before fixing anything):
1. `cd tools/aidd-master && python scripts/aidd.py compose <temp_dir> "Test" crm`
2. `cd <temp_dir> && python scripts/add_module.py billing`
3. Start the generated server: `python src/server.py` (default port 3000,
   tries 3000-3025 if busy — read the output to get the real port)
4. `curl http://localhost:<port>/api/crm` → should respond 200
5. `curl http://localhost:<port>/api/billing` → today responds 404 (bug).
   After your fix, it must respond 200 as well.

Additionally, `db_engine` (sqlite/postgres, chosen at `compose` time) is
NEVER persisted in the `PLANO-EXECUCAO-ESTRUTURADO.json` manifest — it only
exists as a function parameter at composition time. This matters because
the fix below needs to regenerate `server.py`, and without knowing the
original `db_engine` it would silently revert a Postgres suite back to
SQLite.

DEFINITION OF DONE — implement each item, in this order, in BOTH tools
(tools/aidd-master and tools/aidd-enterprise — the relevant source files
are byte-for-byte identical between the two today, so the same change
applies equally to both, with no runtime coupling between them):

1. In `scripts/compose_suite.py`, inside the `compose_suite()` function,
   when building `plano_dict`, add
   `plano_dict["projeto"]["db_engine"] = db_engine` (persists the chosen
   persistence engine in the manifest).

2. In `scripts/add_module.py`, inside the `criar_modulo()` function, AFTER
   updating `plano["modulos"]` with the new module, regenerate
   `src/server.py`:
   - Import `generate_modular_server_code` from `compose_suite.py` (same
     directory — follow whatever import pattern the file already uses to
     import functions between sibling scripts).
   - Read `suite_name` from `plano["projeto"]["nome"]`.
   - Read `db_engine` from `plano["projeto"].get("db_engine", "sqlite")`
     (fallback only for older manifests that don't have the field yet).
   - Build the full list of module slugs from `plano["modulos"]` (which
     already includes both the modules composed at creation time AND the
     ones added later — confirm this by reading the manifest of a real
     test project) PLUS the slug of the module that was just created in
     this call (it is only added to the manifest's list during this same
     execution — make sure the new slug is included before calling
     `generate_modular_server_code`).
   - Call `generate_modular_server_code(suite_name, full_slug_list,
     db_engine=db_engine)` and overwrite `src/server.py` with the result.
   - This should only run when `add_module.py` is being called inside an
     ALREADY-COMPOSED project (i.e., when the manifest and `src/server.py`
     already exist) — don't break the internal use of `add_module.py` that
     `compose_suite()` itself calls during initial composition (that path
     already generates the full `server.py` afterward, inside
     `compose_suite` itself; regenerating it again there shouldn't cause
     an error, but avoid unnecessary duplicate work if you can cleanly
     distinguish the two cases, e.g. "does `src/server.py` already exist
     in the target").

3. Write a REAL end-to-end test (no mocks, no code reading) — suggested
   name: `tools/aidd-master/tests/integration/test_add_module_server_wiring.py`
   (and the equivalent in aidd-enterprise). The test should, using
   `tmp_path` and `subprocess`:
   a. Compose a real suite with 1 initial module.
   b. Call `add_module.py` to add a second module.
   c. Start `src/server.py` via `subprocess.Popen` (same pattern already
      used in `tests/unit/test_compose_suite.py`, which already starts a
      generated server via subprocess and hits a real endpoint — follow
      that pattern).
   d. Make a real HTTP request (`requests` library or `urllib.request`)
      against the route of the INITIAL module and against the route of the
      module ADDED AFTERWARD. Both must respond 200.
   e. Always terminate the server process at the end, even if the test
      fails (use try/finally or a fixture with yield).

   BEFORE applying the fix from item 2, run this new test and confirm it
   FAILS (the route of the module added afterward responds 404 or a
   connection error) — this proves the test actually catches the bug.
   AFTER applying the fix, run it again and confirm it passes. Report both
   results (failing before / passing after) as evidence, with the real
   pytest output.

4. Write a regression test for `db_engine`: compose a suite with
   `db_engine="postgres"`, call `add_module.py`, and confirm (by reading
   the regenerated `src/server.py`, e.g. via a grep/string assertion) that
   it still references postgres, not sqlite.

5. `tools/aidd-master/tests/unit/test_modulo1.py` (and the equivalent in
   aidd-enterprise) today tests a statically committed
   `src/modules/modulo1/` fixture, generated by an OLD version of
   `add_module.py` (it already diverges from what the generator produces
   today — reordered code in `models.py`, equivalent behavior, but proof
   that the test doesn't exercise the current generator). Replace it with
   (or complement it with) a test that dynamically generates the module by
   calling `add_module.py` into a temporary directory, so that any future
   edit to the generator gets caught automatically.

6. Run and paste the real output (do not summarize, do not truncate exit
   codes) of:
   - `cd tools/aidd-master && python -m pytest tests/ -q`
   - `cd tools/aidd-enterprise && python -m pytest tests/ -q`
   - `cd tools/aidd-generator && python -m pytest tests/ -q`
   - `cd tools/aidd-forge && python -m pytest tests/ -q`
   - `python ecossistema.py audit` (at the monorepo root)
   All of them must pass (exit code 0) — no regression is acceptable.

SCOPE RULES — DO NOT:
- Do not touch any file other than the ones listed above.
- Do not invent abstractions beyond what's needed (e.g., do not build a
  generic plugin system — the fix is to regenerate server.py by reusing
  `generate_modular_server_code`, which already exists and is already
  tested).
- Do not `git commit` or `git push` — that happens after the audit.
- Do not modify
  `docs/planos/evolucao-notas-auditoria/02-testabilidade-e-determinismo.md`
  (whoever fills in the final Verdict is whoever audits afterward).

EXPECTED DELIVERABLE (your final report, in text):
- Exact list of files modified/created.
- For each item in the Definition of Done above: what was done, and the
  command + real output that proves it (not "should work" — actual output,
  including the test failing BEFORE the item 2 fix and passing AFTER).
- Full result of the 4 complete test suites + `ecossistema.py audit`
  (item 6), pasted in full, not summarized.
- Any deviation from the Definition of Done you had to make, and why (if
  you find a reason to deviate, STOP and report it instead of deciding on a
  larger scope change by yourself).
```

---

## Veredito

**Auditoria independente realizada — não me baseei no relatório do agente executor, reproduzi tudo eu mesmo.**

**Implementação (itens 1-6 da DoD), verificada arquivo por arquivo:**
1. `plano_dict["projeto"]["db_engine"] = db_engine` adicionado em `compose_suite()` — confirmado idêntico em `aidd-master` e `aidd-enterprise` via `diff`.
2. `add_module.py` regenera `src/server.py` reaproveitando `generate_modular_server_code()` — lida corretamente com o caso "chamado durante o `compose` inicial" (server.py ainda não existe, então pula) vs. "chamado depois, num projeto já composto" (regenera). Lê `suite_name`/`db_engine`/lista completa de slugs do manifesto, soma o slug novo. Confirmado idêntico (`diff`) entre as duas ferramentas.
3. Teste `tests/integration/test_add_module_server_wiring.py` (novo, nas duas ferramentas) — **reproduzi a prova eu mesmo**: revertei a correção (`git stash`) dos itens 1-2, rodei o teste → **falhou** (exatamente como esperado, prova que não é um teste tautológico). Restaurei a correção → voltou a passar. Isso fecha o item mais importante da Definição de Pronto: o teste realmente pega o bug.
4. Teste de regressão do `db_engine` (postgres) — confirmei que as strings verificadas (`"postgresql://"` e a ausência de `DB_PATH = os.path.join(CURRENT_DIR, "..", "suite.db")`) batem exatamente com os dois ramos reais de `generate_modular_server_code()` — não é uma asserção vazia.
5. `test_modulo1.py` — o agente optou por **complementar** (manteve os testes da fixture estática e acrescentou um teste que gera o módulo com o gerador atual, sobe o servidor real e faz CRUD via HTTP) em vez de substituir — opção explicitamente permitida pela DoD. Bom design: não sobrepõe o teste do item 3 (aquele testa "módulo adicionado depois"; este testa "o gerador atual produz um módulo funcional", usando `compose_suite(["itemdinamico"])`).
6. Zero regressão confirmada por mim, execuções reais: `aidd-master` 194 passed/4 skipped; `aidd-enterprise` 199 passed/4 skipped; `aidd-generator` 756 passed; `aidd-forge` 191 passed/1 skipped; `python ecossistema.py audit` (raiz) → 5/5 gates aprovados. Também confirmei que o agente **não commitou nem fez push** (`git log` idêntico a `origin/main`), respeitando a regra do prompt.

**Defeitos menores encontrados (não bloqueiam o pacote, registrados para não se perder):**
- Os `subprocess.run(..., capture_output=True, text=True)` nos testes novos não especificam `encoding`/`errors`, e no Windows isso usa o codepage do console (cp1252) para decodificar a saída do processo filho — que imprime emojis/acentos em UTF-8. Isso gera `UnicodeDecodeError` numa thread de leitura em segundo plano (`PytestUnhandledThreadExceptionWarning`) em pelo menos 2 dos novos testes. Não derruba o teste hoje (o erro fica isolado na thread de captura), mas é frágil — o padrão já usado no resto do projeto é `encoding='utf-8', errors='replace'` (ver `sys.stdout.reconfigure` nos próprios scripts). Recomendo aplicar o mesmo padrão nos `subprocess.run`/`Popen` dos novos testes numa próxima passada.
- Porta do servidor hardcoded em `3000` nos testes novos, em vez de ler a porta real do output do servidor (que tenta 3000-3025 se 3000 estiver ocupada, conforme o próprio `server.py`). Risco baixo de teste instável (flaky) se a porta 3000 estiver ocupada por outro processo na máquina/CI no momento da execução.

**Achado fora do escopo pedido — requer sua confirmação antes do commit:**
Apareceram 2 arquivos novos, não relacionados a este pacote, não previstos na Definição de Pronto nem no prompt enviado ao agente: `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` e `docs/relatorios/relatorio-skills-e-comandos-aidd.html` (diagnóstico sobre skills não serem descobertas igualmente por todos os harnesses). O próprio documento afirma ter sido feito "por pedido explícito do usuário" e que nenhuma correção foi aplicada, só diagnóstico — mas isso não fazia parte do que pedi nesta Definição de Pronto. Preciso que você confirme se foi um pedido seu à parte (nesse caso, ficam como um novo item a tratar depois) antes de eu incluir ou não esses dois arquivos no commit deste pacote.

**Nota — antes → depois:**
- **Testabilidade / Cobertura Real: 6/10 → 9/10 (alvo atingido).** O ponto cego real (`add_module.py` nunca testado de ponta a ponta, e o bug que isso escondia) está fechado e comprovado por reprodução independente.
- **Determinismo Primeiro: 9/10 → 9.5/10 (alvo atingido).** `add_module.py` agora produz um resultado determinístico e correto (módulo sempre alcançável via HTTP), e o `db_engine` deixa de ser uma informação perdida entre a composição e qualquer operação futura sobre o projeto.

**Pendente antes de comitar:** sua resposta sobre os 2 arquivos fora de escopo (item acima).
