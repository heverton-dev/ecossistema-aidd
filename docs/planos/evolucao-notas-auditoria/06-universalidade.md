# Pacote 6 — Universalidade / Agnosticismo Multi-Harness

> **Status:** ✅ CONCLUÍDO em 05/09/2026 — nota final 9.5/10 (ver Veredito ao final do documento).
> **Origem:** `docs/planos/PLANO-EVOLUCAO-NOTAS-AUDITORIA.md` (dimensão "Universalidade / Agnosticismo", nota 8/10, registrada como "sem mudança possível agora").
> **Contribui para:** dimensão Universalidade/Agnosticismo (8/10 → nota a definir após a Fase 1).

---

## Por que isto foi reaberto (e corrigido no meio do caminho)

A premissa original ("só Claude Code instalado") nunca tinha sido reverificada. Uma checagem real encontrou os 7 harnesses instalados — inclusive MimoCode e FreeBuff, que eu tinha marcado erroneamente como "ausentes" na minha primeira passada por procurar pelos nomes errados (`mimocode` em vez do binário real `mimo`; não tinha verificado `freebuff` de todo). O usuário corrigiu isso me dando os nomes reais dos binários.

Além disso, ao reconferir os resultados, descobri que **o primeiro teste do `opencode` foi um falso negativo** (cache frio na primeira chamada — a segunda e terceira chamadas, estáveis, encontraram as 5 skills). Isso me levou a reconferir TODOS os resultados negativos antes de aceitar qualquer um como definitivo — inclusive uma segunda chamada real de LLM ao `agy` (Antigravity), aprovada explicitamente pelo usuário, que confirmou que aquele resultado negativo É real (estável em 2 chamadas independentes, não cache).

---

## Tabela final — todos os 7 harnesses, testados de verdade, resultado estável confirmado

| Harness | Instalado | Descobre as 5 skills do projeto? | Convenção real observada |
|---|---|---|---|
| **Claude Code** | Sim | Sim (linha de base desta sessão) | `.claude/skills/` |
| **`gemini-cli`** v0.58.0 | Sim | **4/5** — `componentes-runner` falha | `.gemini/skills/`; parser YAML sensível a BOM |
| **`grok`** v1.0.5 | Sim | **5/5** | Lê `.claude/skills/`, tolera BOM |
| **`opencode`** v1.18.27 | Sim | **5/5** (corrigido — 1º teste deu falso negativo por cache frio) | Lê `.claude/skills/`, confirmado estável em 3 chamadas |
| **`mimo`** (MimoCode) v0.1.14 | Sim | **5/5** | Lê `.claude/skills/` |
| **`hermes`** v0.20.4 | Sim | **0/5** (estável, confirmado 2x) | Exige `hermes skills trust` explícito por projeto (nunca feito); convenção documentada é `.agents/skills` (plural) + `.hermes/skills` |
| **`agy`** (Antigravity) | Sim | **0/5** (estável, confirmado com 2 chamadas reais de LLM) | Mecanismo de descoberta real não identificado — não é `.claude/skills/` nem cache frio |
| **`freebuff`** v0.0.170 | Sim | **Não testável via CLI script** | `--help` não expõe nenhum modo não-interativo/headless — só suporta sessão de chat interativa |
| **`kiro-cli`** | Sim | N/A (não é bug) | Usa conceito de "agente" (`.kiro/agents/`), não "skill" — fora desta convenção |

---

## Achados concretos, em ordem de importância

### 1. `.claude/skills/` é, na prática, mais universal do que `.agent/skills/` ou `.gemini/skills/`

`grok`, `opencode` e `mimo` (3 produtos diferentes) leem `.claude/skills/` diretamente — nenhum deles usa a pasta `.agent/skills/` que `AGENTS.md §5` documenta como convenção para "Antigravity / MimoCem / OpenCode". Isso é uma descoberta nova e importante: **a pasta que hoje faz o trabalho pesado de descoberta real não é a que o documento afirma.**

### 2. Bug real e concreto: BOM UTF-8 quebra o parser do `gemini-cli`

