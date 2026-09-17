# Enciclopédia & Carta Magna do Ecossistema AIDD
## Tratado Definitivo de Arquitetura, Engenharia, Cibersegurança, Agnosticismo e Governança

> **Localização:** `docs/explicacoes/CONSOLIDACAO-DECISOES-ARQUITETURA-ECOSSISTEMA.md`  
> **Status:** Tratado Canônico Soberano e Imutável  
> **Versão:** 3.1.0 (Consolidação Holística por Camadas de Engenharia)  
> **Data de Homologação:** 17/09/2026  
> **Padrão de Referência:** Monólito Modular (VSA + Camada Horizontal), Padrão Enterprise CTT, Zero Vendor Lock-in  

---

## 1. O Decálogo das Leis Invioláveis do Ecossistema

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

### 2.1. O Que É
Uma estrutura proativa de proteção multicamada que neutraliza ameaças desde a modelagem de entidades até o tráfego de rede e a execução em containers, tratando a segurança como requisito funcional inegociável de nível bancário.

### 2.2. O Que Tem Dentro
* **Mitigação do OWASP Top 10:**
  * Queries parametrizadas obrigatórias (*prepared statements*) em 100% dos repositórios (`repositories.py`), blindando a aplicação contra SQL Injection (A03:2021).
  * Autenticação com hash Argon2id / bcrypt resistente a força bruta com salt individual.
  * Validação estrita de assinaturas de Webhooks com HMAC SHA-256 via `hmac.compare_digest` para anular ataques de temporização (*timing attacks*).
* **Cofre de Segredos `sops + age`:**
  * Criptografia assimétrica de curva elíptica X25519 para variáveis sensíveis (`secrets.enc.yaml`).
  * Zero credenciais em texto claro no repositório git e deciframento estritamente em memória.
* **Integridade SHA-256 Anti-Tampering:**
  * Manifestos de checksums para templates e módulos enterprise que barram adulterações indevidas.
