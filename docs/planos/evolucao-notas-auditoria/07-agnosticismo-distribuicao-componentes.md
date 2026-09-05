# Pacote 7 — Agnosticismo de Distribuição de Componentes (Supremacia Agnóstica)

> **Status:** Definição de Pronto travada — as 4 decisões e a arquitetura (diretório canônico `componentes/` + sync por cópia + camada híbrida CLI/skill) estão confirmadas. Aguardando sua aprovação final para eu gerar os prompts de execução (2 prompts sequenciais sugeridos — ver seção "Nota sobre o tamanho deste pacote").
> **Origem:** análise feita por outro agente a seu pedido explícito, entregue em `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` + `docs/relatorios/relatorio-skills-e-comandos-aidd.html`. Registrado aqui por instrução sua para entrar no mesmo processo dos demais pacotes.
> **Regra de Ouro violada:** #6 do `AGENTS.md` — *Supremacia Agnóstica*: "Absolutamente TUDO (skills, mcps, specs, hooks, slash commands, fluxos, configurações) deve operar de forma 100% agnóstica a ambiente de execução, sistema operacional, harness [...] e provedor de LLM."

---

## Por que isto é um pacote separado do Pacote 6 (Universalidade)

O Pacote 6 já registrado (`00-PROCESSO-E-DECISOES.md` §5) é sobre uma coisa diferente: **execução** real testada em múltiplos harnesses (Codex, Gemini CLI etc.) — travado porque só há Claude Code instalado nesta máquina, um teto estrutural genuíno que nenhuma quantidade de trabalho remove agora.

Este Pacote 7 é sobre **distribuição de arquivos**: um componente (skill/MCP/spec/config/hook) precisa existir fisicamente na pasta que cada harness lê para descobri-lo. Isso é 100% verificável e corrigível **nesta máquina, agora**, sem precisar instalar mais nenhum harness — não é bloqueado pelo mesmo teto do Pacote 6. Por isso ganha um número próprio em vez de ser misturado ao 6.

---

## Verificação independente que já fiz (antes de aceitar o diagnóstico do outro agente às cegas)

Não aceitei o relatório do outro agente de olhos fechados — conferi os dois achados mais importantes eu mesmo:

1. **Confirmado via checagem direta do disco:** as 4 skills-runner da raiz (`aidd-forge-runner`, `aidd-generator-runner`, `aidd-master-runner`, `aidd-enterprise-runner`) existem em `skills/` e `.agent/skills/`, mas **nenhuma delas existe em `.claude/skills/`** — ou seja, o Claude Code (o harness que estou rodando agora, nesta própria sessão) não descobre nativamente nenhuma das 4 skills-runner do projeto.
2. **Confirmado via `grep` em `gates/G_HARNESS_COMPAT.py`:** o gate nunca menciona `.claude/skills`, `.gemini` ou `.mimocode` em nenhuma linha — por isso `python ecossistema.py audit` passa com exit 0 mesmo com o gap do item 1 presente. O ponto cego é real, não hipotético.

O restante da tabela de diagnóstico (`PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` §2.1-2.5) ainda não foi reverificado item a item por mim — isso entra como parte da Definição de Pronto deste pacote, antes de qualquer implementação (mesma disciplina dos Pacotes 1 e 2: nunca implementar sobre um diagnóstico que eu mesmo não conferi de ponta a ponta).

---

## Decisões — todas resolvidas em 05/09/2026

1. **`.mimocode/skills`: redundante, elimina-se.** Confirmado por citação direta de `AGENTS.md §5`: *"Antigravity / MimoCode / OpenCode: Carrega definições em .agent/commands/ e .agent/skills/"*. Não existe convenção própria documentada para MimoCode — a pasta separada contradiz a regra escrita do próprio ecossistema. MimoCode passa a ser servido por `.agent/skills/`, igual Antigravity/OpenCode. Conteúdo de `.mimocode/skills/` é diffado contra `.agent/skills/` antes de removido (nunca apagar sem checar divergência silenciosa).
   - **Achado adicional nesta verificação:** `AGENTS.md` não menciona Gemini CLI em nenhuma linha, mas `.gemini/skills/` existe e está em uso real (ex.: skill `seguranca-cibernetica`). Diferente do caso do MimoCode, isso é uma **omissão de documentação**, não uma contradição — não há indício de que `.gemini/skills/` seja redundante. Tratamento: mantido como convenção legítima e documentado agora em `AGENTS.md §5` (fecha de vez a causa-raiz nº4 do diagnóstico original, que apontava exatamente essa lacuna).

2. **Auto-criação de pasta de harness ausente: sempre criar (opção A), confirmado.** Coerente com Determinismo Primeiro — com fonte canônica única e comando de sync determinístico, o comportamento correto é completo e previsível, não condicional ao estado prévio do disco.

3. **Unificação dos dois injetores: entra neste mesmo ciclo.** Resolvida pela própria decisão de arquitetura abaixo — com um diretório canônico único, os dois injetores (`aidd-forge`, `aidd-generator`) passam a escrever no mesmo lugar por definição, não é mais uma escolha entre "agora ou depois".

4. **Amplitude do rollout: TODOS os tipos de componente, confirmado.** Skills, specs, MCPs, hooks, arquivos de configuração, comandos, sub-agentes e scripts — não só `skill` como prova de conceito.

---

## Arquitetura confirmada

Por proposta do usuário + reflexão conjunta registrada nesta conversa:

