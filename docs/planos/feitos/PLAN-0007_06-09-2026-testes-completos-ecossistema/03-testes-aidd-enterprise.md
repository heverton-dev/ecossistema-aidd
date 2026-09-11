# Bateria 3 — AIDD Enterprise (`tools/aidd-enterprise`)

> **Escopo:** provar o caminho de ouro completo da CLI (`tools/aidd-enterprise/scripts/aidd.py`) — a mesma superfície de comandos do AIDD Master (Bateria 2), mas com as diferenças reais que a Rodada 2 (Item 4) introduziu/confirmou: 5 harnesses de distribuição (incl. MimoCode), hook em formato `.json` (não `.sh`), detecção de ambiguidade de tipo em linguagem natural, e ausência do comando `verificar-drift` dedicado (o drift aqui é checado via `G_INJECT.py`, não via subcomando de CLI).

---

## Contexto já investigado

CLI real (via `--help`): `plan, apply, bench, heal, prompt, setup, init, compose, compose-orca, add-module, test, audit, deploy, status, export-frontend, refine-module, scaffold-infra, inject` — **sem** `verificar-drift` (diferença real vs. aidd-master; o equivalente aqui é rodar `python scripts/gates/G_INJECT.py --dir <projeto>`, que já roda AMBAS as checagens — infraestrutura do injetor E drift pós-injeção — desde a Rodada 2, Item 4).

Diferenças reais confirmadas na Rodada 2, Item 4 (releia
`docs/planos/refinamento-notas-auditoria/04-unificacao-injetor-aidd-enterprise.md`
antes de escrever o teste, é a fonte de verdade mais recente):
- `inject hook` grava em **5 pastas** de harness (`.claude/hooks`, `.agent/hooks`, `.mimocode/hooks`, `.gemini/hooks`, `.hooks` flat), formato `{nome}.json` — **não** `{nome}/hook.sh` como no master — mais o canônico `componentes/aidd-enterprise/hooks/{nome}/{nome}.json`.
- `inject skill` grava em **5 pastas** (incl. `.mimocode/skills` e `.skills` flat), diferente das 3 do master.
- Deteção de linguagem natural via `IntentRouter`+`detector_camada` detecta **ambiguidade de tipo** (`TIPO_AMBIGUO`, retorna candidatos, não escreve nada) — capacidade nova desde o Item 4, vale a pena provar explicitamente com uma frase ambígua real (ex.: uma frase que bate tanto com padrão de `skill` quanto de `rule`).
- `remover_componente()` de um `hook` limpa também o destino canônico específico de aidd-enterprise (achado da auditoria da Fase 1/2, corrigido no Item 4) — vale testar essa remoção especificamente, não só a remoção genérica.
- `config` usa mapa arbitrário de arquivos via `--files-json` (equivalente ao `--conteudo-file` do master, mas o flag exato é diferente aqui — confirme o nome real do flag lendo `p_inject.add_argument` em `tools/aidd-enterprise/scripts/aidd.py` antes de escrever o comando).

Todos os demais comandos (`compose`, `add-module`, `test`, `audit` do projeto, `plan`/`prompt`, `bench`, `heal`, `deploy`, `export-frontend`, `refine-module`, `scaffold-infra`, `compose-orca`) têm a mesma estrutura/riscos já documentados na Bateria 2 (`02-testes-aidd-master.md`) — releia aquele documento, as mesmas ressalvas de ambiente (Docker, Node, locust, behave) se aplicam aqui.

## Definição de Pronto

Mesma estrutura da Bateria 2 (itens 3.1 a 3.14, espelhando 2.1-2.14 e 2.16-2.17 do Master), adaptada:

