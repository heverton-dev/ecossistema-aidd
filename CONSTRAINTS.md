# CONSTRAINTS — Contrato Inviolável de Qualidade do Ecossistema AIDD

> **Referência Canônica:** Padrão-Ouro de 9 Camadas Base RevNault (`levantamento_stack_tecnologica_base_por_camada_revnault.md` / `docs/padroes/PADRAO-OURO-ARQUITETURA-CAMADAS-MERCADO.md`).
> **Aplicação:** Toda e qualquer aplicação gerada, scaffolded ou mantida pelo ecossistema (`aidd-pure`, `aidd-open`, `aidd-freedom`, `aidd-master`).

---

## 1. As 9 Camadas Base de Produção (Padrão Topo de Linha)

| # | Camada Arquitetural | Stack Obrigatória de Produção |
| :-: | :--- | :--- |
| **01** | **Frontend Core, Roteamento & Estado Assíncrono (SPA)** | `React 19`, `TypeScript 5.8 (Strict)`, `Vite 6`, `TanStack Query v5`, `TanStack Router + Hash Router`, `HTML5 Web APIs Nativas` |
| **02** | **Design System, Estilização & Primitivos de Interface** | `CSS Tokens (tokens.css)`, `Tailwind CSS 3.4/4`, `Radix UI Primitives (shadcn/ui)`, `CVA + clsx + tailwind-merge`, `Lucide React (SVG)` (Zero Emojis - Lei #14) |
| **03** | **Backend Core, Servidor ASGI & Contratos de API** | `Python 3.11/3.12/3.13`, `FastAPI`, `Uvicorn (ASGI)`, `Pydantic v2 (Rust)`, `HTTPX`, `Python-Multipart` |
| **04** | **Persistência Relacional, Busca Vetorial & Migrações** | `PostgreSQL 16` (OLTP + OLAP) + `pgvector (HNSW)`, `SQLite 3 (Modo WAL)`, `SQLAlchemy 2.0 Async`, `asyncpg`, `aiosqlite`, `Alembic` |
| **05** | **Mensageria Assíncrona & Cache Distribuído** | `Redis 7 (Redis Streams XGROUP/XREADGROUP/XACK + Cache TTL)`, `redis-py` |
| **06** | **Object Storage & Documentos Binários** | `Cloudflare R2 (S3-Compatible, Zero Egress Fees)`, `Boto3/Botocore (s3v4)`, `Compilador Nativo PDF (%PDF-1.4) & STL 3D` |
| **07** | **Segurança, Criptografia & Governança RBAC** | `Python Cryptography (AES-256-GCM / PBKDF2HMAC)`, `PyJWT (HS256)`, `Hashlib & HMAC (SHA-256)`, `Anti-SSRF Nativo`, `Motor RBAC DAG Dual` |
| **08** | **Infraestrutura, Containers & Gateway Edge** | `Docker & Docker Swarm / Compose`, `Traefik v3 (Edge Reverse Proxy & Let's Encrypt TLS)`, `Paramiko (SSH/SFTP)`, `python-dotenv & PyYAML` |
| **09** | **Qualidade, Testes & Quality Gates Determinísticos** | `Pytest + FastAPI TestClient`, `ESLint 9 + TypeScript Compiler (tsc --noEmit)`, `Quality Gates AIDD em Python (AST / Regex / Saída Binária)` |

---

## 2. Limiares de Qualidade e Proibições Estritas

1. **Zero Frameworks Monolíticos Engessados no Front:** Next.js está abolido do ecossistema per Lei #11.
2. **Zero Stubs / Zero Mocks de Produção:** Código gerado deve ser 100% tipado, compilável e executável (Lei #5).
3. **Zero Emojis na Interface e Documentação:** Apenas ícones vetoriais SVG (Lucide) com `stroke="currentColor"`. Emojis Unicode em UI são bloqueados pelo linter de design.
4. **Quarteto Sine Qua Non Dinâmico:** Todo projeto deve expor ativamente `/api` (OpenAPI Swagger), `/webhook` (Webhook Studio), `/mcp` (MCP Studio) e `/docs` (Guia do Utilizador).
5. **Tipagem Estrita Ponta a Ponta:** Todo endpoint exposto em FastAPI deve gerar/sincronizar contratos tipados para o frontend (`api_contracts.ts`), validado em pipeline.
6. **Integridade de Saída:** Todo comando e script de validação deve encerrar com `exit 0` limpo. Supressões manuais (`@ts-ignore`, skips) reprovam imediatamente.
