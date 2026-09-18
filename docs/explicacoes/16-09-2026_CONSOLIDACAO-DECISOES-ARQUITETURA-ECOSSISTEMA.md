# Enciclopédia & Carta Magna do Ecossistema AIDD
## Tratado Definitivo de Arquitetura, Engenharia, Cibersegurança, Agnosticismo e Governança

> **Localização:** `docs/explicacoes/CONSOLIDACAO-DECISOES-ARQUITETURA-ECOSSISTEMA.md`  
> **Status:** Revisado factualmente após validação E2E do Fluxo 01 (18/09/2026) — ver ressalvas de status ao longo do documento  
> **Versão:** 3.3.0 (Correção factual pós-validação: nomes reais de gates, rotas, artefatos e stack de frontend)  
> **Data de Homologação Original:** 17/09/2026 · **Última Revisão:** 18/09/2026  
> **Padrão de Referência:** Monólito Modular (VSA + Núcleo Horizontal `src/core/`), Padrão Enterprise CTT, Zero Vendor Lock-in  

> ⚠️ **Nota de fidelidade:** as Camadas 1 a 7 abaixo descrevem decisões arquiteturais de sessões anteriores e não foram todas re-verificadas linha a linha nesta revisão (18/09/2026) — a revisão desta rodada focou nos nomes reais de Quality Gates, rotas HTTP, nomes de artefatos/diretórios e no estado real de cada um dos 3 Fluxos de Criação (Camadas 8-9 e Seções 10-12), que **foram** verificados diretamente no código e em execução real. Onde uma afirmação das Camadas 1-7 cita um Gate Verificador, o nome foi corrigido para o real; o restante do texto de cada módulo foi preservado.

---

## 1. As 11 Leis Invioláveis do Ecossistema (fonte real: `AGENTS.md`, raiz do repositório)

Toda linha de código, manifesto de infraestrutura, contrato de API ou diretiva agêntica dentro do ecossistema AIDD é rigorosamente subordinada a 11 leis universais (o texto abaixo é a tradução fiel do `AGENTS.md` real — a versão anterior deste documento tinha títulos/números que não correspondiam ao arquivo fonte):

```
+--------------------------------------------------------------------------------------------------------+
|                                  AS 11 LEIS INVIOLÁVEIS DO ECOSSISTEMA                                 |
+------------------------------+------------------------------+------------------------------------------+
| 1. Determinismo Primeiro     | 2. Qualidade Binária          | 3. Persistência Estruturada              |
| Scripts determinísticos, AST,| `python ecossistema.py audit`| Estado em arquivos de auditoria (JSON,   |
| regex, JSON Schema — nunca   | exit 0 = passa, exit 1 = bloq.| SQLite), nunca em memória de conversa    |
| LLM p/ tarefa mecânica       |                               |                                           |
+------------------------------+------------------------------+------------------------------------------+
| 4. Economia Extrema de Tokens| 5. Zero Stubs / Zero Mocks   | 6. Agnosticismo Supremo                  |
| Prompts minimalistas, regras | 100% funcional, tipado e     | Zero vendor lock-in em SO, harness       |
| em inglês compacto           | validado com testes reais    | e provedor de LLM                        |
+------------------------------+------------------------------+------------------------------------------+
| 7. Desenvolvedor no Controle | 8. Honestidade de Rótulo     | 9. Disciplina de Teste de Ferramentas    |
| Execução sequencial e        | Nunca alegar certificação/   | Ciclo de 5 passos (auto-fix → commit →   |
| interativa; zero subagente   | cobertura além do resultado  | limpar → executar limpo → atualizar      |
| headless oculto              | real automatizado            | relatório E2E)                           |
+------------------------------+------------------------------+------------------------------------------+
| 10. Quarteto Sine Qua Non Dinâmico                                                                      |
| Todo projeto nasce com Swagger Studio (`/docs`), Webhook Studio (`/webhooks`), MCP Studio (`/mcp`) e     |
| Guia do Utilizador (`/docs/guia`) — dinâmicos, cobrindo 100% dos módulos                                 |
+------------------------------+------------------------------+------------------------------------------+
| 11. Padrão-Ouro de Stack Tecnológica (adicionada 18/09/2026)                                             |
| Todo fluxo que gera Frontend DEVE usar Next.js + TypeScript + Tailwind CSS (Backend Python + SQLite WAL, |
| API OpenAPI 3.1) — só muda com pedido explícito do usuário para aquela camada                           |
+------------------------------+------------------------------+------------------------------------------+
| A Tríade Canônica de Criação                                                                             |
| FORGE (Governança) -> aidd-planner (Intake) -> [GENERATOR | FACTORY | BRIDGE] -> MASTER -> ENTERPRISE -> OPS |
+--------------------------------------------------------------------------------------------------------+
```

