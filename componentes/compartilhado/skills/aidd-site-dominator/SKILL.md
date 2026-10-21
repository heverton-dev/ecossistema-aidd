---
name: aidd-site-dominator
description: Reconstructs and optimizes websites via REA, Top-20 benchmark, Mobbin, SEO/GEO, Impeccable, and Docker. Use when rebuilding market-leading sites.
---

# AIDD Site Dominator — End-to-End Market-Leading Website Reconstruction Pipeline

> **Governance Standard:** Strict Determinism (Law #1), Binary Quality (Law #2), Structured Persistence (Law #3), Extreme Token Economy (Law #4), Zero Stubs (Law #5), Quarteto Sine Qua Non (Law #10), Golden Stack (Law #11), Gates Must Bite (Law #13).

## 1. Purpose & Parameters

Executes a 6-phase deterministic pipeline to reverse-engineer any target website, benchmark the Top 20 domestic and global industry leaders, and rebuild a category-defining production application optimized for human conversion, search engines (SEO), and AI agents (GEO/AEO/MCP).

Required inputs:
- `--url`: Target website URL or local artifact/HAR path.
- `--sector`: Industry vertical (e.g., `"dental implants"`, `"fintech"`, `"industrial automation"`).
- `--market`: Primary and export markets (default: `"BR,LATAM,GLOBAL"`).

---

## 2. The 6-Phase Execution Protocol

### Phase 1 — Deep Reverse Engineering & Asset Mining (`Playwright` + `REA`)
1. Crawl all public routes of `--url` using `playwright` and capture full network traffic (`<target>/docs/reconstruct/01_evidence/network.har`) plus Retina 2x screenshots (`1440x900` desktop, `393x852` mobile).
2. Run REA (`npx -y rea-agents@6.4.0`) to deobfuscate web bundles, extract API schemas, and recover business logic into `<target>/docs/reconstruct/02_decompiled/`.
3. **301 SEO Authority Map:** Generate `<target>/docs/reconstruct/01_evidence/redirect_map_301.json` mapping every legacy URL to its new canonical route (`exit 0` required).
4. **Deep Catalog/PDF Mining:** Extract technical specifications, SKUs, and tables from legacy PDFs/manuals into structured JSON and SQLite WAL tables (`src/modules/`).

### Phase 2 — Dual Benchmarking (`Top 20 Sector Leaders` + `Mobbin MCP`)
1. **Sector Benchmark (Top 20 Domestic + Global):** Audit 10 domestic and 10 global market leaders in `--sector`. Persist findings in `<target>/docs/benchmark/MATRIZ_TOP20_SETOR.md` covering value propositions, interactive tools, SEO keywords, trust signals, and conversion flows.
2. **Anatomical UX Benchmark (`mobbin-mcp`):** Query Mobbin for best-in-class filtering, parametric search, comparison tables, and B2B/B2C checkout/quote anatomy. Persist in `<target>/docs/benchmark/mobbin_references.json`.

### Phase 3 — Domain Architecture, Multi-Market `hreflang` & Dual Findability (`SEO + GEO`)
1. Decompose domain into Vertical Slices (`src/modules/<slice>/`) with `/aidd-spec` and `/aidd-tickets`.
2. **Search Engine Optimization (SEO):** Generate dynamic `/sitemap.xml`, `/robots.txt` (explicitly allowing `GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended`), canonical tags, OpenGraph, and `hreflang` (`pt-BR`, `en`, `es`).
3. **Generative Engine Optimization (GEO / AI-Agent Ready):**
   - Serve `/llms.txt` (executive index) and `/llms-full.txt` (complete structured technical catalog and clinical/engineering specs).
   - Inject deterministic `Schema.org` JSON-LD (`Organization`, `Product`, `FAQPage`, plus sector-specific types such as `MedicalBusiness` / `MedicalDevice`).
   - Expose full catalog and compatibility tools via the native **MCP Server (`/mcp`)** and **OpenAPI 3.1 (`/docs`)**.

### Phase 4 — Unique Craft & Interactive Sector Tooling (`Impeccable` + `aidd-uiux`)
1. Define brand-exclusive `oklch(...)` tokens in `DESIGN.md` and `tokens.css` (WCAG AAA contrast, `tabular-nums` for technical metrics/SKUs, zero hardcoded colors).
2. **Replace Static PDFs with Interactive Tooling:** Build an interactive parametric selector/configurator allowing users to filter and compare products in <= 2 clicks.
3. **B2B/B2C Revenue Engine:** Attach a fast quote cart (*Carrinho de Cotacao Rapida*) to every technical item, routing leads via WhatsApp/CRM and triggering events on `/webhooks` (Webhook Studio).
4. Validate runtime DOM and visual hierarchy with `chrome-devtools-mcp` / `playwright` (`take_screenshot`, `list_console_messages`).

### Phase 5 — Golden-Stack Full-Stack Implementation (`/aidd-tdd`)
1. Implement Backend in pure Python + SQLite WAL (`src/server.py`, `src/core/`, `src/modules/`) exposing the dynamic **Quarteto Sine Qua Non** (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`).
2. Implement Frontend in `frontend/` using **TanStack Start / TanStack Router + React + TypeScript + Tailwind CSS** (Law #11).
3. Enforce Red-Green-Refactor TDD (`pytest -q` 100% green, zero stubs/mocks).

### Phase 6 — Production Packaging & Binary Quality Gates (`aidd-ops` + `aidd-homologue`)
1. Generate multi-stage `Dockerfile`, `docker-compose.yml`, and `nginx/nginx.conf` (including `redirect_map_301.json` rules, Brotli/Gzip, and OWASP security headers).
2. Run all repository Quality Gates, including `modulos/02-triade-motores/fluxo-01-pure/gates/G_STACK_PADRAO_OURO.py` and `modulos/03-plataforma-e-entrega/gates/G_QUARTETO_SINE_QUA_NON.py`.

---

## Negative Guardrails

- NEVER use Next.js or proprietary lock-in runtimes (violates Law #11).
- NEVER hardcode `#hex`, `rgb()`, or `hsl()` colors outside `DESIGN.md` / `tokens.css` or use Unicode emojis in UI components.
- NEVER drop legacy indexed URLs without an entry in `redirect_map_301.json`.
- NEVER leave PDF catalogs unindexed when structured product attributes can be extracted into SQLite WAL and `/llms-full.txt`.
- NEVER commit stubs (`pass`, `TODO`, fake returns) or claim SEO/GEO readiness without automated test verification.

## Failure Modes & Fallback

- **Target URL blocks headless crawler (WAF/403):** Switch to passive HAR ingestion (`<target>/docs/reconstruct/01_evidence/network.har`) or cached sitemap/Wayback inspection; never loop indefinitely on blocked requests.
- **Mobbin MCP unavailable:** Fall back to deterministic extraction of UI patterns from the Top 20 sector benchmark using `playwright` viewport snapshots.
- **Gate failure during Phase 6:** Abort commit immediately, inspect the failing gate output, fix the root cause in the slice/template, and re-run the full gate battery until exit 0.

## Stopping Checklist

- [ ] `<target>/docs/reconstruct/DOSSIE_REVERSA.md` and `redirect_map_301.json` generated and verified.
- [ ] `<target>/docs/benchmark/MATRIZ_TOP20_SETOR.md` completed with 20 sector leaders (domestic + global).
- [ ] `/llms.txt`, `/llms-full.txt`, `/sitemap.xml`, `/robots.txt`, and `Schema.org` JSON-LD active and validated (exit 0).
- [ ] Quarteto Sine Qua Non (`/docs`, `/webhooks`, `/mcp`, `/docs/guia`) responding HTTP 200.
- [ ] Interactive product selector and B2B quote cart functional in `frontend/` (TanStack + TS + Tailwind) with `DESIGN.md` in `oklch`.
- [ ] `Dockerfile`, `docker-compose.yml`, and `nginx/nginx.conf` present and all Quality Gates passing with `exit 0`.
