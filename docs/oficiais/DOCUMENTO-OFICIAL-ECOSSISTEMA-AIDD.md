# TRATADO ARQUITETURAL E ESPECIFICAÇÃO OFICIAL DO ECOSSISTEMA AIDD
## Engenharia de Software Autônoma, Governança Estrita e a Tríade Canônica de Criação

> **Status:** Documento Oficial Canônico — Versão 3.0  
> **Data de Homologação:** 18 de Setembro de 2026  
> **Classificação:** Diretriz Arquitetural e Operacional Inviolável  
> **Repositório Central:** `https://github.com/heverton-dev/ecossistema-aidd`  

---

## 1. PREÂMBULO E PRINCÍPIOS FUNDAMENTAIS

O **Ecossistema AIDD (Artificial Intelligence Driven Development)** é uma plataforma unificada de engenharia agêntica de software projetada para erradicar definitivamente o paradigma amador do *"Vibe Coding"* — a geração cega de código sem testes, acoplada a dependências proprietárias, com alucinações de modelos de linguagem e falsas alegações de conformidade.

O ecossistema estabelece uma barreira de engenharia mecânica onde a IA generativa é estritamente contida por **Quality Gates binários determinísticos**, **Fatias Verticais isoladas (Vertical Slice Architecture)** e **contratos formais de handoff baseados em JSON Schema**.

### As Leis Invioláveis do Ecossistema

1. **Determinismo Primeiro (Zero Token Fallacy):** Toda validação, checagem estrutural, linting, análise sintática (AST) e auditoria de segurança é executada por compiladores e scripts mecânicos determinísticos (Python puro, Hadolint, Checkov, Pytest). A inteligência artificial nunca audita a si mesma com texto livre.
2. **Qualidade Binária:** Qualquer verificação gera apenas dois estados: `exit 0` (aprovado e promovido) ou `exit 1` (bloqueado sumariamente com fail-fast). Não existem avisos toleráveis em produção.
3. **Zero Stubs / Zero Mocks em Produção:** Todo software produzido nasce com 100% de contratos tipados, banco de dados real em execução concorrente e suíte automatizada de testes reais. Proibido o uso de `TODO`, `pass`, mocks estáticos ou retornos fictícios em código de produção.
4. **Padrão-Ouro de Stack Tecnológica:** Salvo especificação contrária expressa no plano de intake:
   - **Frontend:** Next.js 14 (App Router) + TypeScript + Tailwind CSS + Lucide Icons + Validação Zod.
   - **Backend:** Python puro estruturado em Clean Architecture + SQLite em modo WAL concorrente (ou PostgreSQL nativo) + FastAPI com OpenAPI 3.1 nativo.
5. **Quarteto Sine Qua Non Dinâmico:** Todo sistema gerado nasce nativamente com quatro pilares autônomos que cobrem 100% dos módulos:
   - **Swagger Studio (`/swagger` ou `/docs`):** Especificação interativa OpenAPI 3.1.
   - **Webhook Studio (`/webhooks`):** Gestão, teste e disparo de webhooks assíncronos.
   - **MCP Studio (`/mcp`):** Exposição padronizada via Model Context Protocol.
   - **Guia do Utilizador (`/guia` ou `/docs/guia`):** Manual vivo da aplicação para utilizadores finais.
6. **Desenvolvedor no Controle:** A execução de fluxos é sequencial e síncrona. Subagentes paralelos invisíveis em segundo plano são terminantemente proibidos (`G_ZERO_HEADLESS`).

---

## 2. AS 8 FERRAMENTAS HOMOLOGADAS DO ECOSSISTEMA

O ecossistema é modularizado em 8 ferramentas atômicas, com fronteiras funcionais estritas em `tools/`:

