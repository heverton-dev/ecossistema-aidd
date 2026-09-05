# Item 2 — Disclosure: `plan`/`prompt` não avisam que não usam LLM

> **Status:** ✅ CONCLUÍDO em 05/09/2026 — nota final 10/10 (ver Veredito ao final do documento).
> **Origem:** pergunta do usuário — "podemos superar o 10, sem fabricação?" — aplicada à dimensão Transparência (hoje 8,5/10).
> **Contribui para:** Transparência.

---

## As 4 perguntas de rigor, respondidas antes de propor qualquer trabalho

1. **É necessário?** — Sim. `plan`/`prompt` (`aidd-master` e `aidd-enterprise`) são anunciados no `--help` como "Instrução em linguagem natural", mas o mecanismo real é casamento de palavras-chave contra uma lista fixa de ~20 domínios — zero LLM. Isso contradiz a própria Lei Fundamental do ecossistema ("NADA DEVE FICAR OCULTO AO USUÁRIO").
2. **É possível?** — Sim: mudança mecânica, sem exigir acesso externo — só adicionar disclosure real no `--help` e no output de execução.
3. **É real?** — Sim: reproduzi eu mesmo, via subprocess real (não só lendo o código), rodando `python scripts/aidd.py plan "Crie um sistema de agendamento de clinica"` — ver evidência abaixo.
4. **Traz ganho real?** — Sim: evita que o usuário acredite que está conversando com uma IA que "entendeu" o pedido, quando na verdade é casamento de string. Fica mais grave ainda no caminho de fallback genérico (quando nenhum domínio conhecido bate), que é uma heurística ainda mais fraca e hoje é indistinguível do caminho "domínio reconhecido".

---

## Diagnóstico

### Mecanismo real de `cmd_plan` (idêntico em `aidd-master` e `aidd-enterprise`, confirmado por `diff`)

`tools/aidd-master/scripts/aidd.py:786` (mesmo código byte-a-byte em `tools/aidd-enterprise/scripts/aidd.py:642`, confirmado via `diff`):

1. Normaliza o prompt para minúsculas.
2. Varre uma lista fixa `KNOWN_DOMAINS` (`crm`, `erp`, `faturamento`, `financeiro`, `vendas`, `helpdesk`, `suporte`, `logistica`, `estoque`, `membros`, `cursos`, `catalogo`, `produtos`, `pedidos`, `whatsapp`, `afiliados`, `assinaturas`, `fiscal`, `analytics`, `lead`/`leads`, `campanhas`, `marketing`, `tickets`) com `re.search(r'\bDOMINIO\b', prompt_lower)`.
3. **Se nenhum domínio bate:** cai num fallback ainda mais fraco — extrai as primeiras 4 palavras com 4+ letras que não estão numa lista de stop-words (`crie`, `uma`, `aplicacao`, etc.).
4. **Se nem isso encontrar nada:** usa um default hardcoded (`["principal", "configuracao"]`).
5. Zero chamada de LLM em qualquer um dos 3 caminhos.

O comando `prompt` (`p_prompt` no argparse) e o fallback de linguagem natural (quando o primeiro argumento do CLI não é um comando conhecido) **chamam exatamente essa mesma função** — `parse_natural_language_intent()` só encaminha para `cmd_plan()`.

### Onde está a falta de transparência

- **`--help`:** `p_plan.add_argument("prompt", help="Instrução em linguagem natural (ex: 'Crie um CRM e ERP de faturamento')")` e o mesmo texto em `p_prompt` — não há uma palavra sobre o mecanismo ser casamento de palavras-chave fixo.
- **Output de execução:** `cmd_plan` imprime um cabeçalho `[FASE 1.5 - SPEC & PLANEJAMENTO ARQUITETURAL]` e lista as "fatias" encontradas, mas nunca diz *como* elas foram encontradas nem se caiu no fallback genérico.

