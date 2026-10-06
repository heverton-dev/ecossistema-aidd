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
| moldes | 24 |
| arquivos de molde | 367 |

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
| scripts | 50 |
| chamados pelo painel | 18 |
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