| Ferramenta | Diretório | Papel Primário | Entrada Principal | Entrega Primária |
|---|---|---|---|---|
| **AIDD Forge** | `tools/aidd-forge` | Guardião da Governança | Diretório do projeto / Parâmetros | Regras invioláveis (`AGENTS.md`), hooks pre-commit, bloqueios anti-vibe. |
| **AIDD Planner** | `tools/aidd-planner` | Planta Baixa BDD/SDD | Linguagem natural / Requisitos | `PLANNER.json` com cenários BDD, entidades e contrato formal de handoff. |
| **AIDD Generator** | `tools/aidd-generator` | Fábrica Autônoma (8 fases) | `PLANNER.json` | Aplicação construída do zero com TDD estrito Red-Green e monólito VSA. |
| **AIDD Factory** | `tools/aidd-factory` | Montagem Multi-Serviço | Motores OSS + `PLANNER.json` | Gateway FastAPI BFF, Frontend Next.js integrado e Docker Compose unificado. |
| **AIDD Bridge** | `tools/aidd-bridge` | Libertador de Low-Code | Export Lovable/v0/Bolt | Aplicação desatada de BaaS proprietário, PostgreSQL nativo e UI preservada. |
| **AIDD Master** | `tools/aidd-master` | Harmonização Modular VSA | Código das Engines | Fatias Verticais limpas, Frontend Next.js Padrão-Ouro e OpenAPI 3.1. |
| **AIDD Enterprise** | `tools/aidd-enterprise`| Selo de Segurança Corporativo | Código do Master | Injeção SHA-256 de componentes auditados, RBAC, Rate-Limit e Zero-Trust. |
| **AIDD Ops** | `tools/aidd-ops` | Meta-Orquestrador de Infra | Código Enterprise | Sizing VPS, Docker Swarm, Traefik SSL, sops+age e Uptime Kuma. |

---

## 3. A TRÍADE CANÔNICA DE CRIAÇÃO

O ecossistema estabelece que qualquer demanda de software deriva de uma **Fundação de Governança (`aidd-forge`)** e de um **Planejador Estruturado (`aidd-planner`)**, permitindo ao desenvolvedor derivar uma de **três estratégias especializadas**:

```
                              ┌────────────────────────┐
                              │       aidd-forge       │
                              │ (Governança & Regras)  │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │      aidd-planner      │
                              │ (Intake BDD/SDD →      │
                              │  PLANNER.json)         │
                              └───────────┬────────────┘
                                          │
                       Seleção da Estratégia de Criação
                 ┌────────────────────────┼────────────────────────┐
                 │                        │                        │
                 ▼                        ▼                        ▼
           [ FLUXO 01 ]             [ FLUXO 02 ]             [ FLUXO 03 ]
             aidd-pure                aidd-open               aidd-bridge
          (Do Zero Puro)        (Motores Open-Source)     (Low-Code Desatado)
          [aidd-generator]          [aidd-factory]           [aidd-bridge]
                 │                        │                        │
                 └────────────────────────┼────────────────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │      aidd-master       │
                              │ (Monólito Modular VSA) │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │    aidd-enterprise     │
                              │  (Blindagem SHA-256)   │
                              └───────────┬────────────┘
                                          │
                                          ▼
                              ┌────────────────────────┐
                              │        aidd-ops        │
                              │(Deploy VPS & Observab.)│
                              └────────────────────────┘
```

### 3.1. FLUXO 01 — `aidd-pure` (Do Zero Puro)
- **Comando Slash:** `/pure <ideia>`
- **Comando CLI:** `python ecossistema.py run-fluxo --fluxo pure --nome "<nome>" --slug <slug> --dominio <dominio>`
- **Motor Subjacente:** `aidd-generator` (Pipeline de 8 fases com auto-crítica).
- **Adequação:** Demandas com lógica de negócio personalizada, inovadora ou altamente proprietária.
- **Rigor:** Aplica o ciclo TDD Red-Green-Refactor estrito. Os testes são escritos e forçados a falhar antes que qualquer linha de lógica de produção seja implementada.
- **Entregável:** Código de domínio 100% puro, sem bibliotecas alienígenas, com suíte completa de testes unitários e de integração.

### 3.2. FLUXO 02 — `aidd-open` (Motores Open-Source)
- **Comando Slash:** `/open <ideia>`
- **Comando CLI:** `python ecossistema.py run-fluxo --fluxo open --nome "<nome>" --slug <slug> --dominio <dominio>`
- **Motor Subjacente:** `aidd-factory` (Curadoria e orquestração de ecossistemas OSS).
- **Adequação:** Soluções onde a reinvenção da roda é contraproducente (Anti-NIH). Casos como ERPs, CRMs, automação de processos, gateways de mensageria e chatbots.
- **Rigor:** Seleciona engines maduras (ex: PostgreSQL, N8N, Evolution API, Directus), isola cada uma em contêineres OCI herméticos e gera automaticamente um BFF (Backend-for-Frontend) em FastAPI para mediar a integração.
- **Entregável:** Orquestração Compose multi-serviço, adaptadores de gateway tipados e interface unificada em Next.js.