**Reprodução real (não assumida):**
```
$ python scripts/aidd.py plan "Crie um sistema de agendamento de clinica" --dir /tmp
================================================================================
📋 [FASE 1.5 - SPEC & PLANEJAMENTO ARQUITETURAL]
================================================================================
Projeto:       Agendamento Clinica Suite
Destino:       ...\app_agendamento-clinica-suite
Status:        PLANEJADO (Aguardando Aprovação)
Fatias (2):   agendamento, clinica
Documentos:    SPEC-ARQUITETURA.md | PLANO-EXECUCAO-ESTRUTURADO.json
================================================================================
```
Nenhum domínio da lista `KNOWN_DOMAINS` bate em "agendamento de clinica" — as 2 "fatias" vieram do fallback de extração de palavras (não de compreensão da frase), e o output não avisa isso em lugar nenhum. Um usuário lendo essa saída pode legitimamente acreditar que o sistema "entendeu" que ele quer um sistema de agendamento clínico — o que não é o que aconteceu.

---

## Definição de Pronto

**Fase 1 — Disclosure real no `--help` e no output de execução de `plan`/`prompt`**

1.1. Adicionar ao texto de `help=` dos argumentos `prompt` (em `p_plan`) e `texto` (em `p_prompt`), nas duas ferramentas, uma frase explícita: o parsing usa casamento de palavras-chave contra uma lista fixa de domínios conhecidos, não um LLM.
1.2. No output de execução de `cmd_plan`, adicionar uma linha que informe qual dos 3 caminhos foi usado:
   - Domínio(s) conhecido(s) reconhecido(s) (listar quais).
   - Fallback genérico de extração de palavras (avisar explicitamente que é uma heurística mais fraca, sem correspondência a um domínio conhecido).
   - Default hardcoded (`principal`/`configuracao`) — avisar que nada foi reconhecido nem extraído.
1.3. Aplicar a mesma mudança nas duas ferramentas (`aidd-master` e `aidd-enterprise`) — `cmd_plan` é idêntico nas duas, mesmo padrão do Pacote 4 da rodada 1.
1.4. Teste real (subprocess, sem mock) confirmando que a saída contém a linha de disclosure correta em pelo menos 2 cenários: um prompt que bate em domínio conhecido (ex.: "Crie um CRM") e um que cai no fallback genérico (ex.: "Crie um sistema de agendamento de clinica", o mesmo caso já reproduzido acima).
1.5. Teste real de `--help` (subprocess) confirmando que a nova frase de disclosure aparece no texto de ajuda de `plan` e `prompt`, nas duas ferramentas.

**Critério de saída (rodar e colar o output real de cada um):**
- Suíte completa das duas ferramentas (`aidd-master`, `aidd-enterprise`) → sem regressão.
- Reprodução manual real (subprocess) do cenário de domínio conhecido e do cenário de fallback genérico, mostrando a linha de disclosure correta em cada um.
- `--help` de `plan` e `prompt` (nas duas ferramentas) mostrando a nova frase.
- `git status` limpo além dos arquivos de código/teste esperados.

**Regras de escopo — não fazer:**
- Não mudar o mecanismo de matching em si (não é sobre melhorar a heurística, é sobre revelar que ela existe).
- Não tocar em nenhum outro subcomando.
- Não fazer commit/push (isso eu faço depois de auditar).

---

## Ordem de execução

Item único, 1 fase, cabe em 1 prompt — mesmo padrão do Item 1.

**Aprovado pelo usuário em 05/09/2026.** Prompt de execução abaixo.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai fechar um gap real de transparência em duas ferramentas do
monorepo em C:\Users\trcnologia\Desktop\ecossistema-aidd:
tools/aidd-master/scripts/aidd.py e tools/aidd-enterprise/scripts/aidd.py.
Os comandos `plan` e `prompt` são anunciados no --help como "Instrução em
linguagem natural", mas o mecanismo real é casamento de palavras-chave
contra uma lista fixa de domínios (`KNOWN_DOMAINS`) — ZERO LLM. Isso nunca
é revelado ao usuário nem no --help nem no output de execução. Siga
EXATAMENTE a Definição de Pronto abaixo, não invente escopo adicional, e
valide tudo de verdade (execuções reais via subprocess, nunca mascaradas
por pipe).