- **Diretório canônico único na raiz:** `componentes/` (nome escolhido por mim, sem conflito confirmado com nenhum diretório existente).
  ```
  componentes/
    aidd-forge/        {skills, mcps, specs, hooks, config, comandos, subagentes, scripts}/
    aidd-master/        (mesma estrutura)
    aidd-enterprise/     (mesma estrutura)
    aidd-generator/      (mesma estrutura)
    compartilhado/      {skills, comandos}/   ← componentes de escopo ecossistema, não de 1 ferramenta
                                                  (aqui vivem as 4 skills-runner e os slash-commands raiz)
  ```
- **Mecanismo de propagação: cópia física sincronizada por comando determinístico — não symlink.** Motivo (já registrado nesta conversa): symlink no Windows exige Admin ou Modo de Desenvolvedor, e o Git não lida bem com symlink sem configuração extra — trava específica de SO que a própria Regra de Ouro #6 proíbe. Mesma decisão já tomada antes neste projeto (`PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md`).
- **Camada híbrida:** um comando real e único (`python ecossistema.py components sync|verify --tipo <tipo> [--ferramenta <nome>]`), auditável e testável por exit code — e uma skill/slash-command fina por cima, que só invoca esse mesmo comando e apresenta o resultado de forma amigável para quem não conhece a estrutura de pastas. Zero lógica duplicada entre as duas camadas.
- **Fonte única do manifesto:** `gates/manifesto_harnesses.json` (mesmo diretório dos outros arquivos de referência dos gates — `baseline_nucleo_compartilhado.json`, `allowlist_segredos.json`, `allowlist_cli_help.json`), declarando harness × tipo de componente × pasta de destino física.

---

## Definição de Pronto

**Fase 1 — Manifesto + estrutura canônica**
1.1. Criar `gates/manifesto_harnesses.json`: harnesses (Claude Code, Antigravity, MimoCode, OpenCode, Gemini CLI, Cursor) × tipos de componente (skill, mcp, spec, hook, config, comando, subagente, script) × pasta física de destino — já refletindo as decisões 1-2 acima.
1.2. Criar a árvore vazia `componentes/<ferramenta>/<tipo>/` para as 4 ferramentas + `componentes/compartilhado/`.
1.3. Atualizar `AGENTS.md §5` para documentar `.claude/skills/` e `.gemini/skills/` (hoje usados na prática, nunca escritos no documento) e remover qualquer menção a `.mimocode/skills` como pasta própria.

**Fase 2 — Comando único de sync/verify**
2.1. Implementar `scripts/gestor_componentes.py` (raiz) com as funções `sync(tipo, ferramenta=None, dry_run=False)` e `verify(tipo, ferramenta=None)`, lendo `gates/manifesto_harnesses.json`.
2.2. Registrar `python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>] [--dry-run]` e `python ecossistema.py components verify --tipo <tipo> [--ferramenta <nome>]` em `ecossistema.py`.
2.3. `sync` sempre cria as pastas de harness declaradas no manifesto (decisão 2), nunca usa symlink, sobrescreve destino com cópia byte-idêntica da fonte canônica.

**Fase 3 — Reverificação completa do diagnóstico + migração do conteúdo existente**
3.1. Reverificar item a item a tabela §2.1 de `PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` (só 2 dos vários achados foram checados por mim até agora) — confirmar cada divergência antes de migrar.
3.2. Para cada componente hoje espalhado: `diff` manual entre cópias divergentes antes de escolher qual vira a fonte canônica dentro de `componentes/` (nunca sobrescrever sem essa checagem — regra de ouro já usada nesta sessão).
3.3. Mover o conteúdo escolhido para `componentes/<ferramenta ou compartilhado>/<tipo>/`; rodar `components sync --tipo <todos>` para regenerar todas as cópias-destino a partir da nova fonte única.
3.4. Remover `.mimocode/skills/` (decisão 1) depois do diff de segurança do item 3.2.
**Critério de saída:** `python ecossistema.py components verify --tipo <todos>` exit 0 na raiz.

**Fase 4 — Unificar os dois injetores**
4.1. `tools/aidd-forge/aidd_forge/core/injector_profiles.py` e `tools/aidd-generator/scripts/core/injector/` passam a gravar em `componentes/<ferramenta>/<tipo>/` (ou chamar `components sync` ao final da materialização) em vez de decidirem destino cada um por conta própria.
**Critério de saída:** rodar `/forge` do zero produz um projeto cujos componentes de template já nascem espelhados em todas as pastas de harness declaradas, sem passo manual.

**Fase 5 — Camada híbrida para leigos**
5.1. Criar a skill/slash-command fina (nome sugerido: `componentes-runner`) cujo conteúdo é só invocar `ecossistema.py components sync/verify` com os parâmetros certos e reportar o resultado — cobrindo todos os tipos de componente da decisão 4.
**Critério de saída:** pedir em linguagem natural "crie uma skill nova chamada X para a ferramenta Y" resulta na skill aparecendo fisicamente em todas as pastas de harness declaradas, sem o usuário tocar em nenhuma pasta manualmente.

**Fase 6 — Estender o gate existente**
6.1. `gates/G_HARNESS_COMPAT.py` passa a chamar `components verify --tipo <todos>` em vez da checagem manual hardcoded de 2 vias (linhas 34-79 atuais).

