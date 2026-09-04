---
name: aidd-master-pack-v4
version: 4.1.0
description: AIDD v5.1 — Enterprise Suite Engine com Fatias Verticais Isoladas, EventBus Cross-Domain, Webhooks HMAC, OpenAPI 3.1 Swagger Studio, MCP Nativo e Bateria de Quality Gates Rígidos Anti-Atalhos.
---

# 🌐 AIDD Master Pack v5.1 — Enterprise Modular Architecture

O **AIDD v5.1** é o framework definitivo de engenharia agêntica para construção de **Suítes Empresariais Cross-Project** e **Monólitos Modulares de Alta Performance**. Ele une múltiplos domínios de negócio com isolamento de Clean Architecture, comunicação assíncrona por eventos, conformidade de segurança OWASP, documentação interativa ao vivo, conectividade MCP para IAs e **Quality Gates Mecânicos Rígidos** que impedem qualquer atalho ou geração incompleta.

---

## 🏆 As 4 Regras de Ouro do AIDD v5.1

1. **Clean Architecture & Fatias Verticais Isoladas (`src/modules/<dominio>/`):** Cada domínio de negócio (`crm`, `erp`, `logistica`, `helpdesk`, `wms`, `membros`, `catalogo`) é estruturado como uma fatia vertical independente com `models.py`, `services.py`, `routes.py`, comunicando-se exclusivamente via `EventBus` pub/sub. Monólitos sem fatias verticais são bloqueados pelo gate `G_ESTRUTURA`.
2. **Full CRUD Diligente com 100% de Testes Unitários:** Toda entidade possui Create, Read, Update e Delete totalmente funcionais, persistidos no banco de dados SQLite WAL, com modais no front-end e suíte completa de testes unitários com pytest em `tests/unit/test_<modulo>.py`.
3. **Quad-Pillars da Sincronização:**
   - **Super-App Front-End Impeccable:** Header de linha única, scrollbars de 4px, zero emojis, ícones vetoriais SVG Lucide, sem diálogos nativos de SO.
   - **Swagger Studio & OpenAPI 3.1 Nativo (`/docs`):** Todas as rotas registradas com esquemas de entrada/saída via `RouteRegistry` dinâmico.
   - **Disparadores de Webhook em Tempo Real:** Disparo assíncrono com assinatura HMAC para cada evento de domínio.
   - **Servidor Nativo Universal MCP (`/mcp`):** Exposição de 100% das operações como ferramentas JSON-RPC 2.0 para Claude Desktop, Cursor e Antigravity.
4. **Governança por Gates Rígidos Determinísticos:** A entrega só é autorizada após aprovação com exit 0 de todos os gates:
   - `G_ESTRUTURA.py` (validação de fatias verticais e governança)
   - `G_QUALIDADE.py` (compilação sintática sem erros)
   - `G_TESTES.py` (execução obrigatória de testes com pytest)
   - `G_CONTRACTS.py` (validação de contratos OpenAPI e MCP)
   - `G_SEGREDOS.py` (scanner de entropia de Shannon anti-vazamento)
   - `G_HARNESS_COMPAT.py` (compatibilidade multi-harness nativa)

---

## 💬 Protocolo Conversacional de Criação (Zero Atrito para o Usuário)

Quando o usuário solicita a criação de uma aplicação em linguagem natural no chat:
1. **Fase 1.5 (Planejamento & Spec Gate):** O agente executa internamente `python scripts/aidd.py plan "<prompt>"` gerando `SPEC-ARQUITETURA.md` e `PLANO-EXECUCAO-ESTRUTURADO.json` (com status `PLANEJADO`).
2. **Apresentação ao Usuário:** O agente apresenta um resumo conciso da arquitetura (módulos, rotas, banco WAL, testes) e aguarda confirmação.
3. **Fase 2 (Processamento & Execução):** Ao receber a aprovação em linguagem natural (ex: *"Aprovado"*, *"Pode criar"*, *"OK"*), o agente executa `python scripts/aidd.py apply --dir <pasta>` em subprocesso e audita com `python scripts/aidd.py audit --report`.
4. **Entrega Final:** O agente informa a conclusão com os links dos 4 portais (`/`, `/docs`, `/mcp`, `/webhooks`).

---

## 🚀 Comandos Principais da CLI `aidd.py`

```bash
# 0. Diagnóstico e Bootstrap Automático (Pre-Flight, dependências e detecção de ambiente)
python scripts/aidd.py setup

# 1. Planejar e gerar especificação arquitetural (Fase 1.5)
python scripts/aidd.py plan "Crie um CRM e ERP de faturamento"

# 2. Executar plano aprovado (Fase 2)
python scripts/aidd.py apply --dir ./app_crm-erp-faturamento-suite

# 3. Compor diretamente em modo declarativo
python scripts/aidd.py compose <caminho_destino> <nome_suite> crm erp helpdesk logistica

# 4. Adicionar uma nova fatia vertical com Full CRUD, testes e eventos
python scripts/aidd.py add-module faturamento -d "Faturamento e Boletos"

# 5. Executar a Bateria Completa de Testes Unitários
python scripts/aidd.py test

# 6. Executar os Gates Determinísticos e gerar Relatório Factual Auditado
python scripts/aidd.py audit --report

# 7. Executar Benchmark Concorrente de Carga e Latência
python scripts/aidd.py bench -n 100

# 8. Executar Auto-Remediação de Módulos e Manifestos
python scripts/aidd.py heal

# 9. Iniciar o servidor da suíte unificada
python src/server.py
```
