# AIDD-Planner: Motor Canônico de Planejamento e Combustão Primária da Tríade AIDD

O **`aidd-planner`** é a ferramenta que estabelece a ponte de transição entre as regras e governança suprema (`aidd-forge`) e os 3 Motores Especializados de Construção da Tríade Canônica:
- **Fluxo 01:** `aidd-pure` (Do Zero Puro / TDD Red-Green / VSA)
- **Fluxo 02:** `aidd-open` (Motores Open-Source / Gateway VSA)
- **Fluxo 03:** `aidd-freedom` (Desacoplamento Low-Code / PostgreSQL)

---

## 1. Princípios e Paradigmas

- **SDD (Spec-Driven Development):** Todo planejamento é governado por um contrato rígido em JSON Schema (`schemas/planner_schema.json`).
- **BDD (Behavior-Driven Development):** Regras de negócio e casos de aceite no formato canônico *Dado / Quando / Então*.
- **DDD (Domain-Driven Design):** Mapeamento de Bounded Contexts, Entidades de Domínio e Invariantes.
- **Quarteto *Sine Qua Non*:** Projeta obrigatoriamente `/swagger`, `/webhooks`, `/mcp` e `/docs`.
- **Zero Stubs:** Rejeição determinística de `TODO`, `FIXME` e valores indefinidos.

---

## 2. Uso via CLI

```powershell
# 1. Inicializar um novo PLANNER.json para o Fluxo 1 (Generator)
python ecossistema.py planner init --fluxo 1 --nome "Meu App" --pasta ./meu-app

# 2. Inicializar para o Fluxo 2 (Factory / Open-Source)
python ecossistema.py planner init --fluxo 2 --nome "Meu Hub" --pasta ./meu-hub

# 3. Inicializar para o Fluxo 3 (Bridge / Low-Code)
python ecossistema.py planner init --fluxo 3 --nome "Meu Portal" --pasta ./meu-portal

# 4. Validar conformidade de um PLANNER.json existente
python ecossistema.py planner validate ./meu-app/PLANNER.json

# 5. Exportar plano para formato de ferramenta downstream (ex: aidd-open)
python ecossistema.py planner export ./meu-hub/PLANNER.json --formato factory --saida ./meu-hub/plano_factory.json

# 6. Auditar com os Quality Gates
python ecossistema.py planner audit ./meu-app
```

---

## 3. Quality Gates

- `gates/G_PLANNER_SCHEMA.py`: Valida a integridade do JSON Schema e ausência de stubs.
- `gates/G_PLANNER_SINE_QUA_NON.py`: Audita a conformidade da Lei Inviolável 10 (Quarteto).
- `gates/G_PLANNER_COERENCIA_FLUXO.py`: Valida se os dados técnicos do fluxo escolhido estão completos.

---

## Fronteiras Canônicas e Responsabilidades

Conforme o mapa oficial de arquitetura (`MAPA-DONOS-FERRAMENTAS.json` e `G_FRONTEIRA_FERRAMENTAS.py`):

- **Responsabilidades:**
  - `desenho_planta_baixa_arquitetural`
  - `intake_sdd_bdd_e_especificacao`
  - `roteamento_tickets_para_ferramentas`
  - `calculo_dinamico_perfil_app`
- **Pode guardar peças do catálogo:** Não (`pode_guardar_pecas: false`).
- **Dono do conteúdo de:** `planta_arquitetura`, `tickets_roteados`, `perfil_app_dinamico`.
- **Pode conter:** `src/**`, `scripts/**`, `schemas/**`, `tests/**`, `templates/plano/**`.
- **Nunca conter (violações de fronteira):**
  - `**/Dockerfile*`
  - `**/docker-compose*`
  - `**/deploy.sh`
  - `**/nginx/**`
  - `**/mcp_server*`
  - `**/webhook*`
  - `**/openapi*`
  - `**/swagger*`
  - `**/G_*.py`
  - `**/*inject*`
- **Zona de escrita no projeto:** `PLANNER.json`, `HANDOFF_PLANNER_ENGINE.json`, `VSA_DISPATCH.json`, `DESIGN-SYSTEM.json`.
