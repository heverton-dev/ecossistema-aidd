# Enciclopédia & Carta Magna do Ecossistema AIDD
## Tratado Definitivo de Arquitetura, Engenharia, Cibersegurança, Agnosticismo e Governança

> **Localização:** `docs/explicacoes/CONSOLIDACAO-DECISOES-ARQUITETURA-ECOSSISTEMA.md`  
> **Status:** Tratado Canônico Soberano e Imutável  
> **Versão:** 3.2.0 (Consolidação Holística com Detalhamento por Módulos e Cards)  
> **Data de Homologação:** 17/09/2026  
> **Padrão de Referência:** Monólito Modular (VSA + Camada Horizontal), Padrão Enterprise CTT, Zero Vendor Lock-in  

---

## 1. As 10 Leis Invioláveis do Ecossistema (Preservado no Topo)

Toda linha de código, manifesto de infraestrutura, contrato de API ou diretiva agêntica dentro do ecossistema AIDD é rigorosamente subordinada a 10 leis universais:

```
+--------------------------------------------------------------------------------------------------------+
|                                  AS 10 LEIS INVIOLÁVEIS DO ECOSSISTEMA                                 |
+------------------------------+------------------------------+------------------------------------------+
| 1. Determinismo Estrito      | 2. Zero Stubs / Zero Mocks   | 3. Monólito Modular Canônico             |
| Ferramentas mecânicas, AST   | 100% funcional, tipado e     | VSA vertical de domínio + Camada         |
| e schemas; nunca vibe coding | validado com testes reais    | horizontal compartilhada (core/shared)   |
+------------------------------+------------------------------+------------------------------------------+
| 4. Cibersegurança Nativa     | 5. Agnosticismo Supremo      | 6. Quarteto Sine Qua Non                 |
| OWASP Top 10 mitigado,       | Zero vendor lock-in em nuvem,| /swagger, /webhooks, /mcp, /docs         |
| SHA-256, sops+age, HMAC      | SO, harness e modelos LLM    | dinâmicos cobrindo 100% dos módulos      |
+------------------------------+------------------------------+------------------------------------------+
| 7. Missão Crítica Enterprise | 8. Desenvolvedor no Controle | 9. Economia Extrema de Tokens            |
| Circuit Breakers, Retries,   | Zero headless, interatividade| Caveman thinking, saídas ultra-concisas  |
| Rate Limiting, trace_id      | contínua e sem agentes ocultos| e inspeção em grafo first                |
+------------------------------+------------------------------+------------------------------------------+
| 10. A Tríade Canônica de Criação                                                                       |
| FORGE (Constituição) -> PRÉ-PLANO (Intake) -> [GENERATOR | FACTORY | BRIDGE] -> MASTER -> ENTERPRISE -> OPS|
+--------------------------------------------------------------------------------------------------------+
```

---

## 2. Camada 01: Cibersegurança & Defesa em Profundidade

### Módulo 1.1: Queries Parametrizadas & Hash Argon2id (OWASP A03 / A07)
* **O Que É / O Que Faz:** Proibição de interpolação de strings em consultas SQL. Todas as queries usam prepared statements parametrizados. Senhas cifradas com Argon2id/bcrypt com salt individual resistente a ataques por GPU.
* **Gate Verificador:** `G_ECOSSISTEMA_INTEGRIDADE`
* **O Que Entrega:** Zero SQL Injection e proteção contra ataques de dicionário e quebra de hashes vazados.

### Módulo 1.2: HMAC SHA-256 em Tempo Constante (Anti-Timing Attacks)
* **O Que É / O Que Faz:** Validação estrita de assinaturas criptográficas de webhooks e tokens usando a função `hmac.compare_digest`, eliminando vulnerabilidades de temporização side-channel.
* **Gate Verificador:** `G_FACTORY_VSA` e `G_BRIDGE_VSA_COMPAT`
* **O Que Entrega:** Comunicação assíncrona entre sistemas matematicamente inviolável.