3.1. `init`, `compose <tmp>/suite-teste-ent "Suite Enterprise E2E" crm erp --db sqlite`, `add-module`, `test unit`, `audit` do projeto, `status` — mesmos critérios da Bateria 2.
3.2. `plan`/`prompt` com 2 frases não ambíguas (domínios diferentes) → exit 0, zero custo de LLM.
3.3. **Frase ambígua deliberada** (ex.: uma frase que casa com padrões de `skill` E `rule` ao mesmo tempo — ler `detector_camada.py`/`profiles_registry.py` para montar uma frase real que force isso) → deve retornar `TIPO_AMBIGUO` com candidatos, **nenhum arquivo escrito**. Esta é a prova mais importante desta bateria (capacidade que só existe aqui desde o Item 4).
3.4. `inject` — 1 injeção real de cada um dos 7 tipos, confirmando explicitamente: `hook` grava nas 5 pastas certas + canônico `.json`; `skill` grava nas 5 pastas incl. `.mimocode`; `config` com o flag real de mapa de arquivos (confirme o nome do flag no código); `mcp` com comando externo.
3.5. `--dry-run` (nada escrito) e `--remover` de um `hook` (confirmar que os arquivos das 5 pastas E o canônico específico de aidd-enterprise somem).
3.6. `python scripts/gates/G_INJECT.py --dir <projeto-de-teste>` → exit 0 antes de qualquer edição manual; editar manualmente um arquivo de hook injetado e rodar de novo → deve reprovar (drift detectado).
3.7. `bench`, `heal`, `scaffold-infra` → mesmos critérios da Bateria 2.
3.8. `export-frontend`, `refine-module`, `deploy docker` → mesmos critérios/ressalvas de ambiente da Bateria 2.
3.9. `compose-orca` → mesmos critérios da Bateria 2.
3.10. Suíte `pytest` completa de `tools/aidd-enterprise` (`python -m pytest tests/ -q`, cwd `tools/aidd-enterprise`) → exit 0, sem regressão (baseline conhecido: 227 passed, 4 skipped, 38 cenários reais — reconfirmar o número real agora).

## Critério de saída

Mesmo critério da Bateria 2, adaptado: todos os itens com exit code real e saída real citada; nenhum diretório temporário ou container órfão; ambiguidade de tipo comprovada com um caso real; limpeza do canônico de hook comprovada especificamente para aidd-enterprise (não só a remoção genérica).

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido.