IMPORTANTE — o que este prompt NÃO pede: não mude o mecanismo de
casamento de palavras-chave em si (não é sobre melhorar a heurística). O
objetivo é só REVELAR ao usuário qual dos 3 caminhos foi usado, sempre
que `plan`/`prompt` rodar, e mencionar isso no --help.

CONTEXTO JÁ INVESTIGADO (não precisa redescobrir, mas confirme lendo o
código antes de editar):
- `cmd_plan()` é BYTE-IDÊNTICO nos dois arquivos (confirmado via `diff`):
  `tools/aidd-master/scripts/aidd.py` linha 786 e
  `tools/aidd-enterprise/scripts/aidd.py` linha 642. Tem exatamente esta
  estrutura (mesmos nomes de variável nos dois arquivos, texto plano,
  sem cerca de código própria para não quebrar a cópia deste bloco):

  def cmd_plan(prompt: str, base_dir: str = ".", auto_apply: bool = False):
      ensure_environment()
      prompt_lower = prompt.lower()
      KNOWN_DOMAINS = [...]           # lista fixa de ~20 domínios
      found_modules = []
      for d in KNOWN_DOMAINS:
          if re.search(r'\b' + d + r'\b', prompt_lower):
              ...
              found_modules.append(slug)
      if not found_modules:
          words = re.findall(r'\b[a-zA-Z]{4,}\b', prompt_lower)
          stop_words = {...}
          found_modules = [w for w in words if w not in stop_words][:4]
      if not found_modules:
          found_modules = ["principal", "configuracao"]
      ...
      print("=" * 80)
      print("📋 [FASE 1.5 - SPEC & PLANEJAMENTO ARQUITETURAL]")
      print("=" * 80)
      print(f"Projeto:       {suite_title}")
      print(f"Destino:       {target_path}")
      print(f"Status:        PLANEJADO (Aguardando Aprovação)")
      print(f"Fatias ({len(found_modules)}):   {', '.join(found_modules)}")
      print(f"Documentos:    SPEC-ARQUITETURA.md | PLANO-EXECUCAO-ESTRUTURADO.json")
      print("=" * 80)
      ...

  Existem 3 caminhos possíveis para `found_modules`, nesta ordem de
  prioridade: (A) domínio(s) reconhecido(s) da lista `KNOWN_DOMAINS`,
  (B) fallback de extração de palavras (nenhum domínio bateu), (C)
  default hardcoded `["principal", "configuracao"]` (nem o fallback de
  palavras encontrou nada). Hoje o output não distingue esses 3 casos.
- O argparse de `plan`/`prompt` está em `main()`, mesma estrutura nos
  dois arquivos: `tools/aidd-master/scripts/aidd.py` linhas 962-983,
  `tools/aidd-enterprise/scripts/aidd.py` linhas 954-975. Trechos (texto
  plano, sem cerca própria):

  p_plan = subparsers.add_parser("plan", help="Gera especificação arquitetural e plano antes de compor")
  p_plan.add_argument("prompt", help="Instrução em linguagem natural (ex: 'Crie um CRM e ERP de faturamento')")
  ...
  p_prompt = subparsers.add_parser("prompt", help="Gera aplicação a partir de prompt em linguagem natural")
  p_prompt.add_argument("texto", help="Instrução em linguagem natural (ex: 'Crie um CRM e ERP de faturamento')")