### Módulo 1.3: Cofre Assimétrico sops + age (Zero Plain-Text Secrets)
* **O Que É / O Que Faz:** Criptografia de variáveis de ambiente com curva elíptica X25519. Nenhuma chave de API ou senha trafega em texto claro no git. Chaves privadas isoladas e deciframento em memória.
* **Gate Verificador:** `G_OPS_SSH` e `G_BRIDGE_VENDOR_LOCKIN`
* **O Que Entrega:** Repositório seguro contra vazamento involuntário de credenciais de produção.

### Módulo 1.4: Blindagem SHA-256 Anti-Tampering
* **O Que É / O Que Faz:** Checksums estritos de todos os templates e arquivos de segurança enterprise. Se um único byte for adulterado sem autorização, a esteira é bloqueada com Exit 1 imediato.
* **Gate Verificador:** `G_ENTERPRISE_SHA`
* **O Que Entrega:** Integridade verificável do código contra injeção maliciosa em tempo de build.

### Módulo 1.5: Trilha de Auditoria com trace_id & Ofuscação (LGPD/GDPR)
* **O Que É / O Que Faz:** Propagação universal do header `X-Trace-Id` em requisições, logs e eventos assíncronos. Mascaramento automático de dados pessoais identificáveis (PII) antes da gravação de logs.
* **Gate Verificador:** `G_ENTERPRISE_TESTS`
* **O Que Entrega:** Rastreabilidade completa de auditoria em conformidade com as leis de proteção de dados.

### Módulo 1.6: Hadolint, Headers OWASP & Usuário Non-Root
* **O Que É / O Que Faz:** Auditoria determinística de Dockerfiles via Hadolint, execução obrigatória como `USER appuser` e injeção de headers defensivos no Nginx (CSP, HSTS, X-Frame-Options DENY).
* **Gate Verificador:** `G_HADOLINT` e `G_BRIDGE_DOCKER_OCI`
* **O Que Entrega:** Containers OCI minimalistas com superfície de ataque reduzida.

---

## 3. Camada 02: Arquitetura de Software — Monólito Modular Canônico

### Módulo 2.1: Fatias Verticais de Domínio (VSA Eixo Vertical)
* **O Que É / O Que Faz:** Isolamento de cada regra de negócio em `features/<dominio>/`, contendo rotas, serviços puros, repositórios parametrizados, schemas Pydantic e testes de integração próprios.
* **Gate Verificador:** `G_FACTORY_VSA`
* **O Que Entrega:** Coesão máxima por domínio sem acoplamento espaguete entre módulos.

### Módulo 2.2: Camada Compartilhada (Eixo Horizontal `core/` / `shared/`)
* **O Que É / O Que Faz:** Fornece serviços transversais padronizados consumidos por todas as fatias: pool assíncrono de banco de dados, sanitização global, circuit breakers e middlewares unificados.
* **Gate Verificador:** `G_DRIFT_NUCLEO_COMPARTILHADO`
* **O Que Entrega:** Reuso sem duplicação de infraestrutura crítica.

### Módulo 2.3: Roteador Central Declarativo
* **O Que É / O Que Faz:** Registro unificado de endpoints onde novas fatias conectam-se de forma declarativa, garantindo prefixos semânticos padronizados e documentação automática.
* **Gate Verificador:** `G_ECOSSISTEMA_INTEGRIDADE`
* **O Que Entrega:** API consistente sem rotas órfãs ou conflitos de endpoints.

### Módulo 2.4: Gateway de Eventos Desacoplado
* **O Que É / O Que Faz:** Barramento de eventos assíncronos para comunicação inter-fatias. Fatias nunca chamam o banco de dados de outras fatias diretamente.
* **Gate Verificador:** `G_FACTORY_VSA`
* **O Que Entrega:** Arquitetura limpa que permite extrair fatias para microsserviços futuros com atrito zero.

---

## 4. Camada 03: Engenharia de Software & Qualidade Industrial

