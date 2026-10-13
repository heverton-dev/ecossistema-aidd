# Skill `/impeccable` — Dissecação de Comandos e Pipelines

> **Fonte:** `.mimocode/skills/impeccable/SKILL.md` (v4.3.1)
> **Categoria:** Design de frontend (UI/UX, craft visual, design system)
> **Fora de escopo:** tarefas puramente backend / não-UI

---

## 1. Comandos de domínio (comando → para que serve)

| Comando | Categoria | Serve para | Reference |
|---|---|---|---|
| `init` | Build | Capturar contexto durável do produto em `PRODUCT.md` (alias: `teach`) | `reference/init.md` |
| `document` | Build | Gerar `DESIGN.md` (tokens/sistema visual) a partir do código existente | `reference/document.md` |
| `shape [feature]` | Build | Planejar UX/UI antes de escrever código (descoberta de tarefas) | `reference/shape.md` |
| `craft [feature]` | Build | Alias **obsoleto** de new-work comum — não acrescenta nada | `reference/craft.md` |
| `extract [target]` | Build | Extrair tokens/componentes reutilizáveis para o design system | `reference/extract.md` |
| `critique [target]` | Evaluate | Review de design UX com scoring heurístico | `reference/critique.md` |
| `audit [target]` | Evaluate | Checks técnicos: a11y, performance, responsivo | `reference/audit.md` · `audit.native.md` |
| `polish [target]` | Refine | Passe final de qualidade antes do ship | `reference/polish.md` |
| `bolder [target]` | Refine | Amplificar designs seguros/apagados | `reference/bolder.md` |
| `quieter [target]` | Refine | Reduzir designs agressivos/estimulantes demais | `reference/quieter.md` |
| `distill [target]` | Refine | Destilar à essência, remover complexidade | `reference/distill.md` |
| `harden [target]` | Refine | Pronto p/ produção: erros, i18n, edge cases | `reference/harden.md` |
| `onboard [target]` | Refine | Primeiro uso, empty states, ativação | `reference/onboard.md` |
| `animate [target]` | Enhance | Animações e motion com propósito | `reference/animate.md` |
| `colorize [target]` | Enhance | Cor estratégica em UIs monocromáticas | `reference/colorize.md` |
| `typeset [target]` | Enhance | Hierarquia tipográfica e fontes | `reference/typeset.md` |
| `layout [target]` | Enhance | Spacing, ritmo e hierarquia visual | `reference/layout.md` |
| `delight [target]` | Enhance | Personalidade e toques memoráveis | `reference/delight.md` |
| `overdrive [target]` | Enhance | Empurrar além dos limites convencionais | `reference/overdrive.md` |
| `clarify [target]` | Fix | UX copy, labels e mensagens de erro | `reference/clarify.md` |
| `adapt [target]` | Fix | Dispositivos e tamanhos de tela | `reference/adapt.md` · `adapt.native.md` |
| `optimize [target]` | Fix | Diagnosticar e corrigir performance de UI | `reference/optimize.md` |
| `live` | Iterate | Modo variante visual: escolher elementos no browser e gerar alternativas | `reference/live.md` |

---

## 2. Meta-comandos e utilitários

| Comando | Serve para |
|---|---|
| `/impeccable` (sem argumento) | Menu de roteamento context-aware — **nunca auto-executa** comando |
| `pin <comando>` / `unpin <comando>` | Criar/remover atalho standalone `/<comando>` |
| `hooks on\|off\|status\|ignore-rule\|ignore-file\|ignore-value\|reset` | Gerenciar o hook do detector de design (auto-ride após edits de UI) |
| `doctor` | Reportar e reparar drift entre artefatos do projeto e a versão atual da skill |
| `impeccable context` | Setup por sessão: carrega PRODUCT.md, DESIGN.md, surface brief e guias nativos |
| `impeccable signals` | JSON de sinais do projeto usado pelo menu de roteamento |
| `impeccable detect --json [alvos]` | Detector de design em arquivos locais (HTML/CSS; web-only) |
| `impeccable concept-seed --scope surface\|direction --mode <mode>` | Sorteio/direções criativas para nova superfície ou novo mundo visual |
| `impeccable surface-brief read\|write` | Ler/gravar o surface brief (contrato de direção) |
| `impeccable build-phase start\|advance\|scaffold\|record` | Máquina de estados do build comp-led (gates por fase) |
| `impeccable comp-spec` | Medir o comp: grid, regiões, crop, plate-prompt |
| `impeccable font-match --measure\|--rank` | Medir/ranking de fontes a partir dos pixels do comp |
| `impeccable comp-diff` | Diferença comp vs build (heatmap, crops pareados, report.json) |
| `impeccable embed-prompt` / `--scan` | Embedder de proveniência (prompt de geração/origem) em rasters |
| `impeccable generate-image` | Fallback de geração de imagem via API |
| `impeccable serve-question --schema` | Servir página de decisão (cards/wireframes) |

