# Enciclopédia & Carta Magna do Ecossistema AIDD
## Tratado Definitivo de Arquitetura, Engenharia, Cibersegurança, Agnosticismo e Governança

> **Localização:** `docs/explicacoes/CONSOLIDACAO-DECISOES-ARQUITETURA-ECOSSISTEMA.md`  
> **Status:** Tratado Canônico Soberano e Imutável  
> **Versão:** 3.0.0 (Consolidação Holística Universal)  
> **Data de Homologação:** 17/09/2026  
> **Padrão de Referência:** Monólito Modular (VSA + Camada Horizontal), Padrão Enterprise CTT, Zero Vendor Lock-in  

---

## 1. O Decálogo das Leis Invioláveis do Ecossistema

Toda linha de código, manifesto de infraestrutura, contrato de API ou diretiva agêntica dentro do ecossistema AIDD é subordinada a 10 leis universais inquebráveis:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                  AS 10 LEIS INVIOLÁVEIS DO ECOSSISTEMA                                 │
├──────────────────────────────┬──────────────────────────────┬──────────────────────────────────────────┤
│ 1. Determinismo Estrito      │ 2. Zero Stubs / Zero Mocks   │ 3. Monólito Modular Canônico             │
│ Ferramentas mecânicas, AST   │ 100% funcional, tipado e     │ VSA vertical de domínio + Camada         │
│ e schemas; nunca vibe coding │ validado com testes reais    │ horizontal compartilhada (core/shared)   │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────────────────┤
│ 4. Cibersegurança Nativa     │ 5. Agnosticismo Supremo      │ 6. Quarteto Sine Qua Non                 │
│ OWASP Top 10 mitigado,       │ Zero vendor lock-in em nuvem,│ /swagger, /webhooks, /mcp, /docs         │
│ SHA-256, sops+age, HMAC      │ SO, harness e modelos LLM    │ dinâmicos cobrindo 100% dos módulos      │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────────────────┤
│ 7. Missão Crítica Enterprise │ 8. Desenvolvedor no Controle │ 9. Economia Extrema de Tokens            │
│ Circuit Breakers, Retries,   │ Zero headless, interatividade│ Caveman thinking, saídas ultra-concisas  │
│ Rate Limiting, trace_id      │ contínua e sem agentes ocultos│ e inspeção em grafo first                │
├──────────────────────────────┴──────────────────────────────┴──────────────────────────────────────────┤
│ 10. A Tríade Canônica de Criação                                                                       │
│ FORGE (Constituição) ➔ PRÉ-PLANO (Intake) ➔ [GENERATOR | FACTORY | BRIDGE] ➔ MASTER ➔ ENTERPRISE ➔ OPS  │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tratado de Cibersegurança & Defesa em Profundidade

O ecossistema implementa o princípio de **Defesa em Profundidade (Defense in Depth)** em todas as camadas da aplicação, desde o kernel dos containers até os cabeçalhos HTTP e assinaturas criptográficas.

### 2.1. Mitigação Ativa do OWASP Top 10
* **Injeção de SQL (A03:2021):**
  * Proibição categórica de concatenação ou interpolação de strings em consultas de banco.
  * Obrigatoriedade de **queries parametrizadas** com *prepared statements* em 100% dos repositórios (`repositories.py`).
  * Validação e tipagem de entrada via esquemas Pydantic / JSON Schema antes de atingir a camada de persistência.
* **Quebra de Autenticação e Gestão de Sessão (A07:2021):**
  * Hashing de senhas utilizando algoritmos resistentes a GPU com salt individual (Argon2id ou bcrypt com fator de custo elevado).
  * Sessões e tokens stateless com assinaturas assimétricas ou JWT com expiração curta e rotação de refresh tokens.
* **Falhas Criptográficas (A02:2021):**
  * Proibição absoluta de algoritmos obsoletos (MD5, SHA-1, DES). Uso estrito de **SHA-256**, **AES-256-GCM** e **ChaCha20-Poly1305**.
  * Criptografia de dados em repouso e trânsito forçado via TLS 1.3.
