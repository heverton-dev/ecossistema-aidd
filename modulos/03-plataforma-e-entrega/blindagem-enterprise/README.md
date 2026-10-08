# Fatia — Blindagem Enterprise

Blindagem de projetos para missão crítica: injeta componentes canônicos com selo SHA-256 e impõe Clean Architecture por gates.

## Responsabilidades
- Injeção de componentes e skills com verificação de integridade (`aidd-enterprise`).
- Núcleo vendorizado em `src/core`, vigiado contra drift do núcleo compartilhado.
- Interface pública da fatia: `interface.py`.

Ferramenta: [`aidd-enterprise`](aidd-enterprise/README.md). Regras para agentes: [AGENTS.md](AGENTS.md).
