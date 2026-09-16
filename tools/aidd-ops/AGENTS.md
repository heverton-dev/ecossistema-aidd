# AIDD Ops — Canonical Agent Directives & Infrastructure Rules

> **Tool:** `aidd-ops`  
> **Role:** Agentic Infrastructure Meta-Orchestrator for Self-Hosted VPS Stacks (Docker, Compose, PostgreSQL, Uptime Kuma, Traefik).  
> **Governance Standard:** Zero Stubs, Strict Determinism, Hadolint Best Practices, Idempotent Hardening.

---

## 1. Core Execution Constraints

- **Thinking constraint:** Think strictly in compact English. Focus on container security, OCI linting, network isolation, and idempotent state. Under 150 words.
- **Execution limit:** Resolve tasks in 3 to 5 discrete steps. Stop and request confirmation if more steps are required.
- **Output format:** Silent executor. Return code edits and 1-line execution status only. Do not dump raw compose manifests or logs in chat.
- **Bash rule:** Always pipe verbose commands to tail/grep. E.g., `docker compose config 2>&1 | tail -n 25`.
- **Editing rule:** Use exact search/replace block edits (`replace_file_content`).

---

## 2. Infrastructure Invariants & Quality Gates

1. **Deterministic Compose (G_INFRA_COMPOSE):** Compose manifests must be static, reproducible, and strictly structured under `templates/infra/`.
2. **OCI Best Practices (G_HADOLINT):** All Dockerfiles must pass Hadolint linting with zero high/critical violations (e.g. pinned base images, non-root users).
3. **Active Observability (Anti-NIH #14):** Uptime Kuma official templates only (`templates/infra/uptime-kuma/docker-compose.yml`). Zero fake/mock monitoring dashboards.
4. **Idempotent Hardening (Anti-NIH #15):** VPS configuration uses Ansible collection `devsec.hardening` via `ansible/playbooks/hardening.yml`. Zero ad-hoc shell scripts.
5. **Zero Stubs:** All infrastructure definitions and Python managers must be fully functional and tested.
6. **Engineering Skills Alignment:** Production incidents, container failures, or pipeline regressions must follow the `/aidd-diagnose` protocol (scientific triage & regression test) before applying hotfixes.

---

## 3. Command Dispatch

- `/ops [requirement]`: Orchestrates infrastructure sizing and provisioning via `python ecossistema.py ops [requirement]`.
- `python scripts/pipeline_ops.py monitor export|check`: Manages Uptime Kuma probes and healthchecks.