`componentes/compartilhado/skills/componentes-runner/SKILL.md` (fonte canônica) começa com um BOM UTF-8 (`EF BB BF`) antes do `---` do frontmatter — confirmado via `xxd`. Propagado corretamente (mesmo byte) para as 4 cópias pelo sync do Pacote 7. `gemini-cli` falha silenciosamente ao ver o BOM; `grok`/`opencode`/`mimo`/Claude Code toleram o mesmo arquivo sem problema — confirma que o bug é específico do parser do `gemini-cli`, não do mecanismo de distribuição.

### 3. `hermes` e `agy` (Antigravity) genuinemente não descobrem nada — por razões diferentes e reais

- `hermes`: mecanismo documentado no próprio `--help` (`hermes skills trust`) — decisão de segurança do produto, nunca executada para este projeto. Resolvível com uma chamada de comando, se o usuário quiser confiar no projeto.
- `agy`: mecanismo de descoberta real não identificado nesta investigação — confirmado que NÃO é falso negativo de cache (2 chamadas reais de LLM, mesmo resultado), mas a causa raiz exata fica como item de investigação futura (Fase 3, não bloqueia o fechamento deste pacote).

### 4. `freebuff` não tem modo não-interativo — limitação de ferramenta, não do ecossistema

Instalado e funcional, mas seu `--help` não expõe nenhuma flag de execução headless/script (`-p`, `--print`, etc. como as outras têm). Testar a descoberta de skills exigiria uma sessão de chat interativa manual — fora do que dá para automatizar nesta auditoria. Registrado como "não testável via CLI", não como falha.

### 5. `kiro-cli` continua fora de escopo — conceito diferente, não um harness desta convenção

Confirmado de novo: usa `.kiro/agents/`, não tem noção de "skill" nenhuma.

---

## Definição de Pronto

**Fase 1 — Corrigir o bug real e confirmado (BOM em `componentes-runner`)**
1.1. Remover o BOM UTF-8 de `componentes/compartilhado/skills/componentes-runner/SKILL.md` (fonte canônica), preservando 100% do conteúdo.
1.2. Rodar `python ecossistema.py components sync --tipo skill --ferramenta compartilhado` para repropagar a versão corrigida.
1.3. Teste real: rodar `gemini skills list --all` de novo e confirmar que `componentes-runner` passa a aparecer — teste 100% real, sem mock, contra a instalação real desta máquina.
1.4. Adicionar checagem permanente (estender `gates/G_HARNESS_COMPAT.py` ou o `verify()` de `gestor_componentes.py`, decidir qual encaixa melhor durante a implementação) que reprova qualquer componente da fonte canônica que comece com um BOM UTF-8 — para que este tipo de regressão silenciosa não se repita.

**Fase 2 — Corrigir `AGENTS.md §5` com a convenção real confirmada**
2.1. Reescrever a seção sobre convenções de harness para refletir o que foi **realmente testado e confirmado**, não suposição:
   - `.claude/skills/`: confirmado funcionando em Claude Code, `grok`, `opencode`, `mimo` (MimoCode) — é a convenção mais amplamente compatível encontrada.
   - `.gemini/skills/`: confirmado funcionando em `gemini-cli` (com a ressalva do bug de BOM corrigido na Fase 1).
   - `.agent/skills/`: manter como está fisicamente distribuída (não quebra nada), mas remover/corrigir a afirmação de que é isso que Antigravity/MimoCode/OpenCode carregam — a evidência real mostra que MimoCode e OpenCode carregam de `.claude/skills/`, não de `.agent/skills/`.
   - `hermes`: documentar a convenção real (`.agents/skills` plural + `.hermes/skills`) e o requisito de `hermes skills trust` por projeto — e registrar explicitamente que este ecossistema ainda não executou esse passo.
   - `agy`/Antigravity: documentar como "instalado e funcional, mas mecanismo de descoberta de skills do projeto não confirmado nesta auditoria" — honesto, não uma afirmação de que funciona.
   - `freebuff`: documentar como "instalado, sem modo não-interativo disponível para testar via automação".
   - `kiro-cli`: documentar como "usa convenção própria de agentes, não parte desta convenção de skills".
