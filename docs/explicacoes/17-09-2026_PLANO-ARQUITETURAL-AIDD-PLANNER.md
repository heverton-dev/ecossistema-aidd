# Plano Arquitetural e Especificação Técnica: `aidd-planner`

> **Status:** Aprovado para Implementação  
> **Papel no Ecossistema:** Motor Canônico de Planejamento, Intake e Combustão Primária (SDD/BDD)  
> **Localização:** `tools/aidd-planner/`  
> **Comando CLI:** `python ecossistema.py planner [init|validate|audit]`  

---

## 1. Visão Geral e Filosofia

O **`aidd-planner`** é o ponto de convergência de entrada entre a governança pura (`aidd-forge`) e os 3 Motores de Construção da Tríade Canônica (`aidd-generator`, `aidd-factory` e `aidd-bridge`).

Ele materializa o conceito de **AI-Driven Development (AI-DD)** integrando:
- **SDD (Spec-Driven Development):** Produz um contrato rigoroso `PLANNER.json` governado por JSON Schema.
- **BDD (Behavior-Driven Development):** Estrutura requisitos funcionais no formato *Dado / Quando / Então*.
- **DDD (Domain-Driven Design):** Mapeia Bounded Contexts, Entidades e Regras de Negócio invariantes.
- **Quarteto *Sine Qua Non*:** Projeta nativamente `/swagger`, `/webhooks`, `/mcp` e `/docs` em 100% dos módulos.

```
                   ┌───────────────────────────────────────────────┐
                   │        aidd-forge (Regras e Governança)       │
                   └───────────────────────┬───────────────────────┘
                                           ▼
                   ┌───────────────────────────────────────────────┐
                   │                 aidd-planner                  │
                   │    - Intake Socrático (LLM Probabilística)    │
                   │    - Compilação SDD / BDD / DDD               │
                   │    - Validação Binária (Quality Gates AST)    │
                   └───────┬───────────────┼───────────────┬───────┘
                           │               │               │
                           ▼               ▼               ▼
                      FLUXO 01         FLUXO 02         FLUXO 03
                    (Do Zero Puro)   (Open-Source)     (Low-Code)
                    aidd-generator    aidd-factory    aidd-bridge
```

---

## 2. O Equilíbrio Canônico: Probabilístico vs Determinístico

1. **Camada Probabilística (LLM / Raciocínio):**
   - Conduz o intake socrático interativo ou ingere documentos não estruturados (PRDs, briefings, ideias brutas).
   - Realiza pesquisa arquitetural, curadoria de tecnologias e formulação de regras de negócio.
   - Compila o raciocínio no documento formal `PLANNER.json`.

2. **Camada Determinística (Python / Quality Gates):**
   - Não aceita alucinações ou stubs vazios (`"TODO"`, `"a definir"`).
   - Audita o plano através de Quality Gates rígidos com código de saída binário (`exit 0` = aprovado, `exit 1` = bloqueio absoluto).

---

## 3. Schema Polimórfico do `PLANNER.json`

Todo plano possui um **Núcleo Comum Invariante** e uma **Seção Especializada** conforme o fluxo de destino:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "meta": {
    "projeto_nome": "string",
    "slug": "string",
    "versao": "1.0.0",
    "descricao": "string",
    "dominio": "string",
    "fluxo_alvo": "fluxo_01_generator | fluxo_02_factory | fluxo_03_bridge"
  },
  "ddd_bounded_contexts": [
    {
      "modulo": "string",
      "descricao": "string",
      "entidades": [
        {
          "nome": "string",
          "atributos": { "campo": "tipo" },
          "regras_invariantes": ["string"]
        }
      ]
    }
  ],
  "bdd_cenarios": [
    {
      "id": "SCN-001",
      "modulo": "string",
      "dado": "string",
      "quando": "string",
      "entao": "string"
    }
  ],
  "quarteto_sine_qua_non": {
    "swagger": { "ativo": true, "prefixo": "/swagger" },
    "webhooks": { "ativo": true, "eventos_suportados": ["string"] },
    "mcp": { "ativo": true, "ferramentas_expostas": ["string"] },
    "docs": { "ativo": true, "guia_usuario": true }
  },
  "infraestrutura_alvo": {
    "banco_dados": "postgresql | sqlite",
    "porta_api": 8000,
    "ambiente": "vps_docker"
  },
  "payload_especifico_fluxo": {
    "detalhes": "Varia conforme fluxo_alvo (ver seção 4)"
  }
}
```

---

## 4. O Payload Especializado por Fluxo

1. **Se `fluxo_01_generator`:**
   - Lista de Fatias VSA (`features/`).
   - Casos de Teste TDD previstos (cenários Red-Green).
   - Endpoints REST detalhados com payload de entrada/saída.
2. **Se `fluxo_02_factory`:**
   - Catálogo de ferramentas open-source curadas (ex: Evolution API, Redis, n8n).
   - Topologia de rede Docker (`aidd_internal`) e portas expostas.
   - Fatias VSA de integração e proxy reverso.
3. **Se `fluxo_03_bridge`:**
   - Diretório de código low-code importado (Lovable, v0, Bolt).
   - Mapeamento de tabelas/APIs mockadas para schema relacional PostgreSQL.
   - Telas e rotas de frontend desacopladas.

---

## 5. Quality Gates Dedicados do `aidd-planner`

| Gate | Tipo | O que valida |
|---|---|---|
| `G_PLANNER_SCHEMA.py` | AST / JSON Schema | Valida estritamente contra o JSON Schema. Rejeita stubs, arrays vazios e dados incompletos. |
| `G_PLANNER_SINE_QUA_NON.py` | Determinístico | Garante que o Quarteto (`/swagger`, `/webhooks`, `/mcp`, `/docs`) está mapeado em todos os contextos. |
| `G_PLANNER_COERENCIA_FLUXO.py` | Lógica de Negócio | Valida se os campos obrigatórios do fluxo escolhido estão 100% preenchidos e compatíveis com a ferramenta de destino. |

---

## 6. Próximos Passos de Execução

1. Criar a pasta canônica `tools/aidd-planner/` com sua estrutura modular.
2. Implementar os 3 Quality Gates determinísticos da ferramenta.
3. Criar a CLI de intake e compilação do `PLANNER.json`.
4. Integrar o comando `planner` na CLI principal `ecossistema.py`.
5. Criar a skill universal `aidd-planner-runner`.
6. Validar 100% dos testes unitários do `aidd-planner`.
