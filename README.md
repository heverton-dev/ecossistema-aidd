# 🌐 Ecossistema AIDD Unificado

> **Repositório Central de Engenharia Agêntica de Software (AI-Driven Development)**  
> **GitHub:** `https://github.com/heverton-dev/ecossistema-aidd`  
> **Orquestração:** ORCA ADE (Lead: Antigravity | Governance: Claude Code | Integration: MimoCode)

---

## 🏛️ Visão Geral

O **Ecossistema AIDD** reúne sob uma arquitetura unificada, modular e de altíssimo determinismo as 4 ferramentas canônicas da metodologia AIDD. Cada ferramenta desempenha um papel cirúrgico no ciclo de vida do software orientado por agentes de IA:

```text
                               ┌─────────────────────────────┐
                               │   ECOSSISTEMA AIDD (Monorepo)│
                               └──────────────┬──────────────┘
                                              │
         ┌──────────────────┬─────────────────┴────────────────┬───────────────────┐
         ▼                  ▼                                  ▼                   ▼
  [ tools/aidd-forge ] [ tools/aidd-generator ]     [ tools/aidd-master ]  [ tools/aidd-master-enterprise ]
  Bootstrap, Fencing    Fábrica Autônoma             Monólito Modular       Missão Crítica Regulada
  & Context-Purge       (Pipeline 8 Fases)           Vertical Slices & DB   Hashes SHA-256 & Zero-Trust
       (/forge)            (/generate)                    (/master)                 (/enterprise)
```

---

## ⚡ As 4 Ferramentas Integradas

| Ferramenta | Diretório | Slash Command | Objetivo Principal |
| :--- | :--- | :--- | :--- |
| **AIDD Forge** | `tools/aidd-forge` | `/forge [caminho]` | Bootstrap de governança agêntica, micro-ambientes isolados por fase (`.aidd/pipeline/`), context-purge e 7 Quality Gates determinísticos. |
| **AIDD Generator** | `tools/aidd-generator` | `/generate <ideia>` | Fábrica autônoma que transforma uma descrição em linguagem natural em software completo através de 8 fases com contratos JSON Schema Draft 2020-12. |
| **AIDD Master** | `tools/aidd-master` | `/master <modulo>` | Framework para monólitos modulares de alta performance com fatias verticais (`Vertical Slices`), SQLite concorrente em modo WAL, Result Monad e Swagger Studio. |
| **AIDD Master Enterprise** | `tools/aidd-master-enterprise` | `/enterprise <tipo> <nome>` | Plataforma corporativa de missão crítica com injeção transacional de componentes (`skill`, `rule`, `mcp`), validação de hashes criptográficos SHA-256 e RLS. |

---

## 🚀 Como Usar

### 1. No Chat de Qualquer Harness (Slash Commands Universais)

Basta clonar o repositório e abrir no seu assistente ou IDE preferido (Antigravity, Claude Code, Cursor, OpenCode, MimoCode):

- **`/forge [caminho]`**: Inicializa e blinda qualquer repositório alvo.
- **`/generate <ideia>`**: Constrói um novo sistema do zero com arquitetura e testes.
- **`/master <modulo>`**: Adiciona uma nova fatia vertical de negócio (`src/modules/<modulo>/`).
- **`/enterprise <tipo> <nome>`**: Injeta um componente homologado com verificação de integridade SHA-256.

### 2. Via CLI Unificada (`ecossistema.py`)

```bash
# Ver o status de todas as ferramentas e componentes
python ecossistema.py status

# Rodar a auditoria e Quality Gates de integridade global
python ecossistema.py audit

# Disparar o aidd-forge
python ecossistema.py forge init meu-novo-projeto

# Disparar o pipeline do aidd-generator
python ecossistema.py generate "Sistema de gerenciamento de frotas com telemetria"

# Criar nova fatia modular no aidd-master
python ecossistema.py master add-module estoque

# Injetar componente certificado no aidd-master-enterprise
python ecossistema.py enterprise inject skill auth-oauth2
```

---

## 📁 Estrutura de Diretórios

```text
ecossistema-aidd/
├── AGENTS.md                               ──► Governança canônica unificada e fonte única de verdade
├── PLANO-EXECUCAO-ESTRUTURADO.json         ──► Telemetria e persistência estruturada do ecossistema
├── README.md                               ──► Portal central do ecossistema
├── ecossistema.py                          ──► CLI unificada de orquestração
│
├── .agent/                                 ──► Compatibilidade canônica (Antigravity, OpenCode, MimoCode)
│   ├── commands/                           ──► Slash commands: forge, generate, master, enterprise
│   └── skills/                             ──► Skills espelhadas para o ambiente
│
├── .claude/                                ──► Configurações para Claude Code
│   ├── CLAUDE.md                           ──► Apontamento para ../AGENTS.md
│   └── commands/                           ──► Comandos /forge, /generate, /master, /enterprise
│
├── .cursor/                                ──► Regras de contexto para Cursor IDE
│   └── rules/                              ──► Diretivas operacionais
│
├── gates/                                  ──► Meta-Quality Gates determinísticos
│   └── G_ECOSSISTEMA_INTEGRIDADE.py        ──► Auditoria automatizada de integridade estrutural e sintática
│
├── skills/                                 ──► Definições oficiais das 4 skills universais
│   ├── aidd-forge-runner/                  ──► Runner do AIDD Forge
│   ├── aidd-generator-runner/              ──► Runner do AIDD Generator
│   ├── aidd-master-runner/                 ──► Runner do AIDD Master
│   └── aidd-enterprise-runner/             ──► Runner do AIDD Master Enterprise
│
├── tools/                                  ──► Os 4 Projetos Homologados (100% intactos e autocontidos)
│   ├── aidd-forge/                         ──► Repositório completo do AIDD Forge
│   ├── aidd-generator/                     ──► Repositório completo do AIDD Generator
│   ├── aidd-master/                        ──► Repositório completo do AIDD Master
│   └── aidd-master-enterprise/             ──► Repositório completo do AIDD Master Enterprise
│
└── planos/                                 ──► Planos táticos e de orquestração
    └── PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md  ──► Especificação do ecossistema
```

---

## 🛡️ As 5 Camadas da Engenharia Agêntica

1. **Camada 1: Contratos e Schemas:** Estruturas de dados regidas por JSON Schema (Draft 2020-12) antes de qualquer geração.
2. **Camada 2: Determinismo Primeiro:** Mecânica em Python puro e scripts diretos (Zero Token Fallacy).
3. **Camada 3: Gates Mecânicos:** Quality Gates binários com bloqueio estrito (`exit 0` / `exit 1`).
4. **Camada 4: Persistência Estruturada:** Estado em arquivos JSON/SQLite auditáveis, nunca na memória volátil do chat.
5. **Camada 5: Bundles Modulares:** Subprojetos e fatias de negócio autocontidas, desacopladas e 100% testadas.

---

## 📜 Licença

Distribuído sob a licença MIT. Consulte os arquivos `LICENSE` em cada subferramenta para termos específicos.