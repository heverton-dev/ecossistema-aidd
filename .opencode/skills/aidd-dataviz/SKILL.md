---
name: aidd-dataviz
description: Validates categorical and ordinal chart palettes with the deterministic OKLCH/OKLab script validate_palette.py (lightness band, chroma floor, CVD separation, normal-vision floor, WCAG contrast). Use when the user wants to check chart colors, "validate palette", "are these series colors accessible", "palette fails CVD", sequential ramp checks, or before shipping any dashboard/chart color set.
---

# aidd-dataviz

Design-system-agnostic palette validation. The color part of a chart is computable, so compute it — this skill never eyeballs hues.

## Script

`scripts/validate_palette.py` (Python 3, stdlib only, zero dependencies) computes the measurable checks from hex values alone:

1. **Lightness band** — OKLCH L inside the mode band (light `0.43–0.77`, dark `0.48–0.67`).
2. **Chroma floor** — OKLCH C ≥ 0.10 (below it a hue reads as gray).
3. **CVD separation** — OKLab ΔE×100 between slots under Machado-Oliveira-Fernandes severity-1.0 protan/deutan simulation; target 8.0, floor 6.0 (6–8 = WARN, needs secondary encoding).
4. **Normal-vision floor** — worst OKLab ΔE×100 ≥ 15.0 under unsimulated vision (hard gate).
5. **Contrast vs surface** — WCAG ratio ≥ 3:1 per mark (below = relief WARN, not a hard fail).

Checks 1 (fixed hue order) and 6 (values resolve to real ramp steps) are structural rules enforced by the surrounding skill, not measurable from hexes alone.

## Usage

```sh
# Categorical (bars/lines/stacks): adjacent pairs
python componentes/compartilhado/skills/aidd-dataviz/scripts/validate_palette.py \
  "#2a78d6,#eb6834,#1baf7a,#eda100,#e87ba4,#008300,#4a3aa7,#e34948" --mode light

# Scatter/bubble/maps: any two marks can sit side by side
python scripts/validate_palette.py "#256abf,#199e70,..." --mode dark --pairs all

# Ordered categories (funnel, tiers, buckets): one-hue ramp checks
python scripts/validate_palette.py "#123456,#2a78d6,#7fb2f0" --mode light --ordinal
```

| Flag | Meaning |
|---|---|
| `--mode light\|dark` | lightness band + default surface |
| `--surface #rrggbb` | chart surface for the WCAG contrast check |
| `--pairs adjacent\|all` | adjacent (default) or all-pairs CVD/normal-vision floor |
| `--ordinal` | validate a one-hue ramp instead of categorical checks |

## Exit codes

- `0` — all checks pass (WARN bands still exit 0; each WARN is legal only with mandatory secondary encoding: direct labels, gaps, or texture).
- `1` — at least one check hard-FAILs (off-band lightness, chroma below floor, CVD below 6.0, normal-vision below 15.0, ordinal violations).
- `2` — usage error (empty palette or malformed hex; never fails open).

## Determinism

Same input → byte-identical output. Thresholds and the CVD simulation matrices are part of the standard, not tunable flags: swapping the simulation model would require recalibrating the thresholds.

## Tests

`tests/test_dataviz_palette_validation.py` proves the gate bites: valid palettes exit 0, gray/out-of-band palettes exit 1, malformed hex exits 2, ordinal mode distinguishes ramps from categorical sets, and two identical runs produce identical output.

```sh
python -m pytest -q -p no:cacheprovider tests/test_dataviz_palette_validation.py
```
