# PLANO DE EVOLUÇÃO (Migração VSA - Monólito Modular)

## Ticket 1: Migração do Núcleo de Governança (aidd-forge)
*   **Ação:** Mover `tools/aidd-forge/` para `modulos/01-governanca-e-qualidade/core/aidd-forge/`.
*   **Proxy:** Criar um script proxy em `tools/aidd-forge/__init__.py` (se aplicável) e alias em `ecossistema.py` caso ele chame diretamente, garantindo que `python ecossistema.py forge` e importações legadas funcionem.
*   **Gate:** Passar nos testes unitários e `python ecossistema.py audit`.

## Ticket 2: Migração da Tríade de Motores (Pure, Open, Freedom)
*   **Ação:** Mover:
    *   `tools/aidd-pure/` ➔ `modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/`
    *   `tools/aidd-open/` ➔ `modulos/02-triade-motores/fluxo-02-open/core/aidd-open/`
    *   `tools/aidd-freedom/` ➔ `modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom/`
*   **Proxy:** Redirecionadores leves em `tools/` que emitem Warning e importam o novo caminho.
*   **Gate:** Passar em todos os testes e testes de engine (`aidd-pure`, etc).

## Ticket 3: Migração de Plataforma (Master, Enterprise, Ops)
*   **Ação:** Mover:
    *   `tools/aidd-master/` ➔ `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/`
    *   `tools/aidd-enterprise/` ➔ `modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/`
    *   `tools/aidd-ops/` ➔ `modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/`
*   **Proxy:** Redirecionadores em `tools/`.
*   **Gate:** Passar no gate de fatiamento (`validador_fatias_vsa.py`).

## Ticket 4: Distribuição dos Portões (Gates) e Skills
*   **Ação:** Mover scripts de `gates/` (ex: `G_PORTAO_PROVA_QUE_MORDE.py`) para os `gates/` específicos de cada domínio com base em qual núcleo o gate audita, e skills soltas para as pastas `skills/` locais de cada fatia.
*   **Proxy:** O runner de gates (`ecossistema.py audit` e `pre-commit`) precisa ser ajustado para varrer `modulos/**/gates/`.
*   **Gate:** O teste `python ecossistema.py audit` deve encontrar e executar exatamente os 69 gates, nem um a menos, reportando verde (exit 0).
