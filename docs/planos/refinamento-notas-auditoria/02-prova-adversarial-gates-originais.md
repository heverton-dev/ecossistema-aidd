# Item 3 — Prova Adversarial dos Gates Originais: `G_ECOSSISTEMA_INTEGRIDADE` e `G_SEGREDOS`

> **Status:** ✅ CONCLUÍDO em 05/09/2026 — nota final 10/10 (ver Veredito ao final do documento).
> **Origem:** pergunta do usuário — "podemos superar o 10, sem fabricação?" — aplicada à dimensão Gates Mecânicos (hoje 8/10).
> **Contribui para:** Gates Mecânicos.

---

## As 4 perguntas de rigor, respondidas antes de propor qualquer trabalho

1. **É necessário?** — Sim. `gates/G_ECOSSISTEMA_INTEGRIDADE.py` e `gates/G_SEGREDOS.py` são 2 dos 6 gates que `ecossistema.py audit` roda na raiz do meta-repositório, mas nenhum teste em todo o repositório os exercita (confirmei via grep, zero resultado). Os outros 4 gates da mesma lista já têm prova: `G_DRIFT_NUCLEO_COMPARTILHADO` (`tools/aidd-master/tests/unit/test_drift_gate_blind_spot.py`, achado da rodada 1) e `G_CLI_HELP_CONSISTENCIA` (`gates/test_g_cli_help_consistencia.py`, Pacote 1 da rodada 1) têm testes reais de sucesso e falha. `G_HARNESS_COMPAT` e `G_COMPONENTE_AGNOSTICO` (variantes de raiz, distintas dos templates por-projeto do mesmo nome) também não têm teste — acho isso digno de registro, mas fica **fora do escopo deste item**, que é especificamente os 2 gates citados no plano central (`00-PROCESSO-E-DECISOES.md §3`); não vou expandir escopo sem aprovação sua.
2. **É possível?** — Sim, e **já validei a estratégia de teste com reprodução real antes de propor** (não só teorizei): copiar o script do gate de verdade para dentro de uma árvore sintética temporária e rodar via subprocess — como `ROOT_DIR` de cada gate é calculado a partir de `__file__` (não é parâmetro), isso faz o próprio gate real "pensar" que a árvore sintética é a raiz do ecossistema, sem precisar de monkeypatch nem reimplementar nada. Testei os 2 casos (sucesso e falha) nos 2 gates agora mesmo — ver evidência abaixo.
3. **É real?** — Sim: os testes abaixo já foram rodados por mim, de verdade, antes de escrever esta Definição de Pronto.
4. **Traz ganho real?** — Sim: sem esses testes, uma regressão em qualquer um dos 2 gates originais (ex.: alguém "simplifica" a lógica e ela para de detectar um `.git` vazado ou uma chave AWS hardcoded) passaria despercebida — exatamente o tipo de ponto cego que a Rodada 1 já achou em outros gates (drift, cli-help).

---

## Diagnóstico

### Confirmado: zero teste referencia os 2 gates, em todo o repositório

```
grep -rn "gates.*G_ECOSSISTEMA_INTEGRIDADE|gates.*G_SEGREDOS" **/test_*.py
→ nenhum resultado
```

### Estratégia de teste validada com reprodução real (não hipotética)

Ambos os gates calculam `ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` — ou seja, a raiz é sempre "duas pastas acima de onde o próprio script está", nunca um argumento. Isso permite testar o script REAL, sem cópia de lógica nem monkeypatch: basta copiar o arquivo `.py` do gate para dentro de `<tmp>/gates/` de uma árvore sintética e rodar `python <tmp>/gates/<gate>.py` via subprocess — o `ROOT_DIR` resolvido será `<tmp>`.

**`G_ECOSSISTEMA_INTEGRIDADE` — já reproduzi os 2 casos:**
- Construí uma árvore sintética 100% válida (AGENTS.md, .gitignore, 4 `tools/<x>/README.md`, 4 `skills/<x>-runner/SKILL.md` com frontmatter, 8 arquivos de comando em `.agent/commands/` e `.claude/commands/`) → copiei o gate real pra lá → `python gates/G_ECOSSISTEMA_INTEGRIDADE.py` → **exit 0**, `[SUCESSO] ... APROVADO (100% OK)`.
- Removi só `tools/aidd-forge/README.md` dessa mesma árvore → rodei de novo → **exit 1**, mensagem exata `README.md ausente em tools/aidd-forge`.

