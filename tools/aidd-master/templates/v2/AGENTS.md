# Workspace Guidelines & ORCA ADE Orchestration Rules

## 1. Internal Reasoning / Thinking (English Caveman)
- Always execute internal reasoning (`thinking` / CoT) in **ENGLISH CAVEMAN style**.
- Telegraphic, concise phrases. No unnecessary filler words, articles, or polite prose.
- Shorten: "verify" -> "check", "necessary" -> "req", "implement" -> "impl".
- Max 3-5 lines for simple tasks. Ultra-dense logic.

## 2. User Responses (PT-BR)
- Always deliver user-facing outputs and explanations in **Portuguese (PT-BR)**.
- Keep responses objective, structured, and concise.
- Prefer tables, bullet points, and actionable steps over long paragraphs.
- Do not repeat file contents or diffs already visible in tool execution.

## 3. Project Context & Clean Architecture
- Enterprise Modular Suite with Vertical Slices (`src/modules/<domain>/`), EventBus pub/sub, SQLite WAL concurrency, OpenAPI 3.1 Live Swagger Studio (`/docs`), Native MCP Server (`/mcp`), and Impeccable Super-App UI.

---

## 🏆 AS 4 REGRAS DE OURO DA ENGENHARIA AGÊNTICA COM ORCA ADE

| Regra de Ouro | Como Aplicar | Por que evita estourar o limite |
| :--- | :--- | :--- |
| **1. Não use o chat principal como terminal** | Deixe compilação, testes (`pytest`) e tarefas mecânicas rodando via Python local. | Economiza 90% do seu consumo semanal. |
| **2. Use Worktrees do ORCA para frentes grandes** | Cada tarefa separada em sua mesa limpa (`orca worktree create --parent-worktree active`). | Evita que o contexto principal acumule 100k+ tokens desnecessários. |
| **3. Reinicie sessões usando o Plano JSON** | Ao começar um novo dia ou módulo, abra uma sessão nova apontando para o `PLANO-EXECUCAO-ESTRUTURADO.json`. | O agente retoma o estado exato consumindo apenas ~500 tokens em vez de 80.000 tokens do histórico. |
| **4. Governança Rígida por Gates Mecânicos** | A entrega só é aceita se todos os gates (`G_ESTRUTURA`, `G_TESTES`, `G_CONTRACTS`, `G_QUALIDADE`, `G_SEGREDOS`, `G_HARNESS_COMPAT`) retornarem exit 0. | Elimina alucinações e entregas incompletas na raiz. |

---

## 🦴 Caveman Ultra Protocol — Triple Phase Token Optimization

O **Caveman Ultra Protocol** é o motor de compressão tri-fase integrado ao AIDD v5.1. Ele otimiza o consumo de tokens em pipelines de agentes, reduzindo input em 30-50% (BPE) sem perda de qualidade técnica.

### As Três Fases

| Fase | Idioma | Estilo | Objetivo |
| :--- | :--- | :--- | :--- |
| **INPUT** | English Caveman | Compressão de regras | 30-50% redução BPE em instruções |
| **PROCESSING** | English Caveman Ultra | Thinking denso (CoT) | 3-5 linhas de raciocínio ultra-denso |
| **OUTPUT** | PT-BR padrão alto | Completo e estruturado | Código tipado, Result Monad, sem stubs |

### Níveis de Intensidade

| Nível | Quando Usar | Meta de Redução |
| :--- | :--- | :--- |
| **LITE** | Reuniões, docs formais, stakeholder | 20-30% |
| **FULL** | Desenvolvimento diário, code review | 35-50% |
| **ULTRA** | Sprints longas, context window apertado | 50-65% |

### Uso no Pipeline

```python
from src.core.caveman_protocol import CavemanProtocol, IntensidadeCaveman

proto = CavemanProtocol(intensidade=IntensidadeCaveman.FULL)

# Fase 1: Comprimir regras
resultado = proto.format_input(regras_originais)

# Fase 2: Template de thinking
resultado = proto.format_thinking(contexto_tarefa)

# Fase 3: Validar output PT-BR
resultado = proto.format_output(codigo_gerado)

# Estatísticas
stats = proto.estatisticas_sessao()
```

### Regras de Output PT-BR

- Código completo, sem omissões, sem `pass # TODO`
- Type hints obrigatórios em funções públicas
- Result Monad (`ok`/`fail`) para retornos de serviço
- Docstrings em PT-BR para classes e métodos públicos
- Mensagens de erro em PT-BR com códigos padronizados

Referência completa: `templates/rules/caveman-ultra-rules.md`

---

## 5. Zero Friction — Intent Router (Interface de Linguagem Natural)

O AIDD v5.1 inclui uma camada de interface zero-friction que permite comandos em linguagem natural (PT-BR) além dos slash commands tradicionais.

### Como Funciona

O **Intent Router** (`src/core/intent_router.py`) recebe texto livre e converte em comandos AIDD estruturados com `action`, `modules`, `options` e `match_confidence`.

### Slash Commands

| Comando | Descrição |
|:--------|:----------|
| `/compose <módulos>` | Compõe vertical slices |
| `/aidd-pack <módulos>` | Alias para compose |
| `/test [unit\|contracts\|load\|all]` | Executa testes |
| `/audit [--report]` | Auditoria de segurança |
| `/deploy [docker\|vps]` | Deploy |
| `/status` | Status do projeto |
| `/fix` | Auto-correção |
| `/gates [nome]` | Executa gates mecânicos |

> Documentação completa: `templates/slash-commands.md`

### Linguagem Natural → Comando AIDD

| Frase do usuário | Ação AIDD | Módulos | Options |
|:-----------------|:----------|:--------|:--------|
| "arquitetura corporativa para pagamentos" | `compose` | `[pagamentos]` | `{role: architect}` |
| "criar modulo auth" | `add-module` | `[auth]` | `{}` |
| "testar tudo" | `test` | `[]` | `{scope: all}` |
| "fazer deploy" | `deploy` | `[]` | `{}` |
| "auditar seguranca" | `audit` | `[]` | `{report: true}` |
| "compose auth billing" | `compose` | `[auth, billing]` | `{}` |
| "status do projeto" | `status` | `[]` | `{}` |
| "corrigir tudo" | `fix` | `[]` | `{}` |
| "rodar gate G_TESTES" | `gates` | `[g_testes]` | `{}` |

### Confiança do Match

O router retorna `match_confidence` (0.0–1.0) para cada intent:
- **≥ 0.8**: Alta confiança — executar diretamente
- **0.5–0.8**: Média — confirmar antes de executar
- **< 0.5**: Baixa — pedir esclarecimento ao usuário

### Uso Programático

```python
from src.core.intent_router import IntentRouter

router = IntentRouter()
result = router.parse_intent("criar modulo pagamentos")
# result = {
#     "action": "add-module",
#     "modules": ["pagamentos"],
#     "options": {},
#     "match_confidence": 0.85,
#     "raw_text": "criar modulo pagamentos"
# }
```