### Módulo 3.1: Zero Stubs e Zero Mocks
* **O Que É / O Que Faz:** Proibição de stubs (`pass`, `NotImplementedError`, `# TODO`) e mocks estáticos em código de produção. 100% das funções possuem implementação real.
* **Gate Verificador:** `G_TESTES_REAIS`
* **O Que Entrega:** Software entregue pronto para operação real em produção.

### Módulo 3.2: TDD Red-Green Rigoroso
* **O Que É / O Que Faz:** Escrita de testes de integração e unitários antes da implementação da lógica de negócio, garantindo que o código nasça validado.
* **Gate Verificador:** `G_GENERATOR_TESTES`
* **O Que Entrega:** Mais de 2.200 testes reais passando em 100% das ferramentas do ecossistema.

### Módulo 3.3: Tratamento Determinístico de Erros (Result Monad)
* **O Que É / O Que Faz:** Encapsulamento de operações de risco em estruturas `Ok(valor)` ou `Err(erro)`, forçando o chamador a tratar explicitamente todos os caminhos de falha.
* **Gate Verificador:** `G_OPS_SSH`
* **O Que Entrega:** Resiliência extrema contra exceções não tratadas em runtime.

### Módulo 3.4: Pinning com Hash SHA-256
* **O Que É / O Que Faz:** Fixação estrita de dependências em `requirements.txt` e `package.json` com versão exata e hash criptográfico.
* **Gate Verificador:** `G_DEPENDENCIAS_PIN_HASH`
* **O Que Entrega:** Reprodutibilidade de builds garantida em qualquer máquina ou pipeline CI/CD.

---

## 5. Camada 04: Universalidade & Agnosticismo Supremo

### Módulo 4.1: Nuvem & Infraestrutura (Zero Cloud Lock-in)
* **O Que É / O Que Faz:** Infraestrutura baseada em padrões abertos: Linux, Docker Compose, PostgreSQL e Nginx. Roda em qualquer VPS (Hetzner, AWS, GCP, DigitalOcean, bare-metal).
* **Gate Verificador:** `G_INFRA_COMPOSE`
* **O Que Entrega:** Migração entre provedores em menos de 10 minutos sem alterar código.

### Módulo 4.2: Sistema Operacional (Windows, Linux & macOS)
* **O Que É / O Que Faz:** Caminhos normalizados com `pathlib`, fins de linha `LF` forçados em git e scripts polimórficos testados nos 3 sistemas operacionais.
* **Gate Verificador:** `G_ECOSSISTEMA_INTEGRIDADE`
* **O Que Entrega:** Interoperabilidade universal para equipes distribuídas.

### Módulo 4.3: Multi-Harness de IA Sincronizado
* **O Que É / O Que Faz:** Sincronização contínua de regras canônicas entre Claude Desktop, Cursor, Gemini Antigravity, Roo Code e Windsurf a partir do `AGENTS.md` soberano.
* **Gate Verificador:** `G_HARNESS_COMPAT`
* **O Que Entrega:** O agente opera com o mesmo rigor e diretivas em qualquer ferramenta de IA.

### Módulo 4.4: Modelos LLM & Protocolo Aberto MCP
* **O Que É / O Que Faz:** Ferramentas expostas através do padrão aberto Model Context Protocol, desacopladas de SDKs proprietários.
* **Gate Verificador:** `G_COMPONENTE_AGNOSTICO`
* **O Que Entrega:** Portabilidade total entre Claude, GPT, Gemini, DeepSeek ou modelos locais.

---

## 6. Camada 05: O Quarteto Sine Qua Non Dinâmico

### Módulo 5.1: Swagger Studio (`/swagger`)
* **O Que É / O Que Faz:** Documentação interativa OpenAPI 3.0 dinamicamente gerada a partir dos schemas tipados, permitindo testes imediatos no navegador.
* **Gate Verificador:** `G_FACTORY_VSA`
* **O Que Entrega:** Especificação viva de rotas sem documentação manual defasada.

