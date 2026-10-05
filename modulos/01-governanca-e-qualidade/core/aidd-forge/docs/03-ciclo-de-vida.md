# Ciclo de Vida Operacional no Ecossistema AIDD Forge

> **Versão:** 1.0.0  
> **Objetivo:** Definir com precisão matemática os estados, transições e pontos de descarte de contexto no ciclo de vida de projetos geridos pelo AIDD Forge.

---

## 1. O Ciclo de Vida do Subagente Efêmero

Diferente de assistentes convencionais que mantêm sessões contínuas acumulando milhares de mensagens no histórico, o AIDD Forge adota o ciclo estrito **Spawn -> Exec -> AST -> Purge**:

```
 [INATIVO]
     │
     ▼  Recebe prompt atômico (<1.000 tokens)
 [SPAWNING] ───► Ativa flag `session_active = True`
     │
     ▼  Gera código / artefato em memória
 [EXECUTING]
     │
     ▼  Validação sintática mecânica via `ast.parse`
 [VALIDATING] ──(Falha de Sintaxe)──► [PURGE IMEDIATO] ──► Result.fail
     │
     ▼ (Sintaxe Válida)
 [SAVING] ─────► Grava arquivo UTF-8 em disco
     │
     ▼
 [PURGE] ──────► Desliga sessão (`session_active = False`) ──► Result.ok
```

### Regras Invioláveis do Subagente:
1. **Zero Sobrevivência de Contexto:** Nenhuma variável de sessão, histórico de chat ou estado de memória é mantido entre duas invocações.
2. **Atomicidade:** Um subagente gera exatamente um artefato por execução.
3. **Barreira Mecânica:** Se o código gerado possuir erro de sintaxe, o arquivo físico no disco não é criado ou alterado.

---

## 2. O Ciclo de Vida das Fases do Pipeline (`.aidd/pipeline/`)

A transição entre fases obedece a um isolamento estrito de contexto:

| Estado da Fase | Regras Visíveis | MCPs Habilitados | Critério de Saída |
| :--- | :--- | :--- | :--- |
| **Phase 00: Bootstrap** | Hardware, SO, Git, Python | Zero | Host verificado e inventariado |
| **Phase 01: Requirements** | User stories, personas, escopo | Filesystem MCP | Documentos de requisitos gravados |
| **Phase 02: Architecture** | Schemas Draft 2020-12, contratos | Schemas MCP | Validação no `G_CONTRACTS` |
| **Phase 03: Implementation** | Result Monad, TDD, zero stubs | Database MCP | Suíte pytest com 100% de aprovação |
| **Phase 04: Audit & Security** | OWASP Top 10, performance, AST | Security / Linter MCP | Aprovação nos 7 Quality Gates |

---

## 3. Estados de Governança e Idempotência

O processo de injeção gerenciado por `aidd_forge.cli init` é **completamente idempotente**:

1. **Primeira Execução (Cold Start):**
   - Cria diretórios `.aidd/pipeline/`, `.agent/skills/`, `.claude/commands/`, `.cursor/rules/`.
   - Grava arquivos e cria symlinks canônicos.
   - Retorno: `created = N`, `skipped = 0`.
2. **Re-execução sem `--force` (Idempotência Segura):**
   - Detecta arquivos já existentes e não os sobrescreve, preservando customizações do desenvolvedor.
   - Retorno: `created = 0`, `skipped = N`.
3. **Re-execução com `--force` (Self-Healing / Reset):**
   - Restaura os arquivos para o padrão oficial canônico.
   - Retorno: `overwritten = N`.
