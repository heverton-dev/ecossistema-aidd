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

