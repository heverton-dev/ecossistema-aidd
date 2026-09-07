# 06 — Correção de Documentação Desatualizada (Residual dos Itens 2 e 4)

> **Origem:** o usuário perguntou em 06/09/2026 se a documentação do ecossistema está atualizada e reflete o que foi realmente implementado nas Rodadas 1 e 2. Investigação (levantamento factual + verificação manual própria, sem confiar em leitura cruzada) achou 2 gaps reais, ambos residuais de itens desta própria rodada.
> **Escopo:** só correção de texto/documentação. Nenhuma mudança de código, nenhuma mudança de comportamento.

---

## Contexto já investigado (confirmado por leitura direta dos arquivos e execução real do `--help`, não por suposição)

### Gap 1 (menor) — Fase 1 não revela o mecanismo zero-LLM

`tools/aidd-master/docs/01-fases-de-execucao.md` e `tools/aidd-enterprise/docs/01-fases-de-execucao.md` (byte-idênticos nesta seção) descrevem a Fase 1 assim (linha ~39):

> "O Intent Router (`src/core/intent_router.py`) analisa o pedido do usuário em PT-BR (ex: *"preciso de uma arquitetura para crm, erp e billing"*)."

Isso não revela que o mecanismo é **casamento de palavras-chave contra ~20 domínios fixos, ZERO uso de LLM real** — informação que o Item 2 desta rodada (`03-transparencia-disclosure-plan-prompt.md`) já expôs corretamente no `--help` real de `plan`/`prompt` e no próprio output do comando, em ambas as ferramentas. O doc de "fases" (nível manual de uso) nunca foi atualizado para acompanhar essa mudança.

### Gap 2 (grave) — doc de injeção do aidd-enterprise descreve arquitetura que nunca foi construída

`tools/aidd-enterprise/docs/07-sistema-de-injecao-de-componentes.md` tem `Status: PLANEJADO (Aguardando Aprovação)`, datado de 03/09/2026 — é um plano anterior ao Item 4 desta rodada (`04-unificacao-injetor-aidd-enterprise.md`), nunca atualizado depois que o Item 4 foi implementado de verdade. Descreve:
- Flags `--desc`/`--layer`/`--content` (reais são outras, ver abaixo).
- Scripts `scripts/inject_skill.py`, `scripts/inject_mcp.py`, `src/core/global_integrator.py`, `src/core/component_registry.py` — nenhum destes existe no código real.
- Só 6 tipos de componente na tabela de escopo (falta `hook`).
- Nenhuma menção às 5 capacidades reais entregues pelo Item 4: drift detection via SHA-256, `--remover`, rollback com snapshot completo, `--dry-run`, `--files-json` (config com mapa arbitrário de arquivos).

`--help` real confirmado por execução (`python scripts/aidd.py inject --help`, exit 0, rodado em `tools/aidd-enterprise/`):

```text
usage: aidd.py inject [-h] [--descricao DESCRICAO]
                      [--content-file CONTENT_FILE]
                      [--mcp-command MCP_COMMAND] [--mcp-args MCP_ARGS]
                      [--mcp-env MCP_ENV] [--files-json FILES_JSON]
                      [--dry-run] [--remover] [--dir DIR]
                      {skill,mcp,rule,spec,config,hook,agent} nome
```

Este é o achado mais grave dos dois: documentação **ativamente enganosa** (descreve um design que nunca foi o que foi construído), não apenas omissa.

## Definição de Pronto

6.1. `tools/aidd-master/docs/01-fases-de-execucao.md` — seção "Fase 1: Concepção em Linguagem Natural" revisada para declarar explicitamente: mecanismo é casamento de palavras-chave contra domínios fixos, zero LLM real (mesma linguagem de disclosure já usada no `--help` real de `plan`/`prompt`).
6.2. `tools/aidd-enterprise/docs/01-fases-de-execucao.md` — mesma correção; manter os dois arquivos byte-idênticos nesta seção, como já são hoje.
6.3. `tools/aidd-enterprise/docs/07-sistema-de-injecao-de-componentes.md` — reescrito para descrever a arquitetura REAL implementada, confirmada por reprodução: `Status: IMPLEMENTADO`; os 7 tipos de componente (incluindo `hook`); as flags reais do comando `inject` (`--descricao`, `--content-file`, `--mcp-command`, `--mcp-args`, `--mcp-env`, `--files-json`, `--dry-run`, `--remover`, `--dir`); a arquitetura canônica compartilhada (`profiles_registry.py` / `detector_camada.py` / `materializador.py` / `sincronizador_harness.py`) migrada do núcleo de `aidd-master`; as 5 capacidades reais (drift SHA-256, remoção, rollback com snapshot completo, dry-run, config multi-arquivo). Remover toda menção aos scripts/flags que nunca existiram.

