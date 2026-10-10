---
title: "Mapas do Ecossistema AIDD"
subtitle: "As peças, onde moram e o que falta consertar"
author:
  - Ecossistema AIDD
date: "26/09/2026"
lang: pt-BR
institute: "Ecossistema AIDD · mapa de peças, ciclo 01"
eyebrow: "LIVRO DIDÁTICO"
tagline: |
  Os 15 mapas visuais do ecossistema, na ordem de leitura, com os números medidos e cada defeito encontrado.
toc: true
toc-depth: 2
abstract: |
  Este livro percorre o ecossistema do geral para o particular: primeiro as leis, as fábricas e a receita
  que as liga; depois as peças do dia a dia; por fim os moldes, as máquinas e a oficina onde tudo é consertado.
  Cada capítulo corresponde a um mapa visual, na mesma ordem dos arquivos em docs/mapas-visuais/.

  Nada aqui é estimado. Os números vêm do catálogo de peças e os defeitos vêm do arquivo de achados, que
  hoje registra 31 achados em aberto, 0 sob suspeita e 14 resolvidos.
---

# Como ler este livro

## A quem este livro se destina

A quem desenvolve no ecossistema e precisa saber onde cada peça mora antes de mexer, e a quem vai decidir
o que consertar primeiro. Quem só quer a lista de defeitos pode ir direto ao Apêndice B.

## A estrutura

| Parte | Capítulos |
| :-------------------------------------- | :-------------------------------------------- |
| Parte I — As regras e as fábricas | 01, 02, 03 |
| Parte II — As peças do dia a dia | 04, 05, 06, 07, 08 |
| Parte III — O que vai junto e as máquinas | 09, 10 |
| Parte IV — A oficina | 11, 12 |
| Parte V — Os caminhos, as áreas e a equipe | 13, 14, 15 |

Cada capítulo responde sempre às mesmas quatro perguntas: o que é, os números de hoje, o que falta consertar e
de onde vieram as afirmações. O índice dos mapas, com o estado de cada um, está em `docs/mapas-visuais/mapa-00-indice.html`.

## As convenções visuais

```{=typst}
#painel("Números medidos")[
  Todo número deste livro foi lido do catálogo de peças no dia da geração. Se o catálogo mudar, o livro é
  gerado de novo pelo scripts/livro_mapas.py; nenhum número é digitado à mão.
]
```

# PARTE I — AS REGRAS E AS FÁBRICAS

O nível macro: as leis que governam a casa, as fábricas que produzem e a receita que as liga.

# Capítulo 1 — Mapa das leis

```{=typst}
#ficha(
  ("Mapa", "mapa-01-leis.html"),
  ("Para que serve", "cada lei do AGENTS.md e o guarda que a prova, e onde a prova é fraca"),
  ("Achados em aberto", "2"),
)
```

## 1.1 O que é

Uma lei é uma regra do `AGENTS.md`. Sozinha, ela é um pedido; vira trava quando um guarda a prova. Cada lei declara, numa linha própria, o guarda que a prova.

Onde mora: `AGENTS.md`, seção 2. Quem confere: o meta-guarda `G_LEI_DECLARA_PORTAO` e o `G_PORTAO_PROVA_QUE_MORDE`.

## 1.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| leis | 14 |
| declarações de guarda | 71 |
| declarações que o meta-guarda não lê | 0 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_leis`), os mesmos do mapa `mapa-01-leis.html`.

## 1.3 O que falta consertar

- **Média** · 5 guardas declarados em lei que não rodam no commit (`CAT-declarados-fora-do-commit`).
- **Baixa** · 1 guardas da raiz que nenhuma lei declara (`CAT-guardas-sem-lei`).

Já resolvido:

- G_HANDOFF_MELHORIA reprova com o handoff-melhoria.json versionado (commit `ciclo-01`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 1.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-01-leis.html`
- `docs/mapas-visuais/moldes/leis.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 2 — Mapa das ferramentas

```{=typst}
#ficha(
  ("Mapa", "mapa-02-ferramentas.html"),
  ("Para que serve", "as ferramentas, seus comandos de CLI e as tarefas com mais de uma dona"),
  ("Achados em aberto", "0"),
)
```

## 2.1 O que é

Uma ferramenta é uma pequena fábrica especialista em `modulos/<fatia>/.../aidd-<nome>/`, chamada pelo painel `ecossistema.py`. Cada uma deveria fazer um trabalho só.

Onde mora: `tools/`. Quem confere: o `G_TESTES_REAIS` (pytest de cada ferramenta) e o `G_DISCIPLINA_TESTE_FERRAMENTA`.

## 2.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| ferramentas | 8 |
| comandos de CLI | 74 |
| verbos em mais de uma ferramenta | 0 |
| tarefas com várias donas | 0 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_ferramentas`), os mesmos do mapa `mapa-02-ferramentas.html`.

