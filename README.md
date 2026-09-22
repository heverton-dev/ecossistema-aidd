# 🌐 Ecossistema AIDD Unificado

> **Repositório Central de Engenharia Agêntica de Software (AI-Driven Development)**  
> **GitHub:** `https://github.com/heverton-dev/ecossistema-aidd`  
> **Orquestração:** ORCA ADE (Lead: Antigravity | Governance: Claude Code | Integration: MimoCode)

---

## 💡 O que é o Ecossistema AIDD? (Entenda em 1 Minuto)

> **North Star:** Transformar uma ideia em software testado, e distribuir a mesma governança pra qualquer harness de IA.

Imagine uma **fábrica inteligente de automóveis de alta precisão**:
- Você não constrói um carro no improviso: primeiro monta a **linha de produção blindada** para ninguém se machucar, depois a **engenharia desenha e monta o motor**, os **módulos se encaixam como blocos de Lego**, uma **equipe de auditoria certifica cada parafuso** e, por fim, a **equipe de pista abastece e coloca o carro para rodar no asfalto**.

O **Ecossistema AIDD** faz exatamente isso, só que para **Softwares Modernos construídos por Inteligência Artificial**:
ele transforma uma ideia em software testado, aplicando os mesmos Quality Gates e a mesma governança independente de qual assistente de IA está no comando (Claude Code, Cursor, Antigravity, OpenCode, MimoCode etc.).

---

## 🚀 Primeiros Passos

1. `git clone https://github.com/heverton-dev/ecossistema-aidd.git`
2. Abra a pasta no seu assistente de IA (Claude Code, Cursor, Antigravity, OpenCode, MimoCode etc.) e comece a conversar normalmente.
3. Pronto. As dependências externas (skills e MCPs de terceiros usados pelo agente) se instalam sozinhas na primeira mensagem da sessão — você não precisa digitar nenhum comando no terminal.

**Só o núcleo (clone leve — ~poucas dezenas de MB):**

```bash
git clone --depth 1 --filter=blob:none --sparse https://github.com/heverton-dev/ecossistema-aidd.git
cd ecossistema-aidd
git sparse-checkout set ecossistema.py gates core componentes scripts tools docs/protocolos docs/glossario requirements.txt README.md LICENSE AGENTS.md
# ou pacote zip: python ecossistema.py package --perfil usuario  →  dist/ecossistema-aidd-usuario.zip
```

Quer forçar manualmente ou adicionar uma dependência nova (skill ou MCP de terceiro)? Digite `/dependencia bootstrap` (ou `/dependencia skill <nome>`, `/dependencia mcp <nome>`) no chat. Só use o terminal (`python ecossistema.py dependencia bootstrap`) se preferir.

### 🐍 Ambiente Python do projeto (`.venv`)

Desde 2026-09-19 o repositório usa um **ambiente Python próprio**, em `.venv/`, em vez de instalar os pacotes no Python geral da máquina. O motivo é concreto: com tudo no mesmo lugar, um pacote impedia o outro — o `checkov` travava o `litellm` numa versão com 7 vulnerabilidades conhecidas — e o que rodava na máquina não era o que os arquivos mandavam instalar.

```bash
# Criar e preencher (uma vez por clone)
python -m venv .venv
.venv/Scripts/python.exe -m pip install --require-hashes -r requirements-dev.lock   # Windows
.venv/bin/python -m pip install --require-hashes -r requirements-dev.lock           # Linux/macOS

# Dependências específicas de cada ferramenta
.venv/Scripts/python.exe -m pip install -r tools/aidd-generator/requirements.txt
.venv/Scripts/python.exe -m pip install -r tools/aidd-master/requirements.txt
.venv/Scripts/python.exe -m pip install -r tools/aidd-enterprise/requirements.txt
.venv/Scripts/python.exe -m pip install -r tools/aidd-ops/requirements.txt
```

`--require-hashes` é obrigatório: ele recusa qualquer pacote cuja assinatura não bata com a registrada no lockfile. Nunca instale a partir de `requirements.txt` direto para trabalhar no repositório — esse arquivo é a **fonte** dos pins, e o lockfile é o que tem as assinaturas.

