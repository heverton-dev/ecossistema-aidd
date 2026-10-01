# AIDD-SPEC: Roteamento Probabilístico de Inteligência (Cérebros)

## 1. Context & Explicit Non-Goals
**Context:**  
Transição do roteamento LLM estático e atrelado a "cargos" (Arquiteto, Inspetor) no arquivo `CONFIG-EXECUCAO-USUARIO.json` para um despacho probabilístico por "Classe de Cérebro" (`brain_class`). Os orquestradores (`aidd-dispatch`, `aidd-evolution`) farão parse da categoria de inteligência de cada ticket ou fatia VSA para invocar a stack ideal (ex.: Flash para scaffold, Pro para join-barrier). O objetivo é maximizar a qualidade em tarefas difíceis e derrubar os custos em tarefas triviais.

**Explicit Non-Goals:**  
- Adicionar ou modificar suporte técnico a provedores (OpenAI, Anthropic) no nível da infraestrutura. A responsabilidade do comando CLI via *harness* permanece sendo do agente no terminal.
- Re-arquitetar os motores base (`aidd-open`, `aidd-pure`). Apenas os *dispatchers* serão modificados.

## 2. Contracts & Typed Interfaces

### `CONFIG-EXECUCAO-USUARIO.json` (Schema Extendido)
```json
{
  "pool_cerebros": {
    "flash": { "harness": "agy", "model": "gemini-3.8-flash-low", "comando_terminal": "agy --model gemini-3.8-flash-low --dangerously-skip-permissions" },
    "pro": { "harness": "claude", "model": "haiku", "comando_terminal": "claude --dangerously-skip-permissions --chrome --model haiku" },
    "reasoning": { "harness": "opencode", "model": "opencode/big-pickle", "comando_terminal": "opencode --pure --auto --agent -m opencode/big-pickle" }
  },
  "fallback_padrao": "pro"
}
```

### Manifestos de Pipeline (`PLANNER.json`, Tickets VSA)
```json
{
  "ticket_id": "T001",
  "brain_class": "flash",
  "instrucao": "Gerar scaffold básico de API REST."
}
```

## 3. Invariants & Business Rules
1. **Determinação Precoce:** A seleção do cérebro (`brain_class`) DEVE estar presente no momento de compilação do plano. O orquestrador não infere classes dinamicamente em tempo de execução.
2. **Separação de Camadas:** O *harness* (AGY, Claude, Mimo) não tem conhecimento sobre a classe probabilística; ele recebe cegamente o comando injetado pelo *dispatcher*.
3. **Rigidez de Configuração:** Todas as instâncias do JSON no ciclo de auditoria/evolução DEVEM obedecer rigorosamente ao schema. Se a chave requisitada (`brain_class: "x"`) for chamada no ticket, o perfil `"x"` precisa estar no pool.

## 4. Binary Acceptance Criteria
1. **Exit Code 1 (Missing Profile):** `python scripts/dispatch_pipeline.py` faz *exit 1* se invocado com um ticket que pede uma `brain_class` não mapeada em `pool_cerebros`.
2. **Resolução Dinâmica:** Teste automatizado confirma que, em um manifesto com 3 tickets [flash, pro, reasoning], o gerador de strings de comando instanciará os 3 CLIs distintos em stdout.
3. **Fallback Determinístico:** Se um ticket da spec não carregar a chave `brain_class`, o sistema assume o valor em `fallback_padrao` com *exit 0*.

## 5. Failure & Degradation Modes
- **Arquivo Config Ausente:** Aborta imediatamente a esteira (VSA Join Barrier Bloqueado) com exceção formal para proteger custos e padronização.
- **Payload Malformado:** Tickets passados em formato incompatível falham durante a primeira etapa topológica do Kahn DAG antes de qualquer branch Git efêmera ser criada.