* **Design Inseguro & Ataques de Temporização (Timing Attacks):**
  * Toda verificação de assinaturas (ex: webhooks, tokens) utiliza funções de comparação em tempo constante (`hmac.compare_digest`), eliminando vazamentos de temporização side-channel.
* **Vulnerabilidades de Configuração & Cabeçalhos HTTP (A05:2021):**
  * Injeção nativa de headers de proteção rigorosos em todos os gateways:
    * `Content-Security-Policy (CSP)` restritivo.
    * `Strict-Transport-Security (HSTS)` com `max-age=31536000; includeSubDomains; preload`.
    * `X-Content-Type-Options: nosniff`.
    * `X-Frame-Options: DENY` (anti-clickjacking).
    * `Referrer-Policy: strict-origin-when-cross-origin`.
    * Política CORS explícita por whitelist, proibindo `Access-Control-Allow-Origin: *` em rotas autenticadas.

### 2.2. Gestão Criptográfica de Segredos (`sops + age`)
* **Zero Credenciais em Texto Claro:** Proibição de arquivos `.env` com senhas, chaves de API ou segredos commitados no repositório git.
* **Cofre Criptografado com `sops` e Chaves Assimétricas `age`:**
  * Os arquivos de configuração de ambiente (`secrets.enc.yaml` / `.env.enc`) são versionados criptografados com criptografia moderna de curva elíptica (`X25519`).
  * A chave privada `age` reside exclusivamente no ambiente seguro do desenvolvedor ou no servidor VPS de produção, nunca em repositórios remotos.
  * O deciframento ocorre de forma efêmera em tempo de execução na memória.

### 2.3. Blindagem de Integridade SHA-256 (Anti-Tampering)
* Todos os templates e componentes críticos injetados pelo `aidd-enterprise` possuem manifestos de checksum **SHA-256**.
* O Quality Gate `G_ENTERPRISE_SHA` calcula os hashes dos arquivos sensíveis no início da execução; se um único byte for adulterado sem autorização, a esteira é bloqueada com Exit 1 imediato.

### 2.4. Trilha de Auditoria Imutável (Audit Trail) & Proteção de PII (LGPD/GDPR)
* **Correlação Universal com `trace_id`:** Toda requisição que entra no ecossistema recebe ou gera um identificador único de rastreamento (`X-Trace-Id`), propagado através de middlewares, serviços, chamadas de banco e logs assíncronos.
* **Logs Estruturados e Sanitizados:** Proibição de vazamento de Dados Pessoais Identificáveis (PII) nos logs (senhas, CPFs, cartões e tokens são ofuscados ou mascarados via regex no nível de log).
* **Registro de Auditoria de Mutações:** Operações críticas (criação, alteração, exclusão, troca de privilégios) gravam um evento de auditoria com: timestamp UTC ISO-8601, ator/usuário, ação executada, IP de origem, status da transação e `trace_id`.

### 2.5. Segurança de Containers & Práticas OCI (Hadolint)
* Imagens Docker auditadas deterministicamente pelo gate `G_HADOLINT`.
* Execução estrita em **usuários não-root** (`USER appuser`).
* Imagens base mínimas (Alpine Linux / Distroless) com fixação de versão (pinning) para minimizar superfície de ataque.
* Escaneamento de portas desnecessárias e volumes de dados com permissões estritas de leitura/escrita.

---

## 3. Tratado de Universalidade & Agnosticismo Supremo