> **Nota de discrepância encontrada nesta revisão:** o próprio `AGENTS.md` (Lei #10) ainda cita `/swagger` como o path do Swagger Studio — mas o código real (`server.py` gerado, ver Seção 6) usa `/docs`. `/swagger` não existe em nenhum servidor gerado. A tabela acima já usa o path real; o `AGENTS.md` segue com a inconsistência (não corrigida nesta rodada, fora do escopo pedido).

---

## 2. Camada 01: Cibersegurança & Defesa em Profundidade

### Módulo 1.1: Queries Parametrizadas & Hash Argon2id (OWASP A03 / A07)
* **O Que É / O Que Faz:** Proibição de interpolação de strings em consultas SQL. Todas as queries usam prepared statements parametrizados. Senhas cifradas com Argon2id/bcrypt com salt individual resistente a ataques por GPU.
* **Gate Verificador:** `G_ECOSSISTEMA_INTEGRIDADE`
* **O Que Entrega:** Zero SQL Injection e proteção contra ataques de dicionário e quebra de hashes vazados.

### Módulo 1.2: HMAC SHA-256 em Tempo Constante (Anti-Timing Attacks)
* **O Que É / O Que Faz:** Validação estrita de assinaturas criptográficas de webhooks e tokens usando a função `hmac.compare_digest`, eliminando vulnerabilidades de temporização side-channel.
* **Gate Verificador:** `G_FACTORY_INTEGRATION` (aidd-factory) e `G_BRIDGE_VSA_COMPAT` (aidd-bridge)
* **O Que Entrega:** Comunicação assíncrona entre sistemas matematicamente inviolável.

### Módulo 1.3: Cofre Assimétrico sops + age (Zero Plain-Text Secrets)
* **O Que É / O Que Faz:** Criptografia de variáveis de ambiente com curva elíptica X25519. Nenhuma chave de API ou senha trafega em texto claro no git. Chaves privadas isoladas e deciframento em memória.
* **Gate Verificador:** `G_OPS_SSH` e `G_BRIDGE_VENDOR_LOCKIN`
* **O Que Entrega:** Repositório seguro contra vazamento involuntário de credenciais de produção.

### Módulo 1.4: Blindagem SHA-256 Anti-Tampering
* **O Que É / O Que Faz:** Checksums estritos de todos os templates e arquivos de segurança enterprise. Se um único byte for adulterado sem autorização, a esteira é bloqueada com Exit 1 imediato.
* **Gate Verificador:** `G_SEGURANCA` / `G_CONTRACTS` (aidd-master, aidd-enterprise — não há um gate `G_ENTERPRISE_SHA` dedicado)
* **O Que Entrega:** Integridade verificável do código contra injeção maliciosa em tempo de build.

### Módulo 1.5: Trilha de Auditoria com trace_id & Ofuscação (LGPD/GDPR)
* **O Que É / O Que Faz:** Propagação universal do header `X-Trace-Id` em requisições, logs e eventos assíncronos. Mascaramento automático de dados pessoais identificáveis (PII) antes da gravação de logs.
* **Gate Verificador:** `G_TESTES` (aidd-master, aidd-enterprise)
* **O Que Entrega:** Rastreabilidade completa de auditoria em conformidade com as leis de proteção de dados.

### Módulo 1.6: Hadolint, Headers OWASP & Usuário Non-Root
* **O Que É / O Que Faz:** Auditoria determinística de Dockerfiles via Hadolint, execução obrigatória como `USER appuser` e injeção de headers defensivos no Nginx (CSP, HSTS, X-Frame-Options DENY).
* **Gate Verificador:** `G_HADOLINT` e `G_BRIDGE_DOCKER_OCI`
* **O Que Entrega:** Containers OCI minimalistas com superfície de ataque reduzida.

---

## 3. Camada 02: Arquitetura de Software — Monólito Modular Canônico

### Módulo 2.1: Fatias Verticais de Domínio (VSA Eixo Vertical)
* **O Que É / O Que Faz:** Isolamento de cada regra de negócio em `features/<dominio>/`, contendo rotas, serviços puros, repositórios parametrizados, schemas Pydantic e testes de integração próprios.
* **Gate Verificador:** `G_ARQUITETURA` (aidd-master/aidd-enterprise) e `G_FACTORY_INTEGRATION` (aidd-factory)
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
* **Gate Verificador:** `G_ARQUITETURA` (aidd-master/aidd-enterprise) e `G_FACTORY_INTEGRATION` (aidd-factory)
* **O Que Entrega:** Arquitetura limpa que permite extrair fatias para microsserviços futuros com atrito zero.

---

## 4. Camada 03: Engenharia de Software & Qualidade Industrial

### Módulo 3.1: Zero Stubs e Zero Mocks
* **O Que É / O Que Faz:** Proibição de stubs (`pass`, `NotImplementedError`, `# TODO`) e mocks estáticos em código de produção. 100% das funções possuem implementação real.
* **Gate Verificador:** `G_TESTES_REAIS`
* **O Que Entrega:** Software entregue pronto para operação real em produção.

### Módulo 3.2: TDD Red-Green Rigoroso
* **O Que É / O Que Faz:** Escrita de testes de integração e unitários antes da implementação da lógica de negócio, garantindo que o código nasça validado.
* **Gate Verificador:** `G_INTEGRACAO_CROSS_SCRIPT` e `G_SESSAO_HERMETICA` (aidd-generator — não existe `G_GENERATOR_TESTES`)
* **O Que Entrega:** Mais de 2.200 testes reais passando em 100% das ferramentas do ecossistema.

### Módulo 3.3: Tratamento Determinístico de Erros (Result Monad)
* **O Que É / O Que Faz:** Encapsulamento de operações de risco em estruturas `Ok(valor)` ou `Err(erro)`, forçando o chamador a tratar explicitamente todos os caminhos de falha.
* **Gate Verificador:** sem gate dedicado — convenção de código aplicada via `core/result.py` de cada ferramenta
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

> **Correção de rotas nesta revisão:** o Swagger Studio vive em **`/docs`** (não `/swagger` — path inexistente no código); o Guia do Utilizador vive em **`/docs/guia`** (não `/docs`, que já é do Swagger). Confirmado lendo `src/server.py` gerado (`if path == "/docs"`, `if path == "/docs/guia"`) em `testes/fluxo-01-master/proj_gestao-tarefas-monolito`.

### Módulo 5.1: Swagger Studio (`/docs`)
* **O Que É / O Que Faz:** Documentação interativa OpenAPI **3.1** dinamicamente gerada a partir dos schemas tipados, permitindo testes imediatos no navegador.
* **Gate Verificador:** `G_CONTRACTS` (aidd-master/aidd-enterprise) e `G_FACTORY_INTEGRATION` (aidd-factory)
* **O Que Entrega:** Especificação viva de rotas sem documentação manual defasada.

### Módulo 5.2: Webhook Studio (`/webhooks`)
* **O Que É / O Que Faz:** Gestão, teste, reenvio e simulação de disparos de webhooks com assinatura HMAC SHA-256 e auditoria de status HTTP.
* **Gate Verificador:** `G_BRIDGE_VSA_COMPAT` (aidd-bridge); `G_CONTRACTS` cobre a implementação nativa em aidd-master/aidd-enterprise
* **O Que Entrega:** Integração assíncrona robusta e rastreável.

### Módulo 5.3: MCP Studio (`/mcp`)
* **O Que É / O Que Faz:** Servidor Model Context Protocol nativo que expõe as capacidades do sistema como tools em JSON Schema para consumo por agentes de IA.
* **Gate Verificador:** `G_CONTRACTS` (aidd-master/aidd-enterprise) e `G_FACTORY_INTEGRATION` (aidd-factory)
* **O Que Entrega:** Sistema orquestrável por copilotos inteligentes desde o Dia Zero.

### Módulo 5.4: Guia do Utilizador (`/docs/guia`)
* **O Que É / O Que Faz:** Manual vivo do utilizador contendo arquitetura, exemplos práticos de onboarding, catálogo de endpoints e orientações de suporte.
* **Gate Verificador:** `G_BRIDGE_VSA_COMPAT` (aidd-bridge); `G_FACTORY_INTEGRATION` exige o `docs.html` equivalente em aidd-factory
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

### Módulo 6.3: Proxy Reverso Nginx com TLS
* **O Que É / O Que Faz:** Roteamento de tráfego HTTPS com cabeçalhos defensivos OWASP e rate limiting. **Correção real:** o proxy gerado por `aidd-master`/`aidd-factory` é **Nginx** (não Traefik) com certificado **autoassinado** gerado localmente (`nginx/ssl/generate_ssl.py`, RSA 2048-bit via OpenSSL) — não há emissão automática via Let's Encrypt hoje; isso fica a cargo do operador em produção real com domínio próprio. Roteia por prefixo entre o backend Python e o frontend Next.js (Lei #11) — validado rodando de verdade em Docker nesta sessão (18/09/2026).
* **Gate Verificador:** `G_BRIDGE_DOCKER_OCI` (aidd-bridge); aidd-master/aidd-enterprise não têm gate de nginx dedicado hoje (validação manual)
* **O Que Entrega:** Tráfego criptografado localmente; renovação/Let's Encrypt fica pendente para quando houver domínio público.

### Módulo 6.4: Uptime Kuma & Observabilidade Ativa
* **O Que É / O Que Faz:** Monitoramento contínuo de disponibilidade e latência dos endpoints de healthcheck da aplicação, com alertas automatizados.
* **Gate Verificador:** `G_OPS_MVP` (não existe `G_OPS_OBSERVABILITY`)
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
* **O Que É / O Que Faz:** Construção proprietária sob medida guiada por esteira determinística de 8 fases LLM-guiadas (Spec formal -> TDD Red-Green -> Core VSA -> Quarteto). Desde a correção da Lei #11 nesta revisão, a fase de implementador instrui explicitamente Next.js 14 + TypeScript + Tailwind CSS quando UI web é necessária, nunca HTML/CSS/JS puro por padrão.
* **Gate Verificador:** `G_INTEGRACAO_CROSS_SCRIPT`, `G_CYBERSECURITY_OWASP`, `G_SANDBOX_NIVEL_1` (não existe `G_GENERATOR_*`)
* **O Que Entrega:** Aplicação 100% nativa com controle total sobre cada linha de código.

### Módulo 8.2: FLUXO 02 — Motores Open-Source (`aidd-factory`)
* **O Que É / O Que Faz:** Alavancagem sobre software livre consolidado (filas, bots, mensageria). Sobe containers dos motores e gera fatias VSA de integração com webhooks HMAC seguros. O frontend do "Quarteto Sine Qua Non" gerado por este fluxo também segue a Lei #11 (Next.js) desde a unificação do gerador com `aidd-master` nesta revisão — eliminou-se a duplicação anterior entre `vsa_generator.py` e `frontend_generator.py`.
* **Gate Verificador:** `G_FACTORY_INTEGRATION`, `G_FACTORY_MVP`, `G_FACTORY_COMPOSE` (não existe `G_FACTORY_*` como gate único; `G_FACTORY_VSA` também não existe)
* **O Que Entrega:** Velocidade de entrega aproveitando motores maduros da comunidade.

### Módulo 8.3: FLUXO 03 — Low-Code Desatado (`aidd-bridge`)
* **O Que É / O Que Faz:** Libertação e empacotamento de interfaces do Lovable, v0 ou Bolt. Extirpação de travas de nuvem fechada, conexão ao PostgreSQL corporativo e conteinerização OCI. Fora do escopo da Lei #11 desta revisão por decisão deliberada: o objetivo aqui é preservar a stack visual de origem do projeto clonado (inclusive quando já for Next.js), nunca forçar uma conversão de framework.
* **Gate Verificador:** `G_BRIDGE_VSA_COMPAT`, `G_BRIDGE_DOCKER_OCI` (não existe `G_BRIDGE_*` como gate único)
* **O Que Entrega:** Reaproveitamento de protótipos visuais em produção real sem vendor lock-in.

### Módulo 8.4: Funil de Convergência Universal
* **O Que É / O Que Faz:** Todos os 3 fluxos convergem obrigatoriamente para `aidd-master` (Monólito Modular VSA em `src/modules/`) -> `aidd-enterprise` (SHA-256 + Resiliência) -> `aidd-ops` (Deploy VPS). Desde a correção do backlog "aidd-ops só cobre nicho OSS" nesta revisão, `aidd-ops` reconhece dois tipos de origem (`tipo_origem` no `PLANO-INFRAESTRUTURA.json`): `monolito_customizado` (Fluxos 01/03, motor compose-nativo via SSH) e stacks OSS curadas por nicho (Fluxo 02, motor Coolify) — o motor de deploy é selecionado automaticamente a partir desse campo, nunca mais fixo.
* **Gate Verificador:** Todos os Quality Gates do Ecossistema
* **O Que Entrega:** Solução corporativa final no **Padrão CTT**, independente do fluxo de origem.

---

## 10. Funcionamento Passo a Passo dos 3 Fluxos de Criação

> **Correção de nomenclatura nesta revisão:** o "PRÉ-PLANO" é a ferramenta real `aidd-planner` (`python ecossistema.py planner init --fluxo N`), que gera dois artefatos por projeto: `PLANNER.json` (nunca `PLANO-MESTRE.json`) e, desde a Fase 9 desta revisão, `DESIGN-SYSTEM.json` — a identidade visual (paleta primária), única por projeto, escolhida de forma determinística (catálogo por nicho + fallback por hash, zero LLM) a partir do foco/domínio informado no planejamento.

### FLUXO 01 (Do Zero Puro): `FORGE -> PLANNER -> GENERATOR -> MASTER -> ENTERPRISE -> OPS`
* **Passo 1 (aidd-forge):** Injeta governança, regras de linting, pre-commit hooks e o `AGENTS.md` canônico.
* **Passo 2 (aidd-planner):** Realiza entrevista interativa socrática para coletar requisitos de negócio e gera `PLANNER.json` + `DESIGN-SYSTEM.json` (paleta única do projeto).
* **Passo 3 (aidd-generator):** Dispara a fábrica autônoma em 8 fases determinísticas (Spec formal -> TDD Red-Green -> Core VSA -> Quarteto), gerando frontend em Next.js/TypeScript/Tailwind (Lei #11) quando UI web é necessária.
* **Passo 4 (aidd-master):** Organiza o código gerado em Monólito Modular (Fatias VSA em `src/modules/` conectadas à Camada Horizontal `src/core/`) e exporta o frontend Next.js em `frontend/`, aplicando a paleta do `DESIGN-SYSTEM.json` via `NextJSExporter`.
* **Passo 5 (aidd-enterprise):** Audita integridade por hash SHA-256 e injeta Circuit Breakers, Rate Limiting distribuído e trilha imutável `trace_id`.
* **Passo 6 (aidd-ops):** Reconhece a origem como `monolito_customizado`, dimensiona recursos pela contagem de módulos e provisiona a VPS via SSH em modo compose-nativo (`docker compose up -d --build` remoto), sem depender de curadoria de ferramentas OSS.
* **Linha de Chegada:** Aplicação proprietária 100% testada e funcional no **Padrão CTT**, com Swagger Studio (`/docs`), Webhook Studio (`/webhooks`), MCP Studio (`/mcp`) e Guia (`/docs/guia`) nativos do backend, mais um frontend Next.js com identidade visual própria.

---

### FLUXO 02 (Motores Open-Source): `FORGE -> PLANNER -> FACTORY -> MASTER -> ENTERPRISE -> OPS`
* **Passo 1 (aidd-forge):** Estabelece a fundação inquebrável de regras e governança do repositório.
* **Passo 2 (aidd-planner):** Identifica os requisitos funcionais e mapeia quais motores livres (filas, bots, mensageria) devem compor o sistema, gerando `PLANNER.json` + `DESIGN-SYSTEM.json`.
* **Passo 3 (aidd-factory):** Orquestra os containers de software livre (PostgreSQL, Redis, RabbitMQ, Evolution API), gera as Fatias Verticais VSA de integração e o frontend Next.js unificado (`NextJSExporter`, mesmo motor do Fluxo 01).
* **Passo 4 (aidd-master):** Harmoniza as fatias de conexão periféricas no Monólito Modular da empresa, evitando acoplamento espaguete.
* **Passo 5 (aidd-enterprise):** Injeta resiliência bancária e valida integridade criptográfica.
* **Passo 6 (aidd-ops):** Reconhece a origem como stack OSS curada por nicho e sobe a stack dinamicamente via Coolify — a partir desta revisão, a lista de serviços vem da curadoria real do plano (antes era fixa/hardcoded independentemente do nicho).
* **Linha de Chegada:** Sistema corporativo de alta velocidade alavancado em motores livres, seguro e operando em produção com o Quarteto Sine Qua Non e frontend Next.js.

---

### FLUXO 03 (Low-Code / Apps Unificadas): `FORGE -> PLANNER -> BRIDGE -> MASTER -> ENTERPRISE -> OPS`
* **Passo 1 (aidd-forge):** Blinda o repositório com regras de arquitetura e convenções de código limpo.
* **Passo 2 (aidd-planner):** Recebe o contexto do código exportado das plataformas low-code (Lovable, v0 da Vercel, Bolt.new) e gera `PLANNER.json`.
* **Passo 3 (aidd-bridge):** Executa o pipeline de libertação: extirpa amarras de nuvem fechada, converte Supabase em PostgreSQL corporativo (`init-db.sql`) e gera Dockerfile OCI seguro — preserva a stack visual de origem do projeto (Lei #11 não se aplica aqui por decisão deliberada; ver Módulo 8.3).
* **Passo 4 (aidd-master):** Conecta o frontend desatado às fatias de backend VSA correspondentes em `src/modules/`.
* **Passo 5 (aidd-enterprise):** Aplica blindagem de missão crítica e auditoria estrita.
* **Passo 6 (aidd-ops):** Trata a origem como `monolito_customizado` (mesmo motor compose-nativo do Fluxo 01) e empacota a solução na VPS corporativa com banco PostgreSQL dedicado.
* **Linha de Chegada:** Frontend de alta fidelidade resgatado de ferramentas de IA, operando em VPS corporativa sem vendor lock-in e com o Quarteto Sine Qua Non nativo do backend.

---

## 11. Árvore Física Canônica do Projeto (Padrão CTT)

> **Correção real nesta revisão:** não existe um diretório separado `quarteto_sine_qua_non/` com arquivos `.json`/`.md` próprios — essa era uma descrição aspiracional. Na prática, os 4 Estúdios (Swagger, Webhook, MCP, Guia) são **código Python nativo** dentro de `src/core/` (`openapi.py`, `webhooks.py`, `mcp_server.py`), servido dinamicamente pelo próprio `server.py` nas rotas `/docs`, `/webhooks`, `/mcp` e `/docs/guia` — confirmado lendo o código gerado e rodando o projeto real em Docker (18/09/2026). A árvore abaixo reflete isso, além do novo `frontend/` (Next.js, Lei #11) introduzido nesta revisão.

A materialização em disco de qualquer aplicação gerada no ecossistema organiza-se em 4 Zonas Físicas bem delimitadas:

* **Zona 1: Horizontal (`src/core/`)** — Infraestrutura transversal compartilhada: conexões com banco, cofre de segredos, Circuit Breakers, telemetria `trace_id` e os 4 Estúdios nativos (`openapi.py`, `webhooks.py`, `mcp_server.py`).
* **Zona 2: Vertical VSA (`src/modules/`)** — Fatias verticais autônomas (nunca `src/features/`). Cada módulo tem `models.py`/`services.py`/`routes.py`, camadas DDD opcionais e teste próprio, sem dependências cruzadas.
* **Zona 3: Apresentação (`frontend/`)** — Frontend Next.js 14 App Router + TypeScript + Tailwind CSS (Lei #11), com paleta única por projeto (`DESIGN-SYSTEM.json` gerado pelo `aidd-planner`). Não reimplementa os Estúdios nativos — o Nginx roteia por prefixo entre `frontend/` e o backend Python.
* **Zona 4: Infra & Ops (`infra/`)** — Containers OCI não-root (Hadolint), proxy Nginx blindado por OWASP e segredos cifrados com `sops+age`.

### Estrutura Visual dos Diretórios:
```text
projeto-corporativo/
├── src/
│   ├── core/                      # [Núcleo Horizontal Compartilhado]
│   │   ├── database.py            # Pool assíncrono de conexões PostgreSQL/SQLite WAL
│   │   ├── security.py            # Sanitização de inputs, hashes e secrets
│   │   ├── openapi.py             # Swagger Studio nativo (/docs) — OpenAPI 3.1
│   │   ├── webhooks.py            # Webhook Studio nativo (/webhooks) — HMAC SHA-256
│   │   ├── mcp_server.py          # MCP Studio nativo (/mcp)
│   │   └── design_catalog.py      # Catálogo determinístico de paletas (Lei #1, zero LLM)
│   ├── modules/                   # [Fatias Verticais VSA de Domínio]
│   │   ├── encomendas/            # Fatia vertical 1 (models/services/routes/testes)
│   │   ├── frotas/                # Fatia vertical 2
│   │   └── roteirizacao/          # Fatia vertical 3
│   └── server.py                  # Roteador central declarativo da aplicação (rotas /docs, /docs/guia, /webhooks, /mcp)
├── frontend/                       # [Next.js 14 + TypeScript + Tailwind CSS — Lei #11]
│   ├── app/                       # App Router: layout.tsx, page.tsx (dashboard), <modulo>/page.tsx
│   ├── tailwind.config.ts         # Cores primary/primary-hover injetadas do DESIGN-SYSTEM.json
│   └── Dockerfile                 # Multi-stage node:20-alpine, output standalone, usuário não-root
├── DESIGN-SYSTEM.json             # Paleta única do projeto (gerada pelo aidd-planner)
├── PLANNER.json                   # Plano estruturado do projeto (gerado pelo aidd-planner)
├── infra/                         # [Infraestrutura como Código - aidd-ops]
│   ├── docker-compose.yml         # Orquestração de containers de produção (app + web + nginx)
│   ├── Dockerfile                 # Multi-stage build OCI seguro (USER appuser)
│   ├── nginx.conf                 # Proxy reverso com headers defensivos OWASP, roteia app vs frontend
│   └── secrets.enc.yaml           # Cofre criptografado com sops + age
├── tests/                         # Suíte de regressão E2E e testes globais
├── requirements.txt               # Dependências pinadas com hashes criptográficos SHA-256
└── AGENTS.md                      # Diretivas soberanas de governança e regras do projeto
```

### Dicionário de Pastas & Responsabilidades:

| Diretório Físico | Papel Arquitetural | Quality Gate Verificador |
| :--- | :--- | :--- |
| `src/core/` | Centraliza bibliotecas transversais (DB, segurança, telemetria, Estúdios nativos, Fake Adapters Tipados e Light-Lane CQRS) | `G_DRIFT_NUCLEO_COMPARTILHADO`, `G_LLM_PROMPT_SHIELD` |
| `src/modules/{slug}/` | Encapsula cada fatia de negócio isolada (VSA) — fatias estritamente isoladas via AST e sem duplicidade funcional | `G_ISOLATION_AUDIT`, `G_DRIFT_ANALYZER`, `G_TESTES` / `G_ARQUITETURA` |
| `sandbox/` | Zona experimental de prototipagem efêmera (PoCs), estritamente bloqueada contra promoção direta sem TDD | `G_PROTOTYPE_REWRITE` |
| `frontend/` | Next.js/TypeScript/Tailwind com identidade visual única por projeto (Lei #11) | `G_FRONTEND_LAYERS`, `G_CONTRACTS` |
| `infra/` | Configuração de containers OCI, proxy reverso, rotação de segredos efêmeros e chaves | `G_HADOLINT`, `G_INFRA_COMPOSE` |
| `AGENTS.md & requirements.txt` | Regras invioláveis em código e trava de supply chain por SHA-256 | `G_DEPENDENCIAS_PIN_HASH`, `G_ECOSSISTEMA_INTEGRIDADE`, `G_PROTOCOL_FALLBACK` |

---

## 12. Quadro de Homologação das 8 Ferramentas do Ecossistema

> Contagens de teste medidas de verdade nesta revisão (`python -m pytest -q` real por ferramenta, 18/09/2026) — nunca digitadas de memória. `aidd-planner` é a 8ª ferramenta (antes descrita genericamente como "PRÉ-PLANO"). Total de 2.213 testes unitários reais passando em tools/ e 23 Quality Gates em disco.

| Ferramenta | Papel Central na Tríade | Status | Entregável Consolidado |
| :--- | :--- | :--- | :--- |
| **`aidd-forge`** | Ditador de Governança e Regras | Homologado | Repositório blindado, linters, pre-commit e regras de arquitetura e tokens (294 testes) |
| **`aidd-planner`** | Motor de Planejamento (Ponte Forge -> Tríade) | Homologado | `PLANNER.json` (SDD/BDD/DDD) + `DESIGN-SYSTEM.json` (paleta única por projeto, Fase 9) (10 testes) |
| **`aidd-generator`** | Fábrica Autônoma (FLUXO 01) | Homologado | Aplicação completa em 8 fases (TDD + VSA), frontend Next.js/TS/Tailwind (Lei #11) (1.019 testes) |
| **`aidd-master`** | Arquiteto de Monólito Modular | Homologado | Fatias VSA de domínio (`src/modules/`), VSA Light-Lane, Fake Adapters Tipados + frontend Next.js exportado (386 testes) |
| **`aidd-enterprise`**| Guardião de Missão Crítica | Homologado | Checksums SHA-256, Circuit Breakers, Rate Limiters, PromptShield e trilha `trace_id` (336 testes) |
| **`aidd-ops`** | Orquestrador de Infra & VPS | Homologado | Cobre monólito customizado, rotação determinística de segredos efêmeros (0600) e stack OSS Coolify (178 testes) |
| **`aidd-factory`** | Integrador Open-Source (FLUXO 02) | Homologado | Fatias VSA de conexão, webhooks HMAC seguros, orquestração de motores e frontend Next.js unificado (18 testes) |
| **`aidd-bridge`** | Desacoplador Low-Code (FLUXO 03) | Homologado | Frontend limpo sem vendor lock-in para PostgreSQL VPS, preserva stack visual de origem (Lei #11 não se aplica aqui) (45 testes) |

---

*Este documento estabelece o Tratado Canônico Soberano do Ecossistema AIDD, detalhando cada módulo, seus Quality Gates e entregas concretas.*
