# Item 2 — Factory-Blueprints (Refatoração Arquitetural VSA & Quarteto Sine Qua Non)

> **Escopo:** Refatoração estrutural da ferramenta `aidd-factory` para elevar sua maturidade de 8.5 para 9.8, eliminando o modelo de microsserviços desconectados e alinhando-a aos padrões canônicos do `aidd-master` e `aidd-enterprise`: Vertical Slice Architecture (VSA), Monólito Modular em Python assíncrono, Quarteto *Sine Qua Non* dinâmico (`/swagger`, `/webhooks`, `/mcp`, `/docs`), Repositórios tipados anti-SQL injection e Super-App UI offline-first (Impeccable Design).
> **Fora de Escopo:** Modificação do `PLANO-INFRAESTRUTURA.json` do `aidd-ops` (o contrato de entrada é imutável) e alteração das ferramentas de deploy VPS (`aidd-bridge`).
> **Status:** [EM EXECUCAO]
> **Nota Atual (0-10):** 8.5 — evidencia: `docs/melhorias/16-09-2026_melhoria-elevacao-maturidade-ferramentas.json` e homologação E2E CTT (Seção 6 de `docs/teste-end-to-end/relatorio-teste-end-to-end.md`).
> **Nota Alvo (0-10):** 9.8
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

1. **Homologação E2E no Projeto CTT:**
   - O `aidd-factory` executou e passou nos testes, mas gerou artefatos dissonantes do restante do ecossistema: um proxy FastAPI ralo, um frontend Next.js de prateleira sem modelos de domínio reais e um script bash cru sem camadas de persistência.
2. **Divergência com Leis Invioláveis:**
   - **Lei 10 (Quarteto *Sine Qua Non*):** O código gerado não continha o MCP Studio (`/mcp` com SSE/JSON-RPC) nem o Manual Dinâmico do Utilizador (`/docs` gerado via AST).
   - **Padrão VSA:** Ausência de fatias verticais (`src/<servico>/api.py`, `models.py`, `repositories.py`).
3. **Harmonia do Ecossistema:**
   - O `aidd-factory` deve atuar como o braço executor de aplicação que consome o dimensionamento do `aidd-ops` e materializa a arquitetura de alta densidade do `aidd-master` e `aidd-enterprise`.

---

## Definicao de Pronto (DoD)

1. **Arquitetura Vertical Slice (VSA) por Módulo/Serviço:**
   - O gerador de aplicação deve produzir uma estrutura monolítica modular limpa: para cada ferramenta/serviço do plano, criar a fatia `src/<servico_slug>/` com:
     - `api.py`: endpoints tipados (`FastAPI APIRouter`).
     - `models.py`: esquemas Pydantic e DTOs de entrada/saída.
     - `repositories.py`: repositório tipado isolado com queries parametrizadas (anti-SQL injection).
2. **Servidor Monolítico Modular Canônico (`src/server.py`):**
   - Substituir o gateway genérico por um `src/server.py` que registre dinamicamente os roteadores de todas as fatias verticais, com autenticação JWT (opcional/configurável), CORS blindado e healthcheck global `/healthz`.
3. **Quarteto *Sine Qua Non* Dinâmico (Lei Inviolável 10):**
   - Implementar nativamente os 4 estúdios obrigatórios servidos diretamente pela aplicação gerada:
     - `/swagger`: Swagger Studio com OpenAPI 3.1.0 interativo.
     - `/webhooks`: Webhook Studio com simulador e catálogo de eventos.
     - `/mcp`: MCP Studio com servidor MCP SSE/JSON-RPC real expondo as tools de cada fatia para agentes de IA.
     - `/docs`: Guia/Documentação do Utilizador Comum com layout responsivo e mapa dinâmico de rotas.
4. **Super-App Frontend (Impeccable UI):**
   - Atualizar a geração do frontend para entregar uma interface Super-App coesa (`src/static/index.html` ou scaffold Next.js com páginas de domínio completas):
     - Navegação por abas dinâmicas para cada módulo da stack.
     - Telas operacionais conectadas aos endpoints reais com tabelas, modais e feedback de erro/sucesso.
     - Conformidade com o design system sem caracteres quebrados ou dependências externas pesadas.
5. **Quality Gates da Factory Hardened (`tools/aidd-factory/gates/`):**
   - Atualizar `G_FACTORY_INTEGRATION.py` e `G_FACTORY_ANALYSIS.py` para validar a presença das Fatias Verticais e das 4 rotas do Quarteto *Sine Qua Non*.
   - Garantir 100% de aprovação em todos os gates mecânicos da fábrica.
6. **Zero Stubs e Testes Unitários Reais:**
   - Suíte `tools/aidd-factory/tests` com testes unitários e de integração validando a nova arquitetura gerada, garantindo 100% PASS.

---

## Criterio de Saida

- Templates Jinja2 em `tools/aidd-factory/templates/` refatorados para o padrão VSA e Quarteto *Sine Qua Non*.
- Scripts geradores em `tools/aidd-factory/src/core/` atualizados para orquestrar as fatias e os 4 pilares dinâmicos.
- Suíte `pytest tools/aidd-factory/tests` passando com 100% de sucesso.
- Meta-Quality Gate `python ecossistema.py audit` retornando exit code 0.
- Execução limpa de validação demonstrando a geração da aplicação completa em conformidade.

---

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item 2: Factory-Blueprints (Refatoração Arquitetural VSA & Quarteto Sine Qua Non) do PLAN-0034.
Siga rigorosamente a Definição de Pronto acima:
1. Refatore os geradores e templates de aidd-factory para produzir Vertical Slice Architecture (fatias por serviço com api, models, repositories).
2. Assegure a inclusão nativa do Quarteto Sine Qua Non Dinâmico (/swagger, /webhooks, /mcp, /docs) no servidor gerado.
3. Entregue frontend Super-App alinhado ao Impeccable Design e repositórios tipados seguros.
4. Atualize os Quality Gates da ferramenta e garanta aprovação total de pytest e ecossistema audit.
Não invente aprovações e mantenha as regras do monorepo e token economy.
```

---

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: Factory-Blueprints (VSA & Sine Qua Non Quartet Architectural Refactoring) of PLAN-0034.
Strictly follow the Definition of Done above:
1. Refactor aidd-factory generators and templates to produce Vertical Slice Architecture (slices per service with api, models, repositories).
2. Ensure native inclusion of the Dynamic Sine Qua Non Quartet (/swagger, /webhooks, /mcp, /docs) in the generated server.
3. Deliver Super-App frontend aligned with Impeccable Design and typed secure repositories.
4. Update tool Quality Gates and ensure full approval in pytest and ecossistema audit.
Do not fabricate approvals and maintain monorepo governance and token economy rules.
```