O ecossistema AIDD foi concebido com uma premissa fundamental: **independência total e irrestrita**. Nenhum fornecedor de nuvem, sistema operacional ou empresa de inteligência artificial pode ditar as regras ou prender a solução.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                O QUADRANTE DO AGNOSTICISMO                             │
├───────────────────────────────────────────┬────────────────────────────────────────────┤
│ 1. Agnosticismo de Nuvem & Infra          │ 2. Agnosticismo de Sistema Operacional     │
│ Qualquer VPS Linux (Hetzner, AWS, GCP,    │ Execução determinística em Windows,        │
│ DigitalOcean, Bare-Metal ou Local) via    │ Linux e macOS com caminhos normalizados    │
│ Docker e SSH padronizado.                 │ e scripts polimórficos.                    │
├───────────────────────────────────────────┼────────────────────────────────────────────┤
│ 3. Agnosticismo de Harness de IA          │ 4. Agnosticismo de Modelos e Provedores    │
│ Claude Desktop, Cursor, Gemini, Roo Code, │ Contratos abertos via MCP (Model Context   │
│ Windsurf com sincronização automática     │ Protocol), JSON Schema e prompts           │
│ de regras e ferramentas.                  │ desacoplados de APIs proprietárias.        │
└───────────────────────────────────────────┴────────────────────────────────────────────┘
```

### 3.1. Agnosticismo de Nuvem (Zero Cloud Lock-in)
* A solução não utiliza serviços proprietários de nuvem que cobrem pedágio ou aprisionem a arquitetura (ex: AWS DynamoDB proprietário, Firebase locked, Cloudflare Workers proprietários não portáveis).
* A infraestrutura baseia-se em padrões abertos da indústria: **Linux, Docker, Docker Compose, Nginx/Traefik e PostgreSQL**.
* Uma aplicação do ecossistema pode ser movida de uma VPS de 5 dólares na Hetzner para um servidor dedicado na OVH ou uma instância na AWS/GCP em menos de 10 minutos, sem alterar uma única linha de código da aplicação.

### 3.2. Agnosticismo de Sistema Operacional (Windows / Linux / macOS)
* Toda a engenharia do ecossistema opera perfeitamente em Windows (PowerShell/CMD), Linux (Bash/Zsh) e macOS.
* Tratamento determinístico de separadores de caminho (`pathlib.Path`, `/` canônico), fins de linha (`LF` forçado em git) e codificação de caracteres estrita em `UTF-8`.
* Quality Gates polimórficos que detectam o ambiente e executam comandos nativos sem quebrar a interoperabilidade.

### 3.3. Agnosticismo de Harness Multi-Agente
* O ecossistema mantém paridade absoluta entre as principais ferramentas de desenvolvimento com IA do mercado:
  * Claude Desktop (`CLAUDE.md`)
  * Gemini CLI / Antigravity (`GEMINI.md`)
  * Cursor (`.cursorrules`)
  * Roo Code / Windsurf / Copilot (`AGENTS.md`)
* O gate `G_HARNESS_COMPAT` audita e sincroniza automaticamente as regras e diretivas canônicas para que nenhum ambiente fique defasado em relação ao `AGENTS.md` soberano.

### 3.4. Agnosticismo de LLM & Protocolo Aberto MCP
* As ferramentas do ecossistema expõem suas capacidades através do **Model Context Protocol (MCP)**, padrão aberto mantido pela indústria.
* Qualquer LLM de ponta (Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro, DeepSeek R1, Llama local) pode orquestrar e consumir as ferramentas sem dependência de SDKs fechados.

---

## 4. O Padrão Arquitetural: Monólito Modular Canônico

Abandonamos a dicotomia falha entre "microsserviços caóticos prematuros" e "monólitos espaguete tradicionais". O padrão de ouro do ecossistema é o **Monólito Modular**:

```
                         ┌─────────────────────────────────────────┐
                         │           ROTEADOR UNIFICADO            │
                         │   (/swagger, /webhooks, /mcp, /docs)    │
                         └────────────────────┬────────────────────┘
                                              │
              ┌───────────────────────────────┼───────────────────────────────┐
              ▼                               ▼                               ▼
  ┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
  │  features/encomendas/ │       │    features/frotas/   │       │ features/roteirizacao/│
  │  (VSA de Domínio)     │       │    (VSA de Domínio)   │       │  (VSA de Domínio)     │
  │  - routes.py          │       │    - routes.py        │       │  - routes.py          │
  │  - services.py        │       │    - services.py      │       │  - services.py        │
  │  - repositories.py    │       │    - repositories.py  │       │  - repositories.py    │
  │  - models.py          │       │    - models.py        │       │  - models.py          │
  │  - tests/             │       │    - tests/           │       │  - tests/             │
  └───────────┬───────────┘       └───────────┬───────────┘       └───────────┬───────────┘
              │                               │                               │
              └───────────────────────────────┼───────────────────────────────┘
                                              │ Consomem sem duplicar
                                              ▼
                         ┌─────────────────────────────────────────┐
                         │       CAMADA HORIZONTAL COMPARTILHADA   │
                         │                 (core/ / shared/)       │
                         ├─────────────────────────────────────────┤
                         │ • Database: Pool async e transactions   │
                         │ • Security: Sanitização, Hashes, Secrets│
                         │ • Telemetry: Logs estruturados, trace_id│
                         │ • Resilience: Circuit Breakers, Retries │
                         │ • Event Gateway: Barramento desacoplado │
                         └─────────────────────────────────────────┘