- Testes já existentes que exercitam os 3 caminhos de `cmd_plan`, MESMOS
  nomes/linhas nos dois arquivos —
  `tools/aidd-master/tests/unit/test_cli_commands.py` e
  `tools/aidd-enterprise/tests/unit/test_cli_commands.py`:
  - `test_cmd_plan_dominio_conhecido` (linha 104) — chama
    `cmd_plan("crie um crm", base_dir=str(tmp_path))`, caminho (A).
  - `test_cmd_plan_dominio_desconhecido_fallback_palavras` (linha 125) —
    chama `cmd_plan("desenvolva consultoria veterinaria agendamento", ...)`,
    caminho (B).
  - `test_cmd_plan_prompt_sem_substancia_fallback_final` (linha 147) —
    chama `cmd_plan("crie uma aplicacao com", ...)`, caminho (C).
  Reaproveite exatamente esses 3 cenários (mesmos prompts) para verificar
  a nova linha de disclosure — não invente prompts novos para isso.

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. Adicionar uma variável explícita dentro de `cmd_plan()` (ex.:
   `mecanismo_usado`) que registra qual dos 3 caminhos (A/B/C) foi
   usado, atribuída no MOMENTO em que cada caminho é decidido (não
   inferida depois por comparação de valores — isso evitaria o caso raro
   em que o fallback de palavras coincidentemente produz
   `["principal", "configuracao"]`).
2. No bloco de `print` do cabeçalho `[FASE 1.5 ...]`, adicionar uma
   linha de disclosure ANTES do `print("=" * 80)` final, com texto
   diferente para cada caminho:
   - (A): `f"Mecanismo:     casamento de palavra-chave — domínio(s) reconhecido(s): {', '.join(...)} (lista fixa, SEM LLM)"`
   - (B): `"Mecanismo:     ⚠️ fallback de extração de palavras — NENHUM domínio conhecido reconhecido, sem LLM (heurística mais fraca)"`
   - (C): `"Mecanismo:     ⚠️ nenhuma palavra significativa encontrada — usando módulos padrão fixos, sem LLM"`
   Aplique a mesma mudança, byte-idêntica, nos dois arquivos (`aidd-master`
   e `aidd-enterprise`) — exatamente como `cmd_plan` já é idêntico hoje.
3. No `help=` dos argumentos `prompt` (em `p_plan`) e `texto` (em
   `p_prompt`), nos dois arquivos, adicionar ao texto existente uma
   cláusula explícita, por exemplo: `"... (processado por casamento de
   palavras-chave contra uma lista fixa de domínios conhecidos — NÃO usa
   LLM/IA generativa)"`. Não precisa ser a frase exata, mas tem que
   deixar claro que não é LLM.
4. Não mudar o comportamento de `found_modules` em nenhum caminho — só
   adicionar a variável de rastreamento e os prints/help novos.

DEFINIÇÃO DE PRONTO — nesta ordem, aplicada às DUAS ferramentas:

FASE 1 — Disclosure real no `--help` e no output de execução
1.1. Editar `tools/aidd-master/scripts/aidd.py` e
     `tools/aidd-enterprise/scripts/aidd.py`: dentro de `cmd_plan()`,
     adicionar a variável `mecanismo_usado` e a linha de disclosure
     correspondente no bloco de print, conforme decisão 2 acima.
1.2. Editar o `help=` de `p_plan`/`prompt` e `p_prompt`/`texto` nos dois
     arquivos, conforme decisão 3.
1.3. Teste real (chamando `cmd_plan()` diretamente, sem subprocess — como
     os 3 testes já existentes fazem) confirmando, via `capsys`, que a
     linha de disclosure certa aparece para os 3 cenários já cobertos
     pelos testes existentes (reaproveite os 3 testes citados acima,
     adicionando a asserção de `capsys` a cada um, ou crie 3 testes
     complementares se preferir não tocar nos originais — sua escolha,
     mas não pode haver duplicação de setup desnecessária).
