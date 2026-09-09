# Item 18 — CLI do aidd-forge convertida de argparse para click pela metade (suíte inteira quebrada na coleta)

> **Escopo:** Entra: finalizar ou reverter a conversão em andamento de `tools/aidd-forge/aidd_forge/cli.py de argparse para click (modificação não comitada achada na árvore em 2026-09-09), e adaptar `tests/unit/test_cli.py (que importa `build_parser, símbolo removido pela conversão). Não entra: mudanças de comportamento dos comandos do forge em si nem outros módulos do forge.
> **Status:** [✅ CONCLUÍDO em 2026-09-09 — decisão registrada: REVERTER ao argparse. `aidd_forge/cli.py` atual é idêntico ao HEAD (`import argparse`, `build_parser()` restaurado, zero `import click`); suíte do aidd-forge coleta e roda 100% verde: 197 passed, 1 skipped. Nenhuma dependência nova (click não entrou no manifest do forge).]
> **Modelo sugerido:** Claude Haiku · Antigravity Gemini 3.1 pro · MiMo mimo-v2.5 (finalizar 1 conversão de CLI + 1 arquivo de teste)

---

## Contexto já investigado (evidência real desta sessão)

- Passada final de testes do plano 01-16: `cd tools/aidd-forge && python -m pytest -q → **1 error in 0.24s` (falha de COLEÇÃO, a suíte inteira nem roda):
  - `tests/unit/test_cli.py:5 → `from aidd_forge.cli import build_parser, main → `ImportError: cannot import name 'build_parser'.
- `git diff tools/aidd-forge/aidd_forge/cli.py → conversão não comitada **argparse → click (mesmo padrão do Item 17 no aidd-generator): `import argparse removido, `import click adicionado, `cmd_init(args: argparse.Namespace) substituído por grupo click `forge_cli` + `@forge_cli.command init` — e `build_parser()` removido, sem nenhum shim de compatibilidade.
- **Origem: sessão concorrente** — mtime do arquivo: 2026-09-09 12:34:01 (durante a execução deste plano, sem ligação com nenhum item 01-16; esta sessão nunca tocou em `tools/aidd-forge/). Monitorado por 45s na passada final (~13:15): arquivo estático, conversão NÃO se completou sozinha (diferente do caso do aidd_inject, que a sessão concorrente terminou — Item 17).
- Estado anterior verificado: na telemetria do Item 2 (início da sessão), as 5 ferramentas somavam **1714 passed` incluindo o aidd-forge — a suíte estava verde antes da conversão de 12:34.
- O mesmo `git status que revelou este achado mostrou renames staged de dezenas de pastas de docs e `tools/aidd-ops/scripts/pipeline_ops_deploy.py modificado — atividade paralela confirmada na mesma árvore de trabalho.

## Definição de Pronto

1. Decidir (humano ou regra padrão numa próxima rodada): **reverter** `aidd_forge/cli.py ao argparse (suíte voltava a ficar verde; a conversão não foi pedida por nenhum item) **ou finalizar** a conversão para click (adaptando `test_cli.py ao contrato click, criando o entry `main()` equivalente e, se mantida, declarar `click` nas dependências do forge). Regra padrão sugerida: reverter, pelos mesmos motivos do Item 17 — conversão não solicitada, quebra suíte, adiciona dependência nova; reversível se houver plano externo.
2. `cd tools/aidd-forge && python -m pytest -q → 0 failed, 0 error (suíte completa coleta e roda).
3. Se optar por finalizar: `click declarado no manifest de dependências do aidd-forge.
4. Gates de integridade aprovados.

## Critério de saída

- Suíte do aidd-forge 100% verde de novo.
- Decisão (finalizar vs reverter) registrada aqui com justificativa.
- Nenhuma dependência implícita de terceiro.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item 18: CLI do aidd-forge convertida de argparse para click pela metade.
Siga rigorosamente a Definição de Pronto acima.
Não invente aprovações e mantenha as regras do monorepo.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 18: aidd-forge CLI half-converted from argparse to click.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```

---

## Execução real e evidências (2026-09-09)

### 1. Decisão registrada: REVERTER (argparse permanece)

Mesmos motivos do Item 17: a conversão click não foi pedida por nenhum item,
quebrava a coleta da suíte inteira (`ImportError: cannot import name
'build_parser'`) e adicionaria dependência nova sem necessidade. A sessão
concorrente já havia revertido o arquivo antes desta sessão retomar:

- `tools/aidd-forge/aidd_forge/cli.py` atual: `import argparse` (linha 9),
  `cmd_init(args: argparse.Namespace)` (linha 27), `cmd_inject` (linha 65),
  `build_parser()` (linha 100) — sem nenhum `import click`. Sem diff contra `HEAD`.
- `tools/aidd-forge/requirements.txt`: sem entrada `click` (grep → 0).

### 2. Critérios de saída conferidos

- `cd tools/aidd-forge && python -m pytest -q` → **197 passed, 1 skipped**
  (suíte coleta e roda completa, 0 failed, 0 error). ✅
- Decisão (finalizar vs reverter) registrada aqui com justificativa. ✅
- Nenhuma dependência implícita de terceiro (click permanece fora do manifest
  do forge, e o código não o usa). ✅
