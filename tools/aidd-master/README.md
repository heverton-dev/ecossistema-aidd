# 📦 AIDD Master (Enterprise Modular Framework)

> **O Framework Definitivo para Monólitos Modulares, Clean Architecture, Fatias Verticais e Governança Anti-Atalhos por Gates Rígidos.**

---

## 🏛️ Visão Geral

O **AIDD Master** eleva o ecossistema de desenvolvimento assistido por IA ao nível máximo de robustez, determinismo e alta performance. Ele resolve definitivamente falhas e alucinações de geração ao impor regras mecânicas inegociáveis:

- **Isolamento de Domínios (Vertical Slices):** Cada domínio de negócio reside em seu próprio pacote (`src/modules/<dominio>/`) com `models.py`, `services.py`, `routes.py`, testes `pytest` e componente UI.
- **Banco de Dados Poliglota & Resiliente:** Suporte nativo a SQLite em modo WAL concorrente, PostgreSQL e Supabase via `DatabaseAdapter` e isolamento multi-tenant por Row-Level Security (RLS).
- **Subagentes Efêmeros com Context-Purge:** Composição de módulos via subagentes isolados que consomem apenas suas fatias específicas (~1.200 tokens) e têm o contexto purgado imediatamente após o build.
- **Auto-Descoberta de Frota (ORCA ADE):** Detecção dinâmica de ferramentas de IA no host com fallback em cascata e roteamento por especialidade (Arquiteto, Backend, Database, Frontend).
- **Observabilidade Distribuída (OpenTelemetry):** Rastreamento ponta a ponta com `@trace_span`, histogramas de SLA (`p50`, `p95`, `p99`) e dashboard Prometheus nativo.
- **Swagger Studio OpenAPI 3.1 (`/docs`):** Registro dinâmico de contratos de API com testador interativo ao vivo.
- **Model Context Protocol (`/mcp`):** Servidor JSON-RPC 2.0 nativo pronto para integração com Claude, Cursor, Antigravity e OpenHands.
- **Design System Corporativo Impeccable:** CSS padronizado com variáveis `:root`, dark mode, cards studio e scrollbars sutis de 4px.
- **Suíte de 10 Gates Rígidos:** `G_ESTRUTURA`, `G_ARQUITETURA` (AST de Bounded Context), `G_QUALIDADE`, `G_TESTES`, `G_CONTRACTS`, `G_PERFORMANCE` (SLOs e OTel), `G_SEGREDOS`, `G_SEGURANCA` (OWASP e CVE pip-audit), `G_CHAOS` e `G_HARNESS_COMPAT`.

---

## 📂 Estrutura do Projeto

```
aidd-master/
├── scripts/
│   ├── aidd.py               # CLI unificada (setup, init, compose, compose-orca, test, audit, deploy)
│   ├── compose_suite.py      # Motor de Composição Enterprise Modular
│   ├── add_module.py         # Gerador atômico de Fatias Verticais
│   ├── provision_project.py  # Provisionador de projetos modulares
│   ├── run_all.py            # Orquestrador com Auto-Healing
│   ├── autofix.py            # Mecanismo de auto-correção automática
│   └── gates/                # Suíte de Quality Gates Rígidos
│       ├── G_ESTRUTURA.py
│       ├── G_ARQUITETURA.py
│       ├── G_QUALIDADE.py
│       ├── G_PERFORMANCE.py
│       ├── G_TESTES.py
│       ├── G_CONTRACTS.py
│       ├── G_SEGREDOS.py
│       ├── G_SEGURANCA.py
│       ├── G_CHAOS.py
│       └── G_HARNESS_COMPAT.py
├── src/                      # Código-fonte operacional do framework
│   ├── core/                 # Shared Kernel, Banco Poliglota, OTel, Métricas, Subagentes
│   ├── modules/              # Fatias verticais de negócio
│   └── shared/               # Componentes UI e utilitários de suporte
├── templates/
│   ├── core/                 # Shared Kernel, MCP Server, OpenAPI & UI Components
│   ├── gates/                # Templates dos Quality Gates
│   ├── rules/                # Regras determinísticas por camada (database, serviços, routes, frontend)
│   ├── agents/               # Papéis de subagentes (architect, backend, database, frontend)
│   └── static/               # Design System CSS corporativo
├── tests/                    # Suíte completa de testes unitários automatizados
├── .agent/                   # Suporte canônico para Antigravity e harnesses de IA
├── requirements.txt          # Dependências do framework
├── pytest.ini                # Configuração de execução do Pytest
├── LICENSE                   # Licença MIT
└── README.md
```

---

## 🚀 Como Iniciar

```bash
# 0. Diagnóstico e Inicialização Automática do Ambiente
python scripts/aidd.py setup

# 1. Composição Modular via Subagentes Efêmeros (Context-Purge)
python scripts/aidd.py compose-orca crm erp billing logistica

# 2. Executar toda a suíte de testes unitários
python -m pytest tests/

# 3. Executar o orquestrador com auto-healing de todos os Gates
python scripts/run_all.py

# 4. Executar Gates individuais de certificação
python scripts/gates/G_ARQUITETURA.py
python scripts/gates/G_PERFORMANCE.py
python scripts/gates/G_SEGURANCA.py

# 5. Iniciar a aplicação
python src/server.py
```