```
Você vai escrever e executar uma bateria de testes reais de ponta a ponta
que prova o caminho de ouro completo da CLI do AIDD Enterprise
(tools/aidd-enterprise/scripts/aidd.py) no monorepo ecossistema-aidd
(raiz em C:\Users\trcnologia\Desktop\ecossistema-aidd). Valide tudo de
verdade (execuções reais, exit codes reais, nunca mascarados por pipe,
nunca simulado). NUNCA rode nada contra o repositório real como
diretório alvo de escrita — sempre use diretórios temporários isolados,
limpos ao final.

Esta bateria é irmã da Bateria 2 (AIDD Master,
docs/planos/testes-completos-ecossistema/02-testes-aidd-master.md) —
LEIA aquele documento primeiro, a estrutura de teste (compose, add-
module, test, audit, plan/prompt, bench, heal, scaffold-infra, export-
frontend, refine-module, deploy docker, compose-orca) é a mesma, com as
mesmas ressalvas de ambiente (Docker, Node, locust, behave). Não repita
o trabalho de descoberta já feito lá — adapte os mesmos padrões de
comando para aidd-enterprise.

CONTEXTO JÁ INVESTIGADO ESPECÍFICO DE AIDD-ENTERPRISE (confirme lendo o
código antes de escrever o script):
- CLI (via --help): mesma lista da Bateria 2, SEM `verificar-drift`
  (diferença real). O equivalente aqui é rodar
  `python tools/aidd-enterprise/scripts/gates/G_INJECT.py --dir <projeto>`
  — desde a Rodada 2, Item 4, esse gate roda AMBAS as checagens
  (infraestrutura + drift pós-injeção).
- `inject hook` grava em 5 pastas (.claude/hooks, .agent/hooks,
  .mimocode/hooks, .gemini/hooks, .hooks flat), formato "{nome}.json"
  (NÃO "{nome}/hook.sh" como no master), mais o canônico
  componentes/aidd-enterprise/hooks/{nome}/{nome}.json.
- `inject skill` grava em 5 pastas (incl. .mimocode/skills e .skills
  flat) — mais cobertura que o master (3 pastas).
- Deteção de linguagem natural via IntentRouter+detector_camada detecta
  AMBIGUIDADE de tipo (TIPO_AMBIGUO, com candidatos, nenhum arquivo
  escrito) — capacidade nova desde o Item 4. Monte uma frase real que
  bata com 2 padrões de tipo ao mesmo tempo (leia detector_camada.py e
  profiles_registry.py locais de tools/aidd-enterprise/src/core/ para
  montar essa frase com precisão) e prove esse comportamento
  explicitamente — é o achado mais importante desta bateria.
- remover_componente() de um hook limpa também o destino canônico
  específico de aidd-enterprise (não só a remoção genérica de
  arquivos/mirrors) — teste isso especificamente: injete um hook, rode
  --remover, confirme que TANTO as 5 pastas de harness QUANTO o
  canônico componentes/aidd-enterprise/hooks/... sumiram.
- `config` usa um flag de mapa arbitrário de arquivos — confirme o nome
  EXATO do flag lendo `p_inject.add_argument` em
  tools/aidd-enterprise/scripts/aidd.py antes de montar o comando (pode
  ser diferente do --conteudo-file do master).

Leia `docs/planos/refinamento-notas-auditoria/04-unificacao-injetor-
aidd-enterprise.md` para o histórico completo da migração, se precisar
de mais contexto sobre por que essas diferenças existem.

DEFINIÇÃO DE PRONTO — rode nesta ordem (releia
docs/planos/testes-completos-ecossistema/03-testes-aidd-enterprise.md
por extenso antes de começar, tem os 10 itens detalhados): init,
compose com 2 módulos, add-module, test unit, audit do projeto,
status, plan/prompt (2 frases não ambíguas + 1 frase AMBÍGUA
deliberada provando TIPO_AMBIGUO), inject dos 7 tipos com atenção
especial a hook (5 pastas + .json + canônico) e skill (5 pastas incl.
mimocode), dry-run, remover de hook confirmando limpeza do canônico
específico, G_INJECT.py rodado isolado (caso limpo E caso de drift
real após edição manual), bench, heal, scaffold-infra, export-
frontend, refine-module (ou documentar limitação), deploy docker (ou
documentar limitação, sempre derrubando o container se subir),
compose-orca, e a suíte pytest completa de tools/aidd-enterprise
(python -m pytest tests/ -q, cwd tools/aidd-enterprise) confirmando o
número real de testes passando agora.

Salve os textos de prompt em linguagem natural (incluindo a frase
ambígua) em `docs/testes/prompts/aidd_enterprise_<cenario>.txt`.

Escreva o(s) script(s) reais e salve-os em
`docs/testes/testes/03_aidd_enterprise_*.py`.

Execute de verdade agora. Escreva o relatório em
`docs/testes/relatorios/03_aidd_enterprise.md`: cada item, comando
exato, exit code real, saída relevante, limitações de ambiente,
veredito final. Dê destaque especial (seção própria) à prova de
TIPO_AMBIGUO e à prova de limpeza do canônico de hook — são as 2
capacidades que diferenciam esta ferramenta do master e que a Rodada 2
introduziu. Use as skills `artifact-design` e `dataviz` para uma versão
visual do relatório, mantendo o Markdown como fonte de verdade.

CRITÉRIO DE SAÍDA:
- Todos os itens rodados de verdade, evidência real no relatório.
- Nenhum diretório temporário ou container Docker órfão.
- `git status` da raiz do ecossistema real limpo ao final.
- Suíte pytest de tools/aidd-enterprise sem regressão do baseline
  conhecido (227 passed, 4 skipped) — investigar qualquer divergência
  antes de reportar.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não teste aidd-master, aidd-forge ou aidd-generator aqui.
- Não faça git commit nem git push em nenhum repositório.
- Não deixe containers, processos ou diretórios temporários órfãos.

ENTREGÁVEL: lista de scripts salvos, lista de prompts salvos, caminho
do relatório, resumo de 5-8 linhas do veredito final.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to write and run a battery of real end-to-end tests
proving the complete golden path of the AIDD Enterprise CLI
(tools/aidd-enterprise/scripts/aidd.py) works, inside the
ecossistema-aidd monorepo (root at
C:\Users\trcnologia\Desktop\ecossistema-aidd). Validate everything for
real (real runs, real exit codes, never masked by a pipe, never
simulated). NEVER run anything against the real repository as a write
target — always use isolated temporary directories, cleaned up at the
end.

This battery is the sibling of Battery 2 (AIDD Master,
docs/planos/testes-completos-ecossistema/02-testes-aidd-master.md) —
READ that document first, the test structure (compose, add-module,
test, audit, plan/prompt, bench, heal, scaffold-infra, export-frontend,
refine-module, deploy docker, compose-orca) is the same, with the same
environment caveats (Docker, Node, locust, behave). Do not repeat the
discovery work already done there — adapt the same command patterns to
aidd-enterprise.

ALREADY-INVESTIGATED CONTEXT SPECIFIC TO AIDD-ENTERPRISE (confirm by
reading the code before writing the script):
- CLI (via --help): same list as Battery 2, WITHOUT `verificar-drift`
  (real difference). The equivalent here is running
  `python tools/aidd-enterprise/scripts/gates/G_INJECT.py --dir <project>`
  — since Round 2, Item 4, that gate runs BOTH checks (infrastructure +
  post-injection drift).
- `inject hook` writes to 5 harness folders (.claude/hooks,
  .agent/hooks, .mimocode/hooks, .gemini/hooks, flat .hooks), format
  "{nome}.json" (NOT "{nome}/hook.sh" like master), plus the canonical
  componentes/aidd-enterprise/hooks/{nome}/{nome}.json.
- `inject skill` writes to 5 folders (incl. .mimocode/skills and flat
  .skills) — more coverage than master's 3 folders.
- Natural-language detection via IntentRouter+detector_camada detects
  type AMBIGUITY (TIPO_AMBIGUO, with candidates, no file written) — a
  capability new since Item 4. Build a real sentence that matches 2
  type patterns at once (read the local detector_camada.py and
  profiles_registry.py under tools/aidd-enterprise/src/core/ to build
  this sentence precisely) and prove this behavior explicitly — it is
  the single most important finding of this battery.
- remover_componente() of a hook also cleans up the aidd-enterprise-
  specific canonical destination (not just the generic file/mirror
  removal) — test this specifically: inject a hook, run --remover,
  confirm BOTH the 5 harness folders AND the canonical
  componentes/aidd-enterprise/hooks/... are gone.
- `config` uses an arbitrary file-map flag — confirm the EXACT flag
  name by reading `p_inject.add_argument` in
  tools/aidd-enterprise/scripts/aidd.py before building the command (it
  may differ from master's --conteudo-file).

Read `docs/planos/refinamento-notas-auditoria/04-unificacao-injetor-
aidd-enterprise.md` for the full migration history if you need more
context on why these differences exist.

DEFINITION OF DONE — run in this order (re-read
docs/planos/testes-completos-ecossistema/03-testes-aidd-enterprise.md
in full before starting, it has the 10 detailed items): init, compose
with 2 modules, add-module, test unit, audit of the composed project,
status, plan/prompt (2 non-ambiguous sentences + 1 deliberately
AMBIGUOUS sentence proving TIPO_AMBIGUO), inject of all 7 types with
special attention to hook (5 folders + .json + canonical) and skill (5
folders incl. mimocode), dry-run, removing a hook confirming cleanup of
its specific canonical, G_INJECT.py run standalone (clean case AND
real-drift case after manual edit), bench, heal, scaffold-infra,
export-frontend, refine-module (or document the limitation), deploy
docker (or document the limitation, always tearing down the container
if it comes up), compose-orca, and the full pytest suite of
tools/aidd-enterprise (python -m pytest tests/ -q, cwd
tools/aidd-enterprise) confirming the real number of tests passing
right now.

Save the natural-language prompt texts (including the ambiguous
sentence) under
`docs/testes/prompts/aidd_enterprise_<scenario>.txt`.

Write the real script(s) and save them under
`docs/testes/testes/03_aidd_enterprise_*.py`.

Run everything for real now. Write the report at
`docs/testes/relatorios/03_aidd_enterprise.md`: each item, exact
command, real exit code, relevant output, environment limitations,
final verdict. Give special emphasis (its own section) to the proof of
TIPO_AMBIGUO and to the proof of canonical-hook cleanup — these are the
2 capabilities that differentiate this tool from master and that Round
2 introduced. Use the `artifact-design` and `dataviz` skills for a
visual version of the report, keeping the Markdown as the source of
truth.

EXIT CRITERIA:
- All items run for real, real evidence in the report.
- No orphaned temporary directory or Docker container.
- The real ecosystem repository root's `git status` clean at the end.
- tools/aidd-enterprise's pytest suite with no regression from the
  known baseline (227 passed, 4 skipped) — investigate any divergence
  before reporting.

SCOPE RULES — DO NOT:
- Do not test aidd-master, aidd-forge, or aidd-generator here.
- Do not git commit or git push in any repository.
- Do not leave orphaned containers, processes, or temporary
  directories.

DELIVERABLE: list of saved scripts, list of saved prompts, report path,
5-8 line summary of the final verdict.
```