2.2. Deixar explícito que esta seção reflete testes reais rodados em 05/09/2026 nesta máquina, com nota para reverificar se alguma dessas ferramentas for atualizada.

**Fase 3 — Investigação adicional (opcional, não bloqueia o fechamento)**
3.1. Se houver tempo/interesse: investigar o mecanismo real de descoberta de skills do `agy`/Antigravity (não identificado nesta rodada) e se `hermes skills trust` resolveria de fato a descoberta para esse harness (testável com 1 comando, sem custo de LLM). Documentar como "mecanismo desconhecido" é uma resposta honesta e válida se não for encontrado facilmente.

**Critério de saída (rodar e colar o output real de cada um):**
- `gemini skills list --all` → `componentes-runner` aparece na lista.
- `python ecossistema.py components verify --tipo skill --ferramenta compartilhado` → exit 0.
- Gate novo/estendido de checagem de BOM → testado com um arquivo de teste deliberadamente criado com BOM (confirma reprovação), removido depois; confirma que passa com os arquivos reais (sem BOM, pós Fase 1).
- `python ecossistema.py audit` (bateria raiz) → exit 0, sem regressão.
- Diff de `AGENTS.md §5` revisado na auditoria, confirmando que cada frase nova tem evidência real correspondente neste documento.

---

## Nota sobre o tamanho deste pacote

Pequeno e focado — 1 bug real (BOM) + 1 correção de documentação (convenções reais vs. supostas), ambos no monorepo raiz. Cabe em **1 prompt único**.

**Aprovado pelo usuário em 05/09/2026.** Prompt de execução abaixo.

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai corrigir um bug real e uma imprecisão documental real no
ecossistema-aidd (monorepo em C:\Users\trcnologia\Desktop\ecossistema-aidd),
achados numa auditoria que testou de verdade 7 harnesses de IA reais e
instalados nesta máquina (Claude Code, gemini-cli, grok, opencode, mimo/
MimoCode, hermes, agy/Antigravity — mais freebuff e kiro-cli, sem achado
acionável para eles). Siga EXATAMENTE a Definição de Pronto abaixo, não
invente escopo adicional, e valide tudo de verdade (execuções reais, exit
codes reais, nunca mascarados por pipe).

CONTEXTO JÁ INVESTIGADO E CONFIRMADO (não precisa redescobrir, mas
reproduza você mesmo os comandos-chave para confirmar antes de aplicar a
correção):
- `componentes/compartilhado/skills/componentes-runner/SKILL.md` (fonte
  canônica) começa com um BOM UTF-8 (bytes `EF BB BF`) antes do `---` do
  frontmatter YAML — confirmado via `xxd componentes/compartilhado/skills/componentes-runner/SKILL.md | head -1`.
  Os outros 4 arquivos-fonte em `componentes/compartilhado/skills/`
  (`aidd-forge-runner`, `aidd-generator-runner`, `aidd-master-runner`,
  `aidd-enterprise-runner`) NÃO têm esse BOM.
- Rodando `gemini skills list --all` (binário real `gemini`, instalado
  nesta máquina) a partir da raiz do monorepo, as 4 skills sem BOM
  aparecem na lista; `componentes-runner` NÃO aparece, sem nenhum erro
  impresso — o parser de frontmatter do `gemini-cli` falha silenciosamente
  ao encontrar o BOM antes do `---`.
- Rodando `grok inspect` (binário real `grok`, instalado nesta máquina),
  `componentes-runner` aparece normalmente, mesmo com o BOM — confirma que
  o bug é específico do parser do `gemini-cli`, não do arquivo em si nem
  do mecanismo de sync do Pacote 7 (que já propagou o BOM corretamente,
  byte a byte, para as 4 cópias — isso está certo, o problema é o BOM
  estar lá desde a criação original do arquivo).