* **Proteção de Headers HTTP:**
  * Injeção forçada de `Content-Security-Policy`, `Strict-Transport-Security (HSTS)`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` e CORS restritivo por whitelist.
* **Segurança de Containers (Hadolint):**
  * Execução em usuário não-privilegiado (`USER appuser`), imagens base Alpine/Distroless e portas acima de 1024.

### 2.3. Quality Gates Associados
* `G_ENTERPRISE_SHA`: Audita hashes SHA-256 e bloqueia templates alterados sem autorização.
* `G_HADOLINT`: Bloqueia Dockerfiles com violações de boas práticas OCI ou execução como root.
* `G_BRIDGE_VENDOR_LOCKIN`: Detecta e bloqueia credenciais ou URLs proprietárias expostas.
* `G_BRIDGE_DOCKER_OCI`: Audita cabeçalhos OWASP no Nginx e multi-stage no Dockerfile.

### 2.4. O Que Entrega na Prática
* **No Ecossistema:** Repositório protegido contra vazamento acidental de chaves e blindado contra sabotagem de código.
* **Nas Aplicações Corporativas:** Aplicação em conformidade com normas bancárias e exigências de privacidade da LGPD e GDPR, tolerante a tentativas de injeção e ataques de canal lateral.

---

## 3. Camada 02: Arquitetura de Software — Monólito Modular Canônico

### 3.1. O Que É
Um modelo de arquitetura de alta coesão e baixo acoplamento que elimina o código espaguete das camadas horizontais dispersas e o custo operacional prematuro de microsserviços, estruturando a aplicação em Fatias Verticais de Domínio (VSA) combinadas a uma Camada Horizontal Compartilhada.

### 3.2. O Que Tem Dentro
* **Eixo Vertical — Fatias de Domínio (VSA):**
  * Diretórios autônomos em `features/<dominio>/` contendo `routes.py`, `services.py`, `repositories.py` (parametrizados), `models.py` e suíte própria de testes.
  * Zero dependências circulares: fatias nunca importam regras internas umas das outras diretamente.
* **Eixo Horizontal Compartilhado (`core/` / `shared/`):**
  * Pool assíncrono de banco de dados e controle de transações.
  * Gestor de segredos e sanitização de payloads.
  * Barramento interno de eventos para comunicação desacoplada inter-fatias.
  * Circuit Breakers e Rate Limiters compartilhados.
* **Roteador Unificado:** Registro determinístico e centralizado de todas as rotas e contratos da aplicação.

### 3.3. Quality Gates Associados
* `G_DRIFT_NUCLEO_COMPARTILHADO`: Audita e sincroniza o núcleo compartilhado entre master e enterprise.
* `G_FACTORY_VSA`: Garante que todo serviço ou motor integrado nasça obrigatoriamente como uma fatia vertical VSA.
* `G_BRIDGE_VSA_COMPAT`: Assegura que o código desatado de low-code respeite a estrutura modular de fatias.

### 3.4. O Que Entrega na Prática
* **No Ecossistema:** Estrutura clara e previsível onde agentes e desenvolvedores navegam sem ambiguidade.
* **Nas Aplicações Corporativas:** Código limpo onde uma feature pode ser alterada, testada ou extraída para um microsserviço independente no futuro sem causar quebras em outras áreas do sistema.

---

## 4. Camada 03: Engenharia de Software & Qualidade Industrial

### 4.1. O Que É
A disciplina de desenvolvimento que substitui a intuição e o "vibe coding" por determinismo estrito, validação mecânica por AST, TDD Red-Green e execução massiva de testes reais automatizados.

### 4.2. O Que Tem Dentro
* **Zero Stubs e Zero Mocks:** Código de produção 100% funcional. Proibição de stubs (`pass`, `NotImplementedError`) e mocks estáticos em produção.
* **TDD Red-Green Rigoroso:** Testes de integração e unitários escritos previamente contra SQLite em memória ou PostgreSQL antes da escrita da lógica de negócio.
* **Tratamento Monádico de Erros (Result Monad):** Operações críticas encapsuladas em estruturas determinísticas `Ok(data)` ou `Err(error)`.
* **Tipagem Estática Total:** Validação em tempo de execução via Pydantic e type hints em Python e TypeScript.
* **Fixação Criptográfica de Dependências:** `requirements.txt` com pinning estrito de versão e hashes SHA-256 de pacotes.

### 4.3. Quality Gates Associados
* `G_TESTES_REAIS`: Execução obrigatória de todos os testes unitários e integrados em todas as 7 ferramentas (mais de 2.200 testes reais com 100% de sucesso).
* `G_ECOSSISTEMA_INTEGRIDADE`: Análise sintática e AST em scripts, comandos e skills para evitar regressões.
* `G_DEPENDENCIAS_PIN_HASH`: Bloqueia qualquer dependência que não possua hash criptográfico exato.

### 4.4. O Que Entrega na Prática
* **No Ecossistema:** Confiança determinística em cada commit; nenhum bug entra na branch principal sem ser barrado na esteira.
* **Nas Aplicações Corporativas:** Aplicação robusta que entra em produção com 100% de cobertura verificada das regras de negócio e estabilidade contínua.

---

## 5. Camada 04: Universalidade & Agnosticismo Supremo

### 5.1. O Que É
A garantia de soberania tecnológica que protege o cliente e a empresa contra vendor lock-in, assegurando que o código pode rodar em qualquer nuvem, sistema operacional, harness de IA ou modelo de linguagem.

### 5.2. O Que Tem Dentro
* **Cloud-Agnostic:** Infraestrutura baseada em Linux, Docker Compose, PostgreSQL e Traefik/Nginx. Roda em qualquer VPS (Hetzner, AWS, GCP, DigitalOcean, bare-metal).
* **OS-Agnostic:** Manipulação canônica de caminhos com `pathlib.Path`, normalização de fins de linha `LF` e comandos polimórficos para Windows, Linux e macOS.
* **Multi-Harness:** Paridade total entre Claude Desktop, Cursor, Gemini Antigravity, Roo Code e Windsurf.
* **Model-Agnostic:** Exposição e consumo de ferramentas através do protocolo aberto Model Context Protocol (MCP).

### 5.3. Quality Gates Associados
* `G_HARNESS_COMPAT`: Audita a sincronização de regras e ferramentas em todos os perfis multi-harness.
* `G_COMPONENTE_AGNOSTICO`: Audita componentes transversais contra o manifesto universal.
* `G_BRIDGE_VENDOR_LOCKIN`: Garante que nenhum código gerado dependa de nuvens proprietárias fechadas.

### 5.4. O Que Entrega na Prática
* **No Ecossistema:** Liberdade para cada engenheiro utilizar o sistema operacional e a interface de IA de sua preferência.
* **Nas Aplicações Corporativas:** Redução drástica de custos de infraestrutura (VPS acessível em vez de serviços gerenciados caros) e portabilidade total em minutos.

---

## 6. Camada 05: O Quarteto Sine Qua Non Dinâmico

### 6.1. O Que É
O contrato de quatro pilares dinâmicos que garante que nenhuma aplicação gerada no ecossistema seja entregue sem documentação viva, simuladores interativos e interfaces para inteligência artificial.

### 6.2. O Que Tem Dentro
* **Swagger Studio (`/swagger`):** Contratos OpenAPI 3.0 dinâmicos, tipados e interativos.
* **Webhook Studio (`/webhooks`):** Gestão, teste e disparo de eventos com validação criptográfica HMAC SHA-256 em tempo constante.
* **MCP Studio (`/mcp`):** Servidor nativo Model Context Protocol para consumo por agentes e LLMs.
* **Guia do Utilizador (`/docs`):** Manuais vivos com fluxos de onboarding, exemplos de chamadas e documentação para desenvolvedores.

### 6.3. Quality Gates Associados
* `G_FACTORY_VSA`: Audita se novas integrações expõem automaticamente os 4 estúdios.
* `G_BRIDGE_VSA_COMPAT`: Audita a integridade dos 4 contratos gerados no empacotamento de low-code.

### 6.4. O Que Entrega na Prática
* **No Ecossistema:** Padronização absoluta de contratos e ferramentas entre módulos.
* **Nas Aplicações Corporativas:** Uma plataforma pronta para integração, onde clientes externos, operadores humanos e copilotos de IA interagem com o sistema sem fricção.

---

## 7. Camada 06: Infraestrutura, DevOps & Observabilidade

### 7.1. O Que É
A esteira de automação operacional que provisiona servidores remotos, isola ambientes em containers seguros, gerencia certificados SSL e monitora a saúde dos serviços em tempo real.

### 7.2. O Que Tem Dentro
* **Deploy Remoto via SSH Determinístico:** Execução remota orquestrada pelo gate `G_OPS_SSH` com idempotência e tratamento monádico.
* **Docker Compose de Produção:** Isolamento de redes internas, volumes persistentes e healthchecks de serviços.
* **Proxy Reverso & SSL:** Configuração automática de certificados Let's Encrypt via Traefik ou Nginx.
* **Observabilidade Contínua:** Monitoramento de disponibilidade e tempo de resposta via Uptime Kuma com alertas automatizados.

### 7.3. Quality Gates Associados
* `G_OPS_SSH`: Valida a conectividade remota e execução segura de comandos na VPS.
* `G_INFRA_COMPOSE`: Valida sintaxe e integridade de manifestos docker-compose e scripts init-db.
* `G_HADOLINT`: Garante conformidade de segurança e boas práticas em Dockerfiles.

### 7.4. O Que Entrega na Prática
* **No Ecossistema:** Comandos determinísticos de deploy e manutenção de servidores.
* **Nas Aplicações Corporativas:** Infraestrutura estável e segura operando em produção, com telemetria 24/7 e tempo de inatividade minimizado.

---

## 8. Camada 07: Governança Agêntica & Economia de Tokens

### 8.1. O Que É
O conjunto de normas comportamentais que governa o assistente de IA, garantindo precisão cirúrgica, consumo consciente de contexto e supervisão contínua pelo desenvolvedor.

### 8.2. O Que Tem Dentro
* **Desenvolvedor no Controle (Zero Headless):** Proibição de subagentes ocultos em segundo plano. Execuções estritamente sequenciais e transparentes.
* **Caveman Thinking:** Raciocínio interno em inglês telegráfico compacto, sem repetições e sem meta-deliberações.
* **Comunicação Direta:** Saídas concisas em português (PT-BR), sem re-resumir artefatos ou duplicar diffs no chat.
* **Graph-First:** Inspeção de dependências e blast radius via MCP `code-review-graph` antes de buscas em texto livre.
* **Orçamento de Contexto:** Diretivas mantidas sob 2.000 tokens de contexto ativo.

### 8.3. Quality Gates Associados
* `G_ZERO_HEADLESS`: Impede qualquer execução que opere de forma oculta sem interação do usuário.
* `G_CLI_HELP_CONSISTENCIA`: Audita flags e ajuda de comandos para prevenir comandos quebrados.

### 8.4. O Que Entrega na Prática
* **No Ecossistema:** Redução drástica do custo e latência de inferência, com foco total na resolução do problema.
* **Nas Aplicações Corporativas:** Código gerado sem alucinações, com total alinhamento às decisões arquiteturais aprovadas.

---

## 9. Camada 08: A Tríade Canônica de Criação

### 9.1. O Que É
A taxonomia de partida que resolve a gênese do software, permitindo derivar a mesma ideia de negócio em três caminhos industriais distintos que convergem obrigatoriamente para a mesma linha de chegada de qualidade.

### 9.2. O Que Tem Dentro
* **`aidd-forge`:** Ditador supremo da governança, linters e regras no Dia Zero.
* **`PRÉ-PLANO`:** Intake interativo gerador do `PLANO-MESTRE.json`.
* **FLUXO 01 (Do Zero Puro):** Engine `aidd-generator` (8 fases determinísticas, TDD Red-Green).
* **FLUXO 02 (Motores Open-Source):** Engine `aidd-factory` (curadoria e orquestração de motores livres + VSA).
* **FLUXO 03 (Low-Code Desatado):** Engine `aidd-bridge` (libertação de protótipos de Lovable/v0/Bolt para PostgreSQL VPS).
* **Funil de Convergência:** Todos os fluxos convergem em `aidd-master` -> `aidd-enterprise` -> `aidd-ops`.

### 9.3. Quality Gates Associados
* `G_FORGE_*`: Valida a fundação de governança do repositório.
* `G_GENERATOR_*`: Valida as 8 fases da fábrica autônoma.
* `G_FACTORY_*`: Valida a integração de motores periféricos em fatias VSA.
* `G_BRIDGE_*`: Valida a libertação de código low-code sem lock-in.

### 9.4. O Que Entrega na Prática
* **No Ecossistema:** Clareza imediata sobre qual ferramenta acionar para cada caso de uso.
* **Nas Aplicações Corporativas:** Solução final no **Padrão CTT**, com robustez enterprise independente do caminho escolhido na largada.

---

## 10. Quadro Consolidado das 7 Ferramentas do Ecossistema

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

*Este Tratado consolida de forma definitiva as 8 camadas de engenharia do Ecossistema AIDD, estabelecendo uma governança sem ambiguidades para todas as ferramentas e aplicações geradas.*