1.4. Teste real via subprocess (`[sys.executable, AIDD_SCRIPT, "plan",
     "--help"]` e `[..., "prompt", "--help"]`, capturando stdout, mesmo
     padrão dos testes de subprocess já existentes no arquivo) confirmando
     que a frase nova aparece no texto de ajuda, nos dois comandos, nas
     duas ferramentas (4 combinações: master/plan, master/prompt,
     enterprise/plan, enterprise/prompt).
1.5. Repita 1.1-1.4 identicamente em `aidd-enterprise` (o código é
     idêntico hoje, então a mudança também deve ser idêntica).

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- Suíte completa de `aidd-master` (`python -m pytest tests/ -q`) e de
  `aidd-enterprise` (`python -m pytest tests/ -q`) → sem regressão.
- Reprodução manual real (subprocess, fora dos arquivos de teste) de:
  `python scripts/aidd.py plan "Crie um CRM"` (caminho A) e
  `python scripts/aidd.py plan "Crie um sistema de agendamento de
  clinica"` (caminho B, mesmo prompt já usado no diagnóstico) — cole o
  output completo de cada execução, mostrando a linha de disclosure
  correta.
- `python scripts/aidd.py plan --help` e `python scripts/aidd.py prompt
  --help` (nas duas ferramentas) mostrando a nova frase — cole o output.
- Confirme por comando (`git status`) que nenhum teste novo deixou
  arquivo fora de `tmp_path`/diretório de teste temporário.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não mude o mecanismo de matching (`KNOWN_DOMAINS`, fallback de
  palavras, default hardcoded) — só revele qual foi usado.
- Não toque em nenhum outro subcomando (`apply`, `compose`, `audit`,
  etc.) nem em `aidd-generator`/`aidd-forge`.
- Não faça `git commit` nem `git push`.
- Não altere
  `docs/planos/refinamento-notas-auditoria/03-transparencia-disclosure-plan-prompt.md`.

ENTREGÁVEL: lista exata de arquivos criados/alterados; comando + output
real que comprova cada item do Critério de Saída; qualquer desvio
necessário, reportado explicitamente em vez de decidido sozinho.
```

## Prompt de Execução — English version

```
You are going to close a real transparency gap in two tools inside the
monorepo at C:\Users\trcnologia\Desktop\ecossistema-aidd:
tools/aidd-master/scripts/aidd.py and
tools/aidd-enterprise/scripts/aidd.py. The `plan` and `prompt` commands
are advertised in --help as "Natural language instruction", but the real
mechanism is keyword matching against a fixed domain list
(`KNOWN_DOMAINS`) — ZERO LLM. This is never disclosed, not in --help nor
in the execution output. Follow the Definition of Done below EXACTLY, do
not invent additional scope, and validate everything for real (real
subprocess runs, never masked by a pipe).

IMPORTANT — what this prompt does NOT ask for: do not change the
keyword-matching mechanism itself (this is not about improving the
heuristic). The goal is only to DISCLOSE to the user which of the 3
paths was used, every time `plan`/`prompt` runs, and to mention it in
--help.

ALREADY-INVESTIGATED CONTEXT (no need to rediscover, but confirm by
reading the code before editing):
- `cmd_plan()` is BYTE-IDENTICAL in both files (confirmed via `diff`):
  `tools/aidd-master/scripts/aidd.py` line 786 and
  `tools/aidd-enterprise/scripts/aidd.py` line 642. It has exactly this
  structure (same variable names in both files, plain text, no fence of
  its own so this whole block can be copied without breaking):

  def cmd_plan(prompt: str, base_dir: str = ".", auto_apply: bool = False):
      ensure_environment()
      prompt_lower = prompt.lower()
      KNOWN_DOMAINS = [...]           # fixed list of ~20 domains
      found_modules = []
      for d in KNOWN_DOMAINS:
          if re.search(r'\b' + d + r'\b', prompt_lower):
              ...
              found_modules.append(slug)
      if not found_modules:
          words = re.findall(r'\b[a-zA-Z]{4,}\b', prompt_lower)
          stop_words = {...}
          found_modules = [w for w in words if w not in stop_words][:4]
      if not found_modules:
          found_modules = ["principal", "configuracao"]
      ...
      print("=" * 80)
      print("📋 [FASE 1.5 - SPEC & PLANEJAMENTO ARQUITETURAL]")
      print("=" * 80)
      print(f"Projeto:       {suite_title}")
      print(f"Destino:       {target_path}")
      print(f"Status:        PLANEJADO (Aguardando Aprovação)")
      print(f"Fatias ({len(found_modules)}):   {', '.join(found_modules)}")
      print(f"Documentos:    SPEC-ARQUITETURA.md | PLANO-EXECUCAO-ESTRUTURADO.json")
      print("=" * 80)
      ...

  There are 3 possible paths for `found_modules`, in this priority order:
  (A) recognized domain(s) from `KNOWN_DOMAINS`, (B) word-extraction
  fallback (no domain matched), (C) hardcoded default
  `["principal", "configuracao"]` (not even the word fallback found
  anything). Today the output does not distinguish these 3 cases.