## 2.3 O que falta consertar

Nenhum achado em aberto para este mapa.

Já resolvido:

- forge audit: AGENTS.md genérico (G04) e forge init ainda cria .agent/ (commit `ciclo-01`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 2.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-02-ferramentas.html`
- `docs/mapas-visuais/moldes/ferramentas.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 3 — Mapa dos encaixes

```{=typst}
#ficha(
  ("Mapa", "mapa-03-encaixes.html"),
  ("Para que serve", "as etapas da Tríade, os contratos entre elas e onde cada fluxo quebra"),
  ("Achados em aberto", "0"),
)
```

## 3.1 O que é

Um encaixe é o formato combinado entre duas peças: a chamada que a receita da Tríade faz a cada ferramenta e o contrato JSON Schema que passa de uma etapa para a outra.

Onde mora: `scripts/orquestrador_sincrono.py` e `componentes/compartilhado/specs/`. Quem confere: o `G_ORQUESTRADOR_SINCRONO` e a conferência de chamadas do `scripts/catalogo_pecas.py`.

## 3.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| etapas na receita | 7 |
| chamadas conferidas | 13 |
| chamadas que quebram | 0 |
| etapas sem ferramenta | 0 |
| contratos | 9 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `verificar_encaixes`), os mesmos do mapa `mapa-03-encaixes.html`.

## 3.3 O que falta consertar

Nenhum achado em aberto para este mapa.

Já resolvido:

- A validação de contrato aprova quando não consegue conferir (commit `ciclo-01`).
- Etapa 7 grava CONFORME_100_POR_CENTO sem rodar guarda nenhum (commit `ciclo-01`).
- Etapa 3 do Fluxo 02 chama o factory sem o PLANO-INFRAESTRUTURA.json que ele exige (commit `ciclo-01`).
- O \-\-dry-run do orquestrador grava README-USUARIO.md no disco (commit `ciclo-01`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 3.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-03-encaixes.html`
- `docs/mapas-visuais/moldes/encaixes.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# PARTE II — AS PEÇAS DO DIA A DIA

O nível meso: quem confere, quem ensina, os botões, as conexões e para onde tudo é copiado.

# Capítulo 4 — Mapa dos guardas

```{=typst}
#ficha(
  ("Mapa", "mapa-04-guardas.html"),
  ("Para que serve", "todos os guardas, onde moram e quem prova que morde"),
  ("Achados em aberto", "1"),
)
```

## 4.1 O que é

Um guarda é um script sem LLM que confere uma coisa só e responde 0 (passa) ou 1 (para tudo). É o que transforma regra em trava.

Onde mora: `gates/` e `tools/<f>/gates/`. Quem confere: o próprio pre-commit e o `G_PORTAO_PROVA_QUE_MORDE`.

## 4.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| guardas (nomes) | 105 |
| no ecossistema | 72 |
| rodam no commit | 67 |
| com versões diferentes | 10 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_gates`), os mesmos do mapa `mapa-04-guardas.html`.

## 4.3 O que falta consertar

- **Média** · 10 guardas com o mesmo nome e código diferente (`CAT-gates-versoes`).

Já resolvido:

- Corrida entre testes no G_PORTAO_PROVA_QUE_MORDE (commit `ciclo-01`).
- O detect-secrets grava o caminho absoluto da máquina no .secrets.baseline (commit `ciclo-01`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 4.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-04-guardas.html`
- `docs/mapas-visuais/moldes/guardas.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 5 — Mapa das skills

```{=typst}
#ficha(
  ("Mapa", "mapa-05-skills.html"),
  ("Para que serve", "todas as skills nossas, os terceiros e como criar uma"),
  ("Achados em aberto", "0"),
)
```

## 5.1 O que é

Uma skill é um manual de tarefa: o agente lê o nome e a descrição de todas e abre o manual inteiro só quando a tarefa combina. A descrição é o gatilho.

Onde mora: `componentes/compartilhado/skills/`. Quem confere: o `G_SKILL_FORMATO`, o `G_SKILL_ROT` e o `G_IDIOMA_LEI_4`.

## 5.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| skills nossas | 44 |
| nomes de terceiros registrados | 15 |
| com "Use when" | 44 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_skills`), os mesmos do mapa `mapa-05-skills.html`.

