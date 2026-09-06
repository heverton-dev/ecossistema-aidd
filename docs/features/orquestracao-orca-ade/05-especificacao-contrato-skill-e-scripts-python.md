# 📜 Especificação do Contrato da Skill e Scripts Determinísticos Python

> **Local Canônico:** `docs/features/orquestracao-orca-ade/05-especificacao-contrato-skill-e-scripts-python.md`  
> **Status:** Especificação Técnica de Engenharia  
> **Data:** 06/09/2026  
> **Idioma Oficial:** Português do Brasil (PT-BR)  

---

## 1. Contrato da Skill (`SKILL.md`)

A skill reside na fonte canônica `componentes/compartilhado/skills/orca-plan-orchestrator/SKILL.md` e é propagada para todos os harnesses (`.agent/`, `.claude/`, `.gemini/`).

### 1.1. Metadados e Frontmatter do `SKILL.md`

```yaml
---
name: orca-plan-orchestrator
description: Orquestra a execução autônoma de planos estruturados em diretórios (fatiamento de frentes, criação de mesas Git Worktrees, disparo de executores em paralelo/fila e gates mecânicos).
version: 1.0.0
author: Ecossistema AIDD (ORCA ADE)
category: orquestracao
triggers:
  - "/orchestrate"
  - "orquestre o plano"
  - "executar plano em worktrees"
  - "orquestracao orca"
parameters:
  plan_dir:
    type: string
    description: Caminho relativo ou absoluto da pasta contendo o plano estruturado (ex.: docs/planos/testes-completos-ecossistema).
    required: true
  resume:
    type: boolean
    description: Retoma uma execução interrompida a partir de memory.md e .orca_state.json.
    default: false
  parallel:
    type: boolean
    description: Habilita execução paralela de frentes independentes em worktrees distintas.
    default: true
  dry_run:
    type: boolean
    description: Apenas gera o grafo e os comandos sem criar worktrees nem disparar agentes.
    default: false
  model_profile:
    type: string
    description: Perfil de alocação de modelos (balanced, eco_tokens, max_reasoning).
    default: "balanced"
---
```

### 1.2. Comportamento Operacional do Agente ao Executar a Skill
Ao ser acionada em qualquer harness, a instrução do `SKILL.md` comanda o agente a:
1. **NÃO tentar executar tudo sozinho** em uma única sessão.
2. Invocar imediatamente o motor mecânico determinístico: `python componentes/compartilhado/skills/orca-plan-orchestrator/scripts/orchestrator_cli.py <plan_dir>`.
3. Assumir o papel de **Auditor Superior**: acompanhar a evolução do `memory.md`, revisar relatórios de Quality Gate de cada mesa e intervir somente se houver falha de gate irrecuperável.

---

## 2. Arquitetura dos Scripts Determinísticos Python (Zero-Token Engine)

Todos os scripts são construídos com a biblioteca padrão do Python (`pathlib`, `subprocess`, `re`, `json`, `argparse`), garantindo execução instantânea sem dependências pesadas e **com consumo rigoroso de zero tokens de LLM**.

```
componentes/compartilhado/skills/orca-plan-orchestrator/scripts/
├── orchestrator_cli.py    # Ponto de entrada CLI unificado
├── plan_parser.py         # Analisa a pasta do plano e monta o grafo DAG
├── state_engine.py        # Gerencia .orca_state.json e renderiza memory.md
├── worktree_engine.py     # Ciclo de vida de Git Worktrees (add, prune, lock)
├── agent_spawner.py       # Spawner multi-harness (agy, claude, opencode, etc.)
└── gate_auditor.py        # Verificação mecânica de exit code e relatórios
```

---

### 2.1. `plan_parser.py` (Parser Estático e Montador de Grafo DAG)

**Função:** Lê os arquivos `.md` na pasta do plano, extrai os números (`00`, `01`, `02...`), lê os cabeçalhos H1/H2 e mapeia tags de dependência.

- **Entrada:** Caminho do diretório (ex.: `docs/planos/testes-completos-ecossistema`).
- **Lógica Mecânica:**
  - `00-*.md` é classificado como **Contexto Mestre** (regras globais injetadas em todas as mesas).
  - `01-*.md`, `02-*.md`, etc., são analisados via Regex em busca de tags opcionais: `<!-- depends-on: 01 -->` ou `<!-- complexity: high -->`.
  - Se não houver declaração explícita de dependência, todas as frentes numeradas acima de `00` são tratadas como **independentes (paralelas)**.
