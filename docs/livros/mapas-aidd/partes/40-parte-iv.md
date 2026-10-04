# PARTE IV — A OFICINA

Onde a fábrica é consertada: os planos, os ciclos de auditoria e a lente que os inspeciona.

# Capítulo 11 — Mapa da oficina

```{=typst}
#ficha(
  ("Mapa", "mapa-11-oficina.html"),
  ("Para que serve", "todos os planos e ciclos de auditoria, com as fases cumpridas"),
  ("Achados em aberto", "2"),
)
```

## 11.1 O que é

A Tríade é a fábrica; a oficina é onde a fábrica é consertada. Ela tem duas trilhas: os planos (`/melhoria`, `/plan`, `/orchestrate`) e os ciclos de auditoria em quatro fases (4F).

Onde mora: `docs/planos/` e `docs/auditoria/`. Quem confere: o `scripts/atualizar_index_planos.py` e o guarda G_auditoria_15D de cada ferramenta auditada (docs/auditoria/<ferramenta>/).

## 11.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| planos | 37 |
| em execução | 11 |
| ciclos de auditoria | 24 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_oficina`), os mesmos do mapa `mapa-11-oficina.html`.

## 11.3 O que falta consertar

- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-skills/ciclo-02 (`CAT-ciclo-aidd-skills-ciclo-02`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: fronteiras-ferramentas/ciclo-01 (`CAT-ciclo-fronteiras-ferramentas-ciclo-01`).

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
  ("Achados em aberto", "0"),
)
```

## 12.1 O que é

A lente 15-D é a lista de 15 perguntas que o Inspetor faz a uma ferramenta num ciclo de auditoria, de contratos e gatilhos até a entrega final.

Onde mora: `docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md`. Quem confere: o Inspetor do ciclo 4F, com o guarda G_auditoria_15D de cada ferramenta.

## 12.2 Os números de hoje

| Medida | Valor |
| :-------------------------------------- | :-------------------------------------------- |
| dimensões | 15 |
| laudos lidos | 19 |
| marcações de falha | 7 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_lente_15d`), os mesmos do mapa `mapa-12-lente15d.html`.

## 12.3 O que falta consertar

Nenhum achado em aberto para este mapa.

O detalhe e a evidência de cada achado estão no Apêndice B e em `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`.

## 12.4 Rastreabilidade do capítulo

- `docs/mapas-visuais/mapa-12-lente15d.html`
- `docs/mapas-visuais/moldes/lente15d.html`
- `docs/auditoria/mapa-pecas/catalogo-pecas.json`
- `docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json`
- `scripts/catalogo_pecas.py`
- `scripts/mapa_visual.py`