**`G_SEGREDOS` — já reproduzi os 3 casos:**
- Repo git real (`git init`) com 1 arquivo limpo → **exit 0**, `0 achado(s) já catalogado(s)`.
- Adicionei `AWS_KEY = 'AKIAABCDEFGHIJKLMNOP'` (padrão AWS Access Key real do gate) e commitei → **exit 1**, achado citado exatamente: `arquivo_com_segredo.py: AWS Access Key ID (AKIA...) (AKIAABCDEFGHIJKLMNOP...)`.
- Catalogando esse mesmo arquivo em `gates/allowlist_segredos.json` → rodei de novo → **exit 0** (prova que o allowlist funciona, não é fabricação nem falso-negativo escondido).

### Achado lateral, fora de escopo deste item (registrado, não implementado agora)

`G_ECOSSISTEMA_INTEGRIDADE`'s checagem de sintaxe (item 5 do seu docstring, "Validação Sintática AST") só analisa 2 arquivos fixos e hardcoded (o próprio `gates/G_ECOSSISTEMA_INTEGRIDADE.py` e `ecossistema.py`) — nunca varre os scripts reais dentro de `tools/*/scripts/`. Ou seja, um erro de sintaxe em qualquer script de qualquer uma das 4 ferramentas não seria pego por este gate. Isso é uma lacuna de cobertura real do próprio gate (não um bug do teste que vou escrever) — mas expandir a checagem do gate está fora do escopo deste item (que é só provar o que o gate JÁ faz, não ampliar o que ele faz). Se quiser, posso abrir isso como um item novo depois.

---

## Definição de Pronto

**Fase 1 — Testes adversariais reais para os 2 gates, usando a técnica já validada (cópia real + subprocess, sem monkeypatch)**

Novos arquivos: `gates/test_g_ecossistema_integridade.py` e `gates/test_g_segredos.py` (mesmo padrão de localização de `gates/test_g_cli_help_consistencia.py`, já existente).

1.1. `test_g_ecossistema_integridade.py` — fixture que constrói uma árvore sintética válida em `tmp_path` (mesma composta no diagnóstico: AGENTS.md, .gitignore, 4 tools com README, 4 skills com frontmatter, 8 comandos, gate copiado para `<tmp>/gates/`) e roda via subprocess:
   - Teste de sucesso: árvore 100% válida → exit 0.
   - 1 teste de falha por categoria auditada pelo gate (mínimo 5, um por bullet do docstring do gate): `README.md` ausente em uma ferramenta; `.git` vazado dentro de uma pasta de ferramenta; `SKILL.md` sem frontmatter YAML válido; comando ausente em `.agent/commands` ou `.claude/commands`; `AGENTS.md` ausente na raiz. Cada teste de falha parte da árvore válida e quebra só UM aspecto, confirmando a mensagem de erro específica no stdout e exit code 1.
1.2. `test_g_segredos.py` — fixture que cria um repositório git real em `tmp_path` (`git init` de verdade, sem mock de subprocess) e roda o gate via subprocess:
   - Teste de sucesso: repo sem nenhum segredo → exit 0.
   - Teste de falha: pelo menos 2 padrões DIFERENTES de segredo (de `PADROES_SEGREDO`, ex.: AWS Access Key e token do GitHub, ou AWS e a atribuição genérica `api_key = "..."`) não catalogados → exit 1, achado citado no stdout.
   - Teste de allowlist: o mesmo segredo do teste anterior, agora catalogado em `allowlist_segredos.json` → exit 0 (prova que o allowlist é respeitado, não é bypass silencioso).
1.3. Nenhum teste deve tocar o `allowlist_segredos.json` real do repositório nem qualquer arquivo fora de `tmp_path`.

**Critério de saída (rodar e colar o output real de cada um):**
- `python -m pytest gates/ -q` (ou `python -m pytest` da raiz, que já usa `testpaths = gates` conforme `pytest.ini`) → sem regressão nos 8 testes já existentes de `G_CLI_HELP_CONSISTENCIA`, com os novos testes incluídos na contagem.
- Reprodução manual real (fora dos arquivos de teste) de pelo menos 1 caso de sucesso e 1 de falha por gate, output colado — mesmo padrão já demonstrado neste diagnóstico.
- `git status` limpo além dos 2 arquivos de teste novos.

