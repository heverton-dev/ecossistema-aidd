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
| guardas (nomes) | 98 |
| no ecossistema | 65 |
| rodam no commit | 64 |
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
| nomes de terceiros registrados | 20 |
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
| MCPs que o agente usa | 12 |
| MCPs dentro das ferramentas | 3 |
| hooks | 3 |

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

Onde mora: `gates/manifesto_harnesses.json`. Quem confere: o `components verify`, o `G_HARNESS_COMPAT` e o `G_UNIVERSAL_HARNESS`.

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

