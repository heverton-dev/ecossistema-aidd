# PLANO ESTRATÉGICO DE ORQUESTRAÇÃO — ECOSSISTEMA AIDD UNIFICADO

> **Repositório GitHub:** `https://github.com/heverton-dev/ecossistema-aidd`  
> **Diretório Local:** `C:\Users\trcnologia\Desktop\ecossistema-aidd`  
> **Fonte dos Projetos Homologados:** `C:\Users\trcnologia\Desktop\proj_aidd`  
> **Data:** 03/09/2026  
> **Status:** PLANEJADO & PRONTO PARA EXECUÇÃO  

---

## 1. VISÃO GERAL DA MISSÃO

O objetivo é transformar os 4 projetos homologados e auditados (`aidd-forge`, `aidd-generator`, `aidd-master`, `aidd-master-enterprise`) em um **Meta-Repositório Unificado de Engenharia Agêntica** (`ecossistema-aidd`).

Este repositório central permitirá que qualquer desenvolvedor, ao realizar um simples `git clone`:
1. Tenha acesso aos 4 projetos em subdiretórios modulares autocontidos.
2. Possa disparar qualquer um dos fluxos do ecossistema por meio de **Slash Commands unificados e universais** no chat de qualquer harness (`/forge`, `/generate`, `/master`, `/enterprise`).
3. Opere sob a **Lei Fundamental de Transparência Total** e as 5 Camadas da Engenharia Agêntica com **economia severa de tokens** (Tríade Caveman Ultra, Context-Purge, Zero Stubs e Gates Determinísticos).

---

## 2. ARQUITETURA DE DIRETÓRIOS DO ECOSSISTEMA UNIFICADO

```text
ecossistema-aidd/
│
├── AGENTS.md                                  ──► Fonte única de verdade de governança agêntica
├── PLANO-EXECUCAO-ESTRUTURADO.json            ──► Persistência e telemetria de estado
├── README.md                                  ──► Portal principal bilíngue e guia do ecossistema
│
├── .agent/                                    ──► Hub Canônico de Harness (AGY / OpenCode / MimoCode)
│   ├── commands/                              ──► Roteadores de comandos (/forge, /gen, /master, /enterprise)
│   └── skills/                                ──► Skills operacionais dos 4 projetos
│
├── .claude/                                   ──► Symlinks/Junctions para Claude Code
│   ├── CLAUDE.md -> ../AGENTS.md
│   └── commands/
│
├── .cursor/                                   ──► Regras para Cursor IDE
│   └── rules/
│
├── gates/                                     ──► Meta-Quality Gates de integridade do ecossistema
│   ├── G_ECOSSISTEMA_INTEGRIDADE.py
│   ├── G_HARNESS_COMPAT.py
│   └── G_SEGREDOS.py
│
├── planos/                                    ──► Planos e especificações executivas
│   └── PLANO-EXECUCAO-ECOSSISTEMA-AIDD.md     ──► Este documento
│
├── tools/ (ou projetos integrados)
│   ├── aidd-forge/                            ──► Motor de Bootstrap & Governança (100% homologado)
│   ├── aidd-generator/                        ──► Fábrica Autônoma de Software (100% homologado)
│   ├── aidd-master/                           ──► Suíte Modular Shared Kernel & SQLite (100% homologado)
│   └── aidd-master-enterprise/                ──► Plataforma de Missão Crítica SHA-256 (100% homologado)
│
└── skills/                                    ──► Skills de alto nível do ecossistema
    ├── aidd-forge-runner/                     ──► Dispara bootstrap e blindagem
    ├── aidd-generator-runner/                 ──► Dispara pipeline autônomo das 8 fases
    ├── aidd-master-runner/                    ──► Dispara composição de fatias verticais
    └── aidd-enterprise-runner/                ──► Dispara injeção de compliance e hashes
```

---

## 3. AS 4 SKILLS & SLASH COMMANDS UNIVERSAIS

Cada ferramenta do ecossistema terá uma Skill formalmente registrada com YAML Frontmatter padrão, operável em Claude Code, MimoCode, OpenCode, Antigravity e Cursor:

| Slash Command | Skill Associada | Ação Executada | Input Esperado |
| :--- | :--- | :--- | :--- |
| **`/forge [caminho]`** | `aidd-forge-runner` | Inicializa blindagem AIDD, micro-ambientes, otimizadores e gates no caminho alvo. | Diretório a ser blindado (ou `.` para o atual). |
| **`/generate <ideia>`** | `aidd-generator-runner` | Dispara o pipeline de 8 fases para criar um sistema completo do zero com persistência e código. | Frase em linguagem natural descrevendo a aplicação. |
| **`/master <modulo>`** | `aidd-master-runner` | Cria nova fatia vertical de negócio (Routes, Services, Models, HTML) com Result Monad. | Nome do módulo (ex: `faturamento`, `estoque`). |
| **`/enterprise <tipo> <nome>`** | `aidd-enterprise-runner`| Injeta componentes regulados com validação de hashes SHA-256 e conformidade Zero Trust. | Tipo (`skill`, `rule`, `mcp`) e nome do componente. |

