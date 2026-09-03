# 02. Arquitetura e Análise Técnica do AIDD Master Enterprise

> **Framework:** AIDD Master Enterprise  
> **Padrão Arquitetural:** Monólito Modular com Clean Architecture e Fatias Verticais (Vertical Slice Architecture).

---

## 1. Visão Arquitetural Geral

O AIDD Master Enterprise foi projetado para eliminar o acoplamento desordenado dos monólitos tradicionais e a complexidade operacional excessiva dos microsserviços. 

Cada fatia vertical (`src/modules/<dominio>/`) é completamente autossuficiente, possuindo suas próprias entidades, regras de serviço, rotas HTTP e testes.

```
src/
├── core/                  # Shared Kernel & Governança do Framework
│   ├── database_adapter.py# Adaptador Poliglota (SQLite WAL / PostgreSQL / Supabase)
│   ├── events.py          # EventBus Pub/Sub com Envelope Padronizado e Tracing UUID
│   ├── result.py          # Result Monad (Result.ok / Result.fail)
│   ├── opentelemetry.py   # Distributed Tracing, Spans e Correlation ID
│   ├── metrics.py         # Histograma SLA (p50/p95/p99) e Dashboard Prometheus
│   ├── fleet_discovery.py # Auto-descoberta dinâmica de agentes e harnesses
│   ├── subagent_engine.py # Orquestrador de subagentes efêmeros com Context-Purge
│   ├── circuit_breaker.py # Proteção contra falhas em cascata
│   ├── outbox_worker.py   # Garantia transacional At-Least-Once
│   └── security.py        # Criptografia PBKDF2, JWT HS256 e RBAC
├── modules/               # Fatias Verticais de Negócio (Bounded Contexts)
│   ├── crm/
│   │   ├── models.py      # Entidades do domínio
│   │   ├── services.py    # Casos de uso e regras de negócio
│   │   └── routes.py      # Endpoints HTTP documentados
│   └── erp/
└── shared/                # Componentes utilitários transversais e UI
```

---

## 2. Pilares Técnicos Fundamentais

### A. Linter AST de Bounded Context (Zero Acoplamento)
* Implementado em `scripts/gates/G_ARQUITETURA.py`.
* Inspeciona a Árvore Sintática Abstrata (AST) dos arquivos Python em `src/modules/`.
* **Regra Inegociável:** É expressamente proibido importar diretamente outro módulo (`import modules.erp` dentro de `modules.crm`).
* **Mecanismo de Comunicação:** Toda troca de informações entre fatias verticais é feita exclusivamente via **EventBus** assíncrono ou contratos do Shared Kernel.

### B. Persistência Poliglota & Multi-Tenant (`DatabaseAdapter`)
* Implementado em `src/core/database_adapter.py`.
* Suporte nativo e transparente com detecção automática pela `DATABASE_URL`:
  - `sqlite:///...`: SQLite local com modo WAL concorrente, pragmas de resiliência e `busy_timeout=5000`.
  - `postgresql://...`: PostgreSQL com pooling de conexões e tradução dinâmica de dialeto.
  - `supabase://...`: Supabase com conexão segura TLS/SSL e injeção de Row-Level Security (RLS).
* **Row-Level Security (RLS):** `RLSConnection` injeta automaticamente o `tenant_id` da sessão em todas as operações de banco, garantindo isolamento criptográfico e lógico de dados entre inquilinos.

### C. Observabilidade Distribuída (OpenTelemetry & Prometheus)
* Implementado em `src/core/opentelemetry.py` e `src/core/metrics.py`.
* **Tracing Ponta a Ponta:** Decorator `@trace_span(name)` injeta `trace_id` e `span_id` no contexto de execução e propaga em cada log estruturado JSON (`structlog`).
* **SLA/SLO Tracking:** Histograma de latência com buckets orientados a SLAs corporativos `[0.05, 0.1, 0.2, 0.5, 1.0, 2.0]` segundos.
* **Dashboard HTML Nativo:** Renderização de página Prometheus com badges visuais em tempo real alertando sobre quebra de SLO (`p99 > 200ms`).

### D. Result Monad Pattern (Zero Exceptions Não Tratadas)
* Todo método de negócio em `services.py` retorna a estrutura imutável `Result[T, E]`:
  ```python
  from core.result import Result

  def criar_cliente(dados: dict) -> Result[Cliente, str]:
      if not dados.get("email"):
          return Result.fail("Email é obrigatório")
      return Result.ok(novo_cliente)
  ```
* O fluxo principal nunca quebra por exceções silenciosas; falhas de domínio são valores de primeira classe tratados de forma explícita.