### Módulo 5.2: Webhook Studio (`/webhooks`)
* **O Que É / O Que Faz:** Gestão, teste, reenvio e simulação de disparos de webhooks com assinatura HMAC SHA-256 e auditoria de status HTTP.
* **Gate Verificador:** `G_BRIDGE_VSA_COMPAT`
* **O Que Entrega:** Integração assíncrona robusta e rastreável.

### Módulo 5.3: MCP Studio (`/mcp`)
* **O Que É / O Que Faz:** Servidor Model Context Protocol nativo que expõe as capacidades do sistema como tools em JSON Schema para consumo por agentes de IA.
* **Gate Verificador:** `G_FACTORY_VSA`
* **O Que Entrega:** Sistema orquestrável por copilotos inteligentes desde o Dia Zero.

### Módulo 5.4: Guia do Utilizador (`/docs`)
* **O Que É / O Que Faz:** Manual vivo do utilizador contendo arquitetura, exemplos práticos de onboarding, catálogo de endpoints e orientações de suporte.
* **Gate Verificador:** `G_BRIDGE_VSA_COMPAT`
* **O Que Entrega:** Onboarding imediato de novos engenheiros e clientes.

---

## 7. Camada 06: Infraestrutura, DevOps & Observabilidade

### Módulo 6.1: Provisionamento Determinístico via SSH
* **O Que É / O Que Faz:** Conexão remota segura e execução idempotente de comandos de infraestrutura orquestrados pelo gate `G_OPS_SSH`.
* **Gate Verificador:** `G_OPS_SSH`
* **O Que Entrega:** Deploy automatizado e seguro sem necessidade de comandos manuais no terminal da VPS.

### Módulo 6.2: Docker Compose de Produção
* **O Que É / O Que Faz:** Manifestos Compose com redes privadas internas, volumes persistentes e limites explícitos de memória e CPU.
* **Gate Verificador:** `G_INFRA_COMPOSE`
* **O Que Entrega:** Isolamento seguro entre serviços periféricos, aplicação e banco.

### Módulo 6.3: Proxy Reverso Traefik/Nginx com Let's Encrypt
* **O Que É / O Que Faz:** Roteamento de tráfego com emissão automática de certificados SSL/TLS, terminação segura e cabeçalhos defensivos injetados.
* **Gate Verificador:** `G_BRIDGE_DOCKER_OCI`
* **O Que Entrega:** Tráfego 100% criptografado com renovação automática de certificados.

### Módulo 6.4: Uptime Kuma & Observabilidade Ativa
* **O Que É / O Que Faz:** Monitoramento contínuo de disponibilidade e latência dos endpoints de healthcheck da aplicação, com alertas automatizados.
* **Gate Verificador:** `G_OPS_OBSERVABILITY`
* **O Que Entrega:** Visibilidade em tempo real do SLA e da saúde dos containers em produção.

---

## 8. Camada 07: Governança Agêntica & Economia Extrema de Tokens

### Módulo 7.1: Zero Headless (Desenvolvedor no Controle)
* **O Que É / O Que Faz:** Execuções estritamente sequenciais, transparentes e interativas. Proibição categórica de subagentes ocultos em background.
* **Gate Verificador:** `G_ZERO_HEADLESS`
* **O Que Entrega:** O desenvolvedor mantém 100% do controle decisório a cada passo.

### Módulo 7.2: Caveman Thinking (Raciocínio Enxuto)
* **O Que É / O Que Faz:** Raciocínio interno telegráfico compacto em inglês técnico, eliminando deliberações prolixas e repetições do prompt.
* **Regra Canônica:** `AGENTS.md Core Constraints`
* **O Que Entrega:** Redução severa de latência de resposta e consumo de tokens.

### Módulo 7.3: Graph-First com `code-review-graph`
* **O Que É / O Que Faz:** Análise de blast radius e impacto via grafo de conhecimento antes de varreduras por grep ou leitura de arquivos inteiros.
* **Regra Canônica:** `AGENTS.md Seção 5`
* **O Que Entrega:** Economia de mais de 60% de tokens de contexto por tarefa.