O `checkov` **não** entra neste ambiente: ele vive no ambiente isolado do hook `g-infra-compose` (ver `.pre-commit-config.yaml`), porque exige uma dependência interna incompatível com o `litellm` corrigido.

---

## 🏛️ A Fábrica de Software AIDD: As 8 Ferramentas Integradas

```text
                                        ┌─────────────────────────────┐
                                        │   ECOSSISTEMA AIDD (Monorepo)│
                                        └──────────────┬──────────────┘
                                                       │
    ┌──────────────┬────────────────┬──────────────────┼─────────────────┬──────────────┬────────────────┬──────────────┬──────────────┐
    ▼              ▼                ▼                  ▼                 ▼              ▼                ▼              ▼              ▼
[ aidd-forge ] [ aidd-planner ] [ aidd-generator ] [ aidd-master ] [ aidd-enterprise ] [ aidd-ops ] [ aidd-factory ] [ aidd-bridge ]
 Linha de Montagem Planejamento BDD Fábrica Autônoma   Blocos de Lego   Selo de Auditoria Pista & Infra  Integração/BFF  Ponte Low-Code
  & Blindagem    & Contratos SDD   (Ideia -> Código)    Modular & Banco  Zero-Trust & Hashes Nuvem/Deploy Multi-Serviço   -> VPS Nativa
   (/forge)         (/planner)       (/generate)          (/master)        (/enterprise)    (/ops)          (/factory)      (/bridge)
```

---

## 🔱 A Tríade Canônica: Os 3 Fluxos de Criação Autônoma

Toda aplicação robusta no ecossistema nasce da fundação **`aidd-forge`** e do intake **`aidd-planner`**, convergindo obrigatoriamente para a harmonização **`aidd-master`**, blindagem **`aidd-enterprise`** e deploy **`aidd-ops`**. A **única diferença** entre os fluxos é a estratégia de construção da Engine intermediária:

| Fluxo | Nome Canônico | Motor Principal | Slash Command | Comando Terminal (CLI) | Estratégia de Construção |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **Fluxo 01** | **`aidd-pure`** | `aidd-generator` | **`/pure`** | `python ecossistema.py run-fluxo --fluxo pure` | **Do Zero Puro:** Código autoral sob medida, gerado via TDD Red-Green estrito com Clean Architecture. |
| **Fluxo 02** | **`aidd-open`** | `aidd-factory` | **`/open`** | `python ecossistema.py run-fluxo --fluxo open` | **Motores Open-Source:** Curadoria, integração e fatiamento VSA de bases OSS consolidadas com Compose. |
| **Fluxo 03** | **`aidd-freedom`** | `aidd-bridge` | **`/freedom`** | `python ecossistema.py run-fluxo --fluxo freedom` | **Desacoplamento Low-Code:** Desmonte de vendor lock-in (Lovable/v0/Bolt), migração para Postgres e preservação pixel-perfect da UI. |

