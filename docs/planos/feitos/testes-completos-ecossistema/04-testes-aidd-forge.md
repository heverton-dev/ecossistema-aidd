# Bateria 4 — AIDD Forge (`tools/aidd-forge`)

> **Escopo:** provar o caminho de ouro completo da CLI (`python -m aidd_forge.cli`, ou via `python ecossistema.py forge ...`) — `init` e `inject`, incluindo o hook de pre-commit REAL instalado num repositório git de teste e os 7 Quality Gates que ele instala no projeto alvo.
> **Custo de LLM:** zero — ferramenta 100% determinística (templating de arquivos + checagens AST/regex), confirmado por investigação de código (nenhuma chamada de rede, nenhuma variável de API key, nenhum "protocolo delegado").

---

## Contexto já investigado

- CLI real: `tools/aidd-forge/aidd_forge/cli.py` — só 2 subcomandos:
  - `init [path] [--force]` (path default `.`).
  - `inject <tipo> <nome> --descricao DESC (--conteudo TXT | --conteudo-file PATH) [--path PATH] [--force]`, `tipo` em `{skill, mcp, rule, spec, roteiro}`.
- Invocação real (via `ecossistema.py`): `python ecossistema.py forge init <path>` / `python ecossistema.py forge inject <tipo> <nome> --descricao "..." --conteudo "..." --path <path>`. Equivalente direto: `PYTHONPATH=tools/aidd-forge python -m aidd_forge.cli init <path>`.
- `init` só funciona por completo (hook de pre-commit incluso) se o `path` alvo já for um repositório git real (`git init` + `user.email`/`user.name` configurados) — sem isso, o teste ainda roda mas não prova o hook.
- Artefatos esperados de um `init` bem-sucedido (releia o teste real existente,
  `tools/aidd-forge/tests/integration/test_full_forge_pipeline.py`, é o padrão de referência a imitar — usa `tmp_path`, `git init` real, roda o hook real via `subprocess.run(["sh", hook_path])`):
  - `governance/AGENTS.md`, `CLAUDE.md`
  - `orca/01_orca_inventory.json`, `orca/02_routing_rules.json`
  - `.aidd/pipeline/phase_00_bootstrap/` … `phase_04_audit_security/` (cada uma com `AGENTS.md` + `mcp_config.json`)
  - `.agent/skills/<skill>/SKILL.md` para pelo menos: caveman-ultra, orca-orchestration, impeccable-ui, open-code-review, post-mortem, cybersecurity-audit
  - `.cursor/rules/forge.md`, `.cursor/rules/aidd-init.md` (e espelhos em `.claude/commands/`, `.agent/commands/`)
  - `gates/<7 arquivos>.py`: `G_BLOQUEAR_SEGREDOS`, `G_CONTRACTS`, `G_CYBERSECURITY_OWASP`, `G_ESTRUTURA_AST`, `G_HARNESS_COMPAT`, `G_INJECT`, `G_PERFORMANCE`, `G_TESTES_REAIS` (**7 gates**, confirme a lista exata lendo o teste de referência).
  - `.git/hooks/pre-commit` contendo a string `"Quality Gates"`.
- `inject skill` cria `.agent/skills/<nome>/SKILL.md`; `inject mcp` cria `aidd_forge/mcps/<nome>.py` + `aidd_forge/mcps/registry.json`.
- Existe já um teste de integração real e completo
  (`tools/aidd-forge/tests/integration/test_full_forge_pipeline.py`) cobrindo: segredo bloqueado pelo hook, erro de sintaxe bloqueado, commit limpo permitido, idempotência/`--force`, `inject` de skill+mcp seguido de re-execução do hook real. **Esta bateria não deve duplicar esse teste** — deve reexercitar o mesmo caminho de ouro via CLI de fora (subprocess real, como um usuário faria), não via `main()` importado diretamente como o teste pytest já faz.

## Definição de Pronto