## 5.3 O que falta consertar

Nenhum achado em aberto para este mapa.

Já resolvido:

- 6 testes falhando na aidd-orca, fora do pre-commit (commit `ciclo-01`).
- Skills repetidas, nomes misturados e terceiros copiados na fonte única (commit `9d66a5e`).
- 2 testes falhando na aidd-improvement, fora do pre-commit (commit `ciclo-01`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 5.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-05-skills.html`
- `docs/mapas-visuais/moldes/skills.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 6 — Mapa dos comandos slash

```{=typst}
#ficha(
  ("Mapa", "mapa-06-comandos.html"),
  ("Para que serve", "o que você digita e qual skill cada comando chama"),
  ("Achados em aberto", "0"),
)
```

## 6.1 O que é

Um comando slash é o botão que a pessoa aperta no chat (`/pure`, `/melhoria`). Ele não trabalha: só chama a skill certa.

Onde mora: `componentes/compartilhado/comandos/`. Quem confere: a conferência de skill por comando do `scripts/catalogo_pecas.py`.

## 6.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| comandos slash | 19 |
| apontam para skill que existe | 19 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_comandos_slash`), os mesmos do mapa `mapa-06-comandos.html`.

## 6.3 O que falta consertar

Nenhum achado em aberto para este mapa.

Já resolvido:

- Comandos /aidd-livro-texto e /planner sem skill válida (commit `2293e13`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 6.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-06-comandos.html`
- `docs/mapas-visuais/moldes/comandos.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 7 — Mapa das conexões

```{=typst}
#ficha(
  ("Mapa", "mapa-07-conexoes.html"),
  ("Para que serve", "os MCPs (telefones para fora) e os hooks (alarmes)"),
  ("Achados em aberto", "0"),
)
```

## 7.1 O que é

O MCP é um telefone para fora: dá ao agente uma ferramenta que mora em outro programa. O hook é um alarme que toca sozinho num momento combinado.

Onde mora: `.mcp.json` e `.claude/settings.json`. Quem confere: o `dependencia verify` para os MCPs de terceiros.

## 7.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| MCPs que o agente usa | 11 |
| MCPs dentro das ferramentas | 5 |
| hooks | 5 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_mcps`), os mesmos do mapa `mapa-07-conexoes.html`.

## 7.3 O que falta consertar

Nenhum achado em aberto para este mapa.

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 7.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-07-conexoes.html`
- `docs/mapas-visuais/moldes/conexoes.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 8 — Mapa dos harnesses

```{=typst}
#ficha(
  ("Mapa", "mapa-08-harnesses.html"),
  ("Para que serve", "para onde cada peça é copiada em cada programa de agente"),
  ("Achados em aberto", "0"),
)
```

## 8.1 O que é

Um harness é o programa onde o agente trabalha (Claude Code, OpenCode, Cursor e outros). Cada um lê as peças de uma pasta própria, gerada a partir de uma fonte única.

Onde mora: `modulos/04-nucleo-compartilhado/contracts/manifesto_harnesses.json`. Quem confere: o `components verify`, o `G_HARNESS_COMPAT` e o `G_UNIVERSAL_HARNESS`.