**Fase 7 — Gate novo, protocolo permanente**
7.1. Criar `gates/G_COMPONENTE_AGNOSTICO.py`: via `git diff --name-only` contra a base, identifica componentes tocados no commit e falha (exit 1) se algum não tiver a cobertura de harness exigida pelo manifesto.
7.2. Registrar em `ecossistema.py audit` (6º gate raiz).
7.3. Extrair o protocolo permanente (Seção 5 de `PLANO-CORRECAO-SKILLS-AGNOSTICAS.md`) para `docs/protocolos/PROTOCOLO-AGNOSTICIDADE-COMPONENTES.md`, referenciado a partir de `AGENTS.md` (Regra de Ouro #6).

**Validação final (todas as fases)**
- `python ecossistema.py audit` (com `G_HARNESS_COMPAT` estendido + `G_COMPONENTE_AGNOSTICO` novo) → exit 0.
- `python ecossistema.py components verify --tipo <todos>` → exit 0 na raiz e nos 4 `tools/*`.
- Suítes completas das 4 ferramentas sem regressão.
- Teste real de ponta a ponta: criar uma skill nova via a camada híbrida (Fase 5), confirmar por comando (não inspeção visual) que ela existe fisicamente em toda pasta de harness declarada no manifesto.
- Teste real de reprodução: um commit de teste que adicione um componente só em 1 harness precisa ser reprovado por `ecossistema.py audit` (prova que o protocolo da Fase 7 não depende de disciplina manual).

---

## Nota sobre o tamanho deste pacote

É o maior dos 7 pacotes — cobre migração de conteúdo real, uma ferramenta nova (`components sync/verify`), unificação de 2 injetores em 2 ferramentas diferentes, uma camada de UX nova e um gate permanente novo. Antes de gerar o prompt de execução, minha recomendação é dividir em **2 prompts sequenciais para o agente executor** (não um só): Prompt A = Fases 1-3 (manifesto, comando, migração — fecha o gap relatado originalmente) e Prompt B = Fases 4-7 (injetores, camada híbrida, gates) só depois do Prompt A auditado e confirmado. Isso reduz o raio de impacto de qualquer desvio e mantém a mesma disciplina de validação incremental já usada nos Pacotes 1 e 2.

---

## Prompt A — Fases 1-3 (manifesto, comando de sync, migração — fecha o gap original)

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa. Rode isto primeiro; só depois de auditado e aprovado o Prompt B é enviado.

```
Você vai corrigir, de forma sistêmica, um gap real de distribuição de
componentes (skills, MCPs, specs, hooks, configs, comandos, sub-agentes,
scripts) no ecossistema-aidd (monorepo em
C:\Users\trcnologia\Desktop\ecossistema-aidd) — hoje eles não existem
fisicamente em todas as pastas que cada harness (Claude Code, Antigravity,
MimoCode, OpenCode, Gemini CLI) precisa para descobri-los, violando a
Regra de Ouro #6 do AGENTS.md ("Supremacia Agnóstica"). Siga EXATAMENTE a
Definição de Pronto abaixo, não invente escopo adicional, e valide tudo
de verdade (execuções reais, exit codes reais, nunca mascarados por pipe).

CONTEXTO JÁ INVESTIGADO (não precisa redescobrir, mas DEVE reverificar
antes de migrar qualquer conteúdo — ver item 3 abaixo):
- Existe um diagnóstico prévio em `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md`
  (seção 2, tabela de inventário) — use como ponto de partida, não como
  verdade absoluta: ele mesmo pode estar desatualizado.
- Confirmado por reprodução direta: as 4 skills-runner da raiz
  (`aidd-forge-runner`, `aidd-generator-runner`, `aidd-master-runner`,
  `aidd-enterprise-runner`) existem em `skills/` e `.agent/skills/`, mas
  NENHUMA existe em `.claude/skills/` — Claude Code não as descobre.
- Confirmado via grep: `gates/G_HARNESS_COMPAT.py` nunca menciona
  `.claude/skills`, `.gemini` ou `.mimocode` — é por isso que
  `python ecossistema.py audit` passa com exit 0 mesmo com esse gap.
- `AGENTS.md §5` diz textualmente: "Antigravity / MimoCode / OpenCode:
  Carrega definições em .agent/commands/ e .agent/skills/" — ou seja,
  MimoCode NÃO tem convenção própria documentada; `.mimocode/skills/`
  (onde existir) é redundante e deve ser eliminado (depois de comparado
  via diff contra `.agent/skills/` para garantir que nada divergiu
  silenciosamente lá).
- `AGENTS.md` não documenta Gemini CLI em nenhuma linha, mas `.gemini/skills/`
  existe e está em uso real — trate como convenção legítima, não redundante,
  e adicione a documentação que falta.

DECISÕES JÁ TOMADAS PELO USUÁRIO (não reabra estas discussões):
1. `.mimocode/skills` é redundante, elimina-se (ver acima).
2. O comando de sincronização SEMPRE cria a pasta de destino de um harness
   declarado no manifesto, mesmo que ela ainda não exista no projeto.
3. Mecanismo de propagação é CÓPIA FÍSICA byte-idêntica, sincronizada por
   comando determinístico — NUNCA symlink (Windows exige Admin/Modo
   Desenvolvedor para symlink, e Git não lida bem com symlink sem config
   extra; isso violaria a própria Regra de Ouro #6 ao introduzir uma
   trava de sistema operacional).
4. O rollout cobre TODOS os tipos de componente desde o início: skill,
   mcp, spec, hook, config, comando, subagente, script — não só skill.

ARQUITETURA-ALVO (você vai construir isto):
```
componentes/
  aidd-forge/        {skills, mcps, specs, hooks, config, comandos, subagentes, scripts}/
  aidd-master/         (mesma estrutura)
  aidd-enterprise/      (mesma estrutura)
  aidd-generator/       (mesma estrutura)
  compartilhado/       {skills, comandos}/   <- componentes de escopo ecossistema,
                                                 não de 1 ferramenta específica
                                                 (aqui vivem as 4 skills-runner e os
                                                 slash-commands da raiz)
```
Este diretório `componentes/` é a ÚNICA fonte de verdade a partir de agora.
As pastas hoje existentes (`.agent/skills`, `.claude/skills`, `.gemini/skills`,
`skills/` bare, etc.) passam a ser DESTINOS GERADOS pelo comando de sync —
nunca mais editados à mão depois desta migração.

DEFINIÇÃO DE PRONTO — nesta ordem:

FASE 1 — Manifesto + estrutura canônica
1.1. Crie `gates/manifesto_harnesses.json`, declarando: cada harness
     suportado (claude-code, antigravity, mimocode, opencode, gemini-cli;
     cursor separado, mecanismo diferente — 1 arquivo de regra, não
     pasta por componente) e, para cada tipo de componente (skill, mcp,
     spec, hook, config, comando, subagente, script), quais harnesses se
     aplicam e qual a subpasta física de destino em cada um (ex.: tipo
     skill -> claude-code usa `.claude/skills`, antigravity/mimocode/
     opencode usam `.agent/skills`, gemini-cli usa `.gemini/skills`, e
     também existe uma cópia "bare" em `skills/` sem prefixo de harness).
     Para os tipos sem convenção física já estabelecida no disco (mcp,
     hook, subagente, script — investigue primeiro com Glob/grep se já
     existe alguma pasta usada na prática antes de assumir que não existe),
     proponha uma convenção consistente com a de skill/comando, documente
     a escolha explicitamente no seu relatório final para revisão, não
     decida silenciosamente algo definitivo sem reportar.
1.2. Crie a árvore vazia `componentes/<ferramenta>/<tipo>/` para as 4
     ferramentas (aidd-forge, aidd-master, aidd-enterprise, aidd-generator)
     e `componentes/compartilhado/{skills,comandos}/`.
1.3. Atualize `AGENTS.md §5`: documente `.claude/skills/` e `.gemini/skills/`
     como convenções reais (hoje usadas na prática mas nunca escritas ali),
     e remova/corrija qualquer implicação de que MimoCode tem pasta própria
     separada de `.agent/`.

FASE 2 — Comando único de sync/verify
2.1. Implemente `scripts/gestor_componentes.py` na raiz do monorepo, com
     duas funções principais: `sync(tipo, ferramenta=None, dry_run=False)`
     e `verify(tipo, ferramenta=None)`, lendo `gates/manifesto_harnesses.json`.
     `sync` copia (cópia física, nunca symlink) cada componente presente em
     `componentes/<ferramenta ou compartilhado>/<tipo>/` para toda pasta de
     destino declarada no manifesto para aquele tipo, criando a pasta de
     destino se não existir (decisão 2). `verify` só lê e compara — não
     escreve nada — e retorna exit 1 se alguma cópia estiver ausente ou
     divergir em conteúdo da fonte canônica.
2.2. Registre em `ecossistema.py`:
     `python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>] [--dry-run]`
     `python ecossistema.py components verify --tipo <tipo> [--ferramenta <nome>]`
     Aceite `--tipo todos` para rodar contra todos os tipos de uma vez.
2.3. Teste este comando ANTES de migrar qualquer conteúdo real: rode
     `sync --dry-run` contra a árvore vazia da Fase 1.2 e confirme que ele
     não quebra com diretórios vazios (não deve tentar copiar nada, mas
     também não deve dar erro).

FASE 3 — Reverificação do diagnóstico + migração do conteúdo real
3.1. Reverifique, item a item, a tabela de inventário (seção 2.1) de
     `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` — rode você mesmo
     os comandos de inventário (Glob por `**/SKILL.md` e equivalentes para
     os outros tipos), não confie cegamente na tabela já escrita lá, ela
     pode estar desatualizada.
3.2. Para cada componente com cópias divergentes entre si (não apenas
     ausentes): rode `diff` entre as cópias ANTES de decidir qual vira a
     fonte canônica dentro de `componentes/`. Se encontrar uma divergência
     de conteúdo real (não só formatação), PARE e relate — não decida
     sozinho qual versão está certa.
3.3. Mova o conteúdo escolhido para `componentes/<ferramenta ou
     compartilhado>/<tipo>/<nome>/...`. Rode
     `python ecossistema.py components sync --tipo todos` para regenerar
     TODAS as cópias-destino a partir da nova fonte única.
3.4. Remova `.mimocode/skills/` (decisão 1), só depois de ter feito o
     diff de segurança do item 3.2 contra `.agent/skills/` para confirmar
     que nada se perde.

CRITÉRIO DE SAÍDA DESTE PROMPT (rode e cole o output real de cada um):
- `python ecossistema.py components verify --tipo todos` → exit 0 na raiz
  do monorepo.
- `python ecossistema.py audit` (bateria completa de gates) → exit 0, sem
  regressão nos outros 5 gates já existentes.
- Suítes completas de aidd-forge, aidd-master, aidd-enterprise,
  aidd-generator (`python -m pytest tests/ -q` em cada) → sem regressão.
- Confirme por comando (não por inspeção visual) que as 4 skills-runner
  agora existem em `.claude/skills/` também.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não implemente ainda a unificação dos dois injetores, a camada híbrida
  de skill/slash-command, nem os gates novos (`G_HARNESS_COMPAT` estendido,
  `G_COMPONENTE_AGNOSTICO`) — isso é o Prompt B, só roda depois deste ser
  auditado.
- Não apague nenhuma cópia existente sem ter feito o diff de segurança do
  item 3.2 primeiro.
- Não faça `git commit` nem `git push`.
- Não altere `docs/planos/evolucao-notas-auditoria/07-agnosticismo-distribuicao-componentes.md`.

ENTREGÁVEL: lista exata de arquivos/pastas criados e movidos; para cada
fase, comando + output real que comprova; toda convenção que você teve
que inventar para um tipo de componente sem precedente no disco (reportada
explicitamente, não decidida em silêncio); qualquer divergência de
conteúdo encontrada no item 3.2 (relatada, não resolvida sozinho); e o
resultado completo dos critérios de saída acima.
```

