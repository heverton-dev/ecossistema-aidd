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

Quer forçar manualmente ou adicionar uma dependência nova (skill ou MCP de terceiro)? Digite `/dependencia bootstrap` (ou `/dependencia skill <nome>`, `/dependencia mcp <nome>`) no chat. Só use o terminal (`python ecossistema.py dependencia bootstrap`) se preferir.

---

## 🏛️ A Fábrica de Software AIDD: As 6 Ferramentas Integradas

```text
                               ┌─────────────────────────────┐
                               │   ECOSSISTEMA AIDD (Monorepo)│
                               └──────────────┬──────────────┘
                                              │
    ┌──────────────┬──────────────────┼─────────────────┬──────────────┬──────────────┐
    ▼              ▼                  ▼                 ▼              ▼              ▼
[ aidd-forge ] [ aidd-generator ] [ aidd-master ] [ aidd-enterprise ] [ aidd-ops ] [ aidd-bridge ]
 Linha de Montagem Fábrica Autônoma   Blocos de Lego   Selo de Auditoria Pista & Entrega  Ponte Low-Code
  & Blindagem    (Ideia -> Código)    Modular & Banco  Zero-Trust & Hashes Infra & Nuvem  -> VPS Nativa
   (/forge)         (/generate)          (/master)        (/enterprise)     (/ops)         (/bridge)
```

---

## ⚡ As 6 Ferramentas: Do Leigo ao PhD

| Ferramenta | Analogia do Dia a Dia (Leigo) | Rigor Arquitetural (PhD / Arquiteto) | Como usar no Chat | Comando no Terminal (CLI) |
| :--- | :--- | :--- | :---: | :--- |
| **AIDD Forge** | **A Fundação e o Chassi:** Prepara o terreno, coloca cercas de proteção e impede que a IA faça bagunça. | Bootstrap determinístico, fatiamento em micro-ambientes efêmeros (`.aidd/pipeline/`), context-purge estrito e 7 Quality Gates locais. | `/forge [pasta]` | `python ecossistema.py forge init [pasta]` |
| **AIDD Generator** | **A Linha de Montagem Autônoma:** Você fala o que quer e a fábrica entrega o software pronto com testes. | Pipeline autônomo de 8 fases (Intake -> Pesquisa -> Análise -> Design -> Decisão -> Criação -> Docs -> Implementação) com JSON Schemas Draft 2020-12. | `/generate <ideia>` | `python ecossistema.py generate "<ideia>"` |
| **AIDD Master** | **Os Blocos de Encaixe Perfeito (Lego):** Permite adicionar novas funções ao sistema sem quebrar nada do que já existia. | Clean Architecture em Fatias Verticais (`Vertical Slices`), SQLite concorrente em modo WAL, Result Monad funcional e auto-documentação OpenAPI. | `/master <modulo>` | `python ecossistema.py master add-module <modulo>` |
| **AIDD Enterprise** | **A Blindagem e Selo de Qualidade:** Verifica a autenticidade de cada componente com selo de segurança nível bancário. | Plataforma de Missão Crítica com injeção criptográfica SHA-256 de componentes (`skill`, `mcp`, `hook`, `rule`), conformidade Zero-Trust e RLS estrito. | `/enterprise <tipo> <nome>` | `python ecossistema.py enterprise inject <tipo> <nome>` |
| **AIDD Ops** | **A Pista de Corrida e Abastecimento:** Pega o software pronto, prepara os servidores na nuvem, ajusta o tráfego e põe para rodar. | Meta-Orquestrador de Infraestrutura: Sizing inteligente de VPS, Hardening SSH anti-injeção, MCPs de borda (Cloudflare/Docker), Compose e Preflight HTTP E2E. | `/ops plan <nicho>` | `python ecossistema.py ops plan "<nicho>"` |
| **AIDD Bridge** | **O Tradutor e Libertador de Código:** Pega apps de plataformas no-code/low-code e coloca para rodar em servidor próprio sem mensalidades extras. | Extrator, unificador e empacotador de projetos Lovable/Supabase para VPS própria: migração SQL para Postgres nativo/PostgREST, unificação de rotas/telas e Docker Compose Swarm com Traefik/Kong. | `/bridge [comando]` | `python ecossistema.py bridge [scan\|convert-db\|merge\|pack]` |

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

### Opção 1: Pelo Chat do seu Assistente (Modo Fácil / Sem Código)
Basta digitar os comandos com barra no chat do seu assistente de IA (Claude, Antigravity, Mimo, Cursor):

```bash
# 1. Transformar uma ideia em código funcional
/generate Sistema de delivery para farmácias com controle de entregas

# 2. Blindar um projeto com regras de qualidade
/forge .

# 3. Adicionar uma nova função completa (rotas + banco de dados + tela)
/master produtos

# 4. Injetar segurança corporativa certificada
/enterprise skill seguranca-cibernetica

# 5. Dimensionar a infraestrutura de servidores e deploy
/ops plan "Farmácias com alto volume de entrega"
```

