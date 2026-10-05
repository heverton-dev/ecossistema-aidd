# PARTE IV — A OFICINA

Onde a fábrica é consertada: os planos, os ciclos de auditoria e a lente que os inspeciona.

# Capítulo 11 — Mapa da oficina

```{=typst}
#ficha(
  ("Mapa", "mapa-11-oficina.html"),
  ("Para que serve", "todos os planos e ciclos de auditoria, com as fases cumpridas"),
  ("Achados em aberto", "23"),
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
| ciclos de auditoria | 48 |

Os números saem de `docs/auditoria/mapa-pecas/catalogo-pecas.json` (função `coletar_oficina`), os mesmos do mapa `mapa-11-oficina.html`.

## 11.3 O que falta consertar

- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-componentes/ciclo-01 (`CAT-ciclo-aidd-componentes-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-dependencias/ciclo-01 (`CAT-ciclo-aidd-dependencias-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-dispatch-runner/ciclo-01 (`CAT-ciclo-aidd-dispatch-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-enterprise-runner/ciclo-01 (`CAT-ciclo-aidd-enterprise-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-forge-runner/ciclo-01 (`CAT-ciclo-aidd-forge-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-freedom-runner/ciclo-01 (`CAT-ciclo-aidd-freedom-runner-ciclo-01`).
- **Baixa** · Ciclo de auditoria sem todos os documentos: aidd-livro-texto/ciclo-01 (`CAT-ciclo-aidd-livro-texto-ciclo-01`).
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
| laudos lidos | 42 |
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