## Critério de saída

- Os 3 arquivos corrigidos, cada afirmação nova conferida contra o `--help` real e/ou o código-fonte (nunca "deveria ser assim").
- Nenhuma mudança de código — só documentação.
- `git status` limpo fora dos 3 arquivos tocados (mais o próprio commit desta correção).

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai corrigir 3 arquivos de documentação do monorepo ecossistema-aidd
(raiz em C:\Users\trcnologia\Desktop\ecossistema-aidd) que ficaram
desatualizados em relação ao código real. NÃO altere nenhum código —
só os 3 arquivos .md abaixo. Toda afirmação nova que você escrever
precisa ser conferida contra o --help real do comando ou contra o
código-fonte antes de escrever — nunca escreva "deveria funcionar assim"
sem confirmar rodando o comando de verdade.

ARQUIVO 1 e 2 (mesma correção, aplicar nos dois, mantendo-os
byte-idênticos nesta seção como já são hoje):
- tools/aidd-master/docs/01-fases-de-execucao.md
- tools/aidd-enterprise/docs/01-fases-de-execucao.md

Na seção "Fase 1: Concepção em Linguagem Natural", o texto atual diz
apenas que "o Intent Router analisa o pedido do usuário em PT-BR", sem
revelar que o mecanismo real é casamento de palavras-chave contra um
conjunto fixo de ~20 domínios conhecidos, SEM uso de LLM real. Antes de
editar, rode você mesmo (em cada uma das duas ferramentas, caminho real
do CLI dentro de tools/aidd-master/ e tools/aidd-enterprise/):
  python scripts/aidd.py plan --help
  python scripts/aidd.py prompt --help
e confirme a frase de disclosure exata que já existe no --help real
(adicionada no Item 2 da rodada de refinamento — ver
docs/planos/refinamento-notas-auditoria/03-transparencia-disclosure-plan-prompt.md
se quiser o histórico completo). Reescreva o passo 1 da Fase 1 nos dois
arquivos usando a MESMA linguagem de disclosure do --help real (não
invente uma frase nova) — deixando claro: zero LLM, casamento de
palavras-chave, lista de domínios fixa.

ARQUIVO 3:
- tools/aidd-enterprise/docs/07-sistema-de-injecao-de-componentes.md

Este arquivo tem "Status: PLANEJADO (Aguardando Aprovação)" e descreve
um design de injeção de componentes que NUNCA foi o que foi construído
de verdade (flags --desc/--layer/--content, scripts inject_skill.py,
global_integrator.py, component_registry.py — nenhum destes existe).
Antes de reescrever, confirme a implementação REAL rodando, dentro de
tools/aidd-enterprise/:
  python scripts/aidd.py inject --help
e leia o código-fonte real do comando inject (procure por onde o
argparse do subcomando "inject" é definido em scripts/aidd.py ou nos
módulos que ele importa) e a arquitetura canônica compartilhada
(profiles_registry.py, detector_camada.py, materializador.py,
sincronizador_harness.py) para confirmar como cada tipo de componente
é de fato criado/removido/sincronizado hoje.

Reescreva o arquivo inteiro (mantendo a numeração de seções, pode
reorganizar o conteúdo interno como fizer mais sentido) para refletir
a arquitetura REAL:
- Status: IMPLEMENTADO (não mais "planejado").
- Os 7 tipos de componente suportados hoje (confirme a lista exata via
  --help: inclui "hook", que o doc antigo não lista).
- As flags reais do comando inject (confirme via --help: --descricao,
  --content-file, --mcp-command, --mcp-args, --mcp-env, --files-json,
  --dry-run, --remover, --dir).
- A arquitetura canônica compartilhada com aidd-master (cite os módulos
  reais pelo nome, sem inventar nomes de arquivo que não existem).
- As 5 capacidades reais entregues pela unificação: drift detection via
  hash SHA-256, remoção de componente (--remover), rollback com
  snapshot completo do conteúdo anterior, modo dry-run (--dry-run),
  config com mapa arbitrário de múltiplos arquivos (--files-json).
- Remova toda menção aos scripts/flags do design antigo que nunca
  existiram (inject_skill.py, global_integrator.py,
  component_registry.py, --desc, --layer, --content).