> **Universal Convergence Funnel:** Qualquer que seja o fluxo, a entrega final entrega nativamente o **Quarteto *Sine Qua Non*** (`/swagger`, `/webhooks`, `/mcp`, `/docs`) e o Frontend no **Padrão-Ouro Next.js + TypeScript + Tailwind CSS** (Lei Inviolável #11).

---

## ⚡ As 8 Ferramentas: Do Leigo ao PhD

| Ferramenta | Analogia do Dia a Dia (Leigo) | Rigor Arquitetural (PhD / Arquiteto) | Como usar no Chat | Comando no Terminal (CLI) |
| :--- | :--- | :--- | :---: | :--- |
| **AIDD Forge** | **A Fundação e o Chassi:** Prepara o terreno, coloca cercas de proteção e impede que a IA faça bagunça. | Bootstrap determinístico, fatiamento em micro-ambientes efêmeros (`.aidd/pipeline/`), context-purge estrito e 15 Quality Gates locais. | `/forge [pasta]` | `python ecossistema.py forge init [pasta]` |
| **AIDD Planner** | **A Planta Baixa e o Contrato:** Escreve as regras de negócio em BDD/SDD e garante os requisitos do Quarteto. | Intake BDD/SDD, modelagem de entidades e contratos formais JSON Schema de handoff com as Engines. | `/planner [args]` | `python ecossistema.py planner init [args]` |
| **AIDD Generator** | **A Linha de Montagem Autônoma:** Você fala o que quer e a fábrica entrega o software pronto com testes. | Pipeline autônomo de 8 fases com TDD Red-Green, consumo nativo de `PLANNER.json` e auto-crítica com métricas de qualidade. | `/generate <ideia>` | `python ecossistema.py generate "<ideia>"` |
| **AIDD Master** | **Os Blocos de Encaixe Perfeito (Lego):** Permite adicionar novas funções ao sistema sem quebrar nada do que já existia. | Clean Architecture em Fatias Verticais (`Vertical Slices`), Frontend Next.js 14 App Router nativo (Lei #11), SQLite WAL concorrente e OpenAPI. | `/master <modulo>` | `python ecossistema.py master add-module <modulo>` |
| **AIDD Enterprise** | **A Blindagem e Selo de Qualidade:** Verifica a autenticidade de cada componente com selo de segurança nível bancário. | Plataforma de Missão Crítica com injeção criptográfica SHA-256 de componentes, detecção de drift e conformidade Zero-Trust. | `/enterprise <tipo> <nome>` | `python ecossistema.py enterprise inject <tipo> <nome>` |
| **AIDD Ops** | **A Pista de Corrida e Abastecimento:** Prepara os servidores na nuvem, ajusta tráfego, sizing e deploy em produção. | Meta-Orquestrador de Infraestrutura: Sizing de VPS, Hardening SSH/Ansible, Traefik, Docker Swarm, Uptime Kuma e Preflight HTTP E2E. | `/ops plan <nicho>` | `python ecossistema.py ops plan "<nicho>"` |
| **AIDD Factory** | **A Central de Montagem & Fiação:** Cria o Gateway/BFF unificado, frontend e conecta todos os serviços entre si. | Gerador de aplicação e integração multi-serviço: Gateway FastAPI, Next.js, webhooks, compose unificado, .env e banco sob plano Ops. | `/factory --plano <arq> --pasta <dest>` | `python ecossistema.py factory --plano <arq> --pasta <dest>` |
| **AIDD Bridge** | **O Tradutor e Libertador de Código:** Pega apps de plataformas no-code/low-code e coloca para rodar em servidor próprio sem mensalidades extras. | Extrator, unificador e empacotador de projetos Lovable/Supabase para VPS própria: migração SQL para Postgres nativo/PostgREST e preservação visual. | `/bridge [comando]` | `python ecossistema.py bridge [scan\|convert-db\|merge\|pack]` |

---

## 🌐 SUPREMACIA AGNÓSTICA — Universalidade Total

O ecossistema segue a **Regra de Ouro da Universalidade**: nada aqui pertence a uma marca, modelo ou fornecedor específico. Você é 100% livre:

1. 💻 **Qualquer Sistema Operacional:** Roda igualzinho no Windows, Linux e macOS (100% Python puro).
2. 🤖 **Qualquer Assistente de IA (Multi-Harness):** Funciona nativamente no **Antigravity (agy), Claude Code, OpenCode, MimoCode, Cursor, Gemini CLI, Hermes e DeepSeek**.
3. 🧠 **Qualquer Modelo de IA:** Opera usando o próprio assistente da sua sessão (Zero custo adicional de token) ou via provedores externos locais/nuvem (Ollama, Groq, Anthropic, OpenAI).
4. 📦 **Escreva Uma Vez, Rode em Todos:** Uma habilidade (skill) ou comando criado é automaticamente distribuído para todos os assistentes em suas respectivas pastas (`.agent/`, `.claude/`, `.gemini/`, `.agents/`).

---

## 🚀 Como Usar na Prática

Você pode usar o ecossistema de duas formas simples, dependendo de como prefere trabalhar:

### Opção 1: Pelo Chat do seu Assistente (Modo Fácil / Sem Fricção)
Basta digitar os comandos com barra no chat do seu assistente de IA (Claude, Antigravity, Mimo, Cursor):

```bash
# 🔱 Disparar a Tríade Canônica de Criação:
/pure "Sistema de Gestão de Tarefas"       # Fluxo 01: Do Zero Puro via TDD Red-Green
/open "ERP para Clínicas com WhatsApp"     # Fluxo 02: Acelerado por Motores Open-Source
/freedom ./meu-export-lovable meu-saas    # Fluxo 03: Desacopla Low-Code preservando a UI

# Ferramentas Especialistas e Comandos Rápidos:
/forge .                                  # Blindar um projeto com regras de qualidade
/generate "Ideia de software"             # Transformar uma ideia em código funcional
/master produtos                          # Adicionar uma nova fatia vertical (rotas + banco + tela)
/enterprise skill seguranca-cibernetica   # Injetar segurança corporativa certificada SHA-256
/ops plan "Clínica com agendamento"       # Dimensionar infraestrutura de servidores e deploy
/factory --plano PLANO.json --pasta ./app # Gerar aplicação completa a partir do plano Ops

# Engenharia Procedimental Anti-Vibe Coding (Skills Universais):
/aidd-grill "Alinhar premissas e invariantes antes de codificar"
/aidd-spec "Gerar especificação técnica formal determinística"
/aidd-tdd "Ciclo Red-Green-Refactor com Zero Stubs"
/aidd-diagnose "Triage científica de falhas via grafo de impacto"
/aidd-handoff "Serializar contexto de sessão para troca de agentes"
```

### Opção 2: Pelo Terminal / Linha de Comando (Modo Engenheiro / CI/CD)
Controle total com determinismo absoluto via `python ecossistema.py`:

```bash
# 🔱 Execução Síncrona da Tríade Canônica de Ponta a Ponta:
python ecossistema.py run-fluxo --fluxo pure --nome "Tarefas" --slug tarefas --dominio produtividade --pasta ./projetos/tarefas
python ecossistema.py run-fluxo --fluxo open --nome "Clínica" --slug clinica --dominio saude --pasta ./projetos/clinica
python ecossistema.py run-fluxo --fluxo bridge --nome "Hub" --slug hub --dominio saas --pasta ./projetos/hub --origem ./exports/lovable

# Ver a saúde e status de todo o ecossistema
python ecossistema.py status

# Rodar a auditoria geral (Quality Gates Globais)
python ecossistema.py audit

# Testar o deploy de ponta a ponta em modo simulação seguro
python ecossistema.py ops deploy staging --dry-run
```

---

## 🛡️ Os 16 Portões de Segurança (Quality Gates Globais)

Antes de qualquer código ser considerado "pronto", ele é obrigado a passar por **16 testes automáticos e rigorosos** (como o raio-x e a alfândega de um aeroporto):

1. 🔍 **G_ECOSSISTEMA_INTEGRIDADE:** Garante que todas as pastas, arquivos essenciais e sintaxe Python estão 100% corretos.
2. ⚖️ **G_DRIFT_NUCLEO_COMPARTILHADO:** Compara os códigos compartilhados entre o Master e o Enterprise para impedir divergências acidentais.
3. 🔄 **G_HARNESS_COMPAT:** Confere se todos os assistentes de IA estão com as ferramentas sincronizadas.
4. 🔐 **G_SEGREDOS:** Varre todo o código em busca de senhas ou chaves de API acidentalmente esquecidas.
5. 💬 **G_CLI_HELP_CONSISTENCIA:** Valida via análise sintática (AST) se as opções explicadas nas mensagens batem exatamente com as flags reais da linha de comando.
6. 🧩 **G_COMPONENTE_AGNOSTICO:** Audita se novos componentes funcionam de forma universal em qualquer ambiente.
7. 🛑 **G_ZERO_HEADLESS:** Garante que o desenvolvedor humano esteja sempre no controle, bloqueando robôs ou subagentes ocultos que gastariam tokens em segundo plano.
8. 🐳 **G_INFRA_COMPOSE:** Audita arquivos Docker Compose delegando ao scanner Checkov e com parsing estruturado PyYAML, garantindo que não existam portas duplicadas, segredos, variáveis faltando ou erros de banco de dados.
9. 🐋 **G_HADOLINT:** Audita todos os Dockerfiles (existentes e gerados) contra as melhores práticas de segurança e sintaxe OCI, via Hadolint.
10. 🧪 **G_TESTES_REAIS:** Roda a suíte de testes de verdade (pytest) de cada ferramenta e reprova se qualquer teste falhar — nunca aceita "confia em mim".
11. 🏷️ **G_HONESTIDADE_ROTULO:** Impede que os próprios gates usem termos de marketing exagerados ("blindagem militar" e afins) em vez de descrever a cobertura real comprovada.
12. 🏛️ **G_ARQUITETURA_DELIVERABLE:** Audita, via análise sintática, se o código gerado e os módulos das ferramentas respeitam Clean Architecture/DDD — bloqueia banco de dados fora do lugar certo, dependências erradas e acoplamento direto entre camadas.
13. 📌 **G_DEPENDENCIAS_PIN_HASH:** Garante que dependências de terceiros estejam amarradas com hash (pinned) para evitar substituições maliciosas.
14. ✍️ **G_ESCRITOR_ATOMICO:** Verifica que arquivos são escritos de forma atômica (temporário + rename) para evitar corrupção em caso de falha.
15. 📋 **G_TRANSACTION_LOG_LRU:** Valida que logs de transações estão íntegros e não corrompidos, usando estratégias LRU.
16. 🌐 **G_UNIVERSAL_HARNESS:** Confere compatibilidade real com todos os harnesses de IA suportados.

> **Validação em um comando:** `python ecossistema.py audit` (Roda os gates em sequência e retorna `exit 0` apenas com 100% de aprovação).

---

## 📁 Mapa do Repositório

```text
ecossistema-aidd/
├── AGENTS.md                               ──► A Lei Fundamental e a governança canônica
├── MEMORY.md                               ──► A memória viva e o histórico consolidado
├── PLANO-EXECUCAO-ESTRUTURADO.json         ──► Telemetria e métricas reais de testes
├── README.md                               ──► Este portal unificado
├── ecossistema.py                          ──► A central de comando unificada (CLI)
│
├── componentes/                            ──► O cofre canônico de onde nascem todos os componentes
│   ├── compartilhado/                      ──► Habilidades e comandos universais
│   └── aidd-master/                        ──► Componentes do AIDD Master
│
├── gates/                                  ──► Os 16 Portões de Segurança determinísticos
│
├── tools/                                  ──► As 8 Ferramentas Homologadas (100% funcionais)
│   ├── aidd-forge/                         ──► Bootstrap e blindagem de governança
│   ├── aidd-planner/                       ──► Planejamento BDD/SDD e contratos formais de handoff
│   ├── aidd-generator/                     ──► Fábrica autônoma de software (8 fases, TDD Red-Green)
│   ├── aidd-master/                        ──► Monólito modular VSA e Frontend Next.js Padrão-Ouro
│   ├── aidd-enterprise/                    ──► Missão crítica e validação criptográfica SHA-256
│   ├── aidd-ops/                           ──► Meta-orquestrador de infraestrutura, Docker e deploy VPS
│   ├── aidd-factory/                       ──► Gerador de aplicação, BFF e integração multi-serviço
│   └── aidd-bridge/                        ──► Extrator e empacotador de apps low-code para VPS própria
│
└── docs/                                   ──► Toda a inteligência documentada
    ├── planos/                             ──► Planos táticos e de auditoria
    │   ├── feitos/                         ──► Concluídos (status real, não alegado)
    │   ├── fazendo/                        ──► Em execução
    │   ├── a-fazer/                        ──► Aguardando execução
    │   └── INDEX.md                        ──► Gerado por scripts/atualizar_index_planos.py — não editar à mão
    ├── protocolos/                         ──► Protocolos canônicos de agnosticidade
    ├── relatorios/                         ──► Relatórios formais e auditorias
    ├── prompts/                            ──► Biblioteca de prompts
    ├── features/                           ──► Documentação de features
    ├── explicacoes/                         ──► Explicações detalhadas
    ├── melhorias/                          ──► Registro de melhorias
    └── testes/                             ──► Baterias de testes E2E e relatórios formais
```

---

## 📜 Licença

Distribuído sob a licença MIT. Construído para ser livre, universal e soberano.