- The argparse wiring for `plan`/`prompt` is in `main()`, same structure
  in both files: `tools/aidd-master/scripts/aidd.py` lines 962-983,
  `tools/aidd-enterprise/scripts/aidd.py` lines 954-975. Snippets (plain
  text, no fence of its own):

  p_plan = subparsers.add_parser("plan", help="Gera especificação arquitetural e plano antes de compor")
  p_plan.add_argument("prompt", help="Instrução em linguagem natural (ex: 'Crie um CRM e ERP de faturamento')")
  ...
  p_prompt = subparsers.add_parser("prompt", help="Gera aplicação a partir de prompt em linguagem natural")
  p_prompt.add_argument("texto", help="Instrução em linguagem natural (ex: 'Crie um CRM e ERP de faturamento')")

- Tests already exercising the 3 `cmd_plan` paths, SAME names/lines in
  both files — `tools/aidd-master/tests/unit/test_cli_commands.py` and
  `tools/aidd-enterprise/tests/unit/test_cli_commands.py`:
  - `test_cmd_plan_dominio_conhecido` (line 104) — calls
    `cmd_plan("crie um crm", base_dir=str(tmp_path))`, path (A).
  - `test_cmd_plan_dominio_desconhecido_fallback_palavras` (line 125) —
    calls `cmd_plan("desenvolva consultoria veterinaria agendamento", ...)`,
    path (B).
  - `test_cmd_plan_prompt_sem_substancia_fallback_final` (line 147) —
    calls `cmd_plan("crie uma aplicacao com", ...)`, path (C).
  Reuse exactly these 3 scenarios (same prompts) to verify the new
  disclosure line — do not invent new prompts for this.

DECISIONS ALREADY MADE (do not reopen these):
1. Add an explicit variable inside `cmd_plan()` (e.g. `mecanismo_usado`)
   that records which of the 3 paths (A/B/C) was used, assigned AT THE
   MOMENT each path is decided (not inferred afterwards by comparing
   values — this avoids the rare case where the word fallback
   coincidentally produces `["principal", "configuracao"]`).
2. In the `[FASE 1.5 ...]` header print block, add a disclosure line
   BEFORE the final `print("=" * 80)`, with different text per path:
   - (A): `f"Mecanismo:     casamento de palavra-chave — domínio(s) reconhecido(s): {', '.join(...)} (lista fixa, SEM LLM)"`
   - (B): `"Mecanismo:     ⚠️ fallback de extração de palavras — NENHUM domínio conhecido reconhecido, sem LLM (heurística mais fraca)"`
   - (C): `"Mecanismo:     ⚠️ nenhuma palavra significativa encontrada — usando módulos padrão fixos, sem LLM"`
   Apply the same change, byte-identical, in both files (`aidd-master`
   and `aidd-enterprise`) — exactly like `cmd_plan` is already identical
   today.