## Prompt A — English version

```
You are going to systematically fix a real component-distribution gap
(skills, MCPs, specs, hooks, configs, commands, sub-agents, scripts) in
the ecossistema-aidd monorepo (C:\Users\trcnologia\Desktop\ecossistema-aidd)
— today they don't physically exist in every folder each harness (Claude
Code, Antigravity, MimoCode, OpenCode, Gemini CLI) needs to discover them,
violating Golden Rule #6 of AGENTS.md ("Agnostic Supremacy"). Follow the
Definition of Done below EXACTLY, do not invent additional scope, and
validate everything for real (real runs, real exit codes, never masked by
a pipe).

ALREADY-INVESTIGATED CONTEXT (no need to rediscover, but you MUST
re-verify before migrating any content — see item 3 below):
- A prior diagnosis exists at `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md`
  (section 2, inventory table) — use it as a starting point, not absolute
  truth: it may itself be outdated.
- Confirmed by direct reproduction: the 4 root runner skills
  (`aidd-forge-runner`, `aidd-generator-runner`, `aidd-master-runner`,
  `aidd-enterprise-runner`) exist in `skills/` and `.agent/skills/`, but
  NONE exist in `.claude/skills/` — Claude Code does not discover them.
- Confirmed via grep: `gates/G_HARNESS_COMPAT.py` never mentions
  `.claude/skills`, `.gemini`, or `.mimocode` — that's why
  `python ecossistema.py audit` passes with exit 0 despite this gap.
- `AGENTS.md §5` literally states: "Antigravity / MimoCode / OpenCode:
  Loads definitions from .agent/commands/ and .agent/skills/" — i.e.
  MimoCode has NO documented convention of its own; `.mimocode/skills/`
  (wherever it exists) is redundant and should be removed (only after
  diffing it against `.agent/skills/` to make sure nothing silently
  diverged there).
- `AGENTS.md` never documents Gemini CLI at all, but `.gemini/skills/`
  exists and is in real use — treat it as a legitimate convention, not
  redundant, and add the missing documentation.

DECISIONS ALREADY MADE BY THE USER (do not reopen these):
1. `.mimocode/skills` is redundant, remove it (see above).
2. The sync command ALWAYS creates a harness's destination folder as
   declared in the manifest, even if it doesn't exist yet in the project.
3. The propagation mechanism is byte-identical PHYSICAL COPY, synchronized
   by a deterministic command — NEVER symlink (Windows requires Admin or
   Developer Mode for symlinks, and Git doesn't handle symlinks well
   without extra config; that would violate Golden Rule #6 itself by
   introducing an OS-specific lock-in).
4. The rollout covers ALL component types from the start: skill, mcp,
   spec, hook, config, command, sub-agent, script — not just skill.

TARGET ARCHITECTURE (you are going to build this):
```
componentes/
  aidd-forge/        {skills, mcps, specs, hooks, config, comandos, subagentes, scripts}/
  aidd-master/         (same structure)
  aidd-enterprise/      (same structure)
  aidd-generator/       (same structure)
  compartilhado/       {skills, comandos}/   <- ecosystem-scoped components,
                                                 not tied to one specific tool
                                                 (this is where the 4 runner
                                                 skills and root slash-commands live)