- `AGENTS.md §5` (linha ~85) afirma: *"Antigravity / MimoCode / OpenCode:
  Carrega definições em .agent/commands/ e .agent/skills/"*. Testes reais
  contra instalações reais de `opencode` (`opencode debug skill`) e
  `mimo`/MimoCode (`mimo debug skill`) mostram que os dois na verdade
  carregam de **`.claude/skills/`** (confirmado pelo campo `location` no
  JSON de saída de ambos os comandos), não de `.agent/skills/`. `grok`
  (não mencionado em `AGENTS.md` hoje) também lê de `.claude/skills/`.
  `hermes` (também não mencionado) tem uma convenção documentada no
  próprio `--help` de `hermes skills trust`: `.agents/skills` (plural) +
  `.hermes/skills`, exigindo um passo explícito de "trust" por projeto
  (nunca executado para este monorepo). `agy` (Antigravity) foi testado
  com uma chamada real de LLM (`agy --print "..."` perguntando por skills
  carregadas mencionando 'aidd') e respondeu que não via nenhuma — 2
  chamadas independentes, mesmo resultado, mecanismo de descoberta real
  não identificado. `freebuff` está instalado mas seu `--help` não expõe
  nenhum modo não-interativo, então não foi possível testar via script.
  `kiro-cli` usa um conceito de "agente" (`.kiro/agents/`) totalmente
  diferente de "skill" — não faz parte desta convenção.

DECISÕES JÁ TOMADAS (não reabra estas discussões):
1. O BOM é o bug real a corrigir — não é para "consertar" o parser de
   nenhum harness externo (não temos acesso ao código deles), é para
   remover a causa raiz do lado do ecossistema.
2. `AGENTS.md §5` deve refletir só o que foi realmente testado e
   confirmado nesta auditoria — nunca reintroduzir uma afirmação não
   verificada no lugar da que está sendo corrigida.
3. Não migrar nenhuma pasta física existente (`.agent/skills/`,
   `.gemini/skills/`, `skills/` bare) — elas continuam existindo e sendo
   geradas pelo `gestor_componentes.py sync` normalmente. Esta correção é
   só sobre a EXATIDÃO da documentação e sobre o bug do BOM, não sobre
   redesenhar a distribuição física.

DEFINIÇÃO DE PRONTO — nesta ordem:

FASE 1 — Corrigir o BOM em `componentes-runner`
1.1. Reescreva `componentes/compartilhado/skills/componentes-runner/SKILL.md`
     sem o BOM UTF-8 inicial, preservando exatamente todo o resto do
     conteúdo, byte a byte (confirme com um diff de conteúdo, ignorando
     só o BOM, que nada mais mudou).
1.2. Rode `python ecossistema.py components sync --tipo skill --ferramenta compartilhado`
     para repropagar a versão corrigida para as 4 cópias
     (`.claude/skills/`, `.agent/skills/`, `.gemini/skills/`, `skills/`
     bare).
1.3. Teste real: rode `gemini skills list --all` (o binário real
     `gemini`, se disponível nesta máquina/ambiente de execução; se não
     estiver disponível no ambiente onde você está rodando, relate isso
     explicitamente e pule para 1.4 sem simular o resultado) e confirme
     que `componentes-runner` agora aparece na lista.
1.4. Adicione uma checagem permanente contra regressão: estenda
     `gates/G_HARNESS_COMPAT.py` OU o `verify()` de
     `scripts/gestor_componentes.py` (escolha o que encaixar melhor na
     estrutura já existente, mas não crie um gate novo e separado se um
     dos dois já rodar em todo `audit`) para reprovar (exit 1) se
     qualquer arquivo dentro de `componentes/` começar com um BOM UTF-8
     (`EF BB BF`). Teste real: crie um arquivo de teste temporário com BOM
     dentro de `componentes/`, confirme que a checagem reprova apontando
     o arquivo certo, remova o arquivo de teste, confirme que a checagem
     volta a passar com o estado real do repositório.