3. In the `help=` of the `prompt` argument (in `p_plan`) and `texto`
   argument (in `p_prompt`), in both files, add an explicit clause to the
   existing text, e.g.: `"... (processed by keyword matching against a
   fixed list of known domains — does NOT use LLM/generative AI)"`. It
   doesn't need to be the exact phrase, but it must make clear this is
   not an LLM.
4. Do not change `found_modules` behavior on any path — only add the
   tracking variable and the new prints/help text.

DEFINITION OF DONE — in this order, applied to BOTH tools:

PHASE 1 — Real disclosure in `--help` and in the execution output
1.1. Edit `tools/aidd-master/scripts/aidd.py` and
     `tools/aidd-enterprise/scripts/aidd.py`: inside `cmd_plan()`, add
     the `mecanismo_usado` variable and the corresponding disclosure
     line in the print block, per decision 2 above.
1.2. Edit the `help=` of `p_plan`/`prompt` and `p_prompt`/`texto` in both
     files, per decision 3.
1.3. Real test (calling `cmd_plan()` directly, no subprocess — like the
     3 existing tests already do) confirming, via `capsys`, that the
     right disclosure line appears for the 3 scenarios already covered
     by the existing tests (reuse the 3 tests cited above, adding the
     `capsys` assertion to each, or create 3 companion tests if you
     prefer not to touch the originals — your choice, but there must be
     no unnecessary duplicated setup).
1.4. Real subprocess test (`[sys.executable, AIDD_SCRIPT, "plan",
     "--help"]` and `[..., "prompt", "--help"]`, capturing stdout, same
     pattern as the subprocess tests already in the file) confirming the
     new phrase appears in the help text, for both commands, in both
     tools (4 combinations: master/plan, master/prompt,
     enterprise/plan, enterprise/prompt).
1.5. Repeat 1.1-1.4 identically in `aidd-enterprise` (the code is
     identical today, so the change must be identical too).

EXIT CRITERIA (run and paste the real output of each):
- Full `aidd-master` suite (`python -m pytest tests/ -q`) and
  `aidd-enterprise` suite (`python -m pytest tests/ -q`) → no regression.
- Real manual reproduction (subprocess, outside the test files) of:
  `python scripts/aidd.py plan "Crie um CRM"` (path A) and
  `python scripts/aidd.py plan "Crie um sistema de agendamento de
  clinica"` (path B, the same prompt already used in the diagnosis) —
  paste the full output of each run, showing the correct disclosure
  line.
- `python scripts/aidd.py plan --help` and `python scripts/aidd.py
  prompt --help` (both tools) showing the new phrase — paste the output.
- Confirm via command (`git status`) that no new test left a file
  outside `tmp_path`/a temporary test directory.

SCOPE RULES — DO NOT:
- Do not change the matching mechanism (`KNOWN_DOMAINS`, word fallback,
  hardcoded default) — only disclose which one was used.
- Do not touch any other subcommand (`apply`, `compose`, `audit`, etc.)
  nor `aidd-generator`/`aidd-forge`.
- Do not `git commit` or `git push`.
- Do not modify
  `docs/planos/refinamento-notas-auditoria/03-transparencia-disclosure-plan-prompt.md`.

