# Bateria 2 — AIDD Master (`tools/aidd-master`)

> **Escopo:** provar o caminho de ouro completo da CLI (`tools/aidd-master/scripts/aidd.py`), incluindo o Injetor Universal (já auditado na Rodada 2, Item 4) e os comandos de composição/módulo/qualidade que ainda não tinham prova de ponta a ponta via CLI real.

---

## Contexto já investigado

CLI real (`tools/aidd-master/scripts/aidd.py`), subcomandos confirmados via `--help`:
`plan, apply, bench, heal, prompt, setup, init, compose, compose-orca, add-module, test, audit, deploy, status, export-frontend, refine-module, scaffold-infra, inject, verificar-drift`.

Pontos relevantes por comando (leia o código antes de escrever o teste — isto é um resumo, não a fonte de verdade):
- **`init <nome> [--dir]`**: provisiona projeto modular novo (`provision_project.py`).
- **`compose <target_dir> <suite_name> [modulos...] [--db sqlite|postgres]`**: gera suíte completa via `compose_suite.py` — default de módulos é `crm erp helpdesk logistica`; use só 2 módulos (ex.: `crm erp`) para manter o teste rápido.
- **`add-module <nome> [--descricao] [--dir]`**: gera nova fatia vertical dentro de um projeto já composto (`add_module.py`).
- **`test [unit|load|contracts|all] [--dir]`**: roda pytest real (`tests/unit` ou `tests/`) dentro do `--dir`, mais gate de contratos e teste de carga Locust (`load`, requer `locust` instalado — se não estiver, documentar como limitação de ambiente, não simular).
- **`audit [--report] [--json] [--dir]`**: roda 6-7 gates DENTRO do projeto composto (G_ESTRUTURA, G_QUALIDADE, G_TESTES, G_CONTRACTS, G_SEGREDOS, G_HARNESS_COMPAT, e G_SEGURANCA se existir) — não confundir com o `audit` da raiz (bateria 1), este é o audit do PROJETO COMPOSTO.
- **`plan "<ideia>" [--dir] [--apply]`** e **`prompt "<texto>" [--dir]`**: entrada em linguagem natural — detecção por casamento de palavras-chave contra lista fixa de domínios, **SEM uso de LLM/IA generativa** (confirmado no próprio help text do CLI) — zero custo, pode/deve ser testado à vontade.
- **`inject <tipo> <nome> [--descricao] [--conteudo-file] [--mcp-command] [--mcp-args] [--mcp-env] [--projeto] [--sobrescrever] [--remover] [--dry-run] [--dir]`**: os 7 tipos são `skill, mcp, rule, spec, config, agent, hook`. As 5 capacidades enriquecidas na Rodada 2 Item 4 (drift SHA-256, remoção com limpeza do canônico, rollback com snapshot completo, dry-run, config com mapa arbitrário de arquivos + path traversal) já têm testes automatizados reais em `tools/aidd-master/tests/unit/test_injector_core.py` — esta bateria deve **reexercitar via CLI direta** (não só reconfirmar o pytest) pelo menos: os 7 tipos uma vez cada, `--dry-run`, `--remover`, `config` com um `--conteudo-file` estruturado, e `mcp` com `--mcp-command`.
- **`verificar-drift [--dir]`**: exclusivo do master (novo na Rodada 2 Item 4) — checa hashes SHA-256 dos componentes injetados.
- **`bench [-n] [--dir]`**: benchmark de concorrência local em SQLite WAL — 100% local, sem dependência externa.
- **`heal [--dir]`**: auto-remediação — só faz algo real se `PLANO-EXECUCAO-ESTRUTURADO.json` existir no `--dir` (ou seja, rodar depois de `compose`).
- **`deploy [docker|vps]`**: **atenção real** — `deploy docker` roda `docker compose up -d --build` de verdade (sobe containers reais) usando o **diretório de trabalho atual do processo**, não `--dir` (não há flag `--dir` neste comando, e o subprocess não faz `cwd=`) — só testar se Docker estiver instalado E disponível, e **sempre** derrubar com `docker compose down` ao final; se Docker não estiver disponível, documentar como limitação de ambiente, nunca simular.
- **`export-frontend [--stack nextjs] [--dir]`**: exporta frontend TypeScript a partir do OpenAPI — requer que `--dir` já tenha sido composto antes.
- **`refine-module <modulo> [--spec] [--dir]`**: roda suíte BDD real via `behave` (instala automaticamente se ausente) — precisa de um arquivo `.feature` real em `features/<modulo>.feature` dentro do `--dir` composto.
- **`scaffold-infra [--dir]`**: gera Terraform + Helm declarativos — 100% local, sem dependência externa.
- **`compose-orca [--dir] [--suite-name] [modulos...]`**: composição via SubagentEngine com Context-Purge — mecanismo interno próprio (não usa agentes de IA externos), 100% local.