FASE 2 — Corrigir `AGENTS.md §5` com a convenção real confirmada
2.1. Reescreva a linha atual (~85) que afirma "Antigravity / MimoCode /
     OpenCode: Carrega definições em .agent/commands/ e .agent/skills/"
     para refletir a evidência real:
     - `.claude/skills/` confirmado funcionando em `grok`, `opencode` e
       `mimo` (MimoCode) — além de Claude Code, já documentado
       separadamente na linha seguinte.
     - Mantenha a menção a `.agent/` como a pasta física que o mecanismo
       de sync do Pacote 7 continua gerando (não pare de gerá-la — ela
       pode servir outras ferramentas no futuro), mas não afirme que
       Antigravity/MimoCode/OpenCode a carregam, já que a evidência real
       mostra que não é por aí que esses 3 descobrem hoje.
     - Adicione entradas novas, honestas, para os harnesses que a
       auditoria testou e que `AGENTS.md` ainda não menciona: `grok` (lê
       `.claude/skills/`), `hermes` (convenção `.agents/skills` plural +
       `.hermes/skills`, exige `hermes skills trust` por projeto — nunca
       executado aqui), `agy`/Antigravity (mecanismo de descoberta real
       não confirmado nesta auditoria — não afirme que funciona),
       `freebuff` (instalado, sem modo não-interativo para testar via
       automação), `kiro-cli` (usa convenção própria de "agentes" em
       `.kiro/agents/`, não é parte desta convenção de skills).
2.2. Adicione uma nota de proveniência: esta seção reflete testes reais
     rodados em 05/09/2026 contra instalações reais nesta máquina — não
     suposição — e deve ser reverificada se alguma dessas ferramentas for
     atualizada ou se o mecanismo de descoberta de `agy`/`freebuff` for
     identificado no futuro.

FASE 3 (OPCIONAL, NÃO BLOQUEIA O FECHAMENTO) — Investigação adicional
3.1. Se sobrar tempo: investigue se `hermes skills trust .` (rodado na
     raiz do monorepo) faz `hermes skills list` passar a descobrir as 5
     skills do projeto — é um teste de 1 comando, sem custo de LLM. Se
     funcionar, documente o comando como parte da Fase 2.1 (nota sobre
     hermes). Se não funcionar ou você não tiver como testar isso no seu
     ambiente, não invente uma explicação — relate que não foi possível
     confirmar.
3.2. NÃO tente investigar o mecanismo de descoberta do `agy` gastando
     chamadas de LLM por conta própria — isso já foi decidido como fora
     de escopo obrigatório deste pacote (item 3.1 do documento original),
     e cada chamada tem custo real na conta do usuário.

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- `gemini skills list --all` (se disponível no seu ambiente) →
  `componentes-runner` aparece na lista, no mesmo formato das outras 4.
- `python ecossistema.py components verify --tipo skill --ferramenta compartilhado` → exit 0.
- O teste da Fase 1.4 (gate/checagem de BOM reprova um arquivo de teste
  com BOM, depois volta a passar após a remoção do arquivo de teste).
- `python ecossistema.py audit` (bateria raiz) → exit 0, sem regressão
  nos outros gates.
- Confirme por comando (`git status`) que nenhum arquivo de teste (BOM ou
  outro) ficou no repositório real.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não tente "consertar" nenhum harness externo (gemini-cli, opencode,
  etc.) — você só tem controle sobre o lado do ecossistema.
- Não migre nem redesenhe a distribuição física de componentes
  (`.agent/skills/`, `.gemini/skills/`, `skills/` bare continuam sendo
  gerados normalmente pelo `gestor_componentes.py sync`).
- Não gaste chamadas de LLM investigando o `agy`/Antigravity por conta
  própria (ver item 3.2).
- Não faça `git commit` nem `git push`.
- Não altere `docs/planos/evolucao-notas-auditoria/06-universalidade.md`.

ENTREGÁVEL: lista exata de arquivos alterados; para cada fase, comando +
output real que comprova; se `gemini`/`hermes` não estiverem disponíveis
no seu ambiente de execução, relate isso explicitamente em vez de
simular o resultado; qualquer desvio necessário, reportado explicitamente
em vez de decidido sozinho.
```

## Prompt de Execução — English version

```
You are going to fix a real bug and a real documentation inaccuracy in
ecossistema-aidd (monorepo at C:\Users\trcnologia\Desktop\ecossistema-aidd),
found during an audit that tested 7 real AI harnesses actually installed
on this machine (Claude Code, gemini-cli, grok, opencode, mimo/MimoCode,
hermes, agy/Antigravity — plus freebuff and kiro-cli, with no actionable
finding for those two). Follow the Definition of Done below EXACTLY, do
not invent additional scope, and validate everything for real (real
runs, real exit codes, never masked by a pipe).