### Módulo 7.4: Saídas Concisas em Listas e Tabelas
* **O Que É / O Que Faz:** Respostas diretas ao usuário em português (PT-BR), proibindo re-resumos de artefatos criados ou repetição de código no chat.
* **Regra Canônica:** `RULE[user_global]`
* **O Que Entrega:** Interação técnica objetiva e sem ruído.

---

## 9. Camada 08: A Tríade Canônica de Criação

### Módulo 8.1: FLUXO 01 — Do Zero Puro (`aidd-generator`)
* **O Que É / O Que Faz:** Construção proprietária sob medida guiada por esteira determinística de 8 fases (Spec formal -> TDD Red-Green -> Core VSA -> Quarteto).
* **Gate Verificador:** `G_GENERATOR_*`
* **O Que Entrega:** Aplicação 100% nativa com controle total sobre cada linha de código.

### Módulo 8.2: FLUXO 02 — Motores Open-Source (`aidd-factory`)
* **O Que É / O Que Faz:** Alavancagem sobre software livre consolidado (filas, bots, mensageria). Sobe containers dos motores e gera fatias VSA de integração com webhooks HMAC seguros.
* **Gate Verificador:** `G_FACTORY_*`
* **O Que Entrega:** Velocidade de entrega aproveitando motores maduros da comunidade.

### Módulo 8.3: FLUXO 03 — Low-Code Desatado (`aidd-bridge`)
* **O Que É / O Que Faz:** Libertação e empacotamento de interfaces do Lovable, v0 ou Bolt. Extirpação de travas de nuvem fechada, conexão ao PostgreSQL corporativo e conteinerização OCI.
* **Gate Verificador:** `G_BRIDGE_*`
* **O Que Entrega:** Reaproveitamento de protótipos visuais em produção real sem vendor lock-in.

### Módulo 8.4: Funil de Convergência Universal
* **O Que É / O Que Faz:** Todos os 3 fluxos convergem obrigatoriamente para `aidd-master` (Monólito Modular VSA) -> `aidd-enterprise` (SHA-256 + Resiliência) -> `aidd-ops` (Deploy VPS, sops+age e Uptime Kuma).
* **Gate Verificador:** Todos os Quality Gates do Ecossistema
* **O Que Entrega:** Solução corporativa final no **Padrão CTT**, independente do fluxo de origem.

---

## 10. Funcionamento Passo a Passo dos 3 Fluxos de Criação

### FLUXO 01 (Do Zero Puro): `FORGE -> PRÉ-PLANO -> GENERATOR -> MASTER -> ENTERPRISE -> OPS`
* **Passo 1 (aidd-forge):** Injeta governança, regras de linting, pre-commit hooks e o `AGENTS.md` canônico.
* **Passo 2 (PRÉ-PLANO):** Realiza entrevista interativa socrática para coletar requisitos de negócio e gera o `PLANO-MESTRE.json`.
* **Passo 3 (aidd-generator):** Dispara a fábrica autônoma em 8 fases determinísticas (Spec formal -> TDD Red-Green -> Core VSA -> Quarteto).
* **Passo 4 (aidd-master):** Organiza o código gerado em Monólito Modular (Fatias VSA em `features/` conectadas à Camada Horizontal `core/` / `shared/`).
* **Passo 5 (aidd-enterprise):** Audita integridade por hash SHA-256 e injeta Circuit Breakers, Rate Limiting distribuído e trilha imutável `trace_id`.
* **Passo 6 (aidd-ops):** Provisiona a VPS via SSH determinístico com Result Monad, configura cofre `sops+age` e ativa observabilidade no Uptime Kuma 24/7.
* **Linha de Chegada:** Aplicação proprietária 100% testada e funcional no **Padrão CTT**, com Swagger, Webhooks HMAC, MCP Studio e Docs dinâmicos.

---