- **Saída:** Objeto JSON estruturado com o grafo de execução.

---

### 2.2. `state_engine.py` (Persistência Atômica e Renderizador de `memory.md`)

**Função:** Garante a transacionalidade do estado e mantém o arquivo humano/LLM sempre sincronizado com o disco.

- **Operações:**
  - `load_or_init(plan_dir)`: Inicializa `.orca_state.json` ou carrega existente.
  - `update_step(frente_id, status, exit_code, commit_sha, details)`: Atualiza o JSON com escrita atômica (`tempfile` + `os.replace` para evitar corrupção em queda de energia).
  - `render_memory_md()`: Gera/atualiza o `memory.md` em Markdown elegante com tabela de status, percentual de progresso e log cronológico.

---

### 2.3. `worktree_engine.py` (Gerenciador de Mesas Isoladas Git)

**Função:** Isola as pastas físicas de trabalho para cada frente sem interferir no diretório de trabalho principal.

- **Métodos Principais:**
  - `create_worktree(frente_id)`:
    - Executa `git worktree add ../wt-<frente_id> -b orca/<frente_id>`.
    - Copia arquivos de configuração essenciais se necessário.
  - `merge_worktree(frente_id)`:
    - Executa `git merge --no-ff orca/<frente_id> -m "orca(<frente_id>): conclusao aprovada por gate"`.
  - `cleanup_worktree(frente_id)`:
    - Executa `git worktree remove ../wt-<frente_id> --force` e `git branch -D orca/<frente_id>`.
  - `prune_orphans()`: Varre worktrees órfãs no Git causadas por falha de energia e remove com segurança.

---

### 2.4. `agent_spawner.py` (Lançador Multi-Harness Agnóstico)

**Função:** Abstrai como cada ferramenta CLI é invocada no sistema operacional (Windows/Linux/macOS), injetando o modelo correto e redirecionando a saída.

- **Matriz de Lançamento por Harness:**
  - **Antigravity (`agy`):**  
    `agy --model <pro|flash> --prompt "<instrucao>"`
  - **Claude Code (`claude`):**  
    `claude --model <opus|sonnet|haiku> -p "<instrucao>"`
  - **OpenCode / MimoCode:**  
    `opencode --model <modelo> -p "<instrucao>"`
- **Prompt Fatiado Injetado:**
  O spawner injeta um prompt compacto padronizado:
  > *"Você é o executor isolado da frente {frente_nome}. Leia estritamente as regras mestras em {arquivo_00} e o plano específico em {arquivo_frente}. Execute todos os passos, execute os Quality Gates da pasta e grave o resultado em .orca_result.json. Garanta exit code 0."*
- **Redirecionamento de Logs:** Cada mesa grava seu próprio `exec.log` em tempo real dentro da worktree.

---

### 2.5. `gate_auditor.py` (Quality Gate Determinístico)

**Função:** Impede que código quebrado ou mocks/stubs sejam mergeados na branch principal.

- **Checklist Mecânico de Aceite:**
  1. O processo do subprocesso retornou `returncode == 0`?
  2. O arquivo `.orca_result.json` foi gerado com `gate_status: "PASSED"`?
  3. O repositório na worktree tem arquivos com modificações não commitadas? Se sim, commita com mensagem rastreável.
  4. Roda o meta-gate global `python ecossistema.py audit` sobre o delta alterado.
  - Se tudo estiver verde: **APROVADO PARA MERGE**.
  - Se qualquer item falhar: **BLOQUEADO**, atualiza `memory.md` com o erro e notifica o orquestrador para retificação.

---

### 2.6. `orchestrator_cli.py` (Ponto de Entrada Integrado ao Ecossistema)

Integrado diretamente ao CLI raiz do monorepo:
```powershell
# Sintaxe unificada
python ecossistema.py orchestrate <caminho_do_plano> [opções]

# Exemplos de uso real:
python ecossistema.py orchestrate docs/planos/testes-completos-ecossistema
python ecossistema.py orchestrate docs/planos/testes-completos-ecossistema --resume
python ecossistema.py orchestrate docs/planos/testes-completos-ecossistema --dry-run
```