**Subagentes embarcados:** `impeccable-asset-producer` (produção de assets) · `impeccable-finish-reviewer` (review final) · `impeccable-documenter` (documentação/DESIGN.md).

---

## 3. Pipelines exclusivos

### 3.1 `/impeccable-full` (wrapper AIDD — maturidade completa)

```
init → document → critique → audit → polish → harden → extract
```

Disparo canônico em criação/alteração de telas e componentes de frontend (Lei #11 do ecossistema).

### 3.2 Superfície nova / redesign (`reference/new-work.md`)

```
init (se faltar PRODUCT.md)
  → decidir o que já é verdade (redesign | mundo estabelecido | brand incompleta | sem autoridade)
  → perguntas ao usuário (modo: Persuade | Operate | Read | Experience)
  → nível de invenção (extensão | superfície no mundo | novo mundo visual)
  → concept-seed (--scope direction|surface)
  → contrato de direção no surface brief (THESIS / OWN-WORLD / STORY / FIRST VIEWPORT / FORM / FINISH)
  → [comp-led: visualize → build-phase: comps → spec → plates → hero → sections → motion → responsive]
  → inspeção em lote (desktop + mobile; 2 rodadas no máximo)
  → finish-reviewer (disposition: recapture | rebuild | fix | ship)
  → documenter (DESIGN.md + .impeccable/design.json)
```

### 3.3 `shape` (planejamento sem execução)

```
shape → descoberta de tarefas → decisões de mundo visual/superfície → retorna direção → PARA
(não persiste, não implementa)
```

### 3.4 `live` (iteração visual)

```
live → seleção de elementos no browser → gera variantes → usuário escolhe
(web-only; proibido em ios / android / adaptive)
```

### 3.5 `doctor` (higiene de artefatos)

```
doctor → relatório de drift (PRODUCT.md, DESIGN.md, config, briefs, hook) → reparo sob demanda
```

---

## 4. Ordem correta de uso (ciclo completo)

1. **Setup** — `impeccable context` (automático por sessão; não rerodar)
2. **Fundação** — `init` → `document`
3. **Planejamento** — `shape` ou fluxo `new-work`
4. **Avaliação** — `critique` → `audit`
5. **Refino** (conforme diagnóstico) — `polish` · `bolder|quieter|distill` · `layout|typeset|colorize|animate|delight|overdrive` · `clarify|adapt|optimize|onboard`
6. **Blindagem** — `harden`
7. **Consolidação** — `extract`
8. **Iteração fina** — `live` · `doctor` quando houver drift · `hooks` para detecção contínua

---

## 5. Regras de roteamento

- **Sem argumento:** menu context-aware com 2–3 recomendações (via `signals` + `detect`); nunca auto-executar.
- **Pedido explícito/implied:** carrega a reference do comando (variante `.native` em plataformas nativas) e executa.
- **Pergunta de workflow:** só conselho, sem executar comandos.
- **Caso geral:** trabalho de design. Sem `PRODUCT.md` → `init` + `new-work`; refinamento estreito → segue o código incumbente.
- **Refinement preserva identidade; redesign substitui o mundo visual.** Nunca misturar os dois.
- **Modos:** Persuade (convencer/agir) · Operate (completar tarefa) · Read (entender) · Experience (estar dentro da obra).
- **Nativo (`ios`/`android`/`adaptive`):** `live` e `detect` são web-only — não usar.