### 3.3. FLUXO 03 — `aidd-bridge` (Low-Code Desatado)
- **Comando Slash:** `/bridge <pasta-origem> <nome>`
- **Comando CLI:** `python ecossistema.py run-fluxo --fluxo bridge --origem <pasta> --nome "<nome>"`
- **Motor Subjacente:** `aidd-bridge` (Scanner estático, AST e migrador de dialeto SQL).
- **Adequação:** Aplicações concebidas em ferramentas visuais rápidas (Lovable, v0, Bolt, Cursor) que se tornaram reféns de BaaS proprietários (Supabase Cloud) e infraestruturas fechadas.
- **Rigor:** Escaneia o código fonte visual, extrai as telas React, elimina dependências de SDK proprietário, compila o schema SQL com compatibilidade para `auth.uid()`, `auth.jwt()` e PostgREST puro, preservando 100% da experiência visual concebida no frontend.
- **Entregável:** Aplicação pronta para self-hosting em VPS própria, banco PostgreSQL autônomo e sem custos de assinatura recorrente de BaaS.

---

## 4. O FUNIL UNIVERSAL DE CONVERGÊNCIA

A maior inovação da Tríade Canônica reside no fato de que **nenhuma aplicação gerada pelas três engines vai direto para produção de forma isolada**. Todas convergem para o mesmo Funil Universal:

### 4.1. Passo 1 — Harmonização em Monólito Modular (`aidd-master`)
- Recebe o código bruto de qualquer uma das três engines.
- Reorganiza o backend em **Fatias Verticais (Vertical Slices)**, eliminando dependências cruzadas entre domínios.
- Constrói o **Frontend Padrão-Ouro** em Next.js 14 App Router integrado via tipagem TypeScript gerada diretamente do OpenAPI.
- Instala a infraestrutura do **Quarteto Sine Qua Non** (`/swagger`, `/webhooks`, `/mcp`, `/guia`).

### 4.2. Passo 2 — Blindagem Corporativa e Auditoria SHA-256 (`aidd-enterprise`)
- Submete o monólito à auditoria criptográfica.
- Injeta componentes de missão crítica certificados (RBAC com Argon2id, Transactional Outbox Worker, Rate Limiting distribuído, Prometheus Metrics e Sanitização OWASP).
- Registra os hashes SHA-256 de integridade para impedir adulteração de código em tempo de execução (*drift*).

