# Item 2 — Preparar projeto com forge

> **Escopo:** Entra: injetar a infraestrutura AIDD (AGENTS.md, gates, skills) dentro de `C:\Users\trcnologia\Desktop\proj_ctt` usando o `aidd-forge`, e auditar a conformidade do resultado. Nao entra: gerar codigo de aplicacao (isso e item 3).
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** 9
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- **CORRECAO de um achado anterior deste mesmo plano:** `python -m aidd_forge.cli` chamado diretamente da raiz do monorepo de fato da `ModuleNotFoundError` — MAS a forma certa e correta de usar o forge NUNCA e essa chamada direta. E sim `python ecossistema.py forge <args>`, rodado da raiz do monorepo. Confirmado lendo `ecossistema.py::cmd_forge`: ele monta o subprocesso com `cwd=tools/aidd-forge` e `PYTHONPATH=tools/aidd-forge` automaticamente. Testado de verdade: `python ecossistema.py forge init <pasta-descartavel>` funcionou (36 arquivos criados, 6 slash commands gravados, 8 gates instalados).
- **Bug real confirmado (fora do escopo deste item, registrado para follow-up separado):** o pacote `aidd-forge` esta instalado via `pip -e` apontando para um worktree Orca antigo/morto (`C:\Users\trcnologia\orca\workspaces\ecossistema-aidd\PLAN-0021-...\tools\aidd-forge`), nao para a pasta atual. Por isso `python -m aidd_forge.cli` so funciona por acidente quando o cwd already e `tools/aidd-forge/` (o Python acha o pacote local via cwd, nao via o pip -e quebrado). Isso quebra os slash commands `/forge` e `/aidd-init` reinjetados num projeto externo, porque o `.md` deles manda rodar exatamente essa chamada direta e quebrada (`python -m aidd_forge.cli init`, sem cwd/PYTHONPATH). Documentado em `docs/MIGRACAO-PROJETO-EXISTENTE.md` (tabela de problemas comuns).
- Comandos reais do CLI (via `python ecossistema.py forge <cmd>`): `init [PATH] [--force]`, `audit [PATH] [--format json|md|html] [--output PATH]`, `inject {skill|mcp|rule|spec|roteiro|config|command|hook|sub-agent|script} NOME --descricao ... [--path PATH]`, `conform`.
- `proj_ctt` hoje so tem os relatorios (`relatorio_frotas_roteirizacao_ctt.md/html/pdf/typ`, `relatorio_logistica_frotas_ctt.*`, `style.css`, `template.html`) — nenhum `AGENTS.md`, nenhum `.git`. O `forge init` precisa injetar a infraestrutura nesse terreno vazio.
- Testado num diretorio descartavel (nao em `proj_ctt`): apos `forge init`, so `.claude/commands/forge.md` e `aidd-init.md` sao gravados (mais os espelhos em `.agent/`, `.cursor/`, `.gemini/`) — os OUTROS comandos (`/generate`, `/master`, `/enterprise`, `/ops`, `/bridge`, `/plan`) NAO sao injetados no projeto externo. Eles continuam sendo comandos do TOOLBOX, chamados de la apontando `--pasta`/caminho pro projeto externo — nao existem "dentro" do projeto do usuario.

## Definicao de Pronto

1. `python -m aidd_forge.cli init "C:\Users\trcnologia\Desktop\proj_ctt"` (rodado de dentro de `tools/aidd-forge/`) termina com exit 0 e cria `AGENTS.md` + gates dentro de `proj_ctt`.
2. `python -m aidd_forge.cli audit "C:\Users\trcnologia\Desktop\proj_ctt" --format md --output relatorio_forge_audit.md` termina com exit 0 e o relatorio mostra conformidade real (nao "0 checks rodados").
3. Se algum item do audit falhar, `python -m aidd_forge.cli conform "C:\Users\trcnologia\Desktop\proj_ctt"` e rodado e o audit e repetido ate exit 0 real.

## Criterio de saida

- `proj_ctt/AGENTS.md` existe e tem conteudo real (nao vazio, nao stub).
- O relatorio de audit foi gerado de verdade (arquivo no disco) e lido, nao inferido pelo agente.
- Os relatorios originais (`relatorio_frotas_roteirizacao_ctt.*` etc.) continuam intactos — o forge so adiciona infraestrutura, nunca apaga conteudo do usuario.

## Comandos estruturados (ordem real de execucao)

```bash
cd ecossistema-aidd
python ecossistema.py forge init "C:\Users\trcnologia\Desktop\proj_ctt"
python ecossistema.py forge audit "C:\Users\trcnologia\Desktop\proj_ctt" --format md --output relatorio_forge_audit.md
# se o audit apontar nao-conformidade:
python ecossistema.py forge conform "C:\Users\trcnologia\Desktop\proj_ctt"
python ecossistema.py forge audit "C:\Users\trcnologia\Desktop\proj_ctt" --format md --output relatorio_forge_audit.md
```

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 2: Preparar projeto com forge.
IMPORTANTE: use sempre "python ecossistema.py forge <args>" rodado da RAIZ do monorepo
(nunca "python -m aidd_forge.cli" direto - isso quebra fora de tools/aidd-forge por causa
de uma instalacao pip -e quebrada, ja documentada em docs/MIGRACAO-PROJETO-EXISTENTE.md).
Rode os comandos da secao "Comandos estruturados" nesta ordem exata.
Leia o arquivo de audit gerado (relatorio_forge_audit.md) de verdade antes de declarar sucesso.
Confirme que os relatorios originais do usuario em proj_ctt nao foram apagados nem sobrescritos.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: Preparar projeto com forge (bootstrap the target project).
IMPORTANT: always use "python ecossistema.py forge <args>" run from the monorepo ROOT
(never call "python -m aidd_forge.cli" directly - it breaks outside tools/aidd-forge due to
a broken pip -e install, already documented in docs/MIGRACAO-PROJETO-EXISTENTE.md).
Run the commands in "Comandos estruturados" in this exact order.
Actually read the generated audit file (relatorio_forge_audit.md) before declaring success.
Confirm the user's original report files under proj_ctt were not deleted or overwritten.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