## Definição de Pronto

2.1. `init` cria um projeto novo válido (estrutura mínima presente).
2.2. `compose <tmp>/suite-teste "Suite Teste E2E" crm erp --db sqlite` → exit 0, estrutura de projeto real gerada (`src/modules/crm`, `src/modules/erp`, `tests/`, `PLANO-EXECUCAO-ESTRUTURADO.json`).
2.3. `add-module estoque --descricao "..." --dir <tmp>/suite-teste` → exit 0, nova fatia vertical `src/modules/estoque` criada.
2.4. `test unit --dir <tmp>/suite-teste` → exit 0, pytest real rodando de verdade contra o projeto composto (capturar contagem de testes).
2.5. `audit --dir <tmp>/suite-teste` → exit 0, todos os gates do PROJETO aprovados (não confundir com os gates da raiz).
2.6. `status --dir <tmp>/suite-teste` → exit 0.
2.7. `plan "Sistema de gestão de estoque com alertas" --dir <tmp>/plan-teste` e `prompt "crie um crm simples" --dir <tmp>/prompt-teste` → exit 0 em ambos, confirmar que a detecção por palavra-chave funcionou (módulo/domínio correto reconhecido), zero chamada de rede/LLM.
2.8. `inject` — pelo menos 1 injeção real de cada um dos 7 tipos num diretório de teste isolado (`<tmp>/inject-teste`), mais: `--dry-run` (confirma nada escrito), `--remover` (confirma remoção limpa incl. canonical de hook), `config` com `--conteudo-file` apontando pra um JSON com múltiplos campos, `mcp` com `--mcp-command`.
2.9. `verificar-drift --dir <tmp>/inject-teste` → exit 0 antes de qualquer edição manual; editar manualmente um arquivo injetado e rodar de novo → exit 1 com `SYNC_DIVERGENTE`.
2.10. `bench -n 50 --dir <tmp>/suite-teste` → exit 0, throughput real reportado.
2.11. `heal --dir <tmp>/suite-teste` → roda sem erro (mesmo que só reconfirme o estado).
2.12. `scaffold-infra --dir <tmp>/suite-teste` → exit 0, arquivos Terraform/Helm reais gerados.
2.13. `export-frontend --dir <tmp>/suite-teste` → rodar e documentar o resultado real (pode depender de Node/TS instalado — se faltar dependência, documentar como limitação de ambiente).
2.14. `refine-module <modulo> --dir <tmp>/suite-teste` → rodar contra um dos módulos compostos, se existir `features/<modulo>.feature` gerado por `compose`; se não existir, documentar honestamente que o cenário BDD não foi gerado automaticamente pelo `compose` e por isso este item não pôde ser exercitado via caminho de ouro puro (não fabricar um `.feature` fake só para forçar passar).
2.15. `deploy docker --dir` (não existe flag `--dir` — rodar com `cwd` = `<tmp>/suite-teste`) → só se Docker disponível; documentar e derrubar container ao final.
2.16. `compose-orca <tmp>/suite-orca "Suite Orca" crm erp` → exit 0, manifesto `COMPOSE-ORCA-MANIFEST.json` real gerado.
2.17. Suíte `pytest` completa de `tools/aidd-master` (`python -m pytest tests/ -q`, do diretório `tools/aidd-master`) → exit 0, sem regressão (baseline conhecido: 238 passed, 4 skipped — reconfirmar o número real agora).

