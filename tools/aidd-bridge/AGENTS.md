# AIDD Bridge — Canonical Agent Directives & Packaging Rules

> **Tool:** `aidd-bridge`  
> **Role:** Low-Code (Lovable, v0, Bolt) Project Extractor, PostgreSQL Unifier & Self-Hosted VPS Packager (Motor do FLUXO 03).  
> **Governance Standard:** Zero Vendor Lock-In, Clean Architecture Slicing, Zero Stubs, Quarteto Sine Qua Non.

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. Focus on schema sanitization, PostgREST compatibility, auth hash migration, and atomic rollback. Under 150 words.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if more steps are required.
- **Output format:** Silent executor. Return code edits and 1-line execution status only. Do not duplicate SQL scripts or component trees in chat.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `pytest tests/ 2>&1 | tail -n 25`.
- **Editing rule:** Use exact search/replace block edits (`replace_file_content`).

---

## 2. Packaging Invariants & Operational Laws (FLUXO 03)

1. **Vendor Liberation:** Ingests React + Vite + Tailwind + Supabase projects and extracts pages, shadcn components, and migrations without proprietary lock-in.
2. **Data Bridge:** Sanitizes Supabase SQL scripts into pure PostgreSQL with PostgREST emulation, allowing frontend `@supabase/supabase-js` clients to run with zero refactoring.
3. **Multi-App Merger:** Merges multiple applications into cleanly segregated vertical slices (`src/modules/<app>/`) with unified routing.
4. **Real Auth Migration:** Preserves password hashes (`auth.users`) when migrating accounts to self-hosted environments. Preview by default; writes only with `--apply`.
5. **Atomic Teardown:** Complete cleanup of Docker Swarm stacks, volumes, and Cloudflare DNS records via `destroy` (confirmation required unless `--yes`).
6. **Quarteto Sine Qua Non Dinâmico:** Exporta nativamente `/swagger`, `/webhooks`, `/mcp` e `/docs` em `quarteto_sine_qua_non/` para harmonização no `aidd-master`.
7. **Quality Gates Dedicados:** Subordina-se a `G_BRIDGE_VENDOR_LOCKIN`, `G_BRIDGE_DOCKER_OCI`, `G_BRIDGE_POSTGRESQL` e `G_BRIDGE_VSA_COMPAT`.

---

## 3. Command Dispatch

- `/bridge [command]`: Dispatches bridge actions via `python ecossistema.py bridge [unpack|scan|convert-db|merge|pack|migrate-auth|destroy]`.
- `python ecossistema.py bridge unpack <projeto>`: Executa o pipeline determinístico completo do FLUXO 03 em 6 fases.