## 8.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| harnesses | 7 |
| pastas legadas versionadas | 0 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_harnesses`), os mesmos do mapa `mapa-08-harnesses.html`.

## 8.3 O que falta consertar

Nenhum achado em aberto para este mapa.

Já resolvido:

- O sync de componentes puxava skills dos harnesses de volta para a fonte (commit `416dcd1`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 8.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-08-harnesses.html`
- `docs/mapas-visuais/moldes/harnesses.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# PARTE III — O QUE VAI JUNTO E AS MÁQUINAS

O nível micro: os moldes que viajam com o app e os scripts que fazem o trabalho mecânico.

# Capítulo 9 — Mapa dos moldes de entrega

```{=typst}
#ficha(
  ("Mapa", "mapa-09-moldes.html"),
  ("Para que serve", "o que cada ferramenta entrega junto com o app gerado"),
  ("Achados em aberto", "0"),
)
```

## 9.1 O que é

Um molde é a forma de onde sai o app gerado. Ele mora dentro da ferramenta, em `templates/`, e vai junto com o que ela entrega ao cliente.

Onde mora: `tools/<f>/templates/`. Quem confere: os guardas de entrega gerados por `scripts/gerador_templates_gates.py`.

## 9.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| moldes | 21 |
| arquivos de molde | 355 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_moldes_entrega`), os mesmos do mapa `mapa-09-moldes.html`.

## 9.3 O que falta consertar

Nenhum achado em aberto para este mapa.

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 9.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-09-moldes.html`
- `docs/mapas-visuais/moldes/moldes.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 10 — Mapa dos scripts

```{=typst}
#ficha(
  ("Mapa", "mapa-10-scripts.html"),
  ("Para que serve", "cada script de scripts/, o que faz e quem o chama"),
  ("Achados em aberto", "1"),
)
```

## 10.1 O que é

Um script é uma máquina sem cérebro: faz um trabalho mecânico sem LLM. Os de `scripts/` servem o ecossistema inteiro.

Onde mora: `scripts/`. Quem confere: nenhum guarda específico; o mapa mede quem cita cada script.

## 10.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| scripts | 59 |
| chamados pelo painel | 22 |
| nenhum código chama | 5 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_scripts`), os mesmos do mapa `mapa-10-scripts.html`.

## 10.3 O que falta consertar

- **Baixa** · 5 scripts que nenhum código chama (`CAT-scripts-sem-chamador`).

Já resolvido:

- O .githooks/pre-commit pode falhar sem mensagem (commit `ciclo-01`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 10.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-10-scripts.html`
- `docs/mapas-visuais/moldes/scripts.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# PARTE IV — A OFICINA

Onde a fábrica é consertada: os planos, os ciclos de auditoria e a lente que os inspeciona.

# Capítulo 11 — Mapa da oficina

```{=typst}
#ficha(
  ("Mapa", "mapa-11-oficina.html"),
  ("Para que serve", "todos os planos e ciclos de auditoria, com as fases cumpridas"),
  ("Achados em aberto", "26"),
)
```

## 11.1 O que é

A Tríade é a fábrica; a oficina é onde a fábrica é consertada. Ela tem duas trilhas: os planos (`/melhoria`, `/plan`, `/orchestrate`) e os ciclos de auditoria em quatro fases (4F).

Onde mora: `docs/planos/` e `docs/auditoria/`. Quem confere: o `scripts/atualizar_index_planos.py` e o guarda G_auditoria_15D de cada ferramenta auditada (docs/auditoria/<ferramenta>/).

## 11.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| planos | 38 |
| em execução | 11 |
| ciclos de auditoria | 54 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_oficina`), os mesmos do mapa `mapa-11-oficina.html`.

## 11.3 O que falta consertar

- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-componentes/ciclo-01 (`CAT-ciclo-aidd-componentes-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-dependencias/ciclo-01 (`CAT-ciclo-aidd-dependencias-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-dispatch-runner/ciclo-01 (`CAT-ciclo-aidd-dispatch-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-enterprise-runner/ciclo-01 (`CAT-ciclo-aidd-enterprise-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-forge-runner/ciclo-01 (`CAT-ciclo-aidd-forge-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-freedom-runner/ciclo-01 (`CAT-ciclo-aidd-freedom-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-livro-texto/ciclo-01 (`CAT-ciclo-aidd-livro-texto-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-master/ciclo-01 (`CAT-ciclo-aidd-master-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-master/ciclo-02 (`CAT-ciclo-aidd-master-ciclo-02`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-master-runner/ciclo-01 (`CAT-ciclo-aidd-master-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-mcp/ciclo-01 (`CAT-ciclo-aidd-mcp-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-open-runner/ciclo-01 (`CAT-ciclo-aidd-open-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-ops-runner/ciclo-01 (`CAT-ciclo-aidd-ops-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-orca/ciclo-01 (`CAT-ciclo-aidd-orca-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-orchestrator-runner/ciclo-01 (`CAT-ciclo-aidd-orchestrator-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-pipeline-runner/ciclo-01 (`CAT-ciclo-aidd-pipeline-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-pure-runner/ciclo-01 (`CAT-ciclo-aidd-pure-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-session/ciclo-01 (`CAT-ciclo-aidd-session-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-skills/ciclo-02 (`CAT-ciclo-aidd-skills-ciclo-02`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: calibracao-pipeline/ciclo-01 (`CAT-ciclo-calibracao-pipeline-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: code-review-graph/ciclo-01 (`CAT-ciclo-code-review-graph-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: fluxo-01-runner/ciclo-01 (`CAT-ciclo-fluxo-01-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: fluxo-02-runner/ciclo-01 (`CAT-ciclo-fluxo-02-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: fluxo-03-runner/ciclo-01 (`CAT-ciclo-fluxo-03-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: fronteiras-ferramentas/ciclo-01 (`CAT-ciclo-fronteiras-ferramentas-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: quadro-kanban-pipelines/ciclo-01 (`CAT-ciclo-quadro-kanban-pipelines-ciclo-01`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 11.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-11-oficina.html`
- `docs/mapas-visuais/moldes/oficina.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 12 — Mapa da lente 15D

```{=typst}
#ficha(
  ("Mapa", "mapa-12-lente15d.html"),
  ("Para que serve", "as 15 dimensões de auditoria e como cada ferramenta se saiu"),
  ("Achados em aberto", "1"),
)
```

## 12.1 O que é

A lente 15-D é a lista de 15 perguntas que o Inspetor faz a uma ferramenta num ciclo de auditoria, de contratos e gatilhos até a entrega final.

Onde mora: `docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md`. Quem confere: o Inspetor do ciclo 4F, com o guarda G_auditoria_15D de cada ferramenta.

## 12.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| dimensões | 15 |
| laudos lidos | 46 |
| marcações de falha | 8 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_lente_15d`), os mesmos do mapa `mapa-12-lente15d.html`.

## 12.3 O que falta consertar

- **Média** · 1 dimensões 15-D com falha no laudo de aidd-orca (`CAT-15d-aidd-orca`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 12.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-12-lente15d.html`
- `docs/mapas-visuais/moldes/lente15d.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# PARTE V — OS CAMINHOS, AS ÁREAS E A EQUIPE

A visão de conjunto: as linhas de montagem de ponta a ponta, as áreas onde o código mora e os modelos de agente que viajam com o app.

# Capítulo 13 — Mapa dos pipelines

```{=typst}
#ficha(
  ("Mapa", "mapa-13-pipelines.html"),
  ("Para que serve", "os caminhos de ponta a ponta: a Tríade, a oficina e a auditoria, etapa por etapa"),
  ("Achados em aberto", "0"),
)
```

## 13.1 O que é

Um pipeline é a ordem fixa em que as peças trabalham: os fluxos da Tríade, a cadeia melhoria, plan e orchestrate e as skills que rodam um pipeline próprio (auditoria 4F, evolução, ingestão).

Onde mora: `scripts/orquestrador_sincrono.py` e `componentes/compartilhado/skills/`. Quem confere: o `G_ORQUESTRADOR_SINCRONO` para a Tríade e o `gate_fase` de cada fase nos pipelines de auditoria.

## 13.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| pipelines | 12 |
| fluxos da Tríade | 0 |
| sem etapas declaradas | 0 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_pipelines`), os mesmos do mapa `mapa-13-pipelines.html`.

## 13.3 O que falta consertar

Nenhum achado em aberto para este mapa.

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 13.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-13-pipelines.html`
- `docs/mapas-visuais/moldes/pipelines.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 14 — Mapa dos módulos VSA

```{=typst}
#ficha(
  ("Mapa", "mapa-14-modulos.html"),
  ("Para que serve", "as áreas de modulos/, as fatias de cada uma e as ferramentas que moram nelas"),
  ("Achados em aberto", "0"),
)
```

## 14.1 O que é

Um módulo VSA é uma área de `modulos/` dividida em fatias verticais; cada fatia abriga ferramentas, guardas ou contratos, e não importa o interior de outra fatia.

Onde mora: `modulos/`. Quem confere: o `G_MODULO_FRONTEIRA`, o `G_FRONTEIRA_FERRAMENTAS` e o `G_COPIA_UNICA_VSA`.

## 14.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| áreas em modulos/ | 4 |
| fatias | 11 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_modulos`), os mesmos do mapa `mapa-14-modulos.html`.

## 14.3 O que falta consertar

Nenhum achado em aberto para este mapa.

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 14.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-14-modulos.html`
- `docs/mapas-visuais/moldes/modulos.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Capítulo 15 — Mapa dos agentes

```{=typst}
#ficha(
  ("Mapa", "mapa-15-agentes.html"),
  ("Para que serve", "os modelos de agente que viajam com o app e as cópias idênticas entre ferramentas"),
  ("Achados em aberto", "0"),
)
```

## 15.1 O que é

Um modelo de agente é a ficha de função de um subagente que vai junto com o app gerado. Cópias idênticas em várias ferramentas são candidatas a fonte única.

Onde mora: `modulos/03-plataforma-e-entrega/**/templates/agents/`. Quem confere: nenhum guarda específico; o mapa compara as cópias por conteúdo.

## 15.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| modelos de agente | 9 |
| arquivos | 18 |
| com versões diferentes | 0 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_agentes`), os mesmos do mapa `mapa-15-agentes.html`.

## 15.3 O que falta consertar

Nenhum achado em aberto para este mapa.

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 15.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-15-agentes.html`
- `docs/mapas-visuais/moldes/agentes.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

# Apêndice A — Glossário

| Termo | Significado |
| :-------------------------------------- | :-------------------------------------------- |
| Guarda (gate) | script sem LLM que responde 0 (passa) ou 1 (para tudo) |
| Skill | manual de tarefa que o agente abre quando a descrição combina |
| Comando slash | botão do chat que chama uma skill |
| MCP | telefone para fora: ferramenta que mora em outro programa |
| Hook | alarme que toca sozinho num momento combinado |
| Harness | programa onde o agente trabalha |
| Contrato (schema) | formato combinado do que passa de uma etapa para outra |
| Tríade | a receita de 7 etapas que produz um app pelos Fluxos 01, 02 e 03 |
| Ciclo 4F | auditoria em quatro fases: Inspetor, Arquiteto, Construtor e Retorno |
| Lente 15-D | as 15 perguntas do Inspetor |

# Apêndice B — Estado honesto

Tabela consolidada de todos os achados dos mapas, gerada de `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`. Em aberto por gravidade: 0 alta, 3 média, 28 baixa. Cada achado em aberto traz no arquivo o texto pronto para abrir o fluxo de melhoria (`pedido_melhoria`).

## Em aberto (31)

| Achado | Gravidade · mapa |
| :-------------------------------------- | :-------------------------------------------- |
| 1 dimensões 15-D com falha no laudo de aidd-orca (`CAT-15d-aidd-orca`) | Média · lente15d |
| 5 guardas declarados em lei que não rodam no commit (`CAT-declarados-fora-do-commit`) | Média · leis |
| 10 guardas com o mesmo nome e código diferente (`CAT-gates-versoes`) | Média · guardas |
| Ciclo de auditoria sem todos os documentos: aidd-componentes/ciclo-01 (`CAT-ciclo-aidd-componentes-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-dependencias/ciclo-01 (`CAT-ciclo-aidd-dependencias-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-dispatch-runner/ciclo-01 (`CAT-ciclo-aidd-dispatch-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-enterprise-runner/ciclo-01 (`CAT-ciclo-aidd-enterprise-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-forge-runner/ciclo-01 (`CAT-ciclo-aidd-forge-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-freedom-runner/ciclo-01 (`CAT-ciclo-aidd-freedom-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-livro-texto/ciclo-01 (`CAT-ciclo-aidd-livro-texto-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-master/ciclo-01 (`CAT-ciclo-aidd-master-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-master/ciclo-02 (`CAT-ciclo-aidd-master-ciclo-02`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-master-runner/ciclo-01 (`CAT-ciclo-aidd-master-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-mcp/ciclo-01 (`CAT-ciclo-aidd-mcp-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-open-runner/ciclo-01 (`CAT-ciclo-aidd-open-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-ops-runner/ciclo-01 (`CAT-ciclo-aidd-ops-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-orca/ciclo-01 (`CAT-ciclo-aidd-orca-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-orchestrator-runner/ciclo-01 (`CAT-ciclo-aidd-orchestrator-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-pipeline-runner/ciclo-01 (`CAT-ciclo-aidd-pipeline-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-pure-runner/ciclo-01 (`CAT-ciclo-aidd-pure-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-session/ciclo-01 (`CAT-ciclo-aidd-session-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: aidd-skills/ciclo-02 (`CAT-ciclo-aidd-skills-ciclo-02`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: calibracao-pipeline/ciclo-01 (`CAT-ciclo-calibracao-pipeline-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: code-review-graph/ciclo-01 (`CAT-ciclo-code-review-graph-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: fluxo-01-runner/ciclo-01 (`CAT-ciclo-fluxo-01-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: fluxo-02-runner/ciclo-01 (`CAT-ciclo-fluxo-02-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: fluxo-03-runner/ciclo-01 (`CAT-ciclo-fluxo-03-runner-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: fronteiras-ferramentas/ciclo-01 (`CAT-ciclo-fronteiras-ferramentas-ciclo-01`) | Baixa · oficina |
| Ciclo de auditoria sem todos os documentos: quadro-kanban-pipelines/ciclo-01 (`CAT-ciclo-quadro-kanban-pipelines-ciclo-01`) | Baixa · oficina |
| 1 guardas da raiz que nenhuma lei declara (`CAT-guardas-sem-lei`) | Baixa · leis |
| 5 scripts que nenhum código chama (`CAT-scripts-sem-chamador`) | Baixa · scripts |

## Resolvidos (14)

| Achado | Gravidade · mapa |
| :-------------------------------------- | :-------------------------------------------- |
| A validação de contrato aprova quando não consegue conferir (`VER-001`) | Alta · encaixes |
| Etapa 7 grava CONFORME_100_POR_CENTO sem rodar guarda nenhum (`VER-002`) | Alta · encaixes |
| Etapa 3 do Fluxo 02 chama o factory sem o PLANO-INFRAESTRUTURA.json que ele exige (`VER-003`) | Alta · encaixes |
| Corrida entre testes no G_PORTAO_PROVA_QUE_MORDE (`VER-005`) | Alta · guardas |
| O sync de componentes puxava skills dos harnesses de volta para a fonte (`VER-013`) | Alta · harnesses |
| O \-\-dry-run do orquestrador grava README-USUARIO.md no disco (`VER-004`) | Média · encaixes |
| 6 testes falhando na aidd-orca, fora do pre-commit (`VER-006`) | Média · skills |
| G_HANDOFF_MELHORIA reprova com o handoff-melhoria.json versionado (`VER-008`) | Média · leis |
| O .githooks/pre-commit pode falhar sem mensagem (`VER-009`) | Média · scripts |
| Skills repetidas, nomes misturados e terceiros copiados na fonte única (`VER-012`) | Média · skills |
| Comandos /aidd-livro-texto e /planner sem skill válida (`VER-014`) | Média · comandos |
| 2 testes falhando na aidd-improvement, fora do pre-commit (`VER-007`) | Baixa · skills |
| forge audit: AGENTS.md genérico (G04) e forge init ainda cria .agent/ (`VER-010`) | Baixa · ferramentas |
| O detect-secrets grava o caminho absoluto da máquina no .secrets.baseline (`VER-011`) | Baixa · guardas |
