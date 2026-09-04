# 🐋 PLANO MESTRE DE ORQUESTRAÇÃO ORCA 3: INJETOR UNIVERSAL DE COMPONENTES
> **Arquitetura:** ORCA ADE (Agentic Development Environment) + AIDD 5 Camadas  
> **Modelo de Execução:** Orquestração Multi-Agente com Mesas Isoladas (Worktrees Git)  
> **Escopo de Aplicação:** 4 Projetos (`aidd-generator`, `aidd-master`, `aidd-master-enterprise`, `aidd-forge`)  
> **Feature Central:** Auto-Injeção e Auto-Integração de Skills, MCPs, Rules, Specs, Configs, Hooks e Agents  
> **Data de Emissão:** 03/09/2026  
> **Idioma Oficial:** Português do Brasil (PT-BR)

---

## 🧭 1. Resumo Executivo e Confirmação de Entendimento

### 1.1. O Desafio
Integrar nos 4 projetos do ecossistema AIDD uma capacidade unificada de **Auto-Injeção de Artefatos**. Quando o usuário solicitar (via terminal ou em linguagem natural em PT-BR) a inclusão de uma nova skill (ex.: *"crie uma skill de cibersegurança"*), MCP, regra, especificação ou configuração, o sistema deve:
1. **Detectar a camada de destino** arquitetural adequada (Camadas 1 a 5 da metodologia AIDD / diretórios específicos do projeto alvo).
2. **Materializar fisicamente** o pacote de arquivos com scaffold padronizado e propagação para os harnesses configurados (`.claude`, `.agent`, `.gemini`, `.mimocode`).
3. **Integrar ao projeto globalmente**, atualizando catálogos, tabelas no `AGENTS.md`, roteadores de intenção e Quality Gates.
4. **Validar via Gate Mecânico** (`G_INJECT`), garantindo `exit 0` sem stubs e sem alucinações.

### 1.2. A Estratégia de Execução: ORCA 3 ADE
Em vez de executar linearmente em uma única sessão de chat (o que causaria contaminação de contexto, estouraria limites de tokens e demoraria horas), a implementação será executada através da **Tríade de Especialistas do ORCA (ORC 3)** operando em **Worktrees Isoladas** com processo e terminal OS independentes para cada frente de trabalho nos 4 projetos.

---

## 🏗️ 2. Arquitetura da Tríade de Agentes (ORC 3)

```
                            ┌──────────────────────────────────────┐
                            │      MESTRE DE OBRAS / AUDITOR       │
                            │   (Terminal Principal ORCA / Maestro) │
                            └──────────────────┬───────────────────┘
                                               │
                   orca worktree create --parent-worktree active
                                               │
         ┌─────────────────────────────────────┼─────────────────────────────────────┐
         ▼                                     ▼                                     ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐ ┌─────────────────────────────┐
│    MESA 01: CORE ENGINE     │ │    MESA 02: ADAPTERS &      │ │    MESA 03: INTERFACES &    │
│      (Agente Arquiteto)     │ │        PROFILES             │ │      QUALITY GATES          │
│       Harness: AGY/Pro      │ │   (Agente Integrador)       │ │     (Agente Auditor)        │
│                             │ │   Harness: MimoCode/OpenCode│ │       Harness: Claude       │
│ • Schema Draft 2020-12      │ │ • Mapeamento 4 Projetos     │ │ • CLI aidd inject           │
│ • Detector Híbrido          │ │ • Gerador de Scaffolds      │ │ • IntentRouter em PT-BR     │
│ • Motor de Materialização   │ │ • Sincronização Multi-Harness│ │ • Gate Mecânico G_INJECT   │
│ • Transacionalidade/Rollback│ │ • Atualizador de Manifestos │ │ • Testes E2E (Pytest 100%)  │
└──────────────┬──────────────┘ └──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │                               │
               └───────────────────────────────┼───────────────────────────────┘
                                               ▼
                              ┌──────────────────────────────────┐
                              │  MONITORAMENTO: orca worktree ps │
                              │  AUDITORIA DETERMINÍSTICA LOCAL  │
                              │  MERGE & LIMPEZA DE WORKTREES    │
                              └──────────────────────────────────┘
```

### Papéis Definidos na Tríade:

1. **Mesa 01 — Agente Arquiteto (Core Engine):**
   * Constrói o motor compartilhado e agnóstico de projeto (`aidd_core_injector`).
   * Implementa o contrato JSON Schema, a lógica de detecção híbrida (heurística determinística + fallback delegado) e o mecanismo transacional atômico de escrita com rollback.
