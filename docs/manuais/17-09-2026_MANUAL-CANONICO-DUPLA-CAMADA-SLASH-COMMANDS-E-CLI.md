# Manual Canônico: A Arquitetura de Dupla Camada (Slash Commands & CLI Determinística)

> **Status:** Referência Oficial de Operação do Ecossistema AIDD  
> **Caminho:** `docs/manuais/MANUAL-CANONICO-DUPLA-CAMADA-SLASH-COMMANDS-E-CLI.md`  
> **Público:** Desenvolvedores, Engenheiros de Software, Arquitetos e Usuários de Negócio  

---

## 1. Visão Geral e Filosofia da Dupla Camada

O Ecossistema AIDD foi projetado para eliminar o abismo entre usabilidade humana e rigor de engenharia. Para isso, adota estritamente o **Princípio da Dupla Camada Universal**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAMADA 1: ZERO FRICÇÃO HUMANA (Slash Commands & Linguagem Natural)          │
│ • Público: Usuários de negócio, Product Managers, devs júnior a seniores.   │
│ • Interface: Conversação em chat nas IDEs (Antigravity, Claude, Cursor...). │
│ • Experiência: 1 linha de comando ou intenção livre. Zero flags para decorar│
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ O Agente AI interpreta a intenção,
                                       │ alinha os parâmetros e invoca:
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CAMADA 2: ENGENHARIA DETERMINÍSTICA (CLI Unificada & Quality Gates)         │
│ • Público: CI/CD, pipelines automatizados, scripts e auditorias estritas.   │
│ • Interface: Terminal PowerShell/Bash via `python ecossistema.py <tool>`.   │
│ • Regra Inviolável: 100% determinístico, zero stubs, saída binária (0 ou 1).│
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Matriz de Comandos da Tríade Canônica e Ferramentas do Ecossistema

---

### 1. `aidd-forge` — Fundação, Governança e Regras Invioláveis

- **Papel:** Ponto zero de qualquer projeto. Injeta a constituição agêntica (`AGENTS.md`), pre-commit hooks, skills canônicas e isolamento de contexto.

#### Camada 1: Zero Fricção (Slash Commands)
- `/forge`
  * *Caso de Uso:* Inicializa a governança canônica no diretório atual.
- `/forge ./meu-projeto`
  * *Caso de Uso:* Prepara uma pasta alvo externa com Git, ponteiros de harness (`.agents`, `.claude`) e Quality Gates.
- `/aidd-init`
  * *Caso de Uso:* Alias universal para a primeira inicialização de qualquer repositório.

#### Camada 2: CLI Determinística
```powershell
# Inicialização e injeção de governança
python ecossistema.py forge init <caminho_projeto>

# Auditoria mecânica das 15 regras de governança (G01 a G15)
python ecossistema.py forge audit <caminho_projeto>
```

#### Quality Gates Associados
- `G01` a `G15` (AST Python): Valida presença do `AGENTS.md` na raiz, ausência da pasta legada `.agent`, tamanho de skills <= 20 palavras e ponteiros limpos de 1 linha em `CLAUDE.md` e `GEMINI.md`.

---

### 2. `aidd-planner` — Motor de Planejamento, Intake e Combustão (SDD/BDD)

- **Papel:** É o cérebro que antecede a construção. Realiza o alinhamento de negócio e gera o contrato `PLANNER.json` canônico que abastece os 3 fluxos.

#### Camada 1: Zero Fricção (Slash Commands)
- `/planner "Quero um sistema de entregas para a CTT Portugal com frotas e rotas"`
  * *Caso de Uso:* O agente conduz a entrevista socrática de requisitos e gera o plano escolhendo o fluxo mais adequado.
- `/planner 1 "Criar MVP de pagamentos PIX do zero puro"`
  * *Caso de Uso:* Gera diretamente a planta baixa estruturada para o **Fluxo 01 (Generator)**.
- `/planner 2 "Hub de atendimento multicanal com WhatsApp e n8n"`
  * *Caso de Uso:* Gera a planta baixa com catálogo open-source para o **Fluxo 02 (Factory)**.
- `/planner 3 "Resgatar protótipo do Lovable e conectar ao PostgreSQL"`
  * *Caso de Uso:* Gera a planta baixa com mapeamento de banco para o **Fluxo 03 (Bridge)**.

#### Camada 2: CLI Determinística
```powershell
# Inicialização direta do PLANNER.json canônico
python ecossistema.py planner init --fluxo <1|2|3> --nome "Nome do Projeto" --pasta ./destino [--force]

# Validação do plano contra o JSON Schema e regras invariantes
python ecossistema.py planner validate ./destino/PLANNER.json

# Exportação do plano para motores downstream (ex: Factory)
python ecossistema.py planner export ./destino/PLANNER.json --formato factory --saida ./destino/plano_factory.json

# Execução dos Quality Gates de planejamento
python ecossistema.py planner audit ./destino
```