**Regras de escopo — não fazer:**
- Não alterar a lógica dos gates (`G_ECOSSISTEMA_INTEGRIDADE.py`, `G_SEGREDOS.py`) — só adicionar os testes.
- Não expandir a checagem AST do `G_ECOSSISTEMA_INTEGRIDADE` para varrer `tools/*/scripts/` (achado lateral registrado acima, fora de escopo).
- Não tocar em `G_HARNESS_COMPAT`, `G_COMPONENTE_AGNOSTICO`, `G_DRIFT_NUCLEO_COMPARTILHADO` nem `G_CLI_HELP_CONSISTENCIA` — já cobertos ou fora de escopo.
- Não fazer `git commit` nem `git push`.
- Não alterar este documento.

---

## Ordem de execução

Item único, 1 fase, cabe em 1 prompt — mesmo padrão dos Itens 1 e 2.

**Aprovado pelo usuário em 05/09/2026.** Prompt de execução abaixo.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai fechar um gap real de prova adversarial em dois gates
mecânicos na raiz do monorepo em
C:\Users\trcnologia\Desktop\ecossistema-aidd: gates/G_ECOSSISTEMA_INTEGRIDADE.py
e gates/G_SEGREDOS.py. Esses são 2 dos 6 gates que `ecossistema.py audit`
roda contra a raiz do ecossistema, mas nenhum teste em todo o
repositório os exercita hoje (confirmado via grep, zero resultado). Os
outros 4 gates da mesma lista (G_DRIFT_NUCLEO_COMPARTILHADO,
G_HARNESS_COMPAT, G_CLI_HELP_CONSISTENCIA, G_COMPONENTE_AGNOSTICO) NÃO
fazem parte deste trabalho. Siga EXATAMENTE a Definição de Pronto
abaixo, não invente escopo adicional, e valide tudo de verdade
(execuções reais via subprocess, nunca mascaradas por pipe).