```

### 4.1. O Eixo Vertical: Vertical Slice Architecture (VSA)
* **Alta Coesão e Baixo Acoplamento:** Todo o código necessário para cumprir uma capacidade de negócio reside no mesmo diretório de fatia (`features/<nome>/`).
* **Zero Acoplamento Cruzado:** Uma fatia nunca acessa diretamente o repositório ou os modelos internos de outra fatia. A comunicação inter-fatias ocorre exclusivamente via interfaces públicas ou pelo Gateway de Eventos da camada compartilhada.
* **Facilidade de Refatoração e Escala:** Adicionar uma nova feature significa criar um novo diretório com suas próprias rotas e testes, sem tocar em fatias existentes. Se um domínio crescer a ponto de justificar extração para um serviço independente, a fatia VSA já nasce pronta para ser desmembrada com atrito zero.

### 4.2. O Eixo Horizontal Compartilhado (`core/` / `shared/`)
* Fornece a infraestrutura comum que toda fatia de domínio utiliza de maneira limpa:
  * **Conexão Resiliente de Banco:** Pool de conexões assíncrono com healthchecks periódicos e gerenciamento de transações com rollback automático em caso de falha.
  * **Sanitização de Dados:** Filtros determinísticos para limpeza de caracteres maliciosos, prevenção de injeções e normalização de payloads.
  * **Resiliência Compartilhada:** Mecanismos padronizados de Circuit Breakers (*Closed, Open, Half-Open*), Rate Limiters baseados em algoritmos robustos de janelas deslizantes e políticas de Retry com backoff exponencial e jitter estocástico.

---

## 5. O Quarteto *Sine Qua Non* Dinâmico (Os 4 Estúdios)

Toda entrega no ecossistema DEVE expor nativamente, desde o primeiro minuto e cobrindo 100% dos módulos, 4 estúdios contratuais dinâmicos:

| Estúdio | Endpoint | Finalidade Primordial | Garantia Técnica |
| :--- | :--- | :--- | :--- |
| **Swagger Studio** | `/swagger` ou `/docs` | Contratos de API REST interativos | Especificação OpenAPI 3.0 viva, totalmente tipada via Pydantic, com simulação direta de requisições e respostas de exemplo. |
| **Webhook Studio** | `/webhooks` | Gestão de eventos assíncronos | Teste, disparo e validação de assinaturas criptográficas **HMAC SHA-256** em tempo constante, histórico de disparos e reenvio de payloads com telemetria HTTP. |
| **MCP Studio** | `/mcp` | Orquestração agêntica de IA | Servidor nativo no protocolo Model Context Protocol, expondo ferramentas (tools) e recursos tipados em JSON Schema para agentes e copilotos. |
| **Guia do Utilizador** | `/docs` | Manual vivo de produto | Documentação executiva com diagramas, exemplos de autenticação, guia de onboarding e fluxos de integração para operadores e engenheiros humanos. |

---

## 6. Frente de Missão Crítica & Padrão Enterprise CTT

O projeto **CTT** consolidou o padrão de engenharia corporativa de nível bancário que agora serve como a régua de ouro do ecossistema:

* **Zero Mocks e Zero Stubs:** Proibição de stubs como `pass`, `# TODO: implementar`, `NotImplementedError` ou mocks estáticos em código de produção. Todo código é 100% funcional e testado contra banco real ou SQLite em memória nos testes.
* **Cobertura de Testes Verificada:** Baterias de testes reais executadas em pytest por ferramenta e por fatia VSA. Aprovados mais de 2.200 testes reais com taxa de sucesso de 100%.
* **Tratamento Monádico de Erros (Result Monad):** Erros de operações de infraestrutura e regras críticas não estouram exceções cegas; são encapsulados em estruturas determinísticas `Ok(data)` ou `Err(error)`, forçando o chamador a tratar todos os caminhos de falha.

