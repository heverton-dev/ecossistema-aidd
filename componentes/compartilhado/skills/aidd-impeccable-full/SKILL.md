---
name: aidd-impeccable-full
description: Orchestrates full Impeccable design lifecycle across UI/frontend surfaces. Mandatorily triggered whenever any frontend page, component, view or dashboard is created, generated, or scaffolded. Runs structured passes init -> document -> critique -> audit -> polish -> harden -> extract. Use when creating or refining frontend pages, or when user invokes "/impeccable-full", "impeccable-full", "design completo", "força máxima de UI", "craft frontend".
---

# aidd-impeccable-full

Executes the maximum-craft Impeccable design pipeline on UI and frontend surfaces.

## When to Run

- **Mandatory Trigger:** Any time a frontend page, screen, view, or component is created or scaffolded (via `/pure`, `/open`, `/freedom`, `/master`, or manual creation).
- **Manual Trigger:** `/impeccable-full [target-path]` or `/impeccable-full`.

## Pipeline Execution Order

```
[1. INIT] ➔ [2. DOCUMENT] ➔ [3. CRITIQUE] ➔ [4. AUDIT]
          ➔ [5. POLISH]   ➔ [6. HARDEN]   ➔ [7. EXTRACT]
```

### Phase 1: Context Capture (`init`)
1. Verify if `PRODUCT.md` exists in project root or current target.
2. If missing, execute `.claude/skills/impeccable/scripts/impeccable init` to capture product domain, persona, and core visual intent.
3. *Criterion:* `PRODUCT.md` exists and contains defined product and surface goals.

### Phase 2: Design Mapping (`document`)
1. Scan existing styles, CSS/Tailwind configs, and component primitives.
2. Run `/impeccable document` to materialize `DESIGN.md` (typography ramp, palette tokens, component rules).
3. *Criterion:* `DESIGN.md` exists with explicit tokens and design rules.

### Phase 3: UX Review (`critique`)
1. Target the specific created or modified frontend surface:
   `/impeccable critique <target-path>`
2. Extract heuristic score and list of P0/P1 issues.
3. *Criterion:* Critique assessment recorded; zero unhandled P0 issues.

### Phase 4: Technical Auditing (`audit`)
1. Run technical quality pass on the target:
   `/impeccable audit <target-path>`
2. Covers accessibility (contrast, ARIA, focus), responsiveness (mobile/desktop), and bundle/render performance.
3. *Criterion:* Zero critical contrast, viewport overflow, or accessibility failures.

### Phase 5: Refinement Pass (`polish`)
1. Consume actionable feedback from Phase 3 and Phase 4.
2. Run `/impeccable polish <target-path>` to fix visual rhythm, typography scale, padding, and alignment.
3. *Criterion:* Bounded fix pass applied directly to target source files.

### Phase 6: Production Hardening (`harden`)
1. Run `/impeccable harden <target-path>` on the surface.
2. Ensure full coverage for:
   - Loading states (skeletons / spinners)
   - Empty states (with clear CTA)
   - Error states and form validation feedback
   - Truncation / text overflow bounds
3. *Criterion:* All 4 edge-case states handled gracefully in source code.

### Phase 7: Design System Extraction (`extract`)
1. Run `/impeccable extract <target-path>` if new reusable primitives were introduced.
2. Consolidate reusable tokens and components into the shared design system.
3. *Criterion:* Clean, reusable tokens and components without inline duplication.

## Negative Guardrails

- NEVER skip this pipeline when creating, scaffolding, or generating any frontend page, layout, or screen.
- NEVER enter an open-ended loop: apply fixes in bounded batches (max 2 passes).
- NEVER use generic placeholders or low-contrast text without semantic purpose.
- NEVER compromise accessibility, mobile viewport responsiveness, or dark/light contrast.

## Failure Modes & Fallback

- **Launcher unavailable on platform:** Execute the atomic steps directly via local project files (`PRODUCT.md`, `DESIGN.md`, detector) following `reference/craft-floor.md`.
- **Target path not specified:** Default to the current modified frontend directory or prompt the user once for the target screen.

## Stopping Checklist

- [ ] `PRODUCT.md` and `DESIGN.md` exist and reflect current surface truth.
- [ ] Surface inspected for UX, responsive layout, and contrast.
- [ ] Loading, empty, and error states verified.
- [ ] Design detector hook reports clean or approved ignores.