IMPORTANTE — o que este prompt NÃO pede: não mude a lógica de nenhum
dos 2 gates. Não expanda a checagem AST do G_ECOSSISTEMA_INTEGRIDADE
para varrer tools/*/scripts/ (ela hoje só varre 2 arquivos fixos — o
próprio gate e ecossistema.py — isso é uma lacuna real do gate, mas
expandi-la está fora de escopo; só prove o que o gate JÁ faz hoje).

CONTEXTO JÁ INVESTIGADO (não precisa redescobrir, mas confirme lendo o
código antes de escrever cada teste):
- Os dois gates calculam a raiz do ecossistema assim, nos dois arquivos
  (mesma linha, texto plano, sem cerca própria):

  ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

  Isso significa que ROOT_DIR NUNCA é um parâmetro — é sempre "duas
  pastas acima de onde o arquivo .py está fisicamente". A técnica de
  teste (já validada com reprodução real antes de escrever este prompt)
  é: copiar o arquivo .py do gate para dentro de uma pasta gates/ de uma
  árvore sintética em tmp_path, e rodar via subprocess
  (`[sys.executable, str(caminho_copiado)]`). O ROOT_DIR resolvido pelo
  gate será automaticamente a raiz da árvore sintética — sem
  monkeypatch, sem reimplementar a lógica do gate.
- `gates/G_ECOSSISTEMA_INTEGRIDADE.py` (arquivo real, leia antes de
  escrever os testes) audita, nesta ordem: (1) AGENTS.md e .gitignore
  na raiz; (2) tools/aidd-forge, tools/aidd-generator, tools/aidd-master,
  tools/aidd-enterprise — cada um precisa existir, não pode ter um .git
  interno, e precisa ter README.md; (3) skills/<nome>/SKILL.md para
  aidd-forge-runner, aidd-generator-runner, aidd-master-runner,
  aidd-enterprise-runner — cada um precisa de frontmatter YAML válido
  (bloco --- ... --- no início do arquivo); (4) .agent/commands/<cmd> e
  .claude/commands/<cmd> para forge.md, generate.md, master.md,
  enterprise.md; (5) validação AST (ast.parse) de exatamente 2 arquivos
  fixos: gates/G_ECOSSISTEMA_INTEGRIDADE.py e ecossistema.py (relativos
  ao ROOT_DIR resolvido — ou seja, dentro da árvore sintética, esses 2
  arquivos precisam existir e ter sintaxe válida para o gate não
  reprovar por causa deles). Cada erro vira uma entrada na lista
  `erros`; se `erros` não estiver vazia, sys.exit(1) com cada erro
  listado no stdout; senão sys.exit(0).
- `gates/G_SEGREDOS.py` (arquivo real, leia antes de escrever os testes)
  roda `git ls-files` (subprocess de verdade, cwd=ROOT_DIR) para listar
  arquivos rastreados, varre cada um contra 7 padrões regex em
  PADROES_SEGREDO (chaves sk-..., AIzaSy... do Google, AKIA... da AWS,
  ghp_... do GitHub, xox... do Slack, chave privada PEM, e uma
  atribuição genérica tipo api_key="..."/senha="..."), e carrega
  gates/allowlist_segredos.json (relativo ao ROOT_DIR resolvido) para
  saber quais achados já são catalogados/justificados. Acima de 0
  achados NÃO catalogados: retorna 1. Senão: retorna 0. Isso significa
  que testar este gate precisa de um repositório git DE VERDADE
  (`git init` real dentro do tmp_path da árvore sintética) — não dá pra
  mockar `git ls-files`.
- Precedente de localização e padrão de teste já existente no
  repositório: gates/test_g_cli_help_consistencia.py (leia como
  referência de estilo, mas NÃO copie a técnica dele de testar funções
  internas isoladamente — aquele gate expõe funções isoladas, os 2
  gates deste item não expõem, então a técnica certa aqui é a de cópia
  + subprocess descrita acima).
- gates/pytest.ini (raiz do repo) já tem `testpaths = gates`, então
  `python -m pytest` (sem argumento, rodado da raiz do repositório) já
  roda tudo em gates/ automaticamente, incluindo os arquivos novos.

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. Técnica de teste é SEMPRE cópia do arquivo .py real do gate para
   dentro de tmp_path/gates/ + subprocess — nunca monkeypatch de
   ROOT_DIR via importlib, nunca reimplementação da lógica do gate.
2. Para G_ECOSSISTEMA_INTEGRIDADE: crie uma fixture (ex.: função ou
   fixture pytest) que constrói UMA árvore sintética 100% válida em
   tmp_path (AGENTS.md, .gitignore, os 4 tools/<nome>/README.md, as 4
   skills/<nome>-runner/SKILL.md com frontmatter YAML válido, os 8
   arquivos de comando em .agent/commands/ e .claude/commands/, e cópias
   de gates/G_ECOSSISTEMA_INTEGRIDADE.py e ecossistema.py dentro da
   árvore, sintaticamente válidos). Cada teste de FALHA parte dessa
   árvore válida (função helper reaproveitável, não copiar o setup 6x
   manualmente) e quebra exatamente UM aspecto antes de rodar o gate.
3. Para G_SEGREDOS: crie uma fixture que inicializa um repositório git
   REAL em tmp_path (`git init`, com `git -c user.email=... -c
   user.name=... commit` para os commits, mesma sintaxe já usada no
   diagnóstico) e copia gates/G_SEGREDOS.py para tmp_path/gates/. Nunca
   toque em gates/allowlist_segredos.json do repositório real — cada
   teste usa seu próprio allowlist dentro de tmp_path.
4. Os 2 padrões de segredo usados no teste de falha devem ser
   DIFERENTES entre si (ex.: um AKIA... de AWS e um ghp_... do GitHub,
   ou AWS + a atribuição genérica api_key="...") — não teste a mesma
   classe de regex duas vezes.
5. Não altere gates/G_ECOSSISTEMA_INTEGRIDADE.py nem gates/G_SEGREDOS.py
   — só crie os 2 arquivos de teste novos.

DEFINIÇÃO DE PRONTO — nesta ordem:

FASE 1 — Testes adversariais reais para os 2 gates
1.1. Criar gates/test_g_ecossistema_integridade.py com, no mínimo:
     - 1 teste de sucesso: árvore sintética válida → exit 0, mensagem de
       aprovação no stdout.
     - 1 teste de falha por categoria (mínimo 5): tools/aidd-forge sem
       README.md; .git vazado dentro de tools/aidd-forge; SKILL.md de
       aidd-forge-runner sem frontmatter YAML válido; comando
       forge.md ausente de .agent/commands OU .claude/commands;
       AGENTS.md ausente na raiz da árvore sintética. Cada um confirma
       exit code 1 E a mensagem de erro específica no stdout.
1.2. Criar gates/test_g_segredos.py com, no mínimo:
     - 1 teste de sucesso: repositório git limpo, sem nenhum segredo →
       exit 0.
     - 1 teste de falha: pelo menos 2 padrões DIFERENTES de segredo
       (decisão 4) não catalogados → exit 1, cada achado citado no
       stdout.
     - 1 teste de allowlist: o(s) mesmo(s) segredo(s) do teste anterior,
       agora catalogado(s) em um allowlist_segredos.json dentro da
       árvore sintética → exit 0.
1.3. Rodar `python -m pytest gates/ -q` (ou `python -m pytest` da raiz)
     e confirmar que os 8 testes já existentes de
     G_CLI_HELP_CONSISTENCIA continuam passando, junto com todos os
     testes novos.

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- `python -m pytest gates/ -q` → sem regressão, com os testes novos
  incluídos na contagem.
- Reprodução manual real (fora dos arquivos de teste, subprocess direto
  como no diagnóstico) de pelo menos 1 sucesso e 1 falha por gate — cole
  o output completo de cada execução.
- Confirme por comando (`git status`, rodado na raiz do repositório
  real, não na árvore sintética) que nenhum teste novo deixou arquivo
  fora de tmp_path, e que gates/allowlist_segredos.json do repositório
  real não foi tocado.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não altere a lógica de gates/G_ECOSSISTEMA_INTEGRIDADE.py nem
  gates/G_SEGREDOS.py.
- Não expanda a checagem AST do G_ECOSSISTEMA_INTEGRIDADE para varrer
  tools/*/scripts/ — fora de escopo deste item.
