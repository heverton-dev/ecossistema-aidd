# AIDD-Planner: Motor Canônico de Planejamento e Combustão Primária da Tríade AIDD

O **`aidd-planner`** é a ferramenta que estabelece a ponte de transição entre as regras e governança suprema (`aidd-forge`) e os 3 Motores Especializados de Construção da Tríade Canônica:
- **Fluxo 01:** `aidd-generator` (Do Zero Puro / TDD Red-Green / VSA)
- **Fluxo 02:** `aidd-factory` (Motores Open-Source / Gateway VSA)
- **Fluxo 03:** `aidd-bridge` (Desacoplamento Low-Code / PostgreSQL)

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

# 5. Exportar plano para formato de ferramenta downstream (ex: aidd-factory)
python ecossistema.py planner export ./meu-hub/PLANNER.json --formato factory --saida ./meu-hub/plano_factory.json

# 6. Auditar com os Quality Gates
python ecossistema.py planner audit ./meu-app
```

---

## 3. Quality Gates

- `gates/G_PLANNER_SCHEMA.py`: Valida a integridade do JSON Schema e ausência de stubs.
- `gates/G_PLANNER_SINE_QUA_NON.py`: Audita a conformidade da Lei Inviolável 10 (Quarteto).
- `gates/G_PLANNER_COERENCIA_FLUXO.py`: Valida se os dados técnicos do fluxo escolhido estão completos.