### 4.3. Passo 3 — Meta-Orquestração de Infraestrutura e VPS (`aidd-ops`)
- Dimensiona o hardware necessário com base no nicho e carga prevista.
- Executa o provisionamento remoto na VPS via SSH/Ansible com chaves criptográficas.
- Publica contêineres Docker sob Traefik com renovação automática de certificados SSL (Let's Encrypt), rede interna isolada, Uptime Kuma para monitoramento e preflight E2E determinístico.

---

## 5. CONTRATOS FORMAIS DE HANDOFF E ESPECIFICAÇÕES

A transição entre ferramentas não ocorre por mensagens soltas de chat, mas sim por contratos JSON Schema estritamente auditados:

```
[aidd-planner]
      │
      ▼  HANDOFF_PLANNER_ENGINE.json
[generator | factory | bridge]
      │
      ▼  HANDOFF_ENGINE_MASTER.json
[aidd-master]
      │
      ▼  HANDOFF_MASTER_ENTERPRISE.json
[aidd-enterprise]
      │
      ▼  HANDOFF_ENTERPRISE_OPS.json
[aidd-ops]
```

### 5.1. `handoff-planner-to-engine.schema.json`
- **Valida:** Metadados do projeto, domínio funcional, personas, cenários BDD obrigatórios no formato `Given/When/Then`, dicionário formal de entidades com tipos de dados, e declaração de conformidade com o Quarteto Sine Qua Non.

### 5.2. `handoff-engine-to-master.schema.json`
- **Valida:** Código-fonte gerado, rotas REST implementadas, schemas Pydantic de entrada e saída, DDL SQL de banco de dados (`schema_sql`), e relatório binário de testes unitários da engine (`testes_passando = true`).

### 5.3. `handoff-master-to-enterprise.schema.json`
- **Valida:** Estrutura de fatias verticais VSA em `src/features/`, paridade OpenAPI 3.1, interfaces e componentes do Frontend Next.js, e endpoints operacionais do Quarteto Sine Qua Non ativos.

### 5.4. `handoff-enterprise-to-ops.schema.json`
- **Valida:** Manifesto de componentes blindados com hashes SHA-256, variáveis de ambiente necessárias para produção, `requirements.lock` auditado com hash por pacote, e parâmetros de sizing de infraestrutura para provisionamento.

---

## 6. MATRIZ INTEGRAL DOS 24 QUALITY GATES

Os Quality Gates são guardiões mecânicos herméticos executados automaticamente antes de cada commit pelo framework `pre-commit` ou sob demanda via `python ecossistema.py audit`:

| Gate | Script Verificador | Alvo de Inspeção Mecânica |
|---|---|---|
| **G1** | `G_ORQUESTRADOR_SINCRONO.py` | Audita conformidade CLI, transições de estado e integridade dos schemas de handoff. |
| **G2** | `G_TESTES_REAIS.py` | Executa pytest real em todas as ferramentas. Reprova com 1 falha sequer (2.304 testes monitorados). |
| **G3** | `G_HARNESS_COMPAT.py` | Audita sincronismo bidirecional de skills e comandos entre todos os 6 harnesses de IA. |
| **G4** | `G_ECOSSISTEMA_INTEGRIDADE.py`| Varre o repositório validando estrutura física e sintaxe de todo código Python via AST. |
| **G5** | `G_DRIFT_NUCLEO_COMPARTILHADO.py`| Bloqueia divergência de código entre bibliotecas compartilhadas do Master e Enterprise. |
| **G6** | `G_DEPENDENCIAS_PIN_HASH.py` | Bloqueia dependências sem pinagem estrita (`==`) ou sem hash criptográfico SHA-256 no lockfile. |
| **G7** | `G_FRONTEND_LAYERS.py` | Audita o frontend Next.js e proíbe chamadas de rede direta em componentes de UI pura. |
| **G8** | `G_ISOLATION_AUDIT.py` | Audita fatias VSA via AST e proíbe imports cruzados entre fatias verticais. |
| **G9** | `G_HADOLINT.py` | Audita conformidade OCI e melhores práticas de segurança em todos os 17 Dockerfiles. |
| **G10**| `G_INFRA_COMPOSE.py` | Audita segurança, portas, redes e volumes em arquivos docker-compose via Checkov e PyYAML. |
| **G11**| `G_PROTOCOL_FALLBACK.py` | Garante paridade absoluta: nenhuma função existe no MCP sem ter contrapartida REST equivalente. |
| **G12**| `G_LLM_PROMPT_SHIELD.py` | Audita via AST se clientes LLM passam obrigatoriamente por sanitização anti-prompt injection. |
| **G13**| `G_DRIFT_ANALYZER.py` | Detecta redundância estrutural entre fatias VSA e orienta extração canônica para o core. |
| **G14**| `G_PROTOTYPE_REWRITE.py` | Garante que protótipos em sandbox/ só sejam promovidos para produção com suíte TDD espelhada. |
| **G15**| `G_ZERO_HEADLESS.py` | Bloqueia o disparo não assistido de subagentes ou subprocessos invisíveis em segundo plano. |
| **G16**| `G_HONESTIDADE_ROTULO.py` | Bloqueia saídas com termos de marketing que excedam o que foi realmente comprovado em testes. |
| **G17**| `G_CLI_HELP_CONSISTENCIA.py` | Compara flags mencionadas em mensagens contra parâmetros reais definidos nos pontos CLI. |
| **G18**| `G_COMPONENTE_AGNOSTICO.py` | Audita a integridade e paridade multi-harness de novos componentes agnósticos. |
| **G19**| `G_SEGREDOS.py` | Escaneia o repositório contra vazamento de credenciais via detect-secrets (stage manual). |
| **G20**| `G_ARQUITETURA_DELIVERABLE.py`| Valida padrões Clean Architecture e DDD em entregáveis estruturados. |
| **G21**| `G_ESCRITOR_ATOMICO.py` | Audita a utilização de escrita atômica para impedir corrupção em arquivos críticos. |
| **G22**| `G_TRANSACTION_LOG_LRU.py` | Audita consistência do Transaction Log com cache LRU e sincronismo em baseline. |
| **G23**| `G_UNIVERSAL_HARNESS.py` | Garante paridade e wiring universal de componentes em todos os ambientes suportados. |
| **G24**| `G_SUPPLY_CHAIN.py` | Audita integridade e proveniência criptográfica de toda a cadeia de suprimentos. |

---

## 7. ARQUITETURA DE CÓDIGO E PADRÕES TÉCNICOS

### 7.1. Vertical Slice Architecture (VSA)
Em vez da tradicional separação em camadas horizontais anêmicas (Controllers, Services, Repositories), o código gerado pelo AIDD Master é organizado por **Fatias Verticais de Negócio**:
```
src/features/
  ├── autenticacao/
  │     ├── models.py
  │     ├── use_cases.py
  │     ├── routes.py
  │     └── tests/
  ├── gestao_tarefas/
  │     ├── models.py
  │     ├── use_cases.py
  │     ├── routes.py
  │     └── tests/
  └── faturamento/
```
Cada fatia é auto-contida. Uma fatia **nunca** importa arquivos internos de outra fatia. A comunicação inter-fatias ocorre exclusivamente via **EventBus assíncrono** com garantia de entrega *At-Least-Once* operada pelo **Transactional Outbox Pattern**.

### 7.2. Result Monad (Railway-Oriented Programming)
Nenhum fluxo de negócio do backend levanta exceções não tratadas (`raise Exception`). Toda operação retorna um objeto determinístico `Result[T, E]`:
- Em caso de sucesso: `Success(value=dado)`
- Em caso de falha: `Failure(error=DomainError)`

Isso garante rastreabilidade estrita, elimina telas de erro 500 imprevisíveis e força o compilador e os testes a cobrirem os fluxos alternativos de erro.

---

## 8. DUALIDADE DE INTERFACE & GUIA OPERACIONAL

O Ecossistema AIDD elimina a fricção de entrada, permitindo que a mesma infraestrutura profissional seja operada tanto por desenvolvedores seniores quanto por utilizadores leigos:

### 8.1. Operação por Desenvolvedores Seniores (CLI Pura)
```bash
# Execução da Tríade Canônica de Ponta a Ponta:
python ecossistema.py run-fluxo --fluxo pure   --nome "SaaS Tarefas" --slug tarefas --dominio produtividade
python ecossistema.py run-fluxo --fluxo open   --nome "CRM Médico"   --slug crm     --dominio saude
python ecossistema.py run-fluxo --fluxo bridge --nome "App Delivery" --origem ./exports/lovable

# Operações Individuais de Engenharia:
python ecossistema.py audit                          # Auditoria dos 24 Quality Gates
python ecossistema.py status                         # Telemetria e saúde do monorepo
python ecossistema.py components sync --tipo todos  # Sincronização multi-harness
python ecossistema.py ops plan "ERP Financeiro"      # Dimensionamento de infraestrutura VPS
python ecossistema.py ops deploy staging --dry-run   # Simulação de deploy em contêiner
```

### 8.2. Operação por Usuários Finais e Negócio (Chat e Slash Commands)
Basta digitar os comandos no assistente de inteligência artificial de sua escolha (Claude Code, Cursor, Antigravity, OpenCode, MimoCode):
```bash
# Criar sistemas completos sem tocar no terminal:
/pure "Construir um sistema de gestão de estoque para lojas de calçados com leitor de código de barras"
/open "Criar uma plataforma de atendimento ao cliente multicanal com N8N e WhatsApp"
/bridge ./meu-projeto-lovable meu-sistema-saas

# Comandos Rápidos e Refinamentos:
/master produtos                 # Adiciona uma nova fatia vertical com tela e banco
/enterprise rbac autenticacao    # Injeta blindagem empresarial SHA-256
/ops plan "Clínica médica"       # Dimensiona os servidores para deploy
/aidd-orchestrator               # Inicia o assistente socrático que conduz o projeto
```

---

## 9. CONCLUSÃO E CERTIFICAÇÃO DE HOMOLOGAÇÃO

O Ecossistema AIDD consolida o estado da arte em engenharia de software agêntica. Ao unir planejamento estruturado BDD/SDD, a flexibilidade da Tríade Canônica de Criação, a convergência para um Monólito Modular VSA em Next.js e a proteção mecânica inegociável de 24 Quality Gates com 2.304 testes reais automatizados, a plataforma assegura que **todo software produzido seja soberano, auditável, resiliente e pronto para missão crítica desde o primeiro commit.**