- Não toque em G_HARNESS_COMPAT, G_COMPONENTE_AGNOSTICO,
  G_DRIFT_NUCLEO_COMPARTILHADO nem G_CLI_HELP_CONSISTENCIA.
- Não faça `git commit` nem `git push`.
- Não altere
  `docs/planos/refinamento-notas-auditoria/02-prova-adversarial-gates-originais.md`.

ENTREGÁVEL: lista exata de arquivos criados/alterados; comando + output
real que comprova cada item do Critério de Saída; qualquer desvio
necessário, reportado explicitamente em vez de decidido sozinho.
```

## Prompt de Execução — English version

```
You are going to close a real adversarial-proof gap in two mechanical
gates at the root of the monorepo at
C:\Users\trcnologia\Desktop\ecossistema-aidd: gates/G_ECOSSISTEMA_INTEGRIDADE.py
and gates/G_SEGREDOS.py. These are 2 of the 6 gates that `ecossistema.py
audit` runs against the ecosystem root, but no test anywhere in the
repository exercises them today (confirmed via grep, zero results). The
other 4 gates on that same list (G_DRIFT_NUCLEO_COMPARTILHADO,
G_HARNESS_COMPAT, G_CLI_HELP_CONSISTENCIA, G_COMPONENTE_AGNOSTICO) are
NOT part of this work. Follow the Definition of Done below EXACTLY, do
not invent additional scope, and validate everything for real (real
subprocess runs, never masked by a pipe).

