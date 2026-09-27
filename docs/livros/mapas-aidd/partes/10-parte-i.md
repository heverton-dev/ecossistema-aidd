# PARTE I — AS REGRAS E AS FÁBRICAS

O nível macro: as leis que governam a casa, as fábricas que produzem e a receita que as liga.

# Capítulo 1 — Mapa das leis

```{=typst}
#ficha(
  ("Mapa", "mapa-01-leis.html"),
  ("Para que serve", "cada lei do AGENTS.md e o guarda que a prova, e onde a prova é fraca"),
  ("Achados em aberto", "4"),
)
```

## 1.1 O que é

Uma lei é uma regra do `AGENTS.md`. Sozinha, ela é um pedido; vira trava quando um guarda a prova. Cada lei declara, numa linha própria, o guarda que a prova.

Onde mora: `AGENTS.md`, seção 2. Quem confere: o meta-guarda `G_LEI_DECLARA_PORTAO` e o `G_PORTAO_PROVA_QUE_MORDE`.

## 1.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| leis | 13 |
| declarações de guarda | 32 |
| declarações que o meta-guarda não lê | 10 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_leis`), os mesmos do mapa `mapa-01-leis.html`.

## 1.3 O que falta consertar

- **Média** · 10 declarações de lei que o meta-guarda não lê (`CAT-declaracoes-invisiveis`).
- **Média** · 7 guardas declarados em lei que não rodam no commit (`CAT-declarados-fora-do-commit`).
- **Média** · G_HANDOFF_MELHORIA reprova com o handoff-melhoria.json versionado (`VER-008`).
- **Baixa** · 22 guardas da raiz que nenhuma lei declara (`CAT-guardas-sem-lei`).

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
  ("Para que serve", "as 8 ferramentas, seus comandos de CLI e as tarefas com mais de uma dona"),
  ("Achados em aberto", "4"),
)
```

## 2.1 O que é

Uma ferramenta é uma pequena fábrica especialista em `tools/aidd-<nome>/`, chamada pelo painel `ecossistema.py`. Cada uma deveria fazer um trabalho só.

Onde mora: `tools/`. Quem confere: o `G_TESTES_REAIS` (pytest de cada ferramenta) e o `G_DISCIPLINA_TESTE_FERRAMENTA`.

## 2.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| ferramentas | 8 |
| comandos de CLI | 69 |
| verbos em mais de uma ferramenta | 20 |
| tarefas com várias donas | 10 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_ferramentas`), os mesmos do mapa `mapa-02-ferramentas.html`.

## 2.3 O que falta consertar

- **Alta** · 100 arquivos idênticos copiados entre ferramentas (`CAT-arquivos-identicos`).
- **Média** · 10 tarefas feitas por mais de uma ferramenta (`CAT-tarefas-varias-donas`).
- **Baixa** · 20 verbos de CLI em mais de uma ferramenta (`CAT-verbos-repetidos`).
- **Baixa** · forge audit: AGENTS.md genérico (G04) e forge init ainda cria .agent/ (`VER-010`).

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
  ("Achados em aberto", "10"),
)
```

## 3.1 O que é

Um encaixe é o formato combinado entre duas peças: a chamada que a receita da Tríade faz a cada ferramenta e o contrato JSON Schema que passa de uma etapa para a outra.

Onde mora: `scripts/orquestrador_sincrono.py` e `componentes/compartilhado/specs/`. Quem confere: o `G_ORQUESTRADOR_SINCRONO` e a conferência de chamadas do `scripts/catalogo_pecas.py`.

## 3.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| etapas na receita | 7 |
| chamadas conferidas | 9 |
| chamadas que quebram | 2 |
| etapas sem ferramenta | 2 |
| contratos | 8 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `verificar_encaixes`), os mesmos do mapa `mapa-03-encaixes.html`.

## 3.3 O que falta consertar

- **Alta** · Chamada da receita não encaixa: ecossistema.py bridge scan \-\-dir <var> (`CAT-encaixe-ecossistema-py-bridge-scan-dir-var`).
- **Alta** · Chamada da receita não encaixa: ecossistema.py factory curate \-\-dominio <var> \-\-output <var> (`CAT-encaixe-ecossistema-py-factory-curate-dominio-var-output-var`).
- **Alta** · Etapa da receita não chama ferramenta: etapa_06_ops (`CAT-etapa-sem-ferramenta-etapa-06-ops`).
- **Alta** · Etapa da receita não chama ferramenta: etapa_07_auditoria (`CAT-etapa-sem-ferramenta-etapa-07-auditoria`).
- **Alta** · A validação de contrato aprova quando não consegue conferir (`VER-001`).
- **Alta** · Etapa 7 grava CONFORME_100_POR_CENTO sem rodar guarda nenhum (`VER-002`).
- **Alta** · Etapa 3 do Fluxo 02 chama o factory sem o PLANO-INFRAESTRUTURA.json que ele exige (`VER-003`).
- **Média** · Etapa mexe por dentro de uma ferramenta: etapa_02_planner (`CAT-atalho-interno-etapa-02-planner`).
- **Média** · Etapa mexe por dentro de uma ferramenta: etapa_03_engine (`CAT-atalho-interno-etapa-03-engine`).
- **Média** · O \-\-dry-run do orquestrador grava README-USUARIO.md no disco (`VER-004`).

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 3.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-03-encaixes.html`
- `docs/mapas-visuais/moldes/encaixes.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