```
This `componentes/` directory is the ONLY source of truth from now on.
The folders that exist today (`.agent/skills`, `.claude/skills`,
`.gemini/skills`, bare `skills/`, etc.) become GENERATED DESTINATIONS
produced by the sync command — never hand-edited again after this
migration.

DEFINITION OF DONE — in this order:

PHASE 1 — Manifest + canonical structure
1.1. Create `gates/manifesto_harnesses.json`, declaring: every supported
     harness (claude-code, antigravity, mimocode, opencode, gemini-cli;
     cursor is separate, different mechanism — 1 rule file, not a
     per-component folder) and, for each component type (skill, mcp, spec,
     hook, config, command, sub-agent, script), which harnesses apply and
     the physical destination subfolder for each (e.g. type skill ->
     claude-code uses `.claude/skills`, antigravity/mimocode/opencode use
     `.agent/skills`, gemini-cli uses `.gemini/skills`, and there's also
     a "bare" copy in `skills/` with no harness prefix). For types with no
     established physical convention on disk yet (mcp, hook, sub-agent,
     script — investigate first with Glob/grep whether any folder is
     already used in practice before assuming there's none), propose a
     convention consistent with skill/command's, document the choice
     explicitly in your final report for review — do not silently decide
     something final without reporting it.
1.2. Create the empty tree `componentes/<tool>/<type>/` for the 4 tools
     (aidd-forge, aidd-master, aidd-enterprise, aidd-generator) and
     `componentes/compartilhado/{skills,comandos}/`.
1.3. Update `AGENTS.md §5`: document `.claude/skills/` and
     `.gemini/skills/` as real conventions (used in practice today but
     never written there), and remove/correct any implication that
     MimoCode has its own folder separate from `.agent/`.

PHASE 2 — Single sync/verify command
2.1. Implement `scripts/gestor_componentes.py` at the monorepo root, with
     two main functions: `sync(tipo, ferramenta=None, dry_run=False)` and
     `verify(tipo, ferramenta=None)`, reading `gates/manifesto_harnesses.json`.
     `sync` copies (physical copy, never symlink) each component present
     in `componentes/<tool or compartilhado>/<type>/` to every destination
     folder declared in the manifest for that type, creating the
     destination folder if it doesn't exist (decision 2). `verify` only
     reads and compares — writes nothing — and returns exit 1 if any copy
     is missing or diverges in content from the canonical source.
2.2. Register in `ecossistema.py`:
     `python ecossistema.py components sync --tipo <type> [--ferramenta <name>] [--dry-run]`
     `python ecossistema.py components verify --tipo <type> [--ferramenta <name>]`
     Accept `--tipo todos` to run against all types at once.
2.3. Test this command BEFORE migrating any real content: run
     `sync --dry-run` against the empty tree from Phase 1.2 and confirm
     it doesn't break on empty directories (it shouldn't try to copy
     anything, but also shouldn't error out).

PHASE 3 — Re-verify the diagnosis + migrate real content
3.1. Re-verify, item by item, the inventory table (section 2.1) of
     `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` — run the inventory
     commands yourself (Glob for `**/SKILL.md` and equivalents for the
     other types), do not blindly trust the table already written there,
     it may be outdated.
3.2. For every component with copies that diverge from each other (not
     just missing ones): run `diff` between the copies BEFORE deciding
     which one becomes the canonical source inside `componentes/`. If you
     find a real content divergence (not just formatting), STOP and
     report it — do not decide by yourself which version is correct.
3.3. Move the chosen content into `componentes/<tool or
     compartilhado>/<type>/<name>/...`. Run
     `python ecossistema.py components sync --tipo todos` to regenerate
     ALL destination copies from the new single source.
3.4. Remove `.mimocode/skills/` (decision 1), only after having done the
     safety diff from item 3.2 against `.agent/skills/` to confirm nothing
     is lost.

EXIT CRITERIA FOR THIS PROMPT (run and paste the real output of each):
- `python ecossistema.py components verify --tipo todos` → exit 0 at the
  monorepo root.
- `python ecossistema.py audit` (full gate battery) → exit 0, no
  regression in the other 5 already-existing gates.
- Full test suites of aidd-forge, aidd-master, aidd-enterprise,
  aidd-generator (`python -m pytest tests/ -q` in each) → no regression.
- Confirm by command (not visual inspection) that the 4 runner skills now
  also exist in `.claude/skills/`.

SCOPE RULES — DO NOT:
- Do not implement yet the injector unification, the hybrid skill/slash-
  command layer, or the new gates (extended `G_HARNESS_COMPAT`,
  `G_COMPONENTE_AGNOSTICO`) — that's Prompt B, only runs after this one
  has been audited.
- Do not delete any existing copy without having done the item 3.2 safety
  diff first.
- Do not `git commit` or `git push`.
- Do not modify
  `docs/planos/evolucao-notas-auditoria/07-agnosticismo-distribuicao-componentes.md`.

DELIVERABLE: exact list of files/folders created and moved; for each
phase, the command + real output that proves it; every convention you had
to invent for a component type with no precedent on disk (explicitly
reported, not silently decided); any content divergence found in item 3.2
(reported, not resolved by yourself); and the full result of the exit
criteria above.
```