ALREADY-INVESTIGATED AND CONFIRMED CONTEXT (no need to rediscover, but
reproduce the key commands yourself to confirm before applying the fix):
- `componentes/compartilhado/skills/componentes-runner/SKILL.md` (the
  canonical source) starts with a UTF-8 BOM (bytes `EF BB BF`) before the
  frontmatter's `---` — confirmed via
  `xxd componentes/compartilhado/skills/componentes-runner/SKILL.md | head -1`.
  The other 4 source files in `componentes/compartilhado/skills/`
  (`aidd-forge-runner`, `aidd-generator-runner`, `aidd-master-runner`,
  `aidd-enterprise-runner`) do NOT have this BOM.
- Running `gemini skills list --all` (the real `gemini` binary, installed
  on this machine) from the monorepo root, the 4 BOM-free skills appear
  in the list; `componentes-runner` does NOT appear, with no error
  printed at all — `gemini-cli`'s frontmatter parser silently fails when
  it encounters the BOM before `---`.
- Running `grok inspect` (the real `grok` binary, installed on this
  machine), `componentes-runner` shows up normally, even with the BOM —
  confirming the bug is specific to `gemini-cli`'s parser, not the file
  itself nor Package 7's sync mechanism (which already propagated the BOM
  correctly, byte for byte, to all 4 copies — that part is correct; the
  problem is the BOM having been there since the file was first created).
- `AGENTS.md §5` (around line 85) states: *"Antigravity / MimoCode /
  OpenCode: Carrega definições em .agent/commands/ e .agent/skills/"*.
  Real tests against real installations of `opencode` (`opencode debug skill`)
  and `mimo`/MimoCode (`mimo debug skill`) show both actually load from
  **`.claude/skills/`** (confirmed by the `location` field in both
  commands' JSON output), not from `.agent/skills/`. `grok` (not
  mentioned in `AGENTS.md` today) also reads from `.claude/skills/`.
  `hermes` (also not mentioned) has a documented convention in its own
  `--help` for `hermes skills trust`: `.agents/skills` (plural) +
  `.hermes/skills`, requiring an explicit per-project "trust" step (never
  run for this monorepo). `agy` (Antigravity) was tested with a real LLM
  call (`agy --print "..."` asking about loaded skills mentioning 'aidd')
  and answered it saw none — 2 independent calls, same result, real
  discovery mechanism not identified. `freebuff` is installed but its
  `--help` exposes no non-interactive mode, so it could not be tested via
  script. `kiro-cli` uses an entirely different "agent" concept
  (`.kiro/agents/`) — not part of this skill convention at all.

DECISIONS ALREADY MADE (do not reopen these):
1. The BOM is the real bug to fix — this is NOT about "fixing" any
   external harness's parser (we have no access to their code), it's
   about removing the root cause on the ecosystem's side.
2. `AGENTS.md §5` should reflect only what was actually tested and
   confirmed in this audit — never reintroduce an unverified claim in
   place of the one being corrected.
3. Do not migrate any existing physical folder (`.agent/skills/`,
   `.gemini/skills/`, bare `skills/`) — they keep existing and being
   generated by `gestor_componentes.py sync` normally. This fix is only
   about the ACCURACY of the documentation and the BOM bug, not about
   redesigning physical distribution.

DEFINITION OF DONE — in this order:

PHASE 1 — Fix the BOM in `componentes-runner`
1.1. Rewrite `componentes/compartilhado/skills/componentes-runner/SKILL.md`
     without the leading UTF-8 BOM, preserving exactly everything else in
     the content, byte for byte (confirm with a content diff, ignoring
     only the BOM, that nothing else changed).
1.2. Run `python ecossistema.py components sync --tipo skill --ferramenta compartilhado`
     to re-propagate the fixed version to all 4 copies (`.claude/skills/`,
     `.agent/skills/`, `.gemini/skills/`, bare `skills/`).
1.3. Real test: run `gemini skills list --all` (the real `gemini` binary,
     if available on this machine/execution environment; if it is not
     available where you're running, explicitly report that and skip to
     1.4 without simulating the result) and confirm `componentes-runner`
     now appears in the list.
