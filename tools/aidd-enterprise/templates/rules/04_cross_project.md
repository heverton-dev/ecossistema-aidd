# 🌐 Cross-Project Enterprise Modular Architecture (AIDD v4)

O **AIDD v4** é o motor de Composição e Unificação Empresarial Cross-Project. Ele permite consolidar múltiplos domínios independentes (ex: CRM, ERP, Helpdesk, Logística, WMS, Catálogo, Membros) em um **Monólito Modular de Alta Performance** seguro, limpo e auditável.

---

## 🏛️ 1. Princípios de Engenharia de Clean Architecture & Clean Code

1. **Isolamento Estrito de Fatias Verticais (`Vertical Slices`):**
   - Cada domínio reside em seu próprio pacote independente (`src/modules/<dominio>/`), contendo suas próprias tabelas, regras de negócio, rotas e testes.
   - Nenhuma fatia vertical acessa tabelas ou regras internas de outra fatia diretamente via SQL ou imports cruzados acoplados.

2. **Comunicação Cross-Domain 100% Desacoplada via EventBus:**
   - A integração entre módulos é realizada **exclusivamente via eventos assíncronos**:
     - *Exemplo 1 (CRM ➔ ERP):* `lead_ganho` ➔ O ERP escuta e gera a Conta a Receber.
     - *Exemplo 2 (Entregas ➔ Financeiro):* `entrega_concluida` ➔ O Financeiro liquida a receita do frete.
     - *Exemplo 3 (Frotas ➔ Suporte):* `veiculo_manutencao` ➔ O Suporte abre automaticamente um incidente P1 no SLA.

3. **Webhook Configuration Studio & Disparadores em Tempo Real:**
   - Studio visual dedicado (`/webhooks`) para gerenciamento completo de assinantes externos, controle de retry inteligente, auditoria em tempo real de logs de entrega e simulador interativo de payloads.
   - Todo evento de domínio relevante (Criação, Atualização, Exclusão, Cross-Domain) notifica os assinantes externos com assinatura HMAC-SHA256 (`X-Webhook-Signature`, `X-Hub-Signature-256`) e payload JSON padronizado.

4. **Documentação Unificada OpenAPI 3.1 & Swagger Studio:**
   - O núcleo compõe dinamicamente todas as rotas e tags das fatias verticais em uma única interface Swagger Studio interativa (`/docs`).

5. **Servidor Nativo Universal MCP (Model Context Protocol):**
   - Todas as operações das fatias unificadas são exportadas como ferramentas JSON-RPC 2.0 (`/mcp` e `/api/mcp/rpc`), permitindo controle total por agentes de IA (Claude Desktop, Cursor, Antigravity).

6. **Impeccable Design System & Super-App UI:**
   - A interface unificada consolida as vistas dos módulos em abas fluidas (`App Switcher`), garantindo:
     - Header de linha única (`overflow-x: auto; scrollbar-width: none;`).
     - Scrollbars de 4px nas cores do design system.
     - Zero emojis com ícones vetoriais SVG Lucide.
     - Modais e feedback visual sem diálogos nativos do sistema operacional.

---

## 📐 2. Estrutura Canônica de um Projeto Cross-Project v4

```
enterprise-suite-v4/
├── src/
│   ├── core/                  # Shared Kernel Cross-Domain
│   │   ├── database.py        # SQLite Concorrente (WAL Mode, PRAGMA foreign_keys)
│   │   ├── events.py          # EventBus Central Pub/Sub Desacoplado
│   │   ├── openapi.py         # Swagger Studio OpenAPI 3.1 Dinâmico
│   │   ├── mcp_server.py      # Servidor Nativo JSON-RPC 2.0 MCP
│   │   ├── webhooks.py        # Dispatcher de Webhooks com Assinatura HMAC
│   │   └── security.py        # Headers OWASP e Sanitização
│   ├── modules/               # Fatias Verticais Isoladas
│   │   ├── crm/               # Pipeline de Vendas & Leads
│   │   ├── erp/               # Gestão Financeira & DRE
│   │   ├── logistica/         # Frotas, Entregas & WMS
│   │   ├── helpdesk/          # Chamados & Matriz de SLA
│   │   └── membros/           # Cursos & Assinaturas VIP
│   ├── shared/                # UI Components & Feedback Engine
│   │   └── ui/
│   │       ├── feedback.py    # Gerador de Toasts e Diálogos de Confirmação
│   │       └── feedback.js    # Motor de UI tátil
│   ├── static/                # Front-End Impeccable Super-App
│   │   ├── index.html         # Super-App Unificado
│   │   └── docs.html          # Guia Oficial de Documentação Técnica
│   └── server.py              # Entrypoint com Inicialização de Rotas e Eventos
├── suite.db                   # Banco de Dados WAL
└── README.md                  # Especificação Técnica
```