2. **Mesa 02 — Agente Integrador (Adapters & Project Profiles):**
   * Configura os perfis dos 4 projetos (`generator`, `master`, `enterprise`, `forge`).
   * Define as rotas físicas de destino e os arquivos-âncora a serem alterados em cada repositório (ex.: `AGENTS.md`, `CAPABILITIES.json`, `suite.db`, `templates/`).
3. **Mesa 03 — Agente Auditor (Interfaces & Quality Gates):**
   * Constrói a interface de linha de comando (`scripts/aidd.py inject`), a expansão do `IntentRouter` para linguagem natural e o gate determinístico `G_INJECT.py`.
   * Escreve e roda a suíte de testes de ponta a ponta em Pytest.

---

## ⚡ 3. Protocolo de Operação via Terminal ORCA

### Passo 1: Registro dos 4 Repositórios no ORCA
Executado pelo Mestre de Obras no terminal raiz:
```powershell
# Registrar os 4 projetos no catálogo do ORCA
orca repo add --path "C:/Users/trcnologia/Desktop/proj_aidd/aidd-generator"
orca repo add --path "C:/Users/trcnologia/Desktop/proj_aidd/aidd-master"
orca repo add --path "C:/Users/trcnologia/Desktop/proj_aidd/aidd-master-enterprise"
orca repo add --path "C:/Users/trcnologia/Desktop/proj_aidd/aidd-forge"

# Listar IDs atribuídos
orca repo list
```

### Passo 2: Criação das Mesas Isoladas (Worktrees Filhas)
Para cada frente de implementação, criam-se worktrees com isolamento total de branch e pasta:
```powershell
# Mesa 01: Core Engine
orca worktree create --name feat-injector-core --parent-worktree active

# Mesa 02: Adapters dos 4 Projetos
orca worktree create --name feat-injector-adapters --parent-worktree active

# Mesa 03: Interfaces e Gates
orca worktree create --name feat-injector-gates --parent-worktree active
```

### Passo 3: Inicialização dos Agentes Especialistas nos Terminais
Disparo de cada especialista com terminal dedicado e contexto isolado:
```powershell
# Terminal 01 - Agente Arquiteto
orca terminal create --worktree branch:feat-injector-core --title "Mesa 01 - Core Engine" --command "antigravity"

# Terminal 02 - Agente Integrador
orca terminal create --worktree branch:feat-injector-adapters --title "Mesa 02 - Adapters 4 Projs" --command "mimocode"

# Terminal 03 - Agente Auditor
orca terminal create --worktree branch:feat-injector-gates --title "Mesa 03 - Gates e CLI" --command "opencode"
```

### Passo 4: Monitoramento Central com "Câmeras ao Vivo"
O Mestre de Obras acompanha o avanço sem interromper as IAs:
```powershell
# Visão global das mesas, estados de pensamento e progresso
orca worktree ps
```

### Passo 5: Auditoria Mecânica Local e Fusão (Merge)
Conforme a Regra de Ouro da Auditoria (*"Nunca confie apenas na palavra da IA. Teste com as suas próprias mãos"*), o Mestre de Obras valida cada mesa com testes antes de integrar:
```powershell
# 1. Auditar testes da mesa
pytest tests/test_injector_core.py

# 2. Executar Gate Mecânico
python scripts/gates/G_INJECT.py

# 3. Mesclar alterações aprovadas
git merge feat-injector-core
git merge feat-injector-adapters
git merge feat-injector-gates

# 4. Descartar mesas de trabalho finalizadas
orca worktree delete --worktree branch:feat-injector-core
orca worktree delete --worktree branch:feat-injector-adapters
orca worktree delete --worktree branch:feat-injector-gates
```

---

## 📋 4. Plano de Implementação em 6 Fases Estruturadas