---

## 7. A Tríade Canônica de Criação e Entrega

A arquitetura do ecossistema estabelece que toda aplicação de alta qualidade nasce de uma mesma fundação e alinhamento prévio, oferecendo **3 caminhos especializados de construção para o mesmo projeto**:

```
[ aidd-forge ] ────────▶ [ PRÉ-PLANO Interativo ]
(Autoridade Máxima de         (Entrevista Socrática &
 Governança e Regras)          Definição Arquitetural)
                               │
       ┌───────────────────────┼───────────────────────┐
       ▼                       ▼                       ▼
 [ FLUXO 01 ]            [ FLUXO 02 ]            [ FLUXO 03 ]
aidd-generator           aidd-factory            aidd-bridge
(Do Zero Puro)       (Motores Open-Source)     (Low-Code Desatado)
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               ▼
                          [ aidd-master ]
             (Harmonização em Monólito Modular VSA)
                               ▼
                        [ aidd-enterprise ]
                   (Blindagem SHA-256 & Resiliência)
                               ▼
                           [ aidd-ops ]
                   (Deploy VPS, sops+age, Uptime Kuma)
```

### 1. FLUXO 01 — "Do Zero Puro" (Engine: `aidd-generator`)
* **Propósito:** Desenvolvimento proprietário sob medida sem motores de terceiros.
* **Esteira:** 8 fases sequenciais (Spec formal ➔ TDD Red-Green ➔ Core VSA ➔ Quarteto ➔ Auditoria).
* **Entrega:** Código 100% nativo com controle linha a linha.

### 2. FLUXO 02 — "Motores Open-Source" (Engine: `aidd-factory`)
* **Propósito:** Alavancar o sistema sobre software livre consolidado (filas RabbitMQ/Kafka, mensageria Evolution API, bots, N8N, gateways).
* **Esteira:** Curadoria e orquestração de containers de motores reais + geração das fatias VSA de integração (clientes tipados, webhooks HMAC, tratamento de falhas).
* **Entrega:** Fatias verticais de conexão conteinerizadas operando em harmonia com os motores.

### 3. FLUXO 03 — "Low-Code & Apps Unificadas" (Engine: `aidd-bridge`)
* **Propósito:** Libertar telas e protótipos criados em plataformas visuais de IA (Lovable, v0 da Vercel, Bolt.new).
* **Esteira:** Remoção de travas de nuvem fechada (mock backends, Supabase cloud locked), reconexão ao PostgreSQL corporativo e empacotamento conteinerizado.
* **Entrega:** Frontend limpo e desacoplado pronto para se conectar ao backend VSA em VPS.

### O Funil Universal de Convergência
Todos os 3 fluxos convergem obrigatoriamente para:
1. **`aidd-master`**: Harmoniza tudo no Monólito Modular (VSA de domínio + camada horizontal compartilhada).
2. **`aidd-enterprise`**: Injeta blindagem criptográfica SHA-256, Circuit Breakers, Rate Limiting e auditoria `trace_id`.
3. **`aidd-ops`**: Provisiona a VPS via SSH com Result monad, configura segredos com `sops + age`, sobe containers Docker e ativa o monitoramento em tempo real com Uptime Kuma.

