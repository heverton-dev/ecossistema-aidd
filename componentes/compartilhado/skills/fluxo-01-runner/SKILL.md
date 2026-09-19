---
name: fluxo-01-runner
description: Executa de ponta a ponta o Fluxo 01 (Do Zero Puro) da Tríade Canônica de forma estritamente síncrona.
---

# Fluxo 01 Runner — Do Zero Puro

Esta skill executa o pipeline industrial completo para criação de software novo a partir do zero absoluto:
`[FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]`

## Características Técnicas:
- **Fundação e Governança:** Injeção de Git hooks e regras de isolamento via `aidd-forge`.
- **Planejamento BDD/SDD:** Mapeamento de entidades, critérios de aceite e Quarteto Sine Qua Non via `aidd-planner`.
- **Engine TDD (Do Zero):** Ciclo Red-Green estrito gerando Clean Architecture em Python via `aidd-generator`.
- **Harmonização VSA:** Empacotamento em Monólito Modular VSA + Next.js Padrão-Ouro via `aidd-master`.
- **Blindagem Criptográfica:** Injeção e auditoria SHA-256 com trava anti-drift via `aidd-enterprise`.
- **Infraestrutura:** Validação de Dockerfile, Nginx SSL e compose via `aidd-ops`.

## Como Usar
Via CLI Unificada:
```bash
python ecossistema.py run-fluxo --fluxo 1 --nome "Meu Sistema" --slug meu-sistema --dominio gestao --pasta ./projetos/meu-sistema
```
Para simulação sem escrita no disco:
```bash
python ecossistema.py run-fluxo --fluxo 1 --nome "Meu Sistema" --slug meu-sistema --dominio gestao --pasta ./projetos/meu-sistema --dry-run
```