### FLUXO 02 (Motores Open-Source): `FORGE -> PRÉ-PLANO -> FACTORY -> MASTER -> ENTERPRISE -> OPS`
* **Passo 1 (aidd-forge):** Estabelece a fundação inquebrável de regras e governança do repositório.
* **Passo 2 (PRÉ-PLANO):** Identifica os requisitos funcionais e mapeia quais motores livres (filas, bots, mensageria) devem compor o sistema.
* **Passo 3 (aidd-factory):** Orquestra os containers de software livre (PostgreSQL, Redis, RabbitMQ, Evolution API) e gera as Fatias Verticais VSA de integração.
* **Passo 4 (aidd-master):** Harmoniza as fatias de conexão periféricas no Monólito Modular da empresa, evitando acoplamento espaguete.
* **Passo 5 (aidd-enterprise):** Injeta resiliência bancária e valida integridade criptográfica.
* **Passo 6 (aidd-ops):** Sobe a stack unificada de containers na VPS com rede isolada, SSL automático e monitoramento contínuo.
* **Linha de Chegada:** Sistema corporativo de alta velocidade alavancado em motores livres, seguro e operando em produção com o Quarteto Sine Qua Non.

---

### FLUXO 03 (Low-Code / Apps Unificadas): `FORGE -> PRÉ-PLANO -> BRIDGE -> MASTER -> ENTERPRISE -> OPS`
* **Passo 1 (aidd-forge):** Blinda o repositório com regras de arquitetura e convenções de código limpo.
* **Passo 2 (PRÉ-PLANO):** Recebe o código exportado das plataformas low-code (Lovable, v0 da Vercel, Bolt.new).
* **Passo 3 (aidd-bridge):** Executa o pipeline de libertação: extirpa amarras de nuvem fechada, converte Supabase em PostgreSQL corporativo (`init-db.sql`) e gera Dockerfile OCI seguro.
* **Passo 4 (aidd-master):** Conecta o frontend desatado às fatias de backend VSA correspondentes.
* **Passo 5 (aidd-enterprise):** Aplica blindagem de missão crítica e auditoria estrita.
* **Passo 6 (aidd-ops):** Empacota e entrega a solução na VPS corporativa com banco PostgreSQL dedicado.
* **Linha de Chegada:** Frontend de alta fidelidade resgatado de ferramentas de IA, operando em VPS corporativa sem vendor lock-in e com o Quarteto Sine Qua Non.

---

## 11. Árvore Física Canônica do Projeto (Padrão CTT)

A materialização em disco de qualquer aplicação gerada no ecossistema organiza-se em 4 Zonas Físicas bem delimitadas:

* **Zona 1: Horizontal (`src/core/`)** — Infraestrutura transversal compartilhada: conexões com banco, cofre de segredos, Circuit Breakers e telemetria `trace_id`.
* **Zona 2: Vertical VSA (`src/features/`)** — Fatias verticais autônomas. Cada módulo tem rotas, regras, repositórios e testes próprios, sem dependências cruzadas.
* **Zona 3: Contratual (`quarteto_sine_qua_non/`)** — Os 4 estúdios dinâmicos vivos: OpenAPI 3.0 (`/swagger`), HMAC SHA-256 (`/webhooks`), Model Context Protocol (`/mcp`) e Guia do Usuário (`/docs`).
* **Zona 4: Infra & Ops (`infra/`)** — Containers OCI não-root (Hadolint), proxy Nginx blindado por OWASP e segredos cifrados com `sops+age`.