| Fase | Título | Responsável (Mesa) | Entregáveis Técnicos | Critério de Sucesso Mecânico |
| :---: | :--- | :---: | :--- | :--- |
| **Fase 1** | **Contrato Universal & Schema Draft 2020-12** | Mesa 01 | Arquivo `schema_injector_request.json` validando: `tipo`, `nome`, `descricao`, `camada_alvo`, `conteudo`, `alvo_projeto`. | Gate rejeita com erro estruturado qualquer payload incompleto. |
| **Fase 2** | **Matriz de Perfis (Profiles) dos 4 Projetos** | Mesa 02 | `profiles_registry.py` com o mapeamento exato de pastas para `aidd-generator`, `aidd-master`, `aidd-master-enterprise` e `aidd-forge`. | Resolução exata de diretórios para cada tipo em qualquer um dos 4 projetos. |
| **Fase 3** | **Motor de Detecção Híbrida & Materialização Transacional** | Mesa 01 | `detector_camada.py` (heurística + LLM delegado) + `materializador.py` com buffer atômico e rollback automático em falha de I/O. | Zero arquivos órfãos em caso de interrupção; criação limpa em disco. |
| **Fase 4** | **Sincronizador Multi-Harness e Integrador Global** | Mesa 02 | `sincronizador_harness.py` que reflete o novo artefato em `.claude/`, `.agent/`, `.gemini/` e atualiza a tabela do `AGENTS.md` e catálogos JSON. | O artefato é detectado imediatamente em todos os harnesses configurados. |
| **Fase 5** | **CLI Universal & Intent Router em PT-BR** | Mesa 03 | Subcomando `aidd inject <tipo> <nome>` integrado ao `scripts/aidd.py` e padrões de linguagem natural em PT-BR no `IntentRouter`. | Comandos CLI e frases em linguagem natural disparam o fluxo completo. |
| **Fase 6** | **Quality Gate Mecânico (`G_INJECT.py`) & Prova de Fogo** | Mesa 03 + Maestro | Script de validação determinística (`exit 0`/`exit 1`) + injeção real de uma skill de segurança cibernética e um MCP nos 4 projetos. | Todos os testes passam (100% Pytest verde, 0 skips, 0 stubs). |

---

## 🎯 5. Detalhamento dos Profiles dos 4 Projetos (Mapeamento de Destinos)

```json
{
  "aidd-generator": {
    "skill": { "dest": "skills/{nome}/SKILL.md", "mirrors": [".claude/skills/{nome}/SKILL.md"] },
    "mcp": { "dest": "mcps/{nome}/server.py", "registry": "HARNESS-COMPAT.json" },
    "rule": { "dest": "rules/{nome}.md", "anchor": "AGENTS.md" },
    "spec": { "dest": "docs/specs/{nome}.md", "plan_anchor": "PLANO-EXECUCAO-ESTRUTURADO.json" },
    "config": { "dest": "config/{nome}.json" }
  },
  "aidd-master": {
    "skill": { "dest": ".skills/{nome}/SKILL.md", "mirrors": [".claude/skills/{nome}/SKILL.md", ".mimocode/skills/{nome}/SKILL.md"] },
    "mcp": { "dest": "src/core/mcp/{nome}.py", "registry": "CAPABILITIES.json" },
    "rule": { "dest": "templates/rules/{nome}.md", "anchor": "AGENTS.md" },
    "spec": { "dest": "docs/specs/{nome}.md", "db_anchor": "suite.db" },
    "config": { "dest": "templates/core/{nome}.json" }
  },
  "aidd-master-enterprise": {
    "skill": { "dest": ".skills/{nome}/SKILL.md", "mirrors": [".claude/skills/{nome}/SKILL.md", ".agent/skills/{nome}/SKILL.md", "templates/core/skills/{nome}/SKILL.md"] },
    "mcp": { "dest": "src/core/mcp_server.py", "registry": "CAPABILITIES.json" },
    "rule": { "dest": "templates/rules/{nome}.md", "anchors": ["templates/core/AGENTS.md", "templates/core/CLAUDE.md", "templates/core/GEMINI.md"] },
    "spec": { "dest": "src/modules/{nome}/spec.md", "plan_anchor": "PLANO-EXECUCAO-ESTRUTURADO.json" },
    "agent": { "dest": "templates/agents/{nome}.md", "router_anchor": "src/core/intent_router.py" }
  },
  "aidd-forge": {
    "skill": { "dest": ".agents/skills/{nome}/SKILL.md", "mirrors": ["aidd_forge/skills/{nome}/SKILL.md"] },
    "mcp": { "dest": "aidd_forge/mcps/{nome}.py", "registry": "setup.py" },
    "rule": { "dest": "docs/rules/{nome}.md", "anchor": "AGENTS.md" },
    "spec": { "dest": "docs/{nome}-spec.md" },
    "roteiro": { "dest": "tutoriais/{nome}.md" }
  }
}
```

---

## 🛡️ 6. As 3 Leis de Ouro da Execução Paralela

1. **Zero Contaminação de Contexto:** Cada agente opera dentro de sua worktree em terminal separado. O chat do Maestro fica estéril, contendo apenas comandos de despacho e relatórios executivos.
2. **Economia Extrema de Tokens:** O pensamento interno dos agentes opera em *English Caveman Ultra*, poupando 70% de tokens de raciocínio, enquanto todas as entregas, códigos e documentações são em Português do Brasil de alto padrão.
3. **Persistência Estruturada entre Sessões:** Toda a evolução de status, branches ativas e hashes de commits é gravada no `PLANO-EXECUCAO-ESTRUTURADO.json`, permitindo reiniciar ou auditar sessões com custo inferior a 500 tokens.