#### Quality Gates Associados
- `G_PLANNER_SCHEMA.py`: Garante conformidade total com o JSON Schema e ausência de stubs (`TODO`, `FIXME`).
- `G_PLANNER_SINE_QUA_NON.py`: Audita se `/swagger`, `/webhooks`, `/mcp` e `/docs` estão com `ativo: true`.
- `G_PLANNER_COERENCIA_FLUXO.py`: Valida se o payload corresponde aos requisitos estritos do fluxo alvo (1, 2 ou 3).

---

### 3. `aidd-generator` — Fluxo 01: Construção do Zero Puro (TDD Red-Green)

- **Papel:** Fábrica autônoma de software que transforma especificações em código Python de produção através de um pipeline de 8 fases com TDD estrito.

#### Camada 1: Zero Fricção (Slash Commands)
- `/generate "Sistema de agendamento de consultas médicas"`
  * *Caso de Uso:* Dispara o pipeline completo de 8 fases a partir de uma ideia em linguagem natural.
- `/generate --fases 1,2,3 "Módulo de faturamento recorrente"`
  * *Caso de Uso:* Executa apenas a especificação, arquitetura e geração dos testes TDD antes de codificar.

#### Camada 2: CLI Determinística
```powershell
# Execução do pipeline completo (8 fases)
python ecossistema.py generate "Ideia do Projeto"

# Execução direcionada a partir de plano existente
python ecossistema.py generate --plano ./PLANNER.json --pasta ./src
```

#### Quality Gates Associados
- `G_TESTES_REAIS`: Execução obrigatória de suítes `pytest` com zero stubs e validação Red-Green.
- `Fase 8 (Auditoria AST)`: Impede commits com blocos `pass` vazios ou funções não tipadas.

---

### 4. `aidd-factory` — Fluxo 02: Motores Open-Source & Stacks Integradas

- **Papel:** Curadoria e orquestração de softwares livres consolidados (Evolution API, Chatwoot, n8n, Redis), gerando Gateway FastAPI VSA, Docker Compose unificado e scripts de banco.

#### Camada 1: Zero Fricção (Slash Commands)
- `/factory --plano ./PLANNER.json --pasta ./minha-stack`
  * *Caso de Uso:* Gera toda a infraestrutura de containers, proxy reverso e Super-App a partir do plano do planner.
- `/factory "Adicionar Redis e RabbitMQ à aplicação"`
  * *Caso de Uso:* O agente dimensiona as portas, adiciona ao compose e regenera os scripts de banco sem colisão.

#### Camada 2: CLI Determinística
```powershell
# Geração completa da stack via pipeline Factory
python ecossistema.py factory --plano ./plano_factory.json --pasta ./minha-stack [--sem-llm]
```

#### Quality Gates Associados
- `G_FACTORY_ANALYSIS.py`: Valida esquema, ferramentas e dimensionamento de hardware.
- `G_FACTORY_COMPOSE.py`: Valida sintaxe YAML, rede `aidd_internal`, healthchecks e zero colisão de portas.
- `G_FACTORY_ENV.py`: Garante presença de variáveis e ausência de senhas padrão.
- `G_FACTORY_INIT_DB.py`: Audita scripts SQL com `set -euo pipefail` e GRANTs estritos.
- `G_FACTORY_INTEGRATION.py`: Valida fatias VSA, endpoints tipados e o Quarteto *Sine Qua Non*.
- `G_FACTORY_MVP.py`: Compilação Python sem erros de sintaxe e validação AST anti-stubs.

---

### 5. `aidd-bridge` — Fluxo 03: Desacoplamento Low-Code (Lovable/v0/Bolt)

- **Papel:** Liberta aplicações presas em plataformas low-code, remove o vendor lock-in (Supabase mocks), migra o banco para PostgreSQL nativo e empacota o frontend para VPS.

#### Camada 1: Zero Fricção (Slash Commands)
- `/bridge scan ./app-lovable`
  * *Caso de Uso:* Varre a aplicação exportada e identifica chamadas a APIs mockadas e dependências proprietárias.
- `/bridge convert-db ./app-lovable --saida ./db`
  * *Caso de Uso:* Transforma os esquemas do Supabase em migrações SQL para PostgreSQL limpo.
- `/bridge pack ./app-lovable --destino ./producao`
  * *Caso de Uso:* Conteineriza o frontend com Nginx e proxy reverso pronto para subir na VPS.

#### Camada 2: CLI Determinística
```powershell
python ecossistema.py bridge scan <diretorio>
python ecossistema.py bridge convert-db <diretorio> [--output <dest>]
python ecossistema.py bridge pack <diretorio> --dest <pasta_producao>
```

#### Quality Gates Associados
- `G_BRIDGE_SCAN`: Audita ausência de chaves de API mockadas e código remanescente de lock-in.
- `G_BRIDGE_SQL`: Valida a compatibilidade ANSI do schema PostgreSQL gerado.

---

### 6. `aidd-master` — Harmonização em Monólito Modular (VSA)

