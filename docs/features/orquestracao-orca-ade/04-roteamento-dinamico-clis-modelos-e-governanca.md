# 🎛️ Roteamento Dinâmico de CLIs/LLMs, Linguagem Natural e Governança da Skill

> **Local Canônico:** `docs/features/orquestracao-orca-ade/04-roteamento-dinamico-clis-modelos-e-governanca.md`  
> **Status:** Especificação de Usabilidade, Roteamento e Arquitetura  
> **Data:** 06/09/2026  
> **Idioma Oficial:** Português do Brasil (PT-BR)  

---

## 1. Roteamento em Linguagem Natural: Como o Usuário Define Quem Faz o Quê?

O usuário **não precisa memorizar comandos complexos**. O sistema oferece duas formas simples e transparentes de alocação de CLIs e modelos:

### Modo A: Diretiva em Linguagem Natural no Chat (Pré-Execução)
O usuário simplesmente expressa sua vontade ao chamar a orquestração:
> *"Orquestre o plano `docs/planos/testes-completos-ecossistema`. Use Claude como orquestrador raiz. Para as frentes pesadas de Master e Enterprise use o Antigravity com modelo Pro, e para as frentes mais leves de Forge e Raiz use Claude Haiku ou MimoCode."*

O **IntentRouter** da skill interpreta essa instrução e gera a matriz de alocação no arquivo `.orca_state.json` antes de tocar no disco.

### Modo B: Tabela Canônica no `00-PROCESSO-E-DECISOES.md` (Zero-Token Config)
O usuário pode declarar a matriz diretamente no arquivo inicial da pasta de planos:

```markdown
## 👥 Matriz de Alocação de Agentes
| Frente | Complexidade | Harness Recomendado | Modelo / Flag | Justificativa |
|---|---|---|---|---|
| 01-raiz | Baixa | `claude` | `claude-3-5-haiku` | Verificação de integridade e scripts rápidos |
| 02-master | Alta | `agy` | `gemini-1.5-pro` (ou `pro`) | Lógica complexa de Clean Architecture e testes |
| 03-enterprise | Crítica | `agy` | `gemini-1.5-pro` (ou `pro`) | Validação SHA-256 e Zero-Trust |
| 04-forge | Média | `opencode` ou `claude` | `default` | Bootstrap e isolamento de ambientes |
| 05-generator | Alta | `agy` | `pro` | Pipeline completo de 8 fases |
```

Se o usuário não especificar nada, a skill aplica uma **heurística determinística automática** (baseada no tamanho do markdown e presença de termos críticos como *arquitetura*, *segurança*, *testes e2e*).

---

## 2. Roteamento de Modelos por Perfil de Custo e Complexidade

Os comandos disparados pelos scripts traduzem a matriz para os argumentos nativos de cada harness instalado:

```powershell
# Exemplo 1: Antigravity com modelo Pro (Raciocínio Profundo)
agy --model pro --prompt "Leia o plano 02 e execute..."

# Exemplo 2: Claude Code com modelo Haiku (Rápido e Barato)
claude --model claude-3-5-haiku -p "Leia o plano 01 e execute..."

# Exemplo 3: OpenCode / MimoCode para tarefas intermediárias
opencode --model deepseek-coder -p "Leia o plano 04 e execute..."
```

Isso garante a **Economia Extrema de Tokens**:
- Modelos caros/profundos (*Pro/Opus*) são alocados **apenas** nas frentes de alta complexidade.
- Modelos rápidos/leves (*Haiku/Flash/DeepSeek*) assumem as rotinas de verificação, gates e testes mecânicos.

---

## 3. O Ecossistema AIDD já previa ORCA ADE? Por que criar uma SKILL dedicada?

### 3.1. Você está equivocado?
**Não!** O ecossistema AIDD nasceu conceitualmente ancorado no modelo **ORCA ADE (Agentic Development Environment)** — tanto que o `AGENTS.md` cita expressamente o status: `PRODUÇÃO & ORQUESTRADO (ORCA ADE / ORC 3)`.

### 3.2. A Lacuna Existente: A Orquestração era Manual/Documental
Até o momento:
- A orquestração ORCA ADE existia como **guia arquitetural e planos mestres documentais** (como o [PLANO-ORQUESTRACAO-ORCA3-UNIVERSAL-INJECTOR.md](file:///C:/Users/trcnologia/Desktop/PLANO-ORQUESTRACAO-ORCA3-UNIVERSAL-INJECTOR.md)).
- O desenvolvedor ou o harness precisava rodar os comandos `git worktree` e os CLIs manualmente, sem uma máquina de estados autônoma em código para gerenciar o ciclo de vida e o *crash recovery*.

### 3.3. Por que encapsular em uma SKILL Canônica (`orca-plan-orchestrator`)?
Encapsular a orquestração em uma **Skill Canônica** (acompanhada de comando CLI `ecossistema.py orchestrate`) é a melhor decisão de engenharia pelas seguintes razões:

1. **Elimina a "Vontade Própria" do Harness:**  
   Se você deixar a cargo do Claude ou do Antigravity "decidir como orquestrar", cada LLM tentará improvisar scripts de worktree, errará caminhos no Windows ou esquecerá de fazer o merge e o purge.
2. **Determinismo Mecânico (Zero Token Fallacy):**  
   A criação de worktrees, o monitoramento de processos de terminal, a verificação de exit codes e o merge são **operações 100% mecânicas em Python**, sem gastar nenhum token de LLM.
3. **Imunidade a Troca de Harness:**  
   Não importa se você abre o Claude Code, o Antigravity IDE, o MimoCode ou o Cursor: todos encontrarão o comando `/orchestrate`, que acionará o mesmo motor de orquestração testado e blindado.
4. **Resiliência Centralizada:**  
   O arquivo `memory.md` e o `.orca_state.json` são atualizados por scripts certificados, e não por alucinações de modelos no chat.