---

## 4. PLANO DE AÇÃO EM 5 ETAPAS SEQUENCIAIS

### Etapa 1: Inicialização do Repositório Git Local & Conexão Remota
* Inicializar `git init` na pasta `C:\Users\trcnologia\Desktop\ecossistema-aidd`.
* Configurar branch padrão `main` e adicionar o remoto `origin`:  
  `https://github.com/heverton-dev/ecossistema-aidd.git`.
* Criar o `.gitignore` global padronizado (ignorando `.env`, caches, `.pytest_cache`, logs e arquivos temporários).

### Etapa 2: Importação Não-Destrutiva dos 4 Projetos Homologados
* Copiar a integridade limpa dos 4 repositórios a partir de `C:\Users\trcnologia\Desktop\proj_aidd`:
  * `proj_aidd/aidd-forge` -> `ecossistema-aidd/tools/aidd-forge`
  * `proj_aidd/aidd-generator` -> `ecossistema-aidd/tools/aidd-generator`
  * `proj_aidd/aidd-master` -> `ecossistema-aidd/tools/aidd-master`
  * `proj_aidd/aidd-master-enterprise` -> `ecossistema-aidd/tools/aidd-master-enterprise`
* Preservar os testes unitários, scripts e manifestos de cada projeto intactos.

### Etapa 3: Materialização da Governança Central e das 4 Skills
* Criar `AGENTS.md` canônico na raiz do ecossistema explicando a relação entre as 4 ferramentas e a Lei Fundamental de Transparência Total.
* Criar as 4 skills operacionais em `.agent/skills/` com os contratos YAML Frontmatter:
  1. `skills/aidd-forge-runner/SKILL.md`
  2. `skills/aidd-generator-runner/SKILL.md`
  3. `skills/aidd-master-runner/SKILL.md`
  4. `skills/aidd-enterprise-runner/SKILL.md`
* Configurar os Slash Commands correspondentes em `.agent/commands/` e `.claude/commands/`.

### Etapa 4: Criação do Meta-Orquestrador CLI e dos Gates do Ecossistema
* Criar o script CLI central na raiz: `ecossistema.py` (ou `aidd.py` global) para permitir disparar qualquer ferramenta via linha de comando unificada:
  * `python ecossistema.py forge init <pasta>`
  * `python ecossistema.py generate "ideia"`
  * `python ecossistema.py master add-module <nome>`
  * `python ecossistema.py enterprise inject <tipo> <nome>`
* Instalar o Quality Gate `gates/G_ECOSSISTEMA_INTEGRIDADE.py` para garantir que nenhuma ferramenta quebre as outras e que todos os subprojetos continuem com testes passando.

### Etapa 5: Documentação de Alto Nível, Commit e Push Remoto
* Escrever o `README.md` principal do ecossistema contendo o mapa de navegação didático, a tabela comparativa de uso das ferramentas e o guia de início rápido com 1-clique.
* Executar os testes e gates de integridade global.
* Realizar o commit inicial limpo (`Initial commit: Ecossistema AIDD Unificado`) e efetuar o `git push origin main`.

---

## 5. BENEFÍCIOS PARA O USUÁRIO FINAL

1. **Acesso em 1 Único Lugar:** Um único `git clone` disponibiliza todo o ferramental AIDD pronto para rodar.
2. **Zero Fricção de Linha de Comando:** O usuário opera qualquer uma das ferramentas digitando `/forge`, `/generate`, `/master` ou `/enterprise` no chat do seu assistente favorito.
3. **Imutabilidade e Segurança:** As 4 ferramentas originais já auditadas e com 100% de testes verdes são preservadas, funcionando em harmonia sob um mesmo teto de governança.

---

## 6. NOTA DE AUDITORIA (04/09/2026)

Uma auditoria pós-execução encontrou 8 desvios reais entre o que este plano prometia (gates `G_HARNESS_COMPAT`/`G_SEGREDOS`, symlinks funcionais, "191 testes verdes" como validação global, cópia não-destrutiva íntegra) e o estado real do repositório — todos corrigidos e validados. Ver `docs/planos/PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md` para o diagnóstico completo e `PLANO-EXECUCAO-ESTRUTURADO.json` (bloco `testes`, gerado por `python ecossistema.py status --testes`) para a contagem real e reproduzível: **1278 testes passando, 0 falhas**, nas 4 ferramentas.