- **Papel:** Ponto de convergência universal onde os fluxos 1, 2 e 3 se tornam um Monólito Modular robusto com Vertical Slice Architecture (VSA), EventBus assíncrono e SQLite WAL / PostgreSQL.

#### Camada 1: Zero Fricção (Slash Commands)
- `/master init ./meu-monolito`
  * *Caso de Uso:* Inicializa o Shared Kernel (`core/`) com banco de dados, eventos e Quarteto *Sine Qua Non*.
- `/master add-module frotas`
  * *Caso de Uso:* Cria uma fatia vertical completa de domínio (`models.py`, `repositories.py`, `services.py`, `routes.py` e testes).

#### Camada 2: CLI Determinística
```powershell
# Inicialização do kernel compartilhado
python ecossistema.py master init <pasta_projeto>

# Adição de nova fatia vertical de negócio
python ecossistema.py master add-module <nome_modulo> --pasta <pasta_projeto>
```

#### Quality Gates Associados
- `G_MASTER_ISOLATION`: Garante que nenhuma fatia vertical acesse repositórios de outra fatia sem passar por eventos ou contratos públicos.
- `G_MASTER_TESTS`: Execução automatizada e aprovação de 100% dos testes unitários da fatia.

---

### 7. `aidd-enterprise` — Blindagem de Missão Crítica & Resiliência SHA-256

- **Papel:** Injeta componentes corporativos imutáveis e auditados contra adulteração via SHA-256 (Circuit Breakers, Rate Limiting distribuído, Retries com backoff, rastreabilidade `trace_id`).

#### Camada 1: Zero Fricção (Slash Commands)
- `/enterprise inject component circuit_breaker`
  * *Caso de Uso:* Injeta o padrão de Circuit Breaker com auditoria criptográfica.
- `/enterprise inject skill auth`
  * *Caso de Uso:* Injeta módulos de autenticação segura JWT com revogação de tokens em memória.
- `/enterprise audit`
  * *Caso de Uso:* Varre todos os componentes injetados e compara os hashes SHA-256 contra adulterações.

#### Camada 2: CLI Determinística
```powershell
# Injeção de componente enterprise
python ecossistema.py enterprise inject component <nome> --pasta <destino>

# Auditoria de integridade criptográfica
python ecossistema.py enterprise audit <pasta_projeto>
```

#### Quality Gates Associados
- `G_ENTERPRISE_INTEGRITY`: Bloqueia o deploy se qualquer caractere de componente blindado tiver sido adulterado.

---

### 8. `aidd-ops` — Orquestração de Infraestrutura, Segurança e Produção

- **Papel:** Provisionamento determinístico de VPS via SSH, criptografia de segredos com `sops + age`, proxy reverso SSL (Traefik/Nginx) e monitoramento com Uptime Kuma.

#### Camada 1: Zero Fricção (Slash Commands)
- `/ops "Deploy da aplicação CTT na VPS 192.168.1.10 com SSL e monitoramento"`
  * *Caso de Uso:* O agente gera os playbooks, criptografa os segredos e sobe o stack na máquina remota.
- `/ops init-vps`
  * *Caso de Uso:* Hardening inicial do servidor (UFW firewall, Docker, SSH key-only).

#### Camada 2: CLI Determinística
```powershell
# Planejamento e provisionamento da infraestrutura
python ecossistema.py ops "<requisitos>" --pasta <destino>
```

#### Quality Gates Associados
- `G_INFRA_COMPOSE`: Audita a integridade do docker-compose e init.sql do ops.
- `G_HADOLINT`: Valida Dockerfiles conforme melhores práticas OCI.

---

## 3. Comandos Transversais de Apoio

| Slash Command | Comando CLI Equivalente | Finalidade |
|---|---|---|
| `/melhoria <pedido>` | `python ecossistema.py melhoria init --pedido "..."` | Realiza análise profunda de código e gera relatórios em `docs/melhorias/`. |
| `/plan <nome>` | `python ecossistema.py plan init <nome>` | Gerencia planos de iniciativa e auditoria em `docs/planos/`. |
| `/orchestrate <plano>`| `python ecossistema.py orchestrate <plano>` | Gera flight plans para execução de tarefas via ORCA ADE ou Git Worktrees. |
| *(Auditoria Geral)* | `python ecossistema.py audit` | Dispara o Meta-Gate global de integridade do ecossistema. |
| *(Status)* | `python ecossistema.py status` | Exibe o inventário de ferramentas instaladas e skills universais ativas. |

---

## 4. Guia Rápido de Resolução de Erros nos Quality Gates

1. **Gate reprovou com Exit Code 1:**
   - O terminal exibe a lista de violações iniciadas por `[X]`.
   - **Solução:** O agente corrige cirurgicamente os arquivos identificados (sem reescrever o projeto inteiro) e reexecuta o gate até atingir `Passed` (Exit Code 0).
2. **Presença de Stubs:**
   - Termos como `TODO`, `FIXME` ou arrays vazios em campos obrigatórios são barrados na compilação do AST.
   - **Solução:** Preencher com implementações funcionais ou contratos mínimos válidos.