---

## 8. Governança Agêntica & Economia Extrema de Tokens

Para garantir que o assistente opere com máxima precisão, sem alucinações e com consumo mínimo de tokens:

* **Desenvolvedor no Controle Absoluto (Zero Headless):**
  * Nenhuma decisão de arquitetura é tomada de forma oculta.
  * Proibição categórica de subagentes autônomos em segundo plano sem supervisão do desenvolvedor.
  * Execução estritamente sequencial, transparente e com checkpoints de validação.
* **Pensamento Caveman (Caveman Thinking):**
  * Raciocínio interno estritamente telegráfico e abreviado em inglês técnico compacto.
  * Sem meta-deliberações, sem repetições do prompt do usuário e sem floreios.
* **Comunicação Direta e Estruturada:**
  * Respostas ao usuário sempre em português do Brasil (PT-BR), concisas e focadas em listas ou tabelas.
  * Proibição de re-resumir artefatos recém-criados ou repetir código na resposta quando o diff ou arquivo já o apresenta.
* **Grafo em Primeiro Lugar (Graph-First):**
  * Toda busca de impacto, raio de mudança ou dependências consulta primeiro o MCP `code-review-graph` (`detect_changes_tool`, `get_impact_radius_tool`, `query_graph_tool`) antes de recorrer a buscas cegas por grep ou leituras de arquivos completos.
* **Protocolo de 5 Passos para Testes de Ferramentas:**
  * 1. Auto-correção contínua de inconsistências (zero bugs tolerados).
  * 2. Commit e push das melhorias.
  * 3. Limpeza do ambiente de teste alvo.
  * 4. Execução limpa do fluxo.
  * 5. Atualização formal do relatório em `docs/teste-end-to-end/`.

---

## 9. Matriz Consolidada das 7 Ferramentas do Ecossistema

| Ferramenta | Papel Central | Entrada | Saída Primordial | Status |
| :--- | :--- | :--- | :--- | :--- |
| **`aidd-forge`** | Ditador de Governança & Regras | Repositório / Pasta base | Governança canônica, linters, pre-commit e regras universais de arquitetura e tokens | ✅ Homologado |
| **`aidd-generator`** | Fábrica Autônoma de Software | Requisitos / Especificação | Aplicação completa em 8 fases (TDD + VSA) com 1.015 testes passando e Quarteto ativo | ✅ Homologado |
| **`aidd-master`** | Arquiteto de Monólito Modular | Módulos de domínio de negócio | Fatias VSA de domínio isoladas (`features/`) conectadas à camada horizontal compartilhada | ✅ Homologado |
| **`aidd-enterprise`**| Guardião de Missão Crítica | Aplicação VSA existente | Checksums SHA-256, Circuit Breakers, Rate Limiters e trilha imutável `trace_id` | ✅ Homologado |
| **`aidd-ops`** | Orquestrador de Infra & VPS | Plano de infraestrutura | Provisionamento SSH via Result monad, cofre `sops+age`, compose de produção e Uptime Kuma | ✅ Homologado |
| **`aidd-factory`** | Integrador de Motores Open-Source | Especificação de motores livres | Fatias VSA de integração tipadas, webhooks HMAC, compose dos motores e anti-SQL injection | ✅ Homologado |
| **`aidd-bridge`** | Desacoplador de Low-Code | Código exportado Lovable/v0/Bolt | Frontend limpo desatado de nuvem fechada, conectado ao PostgreSQL VPS com OCI seguro e Quarteto | ✅ Homologado |

---

*Este Tratado constitui a Bíblia técnica definitiva do Ecossistema AIDD. Todas as implementações presentes e futuras devem reverência e conformidade estrita a estes termos.*