IMPORTANT — what this prompt does NOT ask for: do not change either
gate's logic. Do not expand G_ECOSSISTEMA_INTEGRIDADE's AST check to
scan tools/*/scripts/ (today it only scans 2 fixed files — the gate
itself and ecossistema.py — this is a real gap in the gate, but
expanding it is out of scope; only prove what the gate ALREADY does
today).

ALREADY-INVESTIGATED CONTEXT (no need to rediscover, but confirm by
reading the code before writing each test):
- Both gates compute the ecosystem root like this, in both files (same
  line, plain text, no fence of its own):

  ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

  This means ROOT_DIR is NEVER a parameter — it's always "two folders
  above wherever the .py file physically lives". The test technique
  (already validated with a real run before writing this prompt) is: copy
  the gate's .py file into a gates/ folder of a synthetic tree under
  tmp_path, and run it via subprocess
  (`[sys.executable, str(copied_path)]`). The ROOT_DIR the gate resolves
  will automatically be the synthetic tree's root — no monkeypatching, no
  reimplementing the gate's logic.
- `gates/G_ECOSSISTEMA_INTEGRIDADE.py` (real file, read it before writing
  the tests) audits, in this order: (1) AGENTS.md and .gitignore at the
  root; (2) tools/aidd-forge, tools/aidd-generator, tools/aidd-master,
  tools/aidd-enterprise — each must exist, must not contain an internal
  .git, and must have README.md; (3) skills/<name>/SKILL.md for
  aidd-forge-runner, aidd-generator-runner, aidd-master-runner,
  aidd-enterprise-runner — each needs valid YAML frontmatter (a --- ... ---
  block at the start of the file); (4) .agent/commands/<cmd> and
  .claude/commands/<cmd> for forge.md, generate.md, master.md,
  enterprise.md; (5) AST validation (ast.parse) of exactly 2 fixed files:
  gates/G_ECOSSISTEMA_INTEGRIDADE.py and ecossistema.py (relative to the
  resolved ROOT_DIR — so inside the synthetic tree, these 2 files must
  exist and have valid syntax for the gate not to fail because of them).
  Each error becomes an entry in the `erros` list; if `erros` is
  non-empty, sys.exit(1) with each error listed in stdout; otherwise
  sys.exit(0).
- `gates/G_SEGREDOS.py` (real file, read it before writing the tests)
  runs `git ls-files` (a real subprocess call, cwd=ROOT_DIR) to list
  tracked files, scans each against 7 regex patterns in
  PADROES_SEGREDO (OpenAI-style sk-... keys, Google AIzaSy..., AWS
  AKIA..., GitHub ghp_..., Slack xox..., PEM private key, and a generic
  assignment like api_key="..."/senha="..."), and loads
  gates/allowlist_segredos.json (relative to the resolved ROOT_DIR) to
  know which findings are already catalogued/justified. More than 0
  un-catalogued findings: returns 1. Otherwise: returns 0. This means
  testing this gate needs a REAL git repository (a real `git init`
  inside the synthetic tree's tmp_path) — `git ls-files` cannot be
  mocked here.
- Existing location and test-style precedent already in the repository:
  gates/test_g_cli_help_consistencia.py (read it as a style reference,
  but do NOT copy its technique of testing isolated internal functions —
  that gate exposes isolated functions, these 2 gates don't, so the
  right technique here is the copy + subprocess one described above).
- The root pytest.ini already has `testpaths = gates`, so
  `python -m pytest` (no argument, run from the repository root) already
  runs everything in gates/ automatically, including the new files.

DECISIONS ALREADY MADE (do not reopen these):
1. Test technique is ALWAYS copying the gate's real .py file into
   tmp_path/gates/ + subprocess — never monkeypatching ROOT_DIR via
   importlib, never reimplementing the gate's logic.
2. For G_ECOSSISTEMA_INTEGRIDADE: create a fixture (e.g. a helper
   function or pytest fixture) that builds ONE fully valid synthetic tree
   under tmp_path (AGENTS.md, .gitignore, the 4
   tools/<name>/README.md, the 4 skills/<name>-runner/SKILL.md with valid
   YAML frontmatter, the 8 command files under .agent/commands/ and
   .claude/commands/, and copies of gates/G_ECOSSISTEMA_INTEGRIDADE.py
   and ecossistema.py inside the tree, syntactically valid). Each FAILURE
   test starts from that valid tree (a reusable helper, not manually
   duplicating the setup 6 times) and breaks exactly ONE aspect before
   running the gate.
3. For G_SEGREDOS: create a fixture that initializes a REAL git
   repository under tmp_path (`git init`, with `git -c user.email=... -c
   user.name=... commit` for commits, same syntax already used in the
   diagnosis) and copies gates/G_SEGREDOS.py into tmp_path/gates/. Never
   touch the real repository's gates/allowlist_segredos.json — each test
   uses its own allowlist inside tmp_path.
4. The 2 secret patterns used in the failure test must be DIFFERENT from
   each other (e.g. an AWS AKIA... and a GitHub ghp_..., or AWS + the
   generic api_key="..." assignment) — do not test the same regex class
   twice.
5. Do not change gates/G_ECOSSISTEMA_INTEGRIDADE.py or
   gates/G_SEGREDOS.py — only create the 2 new test files.

DEFINITION OF DONE — in this order:

PHASE 1 — Real adversarial tests for both gates
1.1. Create gates/test_g_ecossistema_integridade.py with, at minimum:
     - 1 success test: valid synthetic tree → exit 0, approval message in
       stdout.
     - 1 failure test per category (minimum 5): tools/aidd-forge missing
       README.md; a leaked .git inside tools/aidd-forge; aidd-forge-runner's
       SKILL.md without valid YAML frontmatter; forge.md missing from
       .agent/commands OR .claude/commands; AGENTS.md missing from the
       synthetic tree's root. Each confirms exit code 1 AND the specific
       error message in stdout.
1.2. Create gates/test_g_segredos.py with, at minimum:
     - 1 success test: clean git repository, no secrets → exit 0.
     - 1 failure test: at least 2 DIFFERENT secret patterns (decision 4)
       not catalogued → exit 1, each finding cited in stdout.
     - 1 allowlist test: the same secret(s) from the previous test, now
       catalogued in an allowlist_segredos.json inside the synthetic tree
       → exit 0.
1.3. Run `python -m pytest gates/ -q` (or `python -m pytest` from the
     root) and confirm the 8 existing G_CLI_HELP_CONSISTENCIA tests still
     pass, alongside all new tests.

EXIT CRITERIA (run and paste the real output of each):
- `python -m pytest gates/ -q` → no regression, with the new tests
  included in the count.
- Real manual reproduction (outside the test files, direct subprocess as
  in the diagnosis) of at least 1 success and 1 failure per gate — paste
  the full output of each run.
- Confirm via command (`git status`, run at the real repository root, not
  inside the synthetic tree) that no new test left a file outside
  tmp_path, and that the real repository's
  gates/allowlist_segredos.json was not touched.

SCOPE RULES — DO NOT:
- Do not change the logic of gates/G_ECOSSISTEMA_INTEGRIDADE.py or
  gates/G_SEGREDOS.py.
- Do not expand G_ECOSSISTEMA_INTEGRIDADE's AST check to scan
  tools/*/scripts/ — out of scope for this item.