### Opção 2: Pelo Terminal / Linha de Comando (Modo Engenheiro / CI/CD)
Controle total com determinismo absoluto via `python ecossistema.py`:

```bash
# Ver a saúde e status de todo o ecossistema
python ecossistema.py status

# Rodar a auditoria geral (Os 8 Portões de Segurança)
python ecossistema.py audit

# Planejar a infraestrutura de servidores para um nicho de negócio
python ecossistema.py ops plan "Clínica médica com agendamento"

# Testar o deploy de ponta a ponta em modo simulação seguro
python ecossistema.py ops deploy staging --dry-run
```

---

## 🛡️ Os 12 Portões de Segurança (Quality Gates Globais)

Antes de qualquer código ser considerado "pronto", ele é obrigado a passar por **12 testes automáticos e rigorosos** (como o raio-x e a alfândega de um aeroporto):

1. 🔍 **G_ECOSSISTEMA_INTEGRIDADE:** Garante que todas as pastas, arquivos essenciais e sintaxe Python estão 100% corretos.
2. ⚖️ **G_DRIFT_NUCLEO_COMPARTILHADO:** Compara os códigos compartilhados entre o Master e o Enterprise para impedir divergências acidentais.
3. 🔄 **G_HARNESS_COMPAT:** Confere se todos os assistentes de IA (Claude, Antigravity, Mimo) estão com as ferramentas sincronizadas.
4. 🔐 **G_SEGREDOS:** Varre todo o código em busca de senhas ou chaves de API acidentalmente esquecidas.
5. 💬 **G_CLI_HELP_CONSISTENCIA:** Valida via análise sintática (AST) se as opções explicadas nas mensagens batem exatamente com as flags reais da linha de comando.
6. 🧩 **G_COMPONENTE_AGNOSTICO:** Audita se novos componentes funcionam de forma universal em qualquer ambiente.
7. 🛑 **G_ZERO_HEADLESS:** Garante que o desenvolvedor humano esteja sempre no controle, bloqueando robôs ou subagentes ocultos que gastariam tokens em segundo plano.
8. 🐳 **G_INFRA_COMPOSE:** Audita arquivos Docker Compose delegando ao scanner Checkov e com parsing estruturado PyYAML, garantindo que não existam portas duplicadas, segredos, variáveis faltando ou erros de banco de dados.
9. 🐋 **G_HADOLINT:** Audita todos os Dockerfiles (existentes e gerados) contra as melhores práticas de segurança e sintaxe OCI, via Hadolint.
10. 🧪 **G_TESTES_REAIS:** Roda a suíte de testes de verdade (pytest) de cada ferramenta e reprova se qualquer teste falhar — nunca aceita "confia em mim".
11. 🏷️ **G_HONESTIDADE_ROTULO:** Impede que os próprios gates usem termos de marketing exagerados ("blindagem militar" e afins) em vez de descrever a cobertura real comprovada.
12. 🏛️ **G_ARQUITETURA_DELIVERABLE:** Audita, via análise sintática, se o código gerado e os módulos das ferramentas respeitam Clean Architecture/DDD — bloqueia banco de dados fora do lugar certo, dependências erradas e acoplamento direto entre camadas.

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
│   │   └── src-core/                       ──► Núcleo único compartilhado entre Master e Enterprise
│   ├── aidd-ops/                           ──► MCPs, comandos e receitas de infraestrutura
│   ├── aidd-master/                        ──► Componentes do AIDD Master
│   ├── aidd-enterprise/                    ──► Componentes do AIDD Enterprise
│   └── aidd-generator/                     ──► Componentes do AIDD Generator
│
├── gates/                                  ──► Os 12 Portões de Segurança determinísticos
│
├── tools/                                  ──► As 6 Ferramentas Homologadas (100% funcionais)
│   ├── aidd-forge/                         ──► Bootstrap e blindagem de governança
│   ├── aidd-generator/                     ──► Fábrica autônoma de software (8 fases)
│   ├── aidd-master/                        ──► Monólito modular e fatias verticais (Clean Architecture)
│   ├── aidd-enterprise/                    ──► Missão crítica e validação SHA-256
│   ├── aidd-ops/                           ──► Meta-orquestrador de infraestrutura e deploy
│   └── aidd-bridge/                        ──► Extrator e empacotador de apps low-code para VPS própria
│
└── docs/                                   ──► Toda a inteligência documentada
    ├── planos/                             ──► Planos táticos e de auditoria
    │   ├── feitos/                         ──► Concluídos (status real, não alegado)
    │   ├── fazendo/                        ──► Em execução
    │   ├── a-fazer/                        ──► Aguardando execução
    │   └── INDEX.md                        ──► Gerado por scripts/atualizar_index_planos.py — não editar à mão
    ├── protocolos/                         ──► Protocolos canônicos de agnosticidade
    └── testes/                             ──► Baterias de testes E2E e relatórios formais
```

---

## 📜 Licença

Distribuído sob a licença MIT. Construído para ser livre, universal e soberano.