CRITÉRIO DE SAÍDA:
- Os 3 arquivos corrigidos, cada afirmação nova conferida contra --help
  real ou código-fonte real (cite no seu relatório final qual comando
  ou arquivo você rodou/leu para confirmar cada afirmação).
- Nenhum arquivo de código alterado — só os 3 .md acima.
- git status limpo fora dos 3 arquivos tocados.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não altere nenhum arquivo de código (.py, .json de config, etc).
- Não invente capacidades ou flags que não confirmou existirem de
  verdade via --help ou leitura do código-fonte.
- Não faça git commit nem git push.

ENTREGÁVEL: diff dos 3 arquivos corrigidos, e para cada afirmação nova
relevante, qual comando rodou ou qual trecho de código leu para
confirmá-la.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to fix 3 documentation files in the ecossistema-aidd
monorepo (root at C:\Users\trcnologia\Desktop\ecossistema-aidd) that
went stale relative to the real code. Do NOT change any code — only
the 3 .md files below. Every new statement you write must be verified
against the real --help output or the source code before you write it
— never write "this should work like this" without actually running
the command to confirm.

FILES 1 and 2 (same fix, apply to both, keeping them byte-identical in
this section as they already are today):
- tools/aidd-master/docs/01-fases-de-execucao.md
- tools/aidd-enterprise/docs/01-fases-de-execucao.md

In the "Fase 1: Concepção em Linguagem Natural" section, the current
text only says "the Intent Router analyzes the user's request in
PT-BR", without revealing that the real mechanism is keyword matching
against a fixed set of ~20 known domains, with NO real LLM use. Before
editing, run it yourself (in each of the two tools, real CLI path
under tools/aidd-master/ and tools/aidd-enterprise/):
  python scripts/aidd.py plan --help
  python scripts/aidd.py prompt --help
and confirm the exact disclosure sentence that already exists in the
real --help (added in Item 2 of the refinement round — see
docs/planos/refinamento-notas-auditoria/03-transparencia-disclosure-plan-prompt.md
for the full history if you want it). Rewrite step 1 of Fase 1 in both
files using the SAME disclosure language already in the real --help
(don't invent a new sentence) — making clear: zero LLM, keyword
matching, fixed domain list.

FILE 3:
- tools/aidd-enterprise/docs/07-sistema-de-injecao-de-componentes.md

This file has "Status: PLANEJADO (Aguardando Aprovação)" and describes
a component-injection design that was NEVER what was actually built
(flags --desc/--layer/--content, scripts inject_skill.py,
global_integrator.py, component_registry.py — none of these exist).
Before rewriting, confirm the REAL implementation by running, inside
tools/aidd-enterprise/:
  python scripts/aidd.py inject --help
and read the real source code of the inject command (find where the
"inject" subcommand's argparse is defined in scripts/aidd.py or the
modules it imports) and the shared canonical architecture
(profiles_registry.py, detector_camada.py, materializador.py,
sincronizador_harness.py) to confirm how each component type is
actually created/removed/synced today.

Rewrite the entire file (keep the section numbering, you may
reorganize the internal content as makes sense) to reflect the REAL
architecture:
- Status: IMPLEMENTADO (no longer "planned").
- The 7 component types supported today (confirm the exact list via
  --help: includes "hook", which the old doc does not list).
- The real flags of the inject command (confirm via --help:
  --descricao, --content-file, --mcp-command, --mcp-args, --mcp-env,
  --files-json, --dry-run, --remover, --dir).
- The canonical architecture shared with aidd-master (name the real
  modules, don't invent file names that don't exist).
- The 5 real capabilities delivered by the unification: SHA-256 hash
  drift detection, component removal (--remover), rollback with a full
  snapshot of prior content, dry-run mode (--dry-run), config with an
  arbitrary multi-file map (--files-json).
- Remove every mention of the old design's scripts/flags that never
  existed (inject_skill.py, global_integrator.py,
  component_registry.py, --desc, --layer, --content).

EXIT CRITERIA:
- The 3 files fixed, every new statement verified against real --help
  output or real source code (cite in your final report which command
  or file you ran/read to confirm each statement).
- No code file changed — only the 3 .md files above.
- git status clean outside the 3 touched files.

SCOPE RULES — DO NOT:
- Do not change any code file (.py, config .json, etc).
- Do not invent capabilities or flags you did not confirm for real via
  --help or reading the source code.
- Do not git commit or git push.

DELIVERABLE: diff of the 3 fixed files, and for each relevant new
statement, which command you ran or which code snippet you read to
confirm it.
```