- Do not touch G_HARNESS_COMPAT, G_COMPONENTE_AGNOSTICO,
  G_DRIFT_NUCLEO_COMPARTILHADO, or G_CLI_HELP_CONSISTENCIA.
- Do not `git commit` or `git push`.
- Do not modify
  `docs/planos/refinamento-notas-auditoria/02-prova-adversarial-gates-originais.md`.

DELIVERABLE: exact list of files created/changed; command + real output
proving each item of the Exit Criteria; any necessary deviation,
explicitly reported instead of decided by yourself.
```

---

## Veredito — Auditoria

**Auditoria independente realizada — não me baseei no relatório do agente executor, e não rodei nem reaproveitei nenhuma função dos arquivos de teste dele.** Entregável real, confirmado por `git status` no repo inteiro: `gates/test_g_ecossistema_integridade.py` (6 testes) e `gates/test_g_segredos.py` (3 testes) — nada mais foi tocado (lógica dos 2 gates intacta, `gates/allowlist_segredos.json` real não tocado, nenhum outro gate afetado, sem commit/push feito pelo executor, este documento não alterado por ele).

**Suíte completa reproduzida por mim:** `python -m pytest gates/ -q` → **17 passed**, exit code real 0 (8 pré-existentes de `G_CLI_HELP_CONSISTENCIA` + 6 + 3 novos, sem regressão).

**Reprodução totalmente independente — escrevi meu próprio script de auditoria, com árvores/repositórios sintéticos e cenários DIFERENTES dos escolhidos pelo executor (não só rodei o arquivo dele):**
- `G_ECOSSISTEMA_INTEGRIDADE`: (1) árvore válida construída do zero por mim → exit 0. (2) removi uma skill inteira (`aidd-master-runner`, cenário diferente do "sem frontmatter" testado pelo executor) → exit 1, erro cita a skill ausente corretamente. (3) removi o comando do lado `.claude/commands` (o executor só testou `.agent/commands`) → exit 1, erro cita `.claude/commands/enterprise.md` corretamente — confirma que a checagem cobre os dois harness, não só o lado testado pelo executor.
- `G_SEGREDOS`: (1) repo limpo → exit 0. (2) usei 2 padrões de segredo diferentes dos do executor (chave privada PEM + atribuição genérica de senha, em vez de AWS + GitHub) → exit 1, os 2 achados corretamente citados. (3) **verificação extra, além do que foi pedido:** catalguei só o PEM no allowlist (não a senha) e confirmei que o gate continua reprovando — cita só `config.py` como achado novo, não mais o PEM — prova que o allowlist funciona por arquivo individual, não é um bypass geral que desativaria a varredura inteira.

**Nenhum arquivo órfão:** `git status` limpo além dos 2 arquivos de teste + este documento. Nenhum warning de encoding (usei `PYTHONIOENCODING=utf-8` no ambiente do subprocess, mesmo padrão do executor).

**Notável:** fechou de primeira quanto ao COMPORTAMENTO — a auditoria independente, usando cenários deliberadamente diferentes (lado `.claude` em vez de `.agent`, skill inteira ausente em vez de frontmatter quebrado, PEM+senha em vez de AWS+GitHub, mais o teste extra de allowlist parcial), não encontrou nenhuma divergência do comportamento documentado.

**Correção de estilo aplicada após revisão do usuário (não muda comportamento nenhum, só limpeza):** o usuário notou, ao revisar o diff, 3 inconsistências reais de nomenclatura/duplicação entre os 2 arquivos novos e o precedente (`gates/test_g_cli_help_consistencia.py`): (1) constante `REAL_GATE_PATH` nos 2 arquivos novos vs `GATE_PATH` no precedente para o mesmo conceito; (2) função `_git_commit_all` em inglês misturada com `_montar_arvore_valida`/`_init_repo_sintetico`/`_rodar_gate` em PT-BR no mesmo arquivo; (3) a função `_rodar_gate` duplicada byte-a-byte (só o docstring diferia) nos 2 arquivos novos. Corrigi as 3: unifiquei em `GATE_PATH`/`CLI_PATH`, renomeei para `_comitar_tudo`, e extraí o helper compartilhado para `gates/_gate_test_utils.py` (nome que não bate com `test_*.py` nem `G_*.py` do `pytest.ini`, então não é coletado como suíte). Também removi o `import pytest` não utilizado em ambos os arquivos (nenhum dos dois usa `pytest.` diretamente — só a fixture `tmp_path`, injetada automaticamente). Rodei `python -m pytest gates/ -q` de novo após a limpeza: **17 passed, exit 0 real**, mesmo resultado de antes — confirma que a correção foi puramente cosmética, sem efeito colateral.

### Nota Final — Item 3 (Prova Adversarial dos Gates Originais): 10/10

**Por que 10:**
- Todos os critérios de saída cumpridos e verificados com reprodução real e totalmente independente — inclusive além do que o executor testou (3 cenários próprios diferentes + 1 verificação extra de granularidade do allowlist, não pedida na Definição de Pronto).
- Escopo 100% respeitado: lógica dos 2 gates intocada, nenhum outro gate afetado, allowlist real intocado, sem commit/push, sem regressão, sem arquivo órfão.
- Fechou de primeira, sem nenhuma correção necessária.
- **Efeito na dimensão Gates Mecânicos:** o gap identificado (`G_ECOSSISTEMA_INTEGRIDADE` e `G_SEGREDOS` nunca tinham prova de que genuinamente reprovam quando deveriam) está fechado com evidência real e reproduzida de forma independente. Combinado com os 2 gates que já tinham prova antes deste item (`G_DRIFT_NUCLEO_COMPARTILHADO`, `G_CLI_HELP_CONSISTENCIA`), a dimensão **sobe de 8 para 9/10** (não 10: `G_HARNESS_COMPAT` e `G_COMPONENTE_AGNOSTICO`, as 2 variantes de raiz restantes na mesma lista de `cmd_audit`, continuam sem prova — achado lateral já registrado no diagnóstico, fora de escopo deste item específico, mas ainda real e pendente na dimensão como um todo).
