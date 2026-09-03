# PROMPT MESTRE DE ORQUESTRAÇÃO ORCA — IMPLEMENTAÇÃO DO ECOSSISTEMA AIDD

> **Destinatário:** Agente Orquestrador Principal (Antigravity no ORCA ADE)  
> **Espaço de Trabalho:** `C:\Users\trcnologia\Desktop\ecossistema-aidd`  
> **Repositório Remoto:** `https://github.com/heverton-dev/ecossistema-aidd.git`  
> **Fonte dos Projetos Homologados:** `C:\Users\trcnologia\Desktop\proj_aidd`  
> **Referência:** `planos/PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md`  

---

## 🇧🇷 VERSÃO EM PORTUGUÊS (PT-BR)

Você é o **Agente Orquestrador Mestre** operando dentro do **ORCA ADE** para inicializar e construir o repositório central unificado **`ecossistema-aidd`**.

Sua missão é executar de ponta a ponta o plano estratégico definido em `planos/PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md`, utilizando a **orquestração em tríade (ORC 3)** com worktrees isoladas e agentes delegados:
* **Orquestrador Central:** Antigravity (sua sessão atual).
* **Agente Especialista em Governança & Skills:** Claude Code (worktree isolada).
* **Agente Especialista em Integração & Testes:** MimoCode (worktree isolada).

---

### ETAPAS DE EXECUÇÃO MANDATÓRIAS:

#### 1. Inicialização do Repositório Git e Conexão Remota
- Execute `git init` no diretório raiz (`C:\Users\trcnologia\Desktop\ecossistema-aidd`).
- Defina a branch principal como `main`: `git branch -M main`.
- Adicione o controle remoto: `git remote add origin https://github.com/heverton-dev/ecossistema-aidd.git`.
- Crie um arquivo `.gitignore` robusto ignorando `.env`, caches (`__pycache__`, `.pytest_cache`), logs e artefatos temporários.

#### 2. Importação Não-Destrutiva das 4 Ferramentas Homologadas
- Copie de forma autocontida e integral os 4 projetos homologados da pasta de origem `C:\Users\trcnologia\Desktop\proj_aidd` para o diretório `tools/`:
  * `C:\Users\trcnologia\Desktop\proj_aidd\aidd-forge` ➔ `tools/aidd-forge/`
  * `C:\Users\trcnologia\Desktop\proj_aidd\aidd-generator` ➔ `tools/aidd-generator/`
  * `C:\Users\trcnologia\Desktop\proj_aidd\aidd-master` ➔ `tools/aidd-master/`
  * `C:\Users\trcnologia\Desktop\proj_aidd\aidd-master-enterprise` ➔ `tools/aidd-master-enterprise/`
- **Regra Inegociável:** Mantenha os testes unitários, scripts e manifestos de cada projeto 100% intactos e funcionais.

#### 3. Governança Canônica Unificada & 4 Skills com Slash Commands
- Crie na raiz o documento mestre de governança `AGENTS.md` definindo as regras inegociáveis de transparência, determinismo e economia severa de tokens para todo o ecossistema.
- Configure os espelhos canônicos `.agent/`, `.claude/` e `.cursor/rules/`.
- Crie e registre as 4 Skills universais com cabeçalhos YAML Frontmatter padrão em `.agent/skills/` e seus respectivos Slash Commands em `.agent/commands/` e `.claude/commands/`:
  1. **`/forge [caminho]`** (`skills/aidd-forge-runner`): Dispara o motor de bootstrap e blindagem AIDD.
  2. **`/generate <ideia>`** (`skills/aidd-generator-runner`): Dispara o pipeline autônomo de 8 fases do gerador.
  3. **`/master <modulo>`** (`skills/aidd-master-runner`): Adiciona fatias verticais modulares desacopladas no Shared Kernel.
  4. **`/enterprise <tipo> <nome>`** (`skills/aidd-enterprise-runner`): Injeta componentes corporativos regulados com validação criptográfica SHA-256.

#### 4. Meta-Orquestrador CLI & Quality Gates Globais
- Crie o script CLI unificado na raiz: `ecossistema.py` (ou `aidd.py`), permitindo invocar qualquer uma das ferramentas via linha de comando comum.
- Crie o Quality Gate `gates/G_ECOSSISTEMA_INTEGRIDADE.py` que testa se todas as 4 ferramentas mantêm seus testes verdes e se as skills do ecossistema estão devidamente ancoradas.

