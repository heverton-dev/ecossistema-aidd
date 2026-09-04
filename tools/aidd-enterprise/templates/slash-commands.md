# AIDD v5.1 — Slash Commands Reference

## Comandos Disponíveis

| Comando | Descrição | Exemplo |
|:--------|:----------|:--------|
| `/compose <módulos>` | Compõe vertical slices com os módulos especificados | `/compose pagamentos estoque usuarios` |
| `/aidd-pack <módulos>` | Alias para `/compose` | `/aidd-pack auth billing` |
| `/test [tipo]` | Executa suíte de testes | `/test unit`, `/test all` |
| `/audit [--report]` | Auditoria de segurança completa | `/audit --report` |
| `/deploy [alvo]` | Deploy do projeto | `/deploy docker`, `/deploy vps` |
| `/status` | Status geral do projeto (módulos, gates, cobertura) | `/status` |
| `/fix` | Auto-correção de problemas detectados | `/fix` |
| `/gates [nome]` | Executa gates mecânicos específicos ou todos | `/gates G_TESTES` |

---

## Detalhes por Comando

### `/compose <módulos>`
Compõe fatias verticais dos módulos listados. Ativa o papel de arquiteto e gera a estrutura completa com EventBus, CQRS, OpenAPI e MCP.

**Variações reconhecidas (linguagem natural):**
- "arquitetura corporativa para pagamentos e estoque"
- "compose auth billing notifications"
- "montar módulos pagamentos usuarios"

### `/aidd-pack <módulos>`
Alias idêntico ao `/compose`. Mantido por compatibilidade com workflows legados.

### `/test [tipo]`
Executa testes. Tipos suportados:

| Tipo | Descrição |
|:-----|:----------|
| `unit` | Testes unitários |
| `contracts` | Testes de contrato |
| `load` | Testes de carga (Locust) |
| `integration` | Testes de integração |
| `all` (default) | Todos os tipos |

**Variações reconhecidas:**
- "testar tudo"
- "rodar testes unitários"
- "executar testes de carga"

### `/audit [--report]`
Executa auditoria de segurança completa. Com `--report`, gera relatório em `reports/`.

**Variações reconhecidas:**
- "auditar segurança"
- "security audit"

### `/deploy [alvo]`
Deploy do projeto. Alvos suportados: `docker`, `vps`, `production`.

**Variações reconhecidas:**
- "fazer deploy"
- "deploy docker"
- "deploy para produção"

### `/status`
Exibe status consolidado: módulos ativos, último gate executado, cobertura de testes, pendências.

**Variações reconhecidas:**
- "status do projeto"
- "como está o projeto"

### `/fix`
Executa auto-correção: lint, formatação, imports, type-check fixes.

**Variações reconhecidas:**
- "auto-fix"
- "corrigir tudo"
- "consertar erros"

### `/gates [nome]`
Executa gates mecânicos. Se nenhum nome for informado, executa todos.

Gates disponíveis: `G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`, `G_QUALIDADE`, `G_SEGREDOS`, `G_HARNESS_COMPAT`.

**Variações reconhecidas:**
- "rodar gates"
- "executar gate G_TESTES"

---

## Linguagem Natural

O **Intent Router** (`src/core/intent_router.py`) permite usar português natural em vez de comandos slash. Qualquer mensagem passa pelo router que tenta identificar a intenção e converter em comando AIDD.

### Mapeamento NL → Comando

| Frase natural | Comando resultante |
|:--------------|:-------------------|
| "arquitetura corporativa para pagamentos" | `compose` (role=architect, modules=[pagamentos]) |
| "criar modulo auth" | `add-module` (modules=[auth]) |
| "testar tudo" | `test` (scope=all) |
| "fazer deploy" | `deploy` |
| "auditar seguranca" | `audit` (report=true) |
| "compose auth billing" | `compose` (modules=[auth, billing]) |
| "status do projeto" | `status` |
| "corrigir tudo" | `fix` |
| "rodar gate G_TESTES" | `gates` (modules=[g_testes]) |

### Confiança do Match

Cada intent retorna um `match_confidence` (0.0 a 1.0):
- **≥ 0.8**: Alta confiança — executar diretamente
- **0.5 – 0.8**: Média confiança — confirmar com o usuário antes de executar
- **< 0.5**: Baixa confiança — pedir esclarecimento