4.1. `git init` real num diretório temporário + config `user.email`/`user.name` locais.
4.2. `python ecossistema.py forge init <tmp>` (ou equivalente direto via `python -m aidd_forge.cli`) → exit 0; confirmar via `ls`/`Path.exists` a presença de TODOS os artefatos listados no "Contexto já investigado" acima (não só uma amostra).
4.3. Confirmar que `.git/hooks/pre-commit` contém `"Quality Gates"` e é executável.
4.4. Criar um arquivo com um segredo óbvio (ex.: uma chave AWS fake `AKIA...`) dentro do repositório de teste, `git add` + tentar commitar → o hook real deve BLOQUEAR o commit (exit não-zero do `git commit`).
4.5. Remover o segredo, criar um arquivo Python com erro de sintaxe deliberado, tentar commitar → hook deve bloquear (G_ESTRUTURA_AST).
4.6. Corrigir o arquivo, commitar de novo → hook deve PERMITIR o commit desta vez.
4.7. Rodar `init` de novo no mesmo diretório sem `--force` → deve recusar/avisar (não sobrescrever silenciosamente); rodar com `--force` → deve sobrescrever com sucesso (exit 0).
4.8. `inject skill <nome> --descricao "..." --conteudo "..." --path <tmp>` → exit 0, `.agent/skills/<nome>/SKILL.md` criado com o conteúdo certo.
4.9. `inject mcp <nome> --descricao "..." --conteudo-file <arquivo-real> --path <tmp>` → exit 0, `aidd_forge/mcps/<nome>.py` criado e `registry.json` atualizado.
4.10. Rodar o hook de pre-commit de novo depois das injeções (novo commit real) → ainda passa.
4.11. Rodar a suíte `pytest` completa de `tools/aidd-forge` (`python -m pytest tests/ -q`, cwd `tools/aidd-forge`) → exit 0, capturar contagem real (sem regressão em relação ao estado atual do repositório).

## Critério de saída

- Todos os 11 itens com exit code real e evidência real no relatório.
- O bloqueio real de commit (item 4.4 e 4.5) precisa mostrar o `git commit` falhando de verdade, não só o gate rodado isoladamente.
- Nenhum diretório temporário sobrevivendo fora de tmp/scratch ao final.

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido.