DELIVERABLE: exact list of files created/changed; command + real output
proving each item of the Exit Criteria; any necessary deviation,
explicitly reported instead of decided by yourself.
```

---

## Veredito — Auditoria

**Auditoria independente realizada — não me baseei no relatório do agente executor, e não rodei só o arquivo de teste dele.** Entregável real, confirmado por `git status` no repo inteiro: `tools/aidd-master/scripts/aidd.py`, `tools/aidd-enterprise/scripts/aidd.py`, `tools/aidd-master/tests/unit/test_cli_commands.py`, `tools/aidd-enterprise/tests/unit/test_cli_commands.py` — nada mais foi tocado (sem commit/push feito pelo executor, este documento não alterado por ele).

**Reprodução independente via subprocess real (script próprio, fora do arquivo de teste do executor):** escrevi um script de auditoria que roda o CLI real (`python scripts/aidd.py plan "..."` e `--help`) das duas ferramentas, para os 3 caminhos (A/B/C) + `--help` de `plan`/`prompt` — 10 combinações no total. **Todas as 10 confirmadas**, incluindo a checagem dinâmica da lista de domínios reconhecidos no texto do disclosure (não só presença de uma substring fixa).

**Reforço extra — prompts diferentes dos usados pelo executor**, para descartar qualquer coincidência de string:
- `"Crie um sistema de agendamento de clinica"` (o mesmo caso do diagnóstico original) → `Mecanismo: ⚠️ fallback de extração de palavras — NENHUM domínio conhecido reconhecido, sem LLM (heurística mais fraca)`.
- `"faca um sistema de estoque e catalogo para minha loja"` (dois domínios conhecidos simultâneos, nunca testado pelo executor) → `Mecanismo: casamento de palavra-chave — domínio(s) reconhecido(s): estoque, catalogo (lista fixa, SEM LLM)` — confirma que a lista de domínios no disclosure é gerada dinamicamente a partir do que foi de fato reconhecido, não uma string fixa.

**Byte-identidade confirmada:** `diff` do conteúdo alterado (ignorando números de linha) entre `aidd-master` e `aidd-enterprise` é idêntico tanto no código quanto nos testes — a mudança foi aplicada de forma espelhada nas duas ferramentas, como exigido.

**Preservação de comportamento confirmada:** a refatoração do `if not found_modules` duplo para `if found_modules / else` com a variável `mecanismo_usado` mantém exatamente a mesma lógica de fallback (mesma regex, mesma lista de stop-words, mesmo default hardcoded) — só adiciona o rastreamento de qual caminho foi decidido no momento certo, sem inferência posterior.

**Suítes completas rodadas por mim, exit code real (não mascarado):**
- `aidd-master`: `python -m pytest tests/ -q` → 230 passed, 4 skipped, exit 0.
- `aidd-enterprise`: `python -m pytest tests/ -q` → 221 passed, 4 skipped, exit 0. (Nota de transparência: na primeira tentativa rodei isso com `| tail -15`, o que mascarou o exit code real do pytest — percebi o erro, refiz sem pipe, e só então confirmei o exit 0 de verdade.)
- Os 2 avisos (`PytestUnhandledThreadExceptionWarning`) que aparecem nas duas suítes são de `test_add_module_server_wiring.py`, arquivo não tocado por este item — ruído pré-existente, não regressão introduzida aqui.

**`git status` limpo** além dos 4 arquivos esperados + este documento.

**Notável:** fechou de primeira, sem nenhuma correção necessária.

### Nota Final — Item 2 (Disclosure plan/prompt): 10/10

**Por que 10:**
- Todos os critérios de saída cumpridos e verificados com reprodução real e totalmente independente — inclusive além do que o executor testou (2 cenários extras com prompts próprios, incluindo reconhecimento de múltiplos domínios simultâneos).
- Escopo 100% respeitado: mecanismo de matching intocado (só revelado), nenhum outro subcomando afetado, sem commit/push, sem regressão, sem arquivo órfão.
- Mudança aplicada de forma byte-idêntica nas duas ferramentas, como exigido.
- **Efeito na dimensão Transparência:** o gap identificado no diagnóstico (`plan`/`prompt` nunca revelavam que o "entendimento de linguagem natural" é casamento de palavra-chave, zero LLM) está fechado — o usuário agora vê, em toda execução e no `--help`, exatamente qual dos 3 mecanismos foi usado. A dimensão **sobe de 8,5 para 9/10** (não 10: o disclosure cobre `plan`/`prompt`, que era o escopo deste item, mas a dimensão Transparência tem superfície mais ampla no ecossistema — outros pontos de opacidade eventualmente descobertos em itens futuros ou fora desta rodada não são cobertos por este item específico).