#### 5. Documentação de Alto Nível, Teste e Publicação
- Crie o arquivo `README.md` principal do ecossistema: portal didático, mapa visual da evolução das ferramentas e guia de início rápido com 1-clique.
- Execute os testes e o gate `G_ECOSSISTEMA_INTEGRIDADE.py` garantindo retorno `exit 0`.
- Realize o commit inicial limpo (`Initial commit: Ecossistema AIDD Unificado com ORC 3`) e execute `git push -u origin main`.

---

---

## 🇺🇸 ENGLISH VERSION (EN)

You are the **Master Orchestrator Agent** operating within **ORCA ADE** to initialize and build the central unified repository **`ecossistema-aidd`**.

Your mission is to execute the strategic plan defined in `planos/PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md` end-to-end, leveraging **triad orchestration (ORC 3)** with isolated worktrees and delegated agents:
* **Lead Orchestrator:** Antigravity (your current session).
* **Governance & Skills Specialist Agent:** Claude Code (isolated worktree).
* **Integration & Testing Specialist Agent:** MimoCode (isolated worktree).

---

### MANDATORY EXECUTION PHASES:

#### 1. Git Repository Initialization and Remote Connection
- Run `git init` in the root directory (`C:\Users\trcnologia\Desktop\ecossistema-aidd`).
- Set the primary branch to `main`: `git branch -M main`.
- Add the remote origin: `git remote add origin https://github.com/heverton-dev/ecossistema-aidd.git`.
- Create a comprehensive `.gitignore` file ignoring `.env`, cache folders (`__pycache__`, `.pytest_cache`), logs, and temporary artifacts.

#### 2. Non-Destructive Import of the 4 Certified Tools
- Copy the 4 audited, certified projects from source folder `C:\Users\trcnologia\Desktop\proj_aidd` directly into `tools/` in a self-contained manner:
  * `C:\Users\trcnologia\Desktop\proj_aidd\aidd-forge` ➔ `tools/aidd-forge/`
  * `C:\Users\trcnologia\Desktop\proj_aidd\aidd-generator` ➔ `tools/aidd-generator/`
  * `C:\Users\trcnologia\Desktop\proj_aidd\aidd-master` ➔ `tools/aidd-master/`
  * `C:\Users\trcnologia\Desktop\proj_aidd\aidd-master-enterprise` ➔ `tools/aidd-master-enterprise/`
- **Non-Negotiable Rule:** Preserve unit tests, scripts, and manifests across all 4 projects completely intact and fully passing.

#### 3. Canonical Unified Governance & 4 Skills with Slash Commands
- Create the master governance document `AGENTS.md` at the root, mandating non-negotiable principles of transparency, determinism, and severe token economy across the entire ecosystem.
- Configure canonical mirrors for `.agent/`, `.claude/`, and `.cursor/rules/`.
- Create and register all 4 universal Skills with standard YAML Frontmatter under `.agent/skills/` alongside their Slash Commands under `.agent/commands/` and `.claude/commands/`:
  1. **`/forge [path]`** (`skills/aidd-forge-runner`): Triggers the AIDD bootstrap and hardening engine.
  2. **`/generate <idea>`** (`skills/aidd-generator-runner`): Triggers the autonomous 8-phase project generator.
  3. **`/master <module>`** (`skills/aidd-master-runner`): Adds decoupled vertical domain slices to the Shared Kernel.
  4. **`/enterprise <type> <name>`** (`skills/aidd-enterprise-runner`): Injects regulated enterprise components with SHA-256 cryptographic hashes.

#### 4. Unified Meta-Orchestrator CLI & Global Quality Gates
- Create the root CLI orchestrator: `ecossistema.py` (or `aidd.py`), enabling execution of any tool via standard command line.
- Implement the Quality Gate `gates/G_ECOSSISTEMA_INTEGRIDADE.py` to verify that all 4 tools maintain green tests and ecosystem skills are correctly anchored.

#### 5. High-Level Documentation, Verification, and Publishing
- Author the primary `README.md` ecosystem portal: didactic visual roadmap, tool evolution comparison, and 1-click quickstart.
- Execute validation tests and verify `G_ECOSSISTEMA_INTEGRIDADE.py` exits with code `0`.
- Perform the clean initial commit (`Initial commit: Ecossistema AIDD Unificado com ORC 3`) and execute `git push -u origin main`.
