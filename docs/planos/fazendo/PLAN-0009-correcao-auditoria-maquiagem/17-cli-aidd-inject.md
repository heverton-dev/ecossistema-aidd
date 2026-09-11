# Item 17 — CLI aidd_inject convertida de argparse para click pela metade (6 testes quebrados + dependência não declarada)

> **Escopo:** Entra: finalizar ou reverter a conversão em andamento de `tools/aidd-generator/scripts/aidd_inject.py` de argparse para click (modificação não comitada encontrada na árvore em 2026-09-09), reverter/adapter os 6 testes de `tests/test_aidd_inject_cli.py` que quebraram com ela, e declarar (ou remover) a dependência `click` em `tools/aidd-generator/requirements.txt`. Não entra: mudanças de comportamento da injeção em si (`injetar()`, injector core), outros scripts CLI do generator, nem o restante do pipeline de 8 fases.
> **Status:** [✅ CONCLUÍDO em 2026-09-09 — DECISÃO REVISTA (mesmo dia, sessão posterior): a reversão para argparse registrada abaixo foi a decisão correta NO MOMENTO em que foi tomada (conversão pela metade, 6 testes quebrados, dependência não declarada). Horas depois, o item 10 do plano estratégico `docs/planos/feitos/02-direcionamento-estrategico-anti-nih/` (Onda 4 — zero argparse nos pontos de entrada de CLI) exigiu migrar `aidd_inject.py` para click de novo, desta vez de forma completa: os 6 testes que quebraram na tentativa anterior foram adaptados ao contrato click (não revertidos), `pipeline_completo.py` também migrado, e `click>=8.0` devidamente declarado em `tools/aidd-generator/requirements.txt` — fechando exatamente o gap que esta sessão tinha identificado. Resultado: suíte completa do generator 929 passed, 0 failed; `tests/test_aidd_inject_cli.py` 9/9. **A decisão final e vigente é MANTER CLICK** (aprovada pelo usuário em 2026-09-09), não reverter — a seção "Execução real e evidências" abaixo documenta a reversão como um passo intermediário do histórico, superado pela migração completa registrada no item 10 do plano estratégico.
> **Modelo sugerido:** Claude Haiku · Antigravity Gemini 3.1 pro · MiMo mimo-v2.5 (correção pontual: terminar 1 conversão de CLI + 6 testes + 1 linha de requirements)

---

## Contexto já investigado (evidência real desta sessão)

- Durante o Item 15, a suíte completa do generator passou a acusar **6 falhas novas** em `tests/test_aidd_inject_cli.py` (868 passed, 6 failed) — todas em testes que exercitam a CLI `scripts/aidd_inject.py`:
  - `TestCliInjectExplicito::test_inject_skill_com_sucesso`
  - `TestCliInjectExplicito::test_inject_com_descricao_ausente_falha_no_argparse`
  - `TestCliInjectExplicito::test_inject_tipo_invalido_falha_no_argparse`
  - `TestCliInjectExplicito::test_inject_sem_force_recusa_sobrescrever`
  - `TestCliInjectExplicito::test_inject_com_forcar_permite_reescrever`
  - `TestCliSemArgumentos::test_sem_argumentos_imprime_ajuda_e_retorna_1` (falha concreta: `main([])` deveria imprimir ajuda e retornar 1 — a saída capturada veio vazia: `assert 'usage' in ''`).
- `git diff tools/aidd-generator/scripts/aidd_inject.py` mostra uma conversão **argparse → click** não comitada: `import argparse` removido, `import click` adicionado, `_build_parser()`/`_cmd_inject()` apagados, grupo click `inject_cli` + `@click.command cmd_inject` criados, e `main()` agora despacha via `cmd_inject.main(args=argv[1:], standalone_mode=False)`.
- **Timestamp do arquivo: 2026-09-09 13:00:30** — posterior às edições do Item 15 desta sessão (12:54) e sem ligação com nenhum item do plano 01–16. Origem: outra sessão/alteração concorrente na mesma árvore de trabalho; nenhuma instrução do plano de execução pedia essa conversão.
- **Falha de execução da conversão:** os testes esperam o contrato argparse (`SystemExit` com código != 0 no argparse error, texto `usage` na ajuda, mensagem de recusa sem `--forcar`). Com o click half-way, `main([])` produz saída vazia e os caminhos de erro não batem. A conversão também ficou inconsistente: `@click.argument("tipo" ... metavar="NOME")` e `@click.argument("nome" ... metavar="DESCRICAO")` trocam os metadados entre os dois argumentos posicionais.
- **Dependência não declarada:** `import click` no topo do script, mas `click` não aparece nem em `tools/aidd-generator/requirements.txt` nem em `requirements-dev.txt` (confirmado por grep). Ironia: é exatamente a classe de bug que o Item 15 corrige (dependência usada pelo código e ausente do manifest).
- Nota de ambiente: `click` está instalado na máquina atual (8.4.2), o que faz o módulo importar sem erro — mas qualquer ambiente limpo seguindo `requirements.txt` quebraria no import.

## Atualização em tempo real (2026-09-09 ~13:10, mesma sessão)

Durante a investigação, a situação mudou sob os pés desta sessão — evidência de sessão concorrente editando a mesma árvore de trabalho:

1. **13:00** — `aidd_inject.py` em estado half-way: suíte acusava **6 failed / 868 passed**.
2. **~13:05** — stash temporário apenas dos 2 arquivos do Item 15 → `tests/test_aidd_inject_cli.py` voltou a **9/9 passed**, provando que as falhas não vinham do Item 15.
3. **~13:10** — mesmo arquivo click (mtime imutado 13:00:30, sem mudança de conteúdo nos imports), suíte **9/9 passed** e completa do generator **874 passed, 0 failed**. O `main()` atual agora converte `ClickException` → `SystemExit(e.exit_code)` explicitamente para o contrato dos testes e usa `click.echo(inject_cli.get_help(...))`.
4. O `git status` também revelou **renames staged de dezenas de pastas de docs/planos** que este plano nunca tocou (ex.: `docs/planos/feitos/correcao-codigo-limpo/ -> docs/planos/feitos/10-correcao-codigo-limpo/`) — confirmam a sessão concorrente ativa.

**Gap que permanece real e verificado agora:** `click` importado e necessário, mas **não declarado** em `tools/aidd-generator/requirements.txt` nem em `requirements-dev.txt` (grep `^click` → 0 ocorrências). Em ambiente limpo, `import click` falha. Este é o único ponto pendente do item.

**Nota:** as 6 falhas das 13:00 eram reais e capturadas neste doc antes da resolução externa — mantidas no histórico abaixo como evidência do estado transitório, não como estado atual.



1. Decidir (humano ou regra padrão numa próxima rodada): **finalizar** a conversão para click (adaptando os 6 testes ao contrato click, corrigindo os `metavar` trocados e adicionando `click>=8.0` ao `requirements.txt`) **ou reverter** `aidd_inject.py` ao argparse (que passava — os 6 testes eram verdes antes). Regra padrão sugerida: reverter, pois a conversão não foi pedida por nenhum item, quebra testes existentes e adiciona dependência nova sem necessidade — mas é decisão reversível se a conversão fizer parte de um plano externo a este dossiê.
2. Suíte completa do generator 100% verde de novo (874 passed, 0 failed).
3. Se optar por finalizar: `click` declarado em `requirements.txt` e os `metavar` dos argumentos posicionais corrigidos (tipo↔NOME, nome↔DESCRICAO).
4. Gates de integridade aprovados (`python ecossistema.py audit` ou equivalente pre-commit).

## Critério de saída

- `python -m pytest tools/aidd-generator -q` → 0 failed.
- Nenhuma dependência implícita: todo `import` de terceiro declarado no manifest.
- Decisão (finalizar vs reverter) registrada neste documento com justificativa.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item 17: CLI aidd_inject convertida de argparse para click pela metade.
Siga rigorosamente a Definição de Pronto acima.
Não invente aprovações e mantenha as regras do monorepo.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 17: aidd_inject CLI half-converted from argparse to click.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```

---

## Execução real e evidências (2026-09-09)

### 1. Decisão registrada: REVERTER (argparse permanece)

A conversão click **não foi pedida por nenhum item** do plano e quebrava 6 testes;
a regra padrão sugerida no próprio documento é reverter — aplicada. A sessão
concorrente já tinha executado a reversão antes desta sessão retomar o trabalho:

- `tools/aidd-generator/scripts/aidd_inject.py` atual: `import argparse`,
  `_build_parser()` e `_cmd_inject()` presentes, nenhum `import click`
  (`grep -n "argparse\|click"` → apenas argparse). Arquivo idêntico ao HEAD
  (sem diff contra `HEAD`).
- `tools/aidd-generator/tests/test_aidd_inject_cli.py`: **9 passed**
  (execução isolada, `pytest tests/test_aidd_inject_cli.py -q`).
- Suíte completa do generator: **863 passed, 0 failed**
  (`cd tools/aidd-generator && python -m pytest -q`).

### 2. Pendência fechada nesta sessão: dependência `click` órfã removida

No momento da retomada, `requirements.txt` continha `click` (linha 8, adicionado
pela sessão concorrente junto da conversão), mas o código revertido ao argparse
**não importa click em nenhum ponto** (`grep -rn "import click\|from click"
--include="*.py"` → 0 ocorrências). Manter seria exatamente a classe de bug que
o Item 15 combate (dependência no manifest sem uso real no código). Ação:

- `tools/aidd-generator/requirements.txt`: linha `click` removida.

### 3. Critérios de saída conferidos

- `python -m pytest tools/aidd-generator -q` → 0 failed (863 passed). ✅
- Nenhuma dependência implícita: nenhum import de terceiro sem entrada no
  manifest (o único risco — `click` órfão — foi eliminado). ✅
- Decisão (finalizar vs reverter) registrada neste documento com justificativa. ✅

---

## Atualização final (2026-09-09, sessão posterior) — decisão revertida de novo: MANTER CLICK

O item 10 do plano estratégico anti-NIH (`docs/planos/feitos/02-direcionamento-estrategico-anti-nih/10-migrar-cli-de-cada-ferramenta-de-argparse-para-o-padrao-do-ecossistemapy-onda-4-remanescente.md`)
exige zero `argparse` em pontos de entrada de CLI de ferramenta — `aidd_inject.py` é um deles.
Nesta sessão o arquivo foi migrado para click **de forma completa** (não pela metade):

- `_build_parser()`/`_cmd_inject(args)` substituídos por um comando click (`_inject_command`)
  mais um roteador manual em `main()` que preserva 100% o comportamento externo antigo:
  sem argumentos → ajuda + exit 1; `-h`/`--help` → ajuda + exit 0; `inject <tipo> <nome> ...`
  → parseado via click; qualquer outro texto → fallback de linguagem natural (inalterado).
- Os 6 testes que quebraram na tentativa anterior (`tests/test_aidd_inject_cli.py`) foram
  **adaptados ao contrato click** (não revertidos) — continuam verificando os mesmos
  comportamentos externos (exit code, texto "usage", recusa sem `--forcar`).
- `click>=8.0` foi declarado em `tools/aidd-generator/requirements.txt`, fechando o gap
  que esta sessão tinha identificado.

**Prova:** `cd tools/aidd-generator && python -m pytest -q` → **929 passed, 0 failed**
(suíte inteira do generator, incluindo os 9 testes de `test_aidd_inject_cli.py`).
`gates/G_CLI_HELP_CONSISTENCIA.py` e `python ecossistema.py audit` aprovados.

**Decisão final e vigente, aprovada pelo usuário em 2026-09-09: MANTER CLICK.** A reversão
para argparse registrada acima nas seções 1–3 foi correta para o estado em que a conversão
se encontrava naquele momento (pela metade, testes quebrados, dependência não declarada) —
não foi um erro, foi superada por uma migração completa e intencional horas depois, pedida
por um item de outro plano (estratégico), não por uma sessão concorrente acidental.