### Estrutura Visual dos Diretórios:
```text
projeto-corporativo/
├── src/
│   ├── core/                      # [Núcleo Horizontal Compartilhado]
│   │   ├── database.py            # Pool assíncrono de conexões PostgreSQL
│   │   ├── security.py            # Sanitização de inputs, hashes e secrets
│   │   ├── resilience.py          # Circuit Breakers e Rate Limiters
│   │   └── telemetry.py           # Logs estruturados e injeção do trace_id
│   ├── features/                  # [Fatias Verticais VSA de Domínio]
│   │   ├── encomendas/            # Fatia vertical 1 (rotas, regras, repositórios, testes)
│   │   ├── frotas/                # Fatia vertical 2
│   │   └── roteirizacao/          # Fatia vertical 3
│   └── server.py                  # Roteador central declarativo da aplicação
├── quarteto_sine_qua_non/         # [Os 4 Estúdios Contratuais Vivos]
│   ├── swagger_spec.json          # Contratos REST OpenAPI 3.0 (/swagger)
│   ├── webhooks_contract.json     # Gestão de eventos com HMAC SHA-256 (/webhooks)
│   ├── mcp_studio.json            # Catálogo de tools MCP para agentes (/mcp)
│   └── USER_GUIDE.md              # Manual vivo de produto para equipes humanas (/docs)
├── infra/                         # [Infraestrutura como Código - aidd-ops]
│   ├── docker-compose.yml         # Orquestração de containers de produção
│   ├── Dockerfile                 # Multi-stage build OCI seguro (USER appuser)
│   ├── nginx.conf                 # Proxy reverso com headers defensivos OWASP
│   └── secrets.enc.yaml           # Cofre criptografado com sops + age
├── tests/                         # Suíte de regressão E2E e testes globais
├── requirements.txt               # Dependências pinadas com hashes criptográficos SHA-256
└── AGENTS.md                      # Diretivas soberanas de governança e regras do projeto
```

### Dicionário de Pastas & Responsabilidades:

| Diretório Físico | Papel Arquitetural | Quality Gate Verificador |
| :--- | :--- | :--- |
| `src/core/` | Centraliza bibliotecas transversais (DB, segurança, telemetria) | `G_DRIFT_NUCLEO_COMPARTILHADO` |
| `src/features/{dominio}/` | Encapsula cada fatia de negócio isolada (VSA) | `G_TESTES_REAIS & G_FACTORY_VSA` |
| `quarteto_sine_qua_non/` | Exposição contratual dinâmica dos 4 pilares | `G_BRIDGE_VSA_COMPAT` |
| `infra/` | Configuração de containers OCI, proxy reverso e chaves | `G_HADOLINT & G_INFRA_COMPOSE` |
| `AGENTS.md & requirements.txt` | Regras invioláveis em código e trava de supply chain por SHA-256 | `G_DEPENDENCIAS_PIN_HASH & G_ECOSSISTEMA_INTEGRIDADE` |

---

## 12. Quadro de Homologação das 7 Ferramentas do Ecossistema

| Ferramenta | Papel Central na Tríade | Status | Entregável Consolidado |
| :--- | :--- | :--- | :--- |
| **`aidd-forge`** | Ditador de Governança e Regras | Homologado | Repositório blindado, linters, pre-commit e regras de arquitetura e tokens |
| **`aidd-generator`** | Fábrica Autônoma (FLUXO 01) | Homologado | Aplicação completa em 8 fases (TDD + VSA) com 1.015 testes passando |
| **`aidd-master`** | Arquiteto de Monólito Modular | Homologado | Fatias VSA de domínio (`features/`) conectadas à camada horizontal compartilhada |
| **`aidd-enterprise`**| Guardião de Missão Crítica | Homologado | Checksums SHA-256, Circuit Breakers, Rate Limiters e trilha `trace_id` |
| **`aidd-ops`** | Orquestrador de Infra & VPS | Homologado | Provisionamento SSH Result monad, cofre `sops+age`, compose e Uptime Kuma |
| **`aidd-factory`** | Integrador Open-Source (FLUXO 02) | Homologado | Fatias VSA de conexão, webhooks HMAC seguros e orquestração de motores |
| **`aidd-bridge`** | Desacoplador Low-Code (FLUXO 03) | Homologado | Frontend limpo sem vendor lock-in para PostgreSQL VPS (45 testes passando) |

---

*Este documento estabelece o Tratado Canônico Soberano do Ecossistema AIDD, detalhando cada módulo, seus Quality Gates e entregas concretas.*