## Critério de saída

- Todos os itens acima com exit code real e saída real citada no relatório.
- Nenhum diretório temporário sobrevive fora de `tmp`/scratch — limpar ao final.
- Qualquer limitação de ambiente (Docker, Node, `locust`, `behave` ausente) documentada honestamente, nunca simulada.

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido.

```
Você vai escrever e executar uma bateria de testes reais de ponta a ponta
que prova o caminho de ouro completo da CLI do AIDD Master
(tools/aidd-master/scripts/aidd.py) no monorepo ecossistema-aidd (raiz em
C:\Users\trcnologia\Desktop\ecossistema-aidd). Valide tudo de verdade
(execuções reais, exit codes reais, nunca mascarados por pipe, nunca
simulado). NUNCA rode nada contra o repositório real como diretório
alvo de escrita — sempre use diretórios temporários isolados
(tmp/mktemp -d), limpos ao final.

CONTEXTO JÁ INVESTIGADO (confirme lendo o código antes de escrever o
script — isto é um resumo, releia `tools/aidd-master/scripts/aidd.py`
antes de codificar cada chamada):
- Subcomandos reais (via --help): plan, apply, bench, heal, prompt,
  setup, init, compose, compose-orca, add-module, test, audit, deploy,
  status, export-frontend, refine-module, scaffold-infra, inject,
  verificar-drift.
- `compose <target_dir> <suite_name> [modulos...] [--db sqlite|postgres]`:
  default de módulos é crm/erp/helpdesk/logistica — use só 2 (ex.: crm
  erp) para manter rápido.
- `inject` tem 7 tipos: skill, mcp, rule, spec, config, agent, hook.
  As 5 capacidades (drift SHA-256, remoção com limpeza do canônico,
  rollback com snapshot, dry-run, config com mapa arbitrário de
  arquivos + path traversal) JÁ têm cobertura pytest real em
  tools/aidd-master/tests/unit/test_injector_core.py (Rodada 2, Item 4)
  — esta bateria deve reexercitar via CLI DIRETA (subprocess real, não
  só reconfirmar o pytest existente).
- `plan`/`prompt` usam casamento de palavras-chave contra lista fixa de
  domínios, SEM LLM — zero custo, teste à vontade.
- `deploy docker` roda `docker compose up -d --build` de verdade,
  usando o cwd atual do processo (não tem flag --dir) — só rode se
  Docker estiver instalado E funcionando nesta máquina; se não estiver,
  documente como limitação de ambiente e não tente simular. Se rodar,
  DERRUBE o container com `docker compose down` ao final, sem exceção.
- `test load` precisa de `locust` instalado; `refine-module` precisa de
  `behave` (se instala sozinho) E de um arquivo `features/<modulo>.feature`
  real dentro do projeto composto — confirme se `compose` gera esse
  arquivo automaticamente; se não gerar, documente honestamente essa
  limitação em vez de fabricar um `.feature` só pra forçar o teste
  passar.
- `export-frontend` pode depender de Node/TypeScript instalados — rode
  e documente o resultado real, seja ele qual for.

DEFINIÇÃO DE PRONTO — rode cada item de verdade, em diretórios
temporários isolados, nesta ordem (numeração corresponde à
`docs/planos/testes-completos-ecossistema/02-testes-aidd-master.md`,
seção "Definição de Pronto" — leia aquele documento por extenso antes
de começar, ele tem os 17 itens detalhados: init, compose com 2
módulos, add-module, test unit, audit do projeto composto, status,
plan/prompt em linguagem natural (2 frases diferentes, domínios
diferentes), inject dos 7 tipos + dry-run + remover + config com
arquivo + mcp com command, verificar-drift (caso limpo E caso de
drift real após edição manual), bench, heal, scaffold-infra,
export-frontend, refine-module (ou documentar limitação), deploy
docker (ou documentar limitação, sempre derrubando o container se
subir), compose-orca, e por fim a suíte pytest completa de
tools/aidd-master (python -m pytest tests/ -q, cwd tools/aidd-master)
confirmando o número real de testes passando agora.

Para os itens de linguagem natural (plan/prompt), salve o texto exato
usado como prompt de teste em arquivos separados dentro de
`docs/testes/prompts/aidd_master_<nome-do-cenario>.txt` — não misture
o texto do prompt de teste com o código do script.

Escreva o(s) script(s) reais (Python recomendado, dado o volume de
subprocess.run com captura de stdout/stderr/exit code) e salve-os em
`docs/testes/testes/02_aidd_master_*.py` (pode dividir em múltiplos
arquivos por grupo de comando, ex.: 02_aidd_master_inject.py,
02_aidd_master_compose.py — o que for mais legível).

Execute os scripts de verdade agora. Depois, escreva o relatório da
bateria em `docs/testes/relatorios/02_aidd_master.md`: para cada um dos
17 itens da Definição de Pronto, comando exato rodado, exit code real,
resumo da saída relevante, e limitações de ambiente encontradas (se
houver). Veredito final claro (PASSOU/FALHOU/PASSOU COM RESSALVAS, com
justificativa). Use as skills `artifact-design` e `dataviz` para uma
versão visual do relatório (ex.: painel com os 17 itens e status),
mantendo o Markdown como fonte de verdade.

CRITÉRIO DE SAÍDA:
- Os 17 itens rodados de verdade, evidência real no relatório.
- Nenhum diretório temporário sobrevivendo fora de tmp/scratch.
- Nenhum container Docker órfão rodando.
- `git status` da raiz do ecossistema real limpo ao final (só os
  arquivos esperados em docs/testes/ novos).
- Suíte pytest de tools/aidd-master sem regressão do baseline conhecido
  (238 passed, 4 skipped) — se o número mudar, investigue por quê antes
  de reportar.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não teste aidd-enterprise, aidd-forge ou aidd-generator aqui (são
  baterias separadas).
- Não faça git commit nem git push em nenhum repositório (nem no
  ecossistema real, nem nos projetos temporários gerados).
- Não deixe containers Docker, processos de servidor ou diretórios
  temporários órfãos.

ENTREGÁVEL: lista de scripts salvos, lista de prompts salvos, caminho
do relatório, e um resumo de 5-8 linhas do veredito final incluindo
qualquer limitação de ambiente encontrada.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to write and run a battery of real end-to-end tests
proving the complete golden path of the AIDD Master CLI
(tools/aidd-master/scripts/aidd.py) works, inside the ecossistema-aidd
monorepo (root at C:\Users\trcnologia\Desktop\ecossistema-aidd).
Validate everything for real (real runs, real exit codes, never masked
by a pipe, never simulated). NEVER run anything against the real
repository as a write target — always use isolated temporary
directories (tmp/mktemp -d), cleaned up at the end.

ALREADY-INVESTIGATED CONTEXT (confirm by reading the code before
writing the script — this is a summary, re-read
`tools/aidd-master/scripts/aidd.py` before coding each call):
- Real subcommands (via --help): plan, apply, bench, heal, prompt,
  setup, init, compose, compose-orca, add-module, test, audit, deploy,
  status, export-frontend, refine-module, scaffold-infra, inject,
  verificar-drift.
- `compose <target_dir> <suite_name> [modulos...] [--db sqlite|postgres]`:
  default modules are crm/erp/helpdesk/logistica — use only 2 (e.g.
  crm erp) to keep it fast.
- `inject` has 7 types: skill, mcp, rule, spec, config, agent, hook.
  The 5 enriched capabilities (SHA-256 drift, removal with canonical
  cleanup, full-snapshot rollback, dry-run, config with an arbitrary
  file map + path-traversal protection) ALREADY have real pytest
  coverage in tools/aidd-master/tests/unit/test_injector_core.py
  (Round 2, Item 4) — this battery must re-exercise them via DIRECT CLI
  (real subprocess, not just re-confirming the existing pytest suite).
- `plan`/`prompt` use keyword matching against a fixed domain list, NO
  LLM — zero cost, test freely.
- `deploy docker` really runs `docker compose up -d --build`, using the
  process's current working directory (no --dir flag on this command,
  and the subprocess call passes no cwd=) — only test it if Docker is
  installed AND working on this machine; if not, document it as an
  environment limitation and do not try to simulate it. If you do run
  it, ALWAYS tear it down with `docker compose down` at the end, no
  exceptions.
- `test load` needs `locust` installed; `refine-module` needs `behave`
  (auto-installs itself) AND a real `features/<modulo>.feature` file
  inside the composed project — check whether `compose` generates that
  file automatically; if it doesn't, document that limitation honestly
  instead of fabricating a `.feature` file just to force the test to
  pass.
- `export-frontend` may depend on Node/TypeScript being installed — run
  it and document the real result, whatever it is.

DEFINITION OF DONE — run each item for real, in isolated temporary
directories, in this order (numbering matches
`docs/planos/testes-completos-ecossistema/02-testes-aidd-master.md`,
"Definição de Pronto" section — read that document in full before
starting, it has the 17 detailed items: init, compose with 2 modules,
add-module, test unit, audit of the composed project, status,
plan/prompt in natural language (2 different sentences, different
domains), inject of all 7 types + dry-run + remover + config with a
file + mcp with command, verificar-drift (clean case AND real-drift
case after manual edit), bench, heal, scaffold-infra, export-frontend,
refine-module (or document the limitation), deploy docker (or document
the limitation, always tearing down the container if it comes up),
compose-orca, and finally the full pytest suite of tools/aidd-master
(python -m pytest tests/ -q, cwd tools/aidd-master) confirming the real
number of tests passing right now.

For the natural-language items (plan/prompt), save the exact text used
as a test prompt in separate files under
`docs/testes/prompts/aidd_master_<scenario-name>.txt` — do not mix the
test-prompt text with the script code.

Write the real script(s) (Python recommended, given the volume of
subprocess.run calls needing stdout/stderr/exit-code capture) and save
them under `docs/testes/testes/02_aidd_master_*.py` (you may split
into multiple files by command group, e.g.
02_aidd_master_inject.py, 02_aidd_master_compose.py — whichever is more
readable).

Run the scripts for real now. Then write the battery report at
`docs/testes/relatorios/02_aidd_master.md`: for each of the 17 items in
the Definition of Done, the exact command run, real exit code, summary
of relevant output, and any environment limitations found (if any).
Clear final verdict (PASSED/FAILED/PASSED WITH CAVEATS, with
justification). Use the `artifact-design` and `dataviz` skills for a
visual version of the report (e.g. a panel with the 17 items and their
status), keeping the Markdown as the source of truth.

EXIT CRITERIA:
- The 17 items run for real, real evidence in the report.
- No temporary directory surviving outside tmp/scratch.
- No orphaned Docker container running.
- The real ecosystem repository's root `git status` clean at the end
  (only the expected new files under docs/testes/).
- tools/aidd-master's pytest suite with no regression from the known
  baseline (238 passed, 4 skipped) — if the number changes, investigate
  why before reporting.

SCOPE RULES — DO NOT:
- Do not test aidd-enterprise, aidd-forge, or aidd-generator here (they
  are separate batteries).
- Do not git commit or git push in any repository (neither the real
  ecosystem one, nor the generated temporary projects).
- Do not leave orphaned Docker containers, server processes, or
  temporary directories.

DELIVERABLE: list of saved scripts, list of saved prompts, report path,
and a 5-8 line summary of the final verdict including any environment
limitation found.
```
