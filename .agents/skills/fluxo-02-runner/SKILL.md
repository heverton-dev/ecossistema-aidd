---
name: fluxo-02-runner
description: Executa de ponta a ponta o Fluxo 02 (Motores Open-Source) da Tríade Canônica de forma estritamente síncrona.
---

# Fluxo 02 Runner — Motores Open-Source

Esta skill executa o pipeline industrial de curadoria, integração e fatiamento VSA a partir de engines open-source:
`[FORGE -> PLANNER] -> FACTORY -> [MASTER -> ENTERPRISE -> OPS]`

## Características Técnicas:
- **Fundação e Governança:** Injeção de governança agêntica e hooks via `aidd-forge`.
- **Planejamento BDD/SDD:** Definição de integrações e requisitos via `aidd-planner`.
- **Engine Open-Source:** Curadoria de engines testadas, compose multi-service e contratos OpenAPI via `aidd-factory`.
- **Harmonização VSA:** Acoplamento em Monólito Modular VSA + Next.js Padrão-Ouro via `aidd-master`.
- **Blindagem Criptográfica:** Auditoria SHA-256 de proxies e gateways via `aidd-enterprise`.
- **Infraestrutura:** Provisionamento de redes isoladas e compose nativo via `aidd-ops`.

## Como Usar
Via CLI Unificada:
```bash
python ecossistema.py run-fluxo --fluxo 2 --nome "ERP Clinicas" --slug erp-clinicas --dominio clinicas --pasta ./projetos/erp-clinicas
```
Para simulação sem escrita no disco:
```bash
python ecossistema.py run-fluxo --fluxo 2 --nome "ERP Clinicas" --slug erp-clinicas --dominio clinicas --pasta ./projetos/erp-clinicas --dry-run
```