```
Você vai escrever e executar uma bateria de testes reais de ponta a
ponta que prova o caminho de ouro completo da CLI do AIDD Forge
(tools/aidd-forge/aidd_forge/cli.py) no monorepo ecossistema-aidd (raiz
em C:\Users\trcnologia\Desktop\ecossistema-aidd). Valide tudo de
verdade (execuções reais, exit codes reais, nunca mascarados por pipe).
NUNCA rode nada contra o repositório real como diretório alvo de
escrita — sempre use um diretório temporário isolado que seja, ele
mesmo, um repositório git novo e real (git init + config local), limpo
ao final.

CONTEXTO JÁ INVESTIGADO (confirme lendo o código, e leia primeiro
tools/aidd-forge/tests/integration/test_full_forge_pipeline.py — é o
padrão de referência real já existente para este exato fluxo, imite o
estilo mas rode via CLI externa/subprocess, não via import direto de
main()):
- CLI real: `init [path] [--force]` e
  `inject <tipo> <nome> --descricao DESC (--conteudo TXT | --conteudo-file PATH) [--path PATH] [--force]`,
  tipo em {skill, mcp, rule, spec, roteiro}. Invocação via wrapper:
  `python ecossistema.py forge init <path>` /
  `python ecossistema.py forge inject <tipo> <nome> --descricao "..." --conteudo "..." --path <path>`.
- Zero custo de LLM — ferramenta 100% determinística, já confirmado por
  investigação de código (sem chamadas de rede, sem API key, sem
  protocolo delegado). Pode/deve testar à vontade sem se preocupar com
  custo.
- `init` só prova o hook de pre-commit de verdade se o `path` alvo já
  for um repositório git real com `user.email`/`user.name`
  configurados — configure isso ANTES de rodar `init`.
- Artefatos esperados de um `init` completo: governance/AGENTS.md,
  CLAUDE.md, orca/01_orca_inventory.json, orca/02_routing_rules.json,
  .aidd/pipeline/phase_00_bootstrap a phase_04_audit_security (cada uma
  com AGENTS.md + mcp_config.json), .agent/skills/<skill>/SKILL.md para
  pelo menos caveman-ultra/orca-orchestration/impeccable-ui/open-code-
  review/post-mortem/cybersecurity-audit, .cursor/rules/forge.md +
  aidd-init.md (e espelhos em .claude/commands/, .agent/commands/), 7
  arquivos de gate em gates/ (G_BLOQUEAR_SEGREDOS, G_CONTRACTS,
  G_CYBERSECURITY_OWASP, G_ESTRUTURA_AST, G_HARNESS_COMPAT, G_INJECT,
  G_PERFORMANCE, G_TESTES_REAIS — confirme a lista exata lendo
  EXPECTED_GATES no teste de referência), e .git/hooks/pre-commit
  contendo a string "Quality Gates".
- `inject skill` cria .agent/skills/<nome>/SKILL.md; `inject mcp` cria
  aidd_forge/mcps/<nome>.py + aidd_forge/mcps/registry.json.

DEFINIÇÃO DE PRONTO — rode nesta ordem (releia
docs/planos/testes-completos-ecossistema/04-testes-aidd-forge.md por
extenso primeiro, tem os 11 itens detalhados): git init + config real
num tmp dir; `forge init` completo com verificação de TODOS os
artefatos esperados (não uma amostra); confirmar conteúdo do hook;
criar arquivo com segredo óbvio (ex.: chave AWS fake AKIA...), tentar
commitar de verdade e confirmar que o `git commit` FALHA por causa do
hook; remover o segredo, criar arquivo Python com erro de sintaxe,
confirmar que o commit falha de novo; corrigir e confirmar que o
commit passa desta vez; rodar `init` sem --force (deve recusar/avisar)
e com --force (deve sobrescrever); `inject skill` e `inject mcp` reais
com conteúdo real; rodar o hook de novo depois das injeções (deve
continuar passando); suíte pytest completa de tools/aidd-forge (python
-m pytest tests/ -q, cwd tools/aidd-forge), capturar contagem real e
exit code.

Escreva o(s) script(s) reais e salve-os em
`docs/testes/testes/04_aidd_forge_*.py` (ou .sh, à sua escolha — dado
que este fluxo envolve muito `git` real, um script Python que usa
subprocess para tudo (incluindo os comandos git) tende a ser mais fácil
de auditar depois). Não há prompt em linguagem natural nesta bateria
(aidd-forge não tem entrada em linguagem natural na CLI) — pode pular
docs/testes/prompts/ para esta bateria.

Execute de verdade agora. Escreva o relatório em
`docs/testes/relatorios/04_aidd_forge.md`: cada item, comando exato,
exit code real, saída relevante — dê destaque especial (seção própria,
com o texto real do erro do git) para os 2 bloqueios reais de commit
(segredo e sintaxe) e para o commit que passa depois da correção, já
que essa é a prova mais forte de que o hook funciona de ponta a ponta,
não só em isolamento. Veredito final claro. Use as skills
`artifact-design` e `dataviz` se fizer sentido visualizar o fluxo
(ex.: um diagrama do pipeline commit → hook → gates → bloqueado/
permitido), mantendo o Markdown como fonte de verdade.

CRITÉRIO DE SAÍDA:
- Todos os 11 itens rodados de verdade, evidência real no relatório.
- Os 2 bloqueios de commit precisam mostrar o `git commit` real
  falhando (código de saída do git, não só do gate isolado).
- Nenhum diretório temporário sobrevivendo fora de tmp/scratch.
- `git status` da raiz do ecossistema real limpo ao final.
- Suíte pytest de tools/aidd-forge sem regressão — reporte o número
  real encontrado.

REGRAS DE ESCOPO — NÃO FAÇA:
- Não teste aidd-master, aidd-enterprise ou aidd-generator aqui.
- Não faça git commit nem git push no repositório REAL do ecossistema
  (commits de teste só dentro do repositório git temporário isolado).
- Não deixe diretórios temporários órfãos.

ENTREGÁVEL: lista de scripts salvos, caminho do relatório, resumo de
5-8 linhas do veredito final.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to write and run a battery of real end-to-end tests
proving the complete golden path of the AIDD Forge CLI
(tools/aidd-forge/aidd_forge/cli.py) works, inside the
ecossistema-aidd monorepo (root at
C:\Users\trcnologia\Desktop\ecossistema-aidd). Validate everything for
real (real runs, real exit codes, never masked by a pipe). NEVER run
anything against the real repository as a write target — always use an
isolated temporary directory that is itself a new, real git repository
(git init + local config), cleaned up at the end.

ALREADY-INVESTIGATED CONTEXT (confirm by reading the code, and read
tools/aidd-forge/tests/integration/test_full_forge_pipeline.py FIRST —
it is the existing real reference pattern for this exact flow; imitate
its style but drive it via external CLI/subprocess, not by importing
main() directly):
- Real CLI: `init [path] [--force]` and
  `inject <tipo> <nome> --descricao DESC (--conteudo TXT | --conteudo-file PATH) [--path PATH] [--force]`,
  tipo in {skill, mcp, rule, spec, roteiro}. Invocation via wrapper:
  `python ecossistema.py forge init <path>` /
  `python ecossistema.py forge inject <tipo> <nome> --descricao "..." --conteudo "..." --path <path>`.
- Zero LLM cost — a fully deterministic tool, already confirmed by
  code investigation (no network calls, no API key, no delegated
  protocol). Test freely without worrying about cost.
- `init` only proves the pre-commit hook for real if the target `path`
  is already a real git repository with `user.email`/`user.name`
  configured — set this up BEFORE running `init`.
- Expected artifacts of a complete `init`: governance/AGENTS.md,
  CLAUDE.md, orca/01_orca_inventory.json, orca/02_routing_rules.json,
  .aidd/pipeline/phase_00_bootstrap through phase_04_audit_security
  (each with AGENTS.md + mcp_config.json),
  .agent/skills/<skill>/SKILL.md for at least caveman-ultra/orca-
  orchestration/impeccable-ui/open-code-review/post-mortem/
  cybersecurity-audit, .cursor/rules/forge.md + aidd-init.md (and
  mirrors under .claude/commands/, .agent/commands/), 7 gate files
  under gates/ (G_BLOQUEAR_SEGREDOS, G_CONTRACTS,
  G_CYBERSECURITY_OWASP, G_ESTRUTURA_AST, G_HARNESS_COMPAT, G_INJECT,
  G_PERFORMANCE, G_TESTES_REAIS — confirm the exact list by reading
  EXPECTED_GATES in the reference test), and .git/hooks/pre-commit
  containing the string "Quality Gates".
- `inject skill` creates .agent/skills/<nome>/SKILL.md; `inject mcp`
  creates aidd_forge/mcps/<nome>.py + aidd_forge/mcps/registry.json.

DEFINITION OF DONE — run in this order (re-read
docs/planos/testes-completos-ecossistema/04-testes-aidd-forge.md in
full first, it has the 11 detailed items): real git init + config in a
tmp dir; a complete `forge init` with verification of ALL expected
artifacts (not a sample); confirm the hook's content; create a file
with an obvious secret (e.g. a fake AWS key AKIA...), try to commit for
real and confirm the `git commit` FAILS because of the hook; remove the
secret, create a Python file with a syntax error, confirm the commit
fails again; fix it and confirm the commit passes this time; run `init`
again without --force (should refuse/warn) and with --force (should
overwrite); real `inject skill` and `inject mcp` with real content; run
the hook again after the injections (should still pass); the full
pytest suite of tools/aidd-forge (python -m pytest tests/ -q, cwd
tools/aidd-forge), capturing the real count and exit code.

Write the real script(s) and save them under
`docs/testes/testes/04_aidd_forge_*.py` (or .sh, your choice — given
how much real `git` is involved in this flow, a Python script that uses
subprocess for everything including the git commands tends to be
easier to audit later). There is no natural-language input in this
battery (aidd-forge's CLI has no natural-language entry point) — you
may skip docs/testes/prompts/ for this battery.

Run everything for real now. Write the report at
`docs/testes/relatorios/04_aidd_forge.md`: each item, exact command,
real exit code, relevant output — give special emphasis (its own
section, with the real git error text) to the 2 real commit blocks
(secret and syntax error) and to the commit that passes after the fix,
since that is the strongest proof that the hook works end to end, not
just in isolation. Clear final verdict. Use the `artifact-design` and
`dataviz` skills if it makes sense to visualize the flow (e.g. a
diagram of commit → hook → gates → blocked/allowed), keeping the
Markdown as the source of truth.

EXIT CRITERIA:
- All 11 items run for real, real evidence in the report.
- Both commit blocks need to show the real `git commit` failing (the
  git command's own exit code, not just the isolated gate's).
- No temporary directory surviving outside tmp/scratch.
- The real ecosystem repository root's `git status` clean at the end.
- tools/aidd-forge's pytest suite with no regression — report the real
  number found.

SCOPE RULES — DO NOT:
- Do not test aidd-master, aidd-enterprise, or aidd-generator here.
- Do not git commit or git push in the REAL ecosystem repository (test
  commits only inside the isolated temporary git repository).
- Do not leave orphaned temporary directories.

DELIVERABLE: list of saved scripts, report path, 5-8 line summary of
the final verdict.
```
