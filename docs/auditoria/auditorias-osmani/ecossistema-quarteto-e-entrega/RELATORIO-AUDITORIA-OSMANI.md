# Relatório de Auditoria Completa — Método Addy Osmani (AIDD-Osmani)

> **Alvo:** Motor de Entrega do Ecossistema AIDD (Quarteto Sine Qua Non, Integração Frontend e Pipeline da Tríade)  
> **Data:** 23/10/2026  
> **Metodologia:** Playbook A (Auditoria Factual nos 5 Eixos do Método Addy Osmani)  
> **Status:** AUDITADO — 4 ACHADOS CRÍTICOS / ALTOS CONFIRMADOS

---

## 1. Contexto e Barra de Qualidade (Constraints)

A auditoria foi disparada para investigar a discrepância entre a esteira formal e a aplicação gerada nos testes E2E do fluxo Pure:
1. **Lei #10 (Quarteto Sine Qua Non Dinâmico):** As rotas OpenAPI 3.1 (`/api`), Webhooks (`/webhook`), MCP (`/mcp`) e Documentação (`/docs`) DEVEM nascer nativamente da consistência do `PLANNER.json`, cobrindo 100% dos módulos do sistema com atualização dinâmica.
2. **Lei #11 (Soberania do Modo Claro):** Inicialização obrigatória em Modo Claro corporativo (superfícies off-white/brancas, contraste WCAG 2.2 AA/AAA, bordas de 1px em ardósia). O tema escuro não pode ser forçado via hardcode.
3. **Lei #1 (Determinismo e Single Source of Truth):** Proibição de cópias locais divergentes de templates e moldes.
4. **Entrega Funcional:** Acesso a `http://localhost:3000/` deve servir a aplicação (frontend compilado com fallback SPA), jamais uma listagem de arquivos de diretório.
5. **Observabilidade Humana:** A rota `/metrics` deve oferecer inspeção amigável (Dashboard visual) para usuários humanos no navegador, além de exportação bruta Prometheus para coletores.

---

## 2. Varredura Factual por Eixo (Addy Osmani)

### Eixo 1: Contratos e Consistência do Quarteto (`api-and-interface-design`)
- **Evidência:** `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/scripts/provision_project.py:160-220` e `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/quarteto_studios.py`.
- **Falha Identificada:** O `provision_project.py` copia templates fixos e o `quarteto_studios.py` retorna dicionários estáticos (`paths: {"/api": ...}`, `tools: []`, `events: []`), ignorando os módulos, endpoints e entidades definidos formalmente em `PLANNER.json` ou `HANDOFF_PLANNER_ENGINE.json`.
- **Impacto:** O Quarteto gerado fica vazio ou genérico, não refletindo a aplicação de domínio concebida pelo Planner.

### Eixo 2: Arquitetura e Single Source of Truth (`code-review-and-quality`)
- **Evidência:** `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/core/swagger.html:2`, `mcp_studio.html:2` vs `componentes/compartilhado/moldes/quarteto/swagger.html:2`.
- **Falha Identificada:** Embora os moldes em `componentes/compartilhado/moldes/quarteto/` tenham sido corrigidos para Modo Claro (`<html lang="pt-BR">`), o `aidd-master` e o `aidd-enterprise` mantiveram cópias locais em `src/core/` com `<html lang="pt-BR" class="dark">` e variáveis escuras hardcoded (`--bg-body: #030712`).
- **Impacto:** O projeto gerado nasce com tela preta legada, violando a Lei #11.

### Eixo 3: Engenharia de Frontend e Entrega Local (`frontend-ui-engineering`)
- **Evidência:** `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/server.py:38-42, 608-615`.
- **Falha Identificada:** O `server.py` define `STATIC_DIR = os.path.join(CURRENT_DIR, "static")` e busca `index.html` estritamente nessa pasta. No entanto, o frontend gerado com Vite fica na pasta irmã `frontend/` e gera o build em `frontend/dist/`. Como `src/static/index.html` não existe, o servidor ativa o fallback padrão de `SimpleHTTPRequestHandler` que despeja `Directory listing for /`.
- **Impacto:** Ao abrir `http://localhost:3000/`, a aplicação web nunca carrega; o usuário vê apenas uma lista de arquivos.

### Eixo 4: Observabilidade e Experiência do Usuário (`observability-and-instrumentation`)
- **Evidência:** `modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/server.py:590-596`.
- **Falha Identificada:** A rota `/metrics` apenas devolve `metrics_registry.render().encode("utf-8")` (`text/plain`). Não há rota JSON (`/api/metrics`) nem renderização de Dashboard HTML para navegadores.
- **Impacto:** Usuários e auditores humanos não conseguem visualizar a saúde do sistema de forma gráfica e amigável.

### Eixo 5: Orquestração e Ciclo da Tríade (`orchestration-patterns`)
- **Evidência:** `scripts/orquestrador_sincrono.py:231-380`.
- **Falha Identificada:** O script orquestrador roda 7 etapas antigas. Ele não constrói o frontend (`npm run build`) após a injeção do código e não compila o bundle para ser servido estaticamente pelo servidor na Etapa de Entrega.
- **Impacto:** O app entregue pelo fluxo Pure fica quebrado localmente.

---

## 3. Contestação Adversarial (Doubt-Driven Development)
- **Dúvida levantada:** *Seria responsabilidade do Nginx servir o frontend em produção e não do `server.py`?*
  - **Refutação:** O projeto precisa rodar de forma agnóstica tanto com Docker/Nginx quanto localmente em modo de desenvolvimento/auditoria (`python src/server.py` ou `make run`). Se o `server.py` não resolve `frontend/dist/` nativamente, a entrega local fica inoperante sem container.
- **Dúvida levantada:** *O Planner contém metadados suficientes para o Quarteto?*
  - **Confirmação:** Sim. O `PLANNER.json` contém `modulos_funcionais`, `entidades`, `rotas_api`, `eventos_webhook` e a especificação de domínio completa. O Quarteto só precisa ler esse arquivo para popular rotas, ferramentas e documentação.