---

## Prompt B — Fases 4-7 (injetores, camada híbrida, gates) — só rodar depois do Prompt A auditado

> Copie o bloco abaixo integralmente para o agente executor, depois que o resultado do Prompt A tiver sido auditado e aprovado. Autocontido.

```
Você vai concluir a correção de agnosticismo de distribuição de
componentes do ecossistema-aidd (monorepo em
C:\Users\trcnologia\Desktop\ecossistema-aidd). Um trabalho anterior (Fases
1-3, já auditado e aprovado) criou o diretório canônico `componentes/`
(fonte única de verdade para skills, MCPs, specs, hooks, configs,
comandos, sub-agentes, scripts) e o comando
`python ecossistema.py components sync|verify --tipo <tipo>` (implementado
em `scripts/gestor_componentes.py`, manifesto em
`gates/manifesto_harnesses.json`). Leia esses dois arquivos primeiro para
entender o mecanismo já existente antes de continuar — não reimplemente
nada que já funciona.

Siga EXATAMENTE a Definição de Pronto abaixo, não invente escopo
adicional, valide tudo de verdade (execuções reais, exit codes reais,
nunca mascarados por pipe).

DEFINIÇÃO DE PRONTO:

FASE 4 — Unificar os dois injetores independentes
O gap original existe porque `tools/aidd-forge/aidd_forge/core/injector_profiles.py`
e `tools/aidd-generator/scripts/core/injector/` decidem, cada um por conta
própria, onde gravar um componente novo — nenhum dos dois conhece
`componentes/` nem chama o comando de sync.
4.1. Modifique `injector_profiles.py` (aidd-forge) para, ao materializar
     qualquer componente, gravar dentro de
     `componentes/aidd-forge/<tipo>/<nome>/...` e então chamar
     `python ecossistema.py components sync --tipo <tipo> --ferramenta aidd-forge`
     (via subprocess ou import direto de `gestor_componentes.py` — use o
     padrão que já existe no arquivo para chamar outros módulos/scripts).
4.2. Faça o mesmo para o injetor de `tools/aidd-generator/scripts/core/injector/`.
4.3. `tools/aidd-forge/aidd_forge/core/harness_sync.py` (o sincronizador
     antigo, que só espelhava harness já existente) deixa de ser
     necessário — remova-o SE E SOMENTE SE nenhum outro código ainda o
     chamar (confirme com grep antes de remover; se algo mais depender
     dele, pare e relate em vez de decidir sozinho).
**Critério de saída:** rodar `/forge` do zero num projeto de teste
(recriar `sandbox-forge-teste` se necessário) produz um projeto cujos
componentes de template já nascem espelhados em todas as pastas de
harness declaradas no manifesto, sem nenhum passo manual.

FASE 5 — Camada híbrida para usuário leigo
5.1. Crie uma skill nova, `componentes-runner` (siga exatamente o mesmo
     padrão estrutural das 4 skills-runner já existentes em `skills/` —
     leia uma delas primeiro), cujo `SKILL.md` documenta: quando o usuário
     pedir em linguagem natural para criar/atualizar um componente (skill,
     mcp, spec, hook, config, comando, subagente ou script) para uma
     ferramenta específica ou para o ecossistema como um todo, o agente
     deve (a) criar o arquivo dentro de
     `componentes/<ferramenta ou compartilhado>/<tipo>/<nome>/...`
     seguindo o template apropriado ao tipo, (b) rodar
     `python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>]`,
     e (c) reportar ao usuário, de forma legível, em quais pastas de
     harness o componente agora existe (saída do próprio comando, não
     invente um resumo). ZERO lógica de sincronização deve viver dentro
     da skill — ela só invoca o comando real que já existe.
5.2. Registre esta skill nas mesmas 2 localizações que as outras 4
     skills-runner (`skills/`, `.agent/skills/`) e rode
     `python ecossistema.py components sync --tipo skill --ferramenta compartilhado`
     para que ela também se propague para `.claude/skills/` e demais
     harnesses automaticamente (prova viva do próprio mecanismo que você
     acabou de construir).
**Critério de saída:** peça, em linguagem natural, para criar uma skill de
teste através desta nova skill/slash-command, e confirme por comando
(`components verify`) que ela aparece fisicamente em toda pasta de
harness declarada — sem você ter tocado em nenhuma pasta manualmente.

FASE 6 — Estender o gate existente
6.1. Reescreva `gates/G_HARNESS_COMPAT.py` para chamar
     `python ecossistema.py components verify --tipo todos` em vez da
     checagem manual hardcoded de 2 vias que existe hoje (skills/ vs
     .agent/skills/, só para as 4 skills-runner). Mantenha as outras
     checagens do arquivo que não são sobre isso (arquivos-ponteiro para
     AGENTS.md, gates documentados vs em disco).
**Critério de saída:** `python ecossistema.py audit` continua exit 0, e
`G_HARNESS_COMPAT` agora reprova de verdade se você remover uma cópia de
`.claude/skills/` manualmente como teste (reverta depois do teste).

FASE 7 — Gate novo, protocolo permanente
7.1. Crie `gates/G_COMPONENTE_AGNOSTICO.py`: via
     `git diff --name-only <base>` (base = HEAD do commit anterior, ou
     parâmetro configurável), identifica quais caminhos tocados pertencem
     a algum `componentes/<...>/<tipo>/<nome>/` e, para cada um, roda
     `components verify --tipo <tipo> --ferramenta <ferramenta>` — falha
     (exit 1) se algum componente tocado não tiver cobertura completa nas
     pastas de harness exigidas pelo manifesto.
7.2. Registre em `ecossistema.py audit` como o 6º gate raiz da bateria.
7.3. Extraia o checklist da Seção 5 de `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md`
     para `docs/protocolos/PROTOCOLO-AGNOSTICIDADE-COMPONENTES.md`, e
     referencie esse documento a partir de `AGENTS.md`, na própria Regra
     de Ouro #6.
7.4. Escreva um teste que prove a Fase 7 funciona de verdade: crie um
     componente de teste só em 1 pasta de harness (violação deliberada),
     confirme que `python ecossistema.py audit` reprova apontando
     exatamente esse componente, depois rode `components sync` para
     corrigir e confirme que audit volta a passar. Limpe o componente de
     teste ao final (não deixe lixo no repositório).

CRITÉRIO DE SAÍDA FINAL (rode e cole o output real de cada um):
- `python ecossistema.py audit` (6 gates agora) → exit 0.
- `python ecossistema.py components verify --tipo todos` → exit 0 na raiz
  e em cada `tools/*`.
- Suítes completas das 4 ferramentas → sem regressão.
- O teste de reprodução da Fase 7.4 (falha antes / passa depois).
- O teste de ponta a ponta da Fase 5 (criar componente via linguagem
  natural, confirmar propagação real).

REGRAS DE ESCOPO — NÃO FAÇA:
- Não toque em nada que já foi implementado e auditado no Prompt A além
  do necessário para integrar com ele.
- Não faça `git commit` nem `git push`.
- Não altere `docs/planos/evolucao-notas-auditoria/07-agnosticismo-distribuicao-componentes.md`.

ENTREGÁVEL: lista exata de arquivos criados/alterados; para cada fase,
comando + output real que comprova; qualquer desvio necessário da
Definição de Pronto, reportado explicitamente em vez de decidido sozinho.
```

## Prompt B — English version

```
You are going to complete the component-distribution agnosticism fix for
ecossistema-aidd (monorepo at C:\Users\trcnologia\Desktop\ecossistema-aidd).
Prior work (Phases 1-3, already audited and approved) created the
canonical `componentes/` directory (single source of truth for skills,
MCPs, specs, hooks, configs, commands, sub-agents, scripts) and the
`python ecossistema.py components sync|verify --tipo <type>` command
(implemented in `scripts/gestor_componentes.py`, manifest at
`gates/manifesto_harnesses.json`). Read both files first to understand
the existing mechanism before continuing — do not reimplement anything
that already works.

Follow the Definition of Done below EXACTLY, do not invent additional
scope, validate everything for real (real runs, real exit codes, never
masked by a pipe).

DEFINITION OF DONE:

PHASE 4 — Unify the two independent injectors
The original gap exists because
`tools/aidd-forge/aidd_forge/core/injector_profiles.py` and
`tools/aidd-generator/scripts/core/injector/` each decide, on their own,
where to write a new component — neither knows about `componentes/` or
calls the sync command.
4.1. Modify `injector_profiles.py` (aidd-forge) so that, when
     materializing any component, it writes into
     `componentes/aidd-forge/<type>/<name>/...` and then calls
     `python ecossistema.py components sync --tipo <type> --ferramenta aidd-forge`
     (via subprocess or by importing `gestor_componentes.py` directly —
     use whatever pattern the file already uses to call other
     modules/scripts).
4.2. Do the same for the injector at
     `tools/aidd-generator/scripts/core/injector/`.
4.3. `tools/aidd-forge/aidd_forge/core/harness_sync.py` (the old
     synchronizer, which only mirrored into already-existing harness
     folders) becomes unnecessary — remove it ONLY IF no other code still
     calls it (confirm with grep before removing; if something else
     depends on it, stop and report instead of deciding by yourself).
**Exit criterion:** running `/forge` from scratch on a test project
(recreate `sandbox-forge-teste` if needed) produces a project whose
template components are already mirrored into every harness folder
declared in the manifest, with no manual step.

PHASE 5 — Hybrid layer for non-technical users
5.1. Create a new skill, `componentes-runner` (follow exactly the same
     structural pattern as the 4 existing runner skills in `skills/` —
     read one of them first), whose `SKILL.md` documents: when the user
     asks, in natural language, to create/update a component (skill, mcp,
     spec, hook, config, command, sub-agent, or script) for a specific
     tool or for the ecosystem as a whole, the agent must (a) create the
     file inside `componentes/<tool or compartilhado>/<type>/<name>/...`
     following the template appropriate to that type, (b) run
     `python ecossistema.py components sync --tipo <type> [--ferramenta <name>]`,
     and (c) report back to the user, in readable form, which harness
     folders the component now exists in (the command's own output, do
     not invent a summary). ZERO sync logic should live inside the skill
     — it only invokes the real command that already exists.
5.2. Register this skill in the same 2 locations as the other 4 runner
     skills (`skills/`, `.agent/skills/`) and run
     `python ecossistema.py components sync --tipo skill --ferramenta compartilhado`
     so it also propagates into `.claude/skills/` and other harnesses
     automatically (live proof of the very mechanism you just built).
**Exit criterion:** ask, in natural language, to create a test skill
through this new skill/slash-command, and confirm by command
(`components verify`) that it physically exists in every declared harness
folder — without you having touched any folder by hand.

PHASE 6 — Extend the existing gate
6.1. Rewrite `gates/G_HARNESS_COMPAT.py` to call
     `python ecossistema.py components verify --tipo todos` instead of
     today's hardcoded manual 2-way check (skills/ vs .agent/skills/,
     only for the 4 runner skills). Keep the file's other checks that
     aren't about this (pointer files to AGENTS.md, gates documented vs
     on disk).
**Exit criterion:** `python ecossistema.py audit` still exits 0, and
`G_HARNESS_COMPAT` now genuinely fails if you manually remove a copy from
`.claude/skills/` as a test (revert after testing).

PHASE 7 — New gate, permanent protocol
7.1. Create `gates/G_COMPONENTE_AGNOSTICO.py`: via
     `git diff --name-only <base>` (base = previous commit's HEAD, or a
     configurable parameter), identify which touched paths belong to some
     `componentes/<...>/<type>/<name>/` and, for each one, run
     `components verify --tipo <type> --ferramenta <tool>` — fail
     (exit 1) if any touched component lacks full coverage across the
     harness folders required by the manifest.
7.2. Register it in `ecossistema.py audit` as the 6th root gate in the
     battery.
7.3. Extract the checklist from Section 5 of
     `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` into
     `docs/protocolos/PROTOCOLO-AGNOSTICIDADE-COMPONENTES.md`, and
     reference that document from `AGENTS.md`, right under Golden Rule #6.
7.4. Write a test that proves Phase 7 genuinely works: create a test
     component in only 1 harness folder (deliberate violation), confirm
     that `python ecossistema.py audit` fails, pointing exactly at that
     component, then run `components sync` to fix it and confirm audit
     passes again. Clean up the test component at the end (leave no
     garbage in the repository).

FINAL EXIT CRITERIA (run and paste the real output of each):
- `python ecossistema.py audit` (6 gates now) → exit 0.
- `python ecossistema.py components verify --tipo todos` → exit 0 at the
  root and in each `tools/*`.
- Full test suites of the 4 tools → no regression.
- The Phase 7.4 reproduction test (failing before / passing after).
- The Phase 5 end-to-end test (creating a component via natural language,
  confirming real propagation).

SCOPE RULES — DO NOT:
- Do not touch anything already implemented and audited in Prompt A
  beyond what's needed to integrate with it.
- Do not `git commit` or `git push`.
- Do not modify
  `docs/planos/evolucao-notas-auditoria/07-agnosticismo-distribuicao-componentes.md`.

DELIVERABLE: exact list of files created/changed; for each phase, the
command + real output that proves it; any necessary deviation from the
Definition of Done, explicitly reported instead of decided by yourself.
```

---

## Veredito

*(pendente — Prompt A pronto para envio ao agente executor; Prompt B só deve ser enviado depois do resultado do Prompt A auditado e aprovado)*