1.4. Add a permanent regression check: extend `gates/G_HARNESS_COMPAT.py`
     OR `scripts/gestor_componentes.py`'s `verify()` (pick whichever fits
     the existing structure better, but don't create a new separate gate
     if one of the two already runs as part of `audit`) to fail (exit 1)
     if any file inside `componentes/` starts with a UTF-8 BOM
     (`EF BB BF`). Real test: create a temporary test file with a BOM
     inside `componentes/`, confirm the check fails pointing at the right
     file, remove the test file, confirm the check passes again with the
     repository's real state.

PHASE 2 — Fix `AGENTS.md §5` with the confirmed real convention
2.1. Rewrite the current line (~85) that states "Antigravity / MimoCode /
     OpenCode: Carrega definições em .agent/commands/ e .agent/skills/"
     to reflect the real evidence:
     - `.claude/skills/` confirmed working in `grok`, `opencode`, and
       `mimo` (MimoCode) — in addition to Claude Code, already documented
       separately on the next line.
     - Keep the mention of `.agent/` as the physical folder Package 7's
       sync mechanism keeps generating (don't stop generating it — it may
       serve other tools in the future), but do not claim Antigravity/
       MimoCode/OpenCode load from it, since the real evidence shows
       that's not how those 3 actually discover things today.
     - Add new, honest entries for the harnesses this audit tested that
       `AGENTS.md` doesn't yet mention: `grok` (reads `.claude/skills/`),
       `hermes` (`.agents/skills` plural + `.hermes/skills` convention,
       requires `hermes skills trust` per project — never run here),
       `agy`/Antigravity (real discovery mechanism not confirmed in this
       audit — do not claim it works), `freebuff` (installed, no
       non-interactive mode available to test via automation), `kiro-cli`
       (uses its own "agent" convention at `.kiro/agents/`, not part of
       this skill convention).
2.2. Add a provenance note: this section reflects real tests run on
     2026-09-05 against real installations on this machine — not
     assumption — and should be re-verified if any of these tools is
     updated or if `agy`/`freebuff`'s discovery mechanism is identified in
     the future.

PHASE 3 (OPTIONAL, DOES NOT BLOCK CLOSING) — Additional investigation
3.1. If time allows: investigate whether `hermes skills trust .` (run at
     the monorepo root) makes `hermes skills list` discover the project's
     5 skills — a 1-command test, no LLM cost. If it works, document the
     command as part of Phase 2.1's hermes note. If it doesn't work or
     you have no way to test this in your environment, don't invent an
     explanation — report that it could not be confirmed.
3.2. Do NOT try to investigate `agy`'s discovery mechanism by spending
     LLM calls on your own — this was already decided as out of
     mandatory scope for this package (item 3.1 of the original
     document), and every call has a real cost on the user's account.

EXIT CRITERIA (run and paste the real output of each):
- `gemini skills list --all` (if available in your environment) →
  `componentes-runner` appears in the list, in the same format as the
  other 4.
- `python ecossistema.py components verify --tipo skill --ferramenta compartilhado` → exit 0.
- The Phase 1.4 test (the check/gate fails on a test file with a BOM,
  then passes again after the test file is removed).
- `python ecossistema.py audit` (root battery) → exit 0, no regression in
  the other gates.
- Confirm via command (`git status`) that no test file (BOM or otherwise)
  was left in the real repository.

SCOPE RULES — DO NOT:
- Do not try to "fix" any external harness (gemini-cli, opencode, etc.)
  — you only control the ecosystem's side.
- Do not migrate or redesign the physical distribution of components
  (`.agent/skills/`, `.gemini/skills/`, bare `skills/` keep being
  generated normally by `gestor_componentes.py sync`).
- Do not spend LLM calls investigating `agy`/Antigravity on your own
  (see item 3.2).
- Do not `git commit` or `git push`.
- Do not modify `docs/planos/evolucao-notas-auditoria/06-universalidade.md`.

