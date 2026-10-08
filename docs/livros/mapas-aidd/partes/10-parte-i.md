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