DELIVERABLE: exact list of files changed; for each phase, the command +
real output that proves it; if `gemini`/`hermes` are not available in
your execution environment, explicitly report that instead of simulating
the result; any necessary deviation, explicitly reported instead of
decided by yourself.
```

---

## Veredito — Auditoria do Prompt de Execução

**Auditoria independente realizada — não me baseei no relatório do agente executor.**

**Confirmado correto, com a prova mais forte de toda esta série de pacotes: reprodução contra instalações reais de harnesses externos, não simulação.**
- **BOM removido:** confirmei via `xxd` que `componentes/compartilhado/skills/componentes-runner/SKILL.md` e as cópias propagadas não têm mais o BOM. O executor também encontrou e corrigiu, por conta própria, **2 arquivos adicionais com o mesmo bug** que eu não tinha diagnosticado (`componentes/aidd-master/skills/resumo-sessao/SKILL.md` e o equivalente em `aidd-enterprise`) — a checagem global que pedi na Fase 1.4 naturalmente os pegou, e o executor corrigiu em vez de só reportar. Confirmei via `xxd` que os 3 arquivos-fonte e amostras das cópias propagadas estão limpos.
- **Prova real definitiva:** rodei `gemini skills list --all` (a instalação real do `gemini-cli` nesta máquina, não um teste simulado) e confirmei que `componentes-runner` agora aparece — exatamente o teste que falhava antes da correção, agora passando de verdade.
- **Gate anti-regressão:** testei ao vivo, criando um arquivo de teste com BOM dentro de `componentes/` — `gestor_componentes.verify()` reprovou apontando o arquivo exato; removi o teste e confirmei que volta a passar.
- **`AGENTS.md §5`:** reescrito com precisão — cada harness recebeu uma frase que corresponde a uma evidência real já documentada nesta auditoria, nenhuma suposição nova foi introduzida.
- **Achado extra do executor (Fase 3 opcional), verificado por mim de forma independente:** testaram `hermes skills trust .` e concluíram que não resolve a descoberta — reproduzi eu mesmo (`hermes skills trust .` seguido de `hermes skills list`) e confirmei: hermes só procura `.hermes/skills` ou `.agents/skills`, nunca `.claude`/`.agent`, mesmo depois de "trust".
- Sem poluição do repositório, `ecossistema.py audit` 6/6 gates, `components verify --tipo todos` exit 0 (15 componentes). Nenhum commit feito, documento do pacote intocado, nenhuma chamada de LLM gasta investigando o `agy` (regra de escopo respeitada).

**Notável:** quinto pacote consecutivo (depois de 3, 4 e 5) a fechar de primeira, sem nenhuma correção necessária — e desta vez com o padrão de evidência mais alto possível: o teste de aceite não foi "os testes automatizados passam", foi "o software externo real, de um fornecedor terceiro, instalado nesta máquina, agora enxerga o componente que antes não enxergava".

### Nota Final — Pacote 6 (Universalidade / Agnosticismo Multi-Harness): 9.5/10

**Por que 9.5, não 10:**
- O bug real e concreto (BOM) foi corrigido e comprovado contra uma instalação externa real — o padrão de prova mais forte que este processo já produziu.
- A correção documental (`AGENTS.md §5`) transformou uma afirmação nunca verificada (e parcialmente falsa) numa seção honesta, harness por harness, com proveniência explícita e data.
- O executor foi além do pedido de forma responsável (achou e corrigiu 2 arquivos adicionais com o mesmo bug, e testou a hipótese do `hermes skills trust` da Fase 3 opcional) sem extrapolar escopo nem gastar chamadas de LLM indevidas.
- **0.5 de desconto:** a causa raiz do não-funcionamento do `agy`/Antigravity continua desconhecida (correto não investigar mais, dado o custo de LLM — mas é uma lacuna real que permanece); e `freebuff` continua genuinamente não testável nesta máquina por limitação da própria ferramenta (não é algo que este pacote pudesse resolver).
- **Efeito na dimensão:** Universalidade/Agnosticismo 8/10 → **9/10**. Não chega a 10 porque 2 dos 7 harnesses (`agy`, `freebuff`) continuam sem confirmação de descoberta — mas a documentação agora é honesta sobre isso em vez de silenciar ou presumir, e o bug real que afetava o `gemini-cli` está corrigido e comprovado contra a instalação real.
