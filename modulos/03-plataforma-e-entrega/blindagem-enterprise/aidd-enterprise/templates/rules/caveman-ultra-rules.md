# 🦴 Caveman Ultra Protocol — Triple Phase Token Optimization

**Protocolo de compressão tri-fase para pipelines de agentes de IA.**
Reduz consumo de tokens em 30-50% (BPE) sem perda de qualidade técnica.

---

## 📐 1. Visão Geral do Protocolo

O Caveman Ultra Protocol opera em três fases sequenciais, cada uma com idioma e estilo otimizados:

| Fase | Idioma | Estilo | Objetivo |
| :--- | :--- | :--- | :--- |
| **INPUT** | English Caveman | Compressão de regras | 30-50% redução BPE em instruções |
| **PROCESSING** | English Caveman Ultra | Thinking denso (CoT) | 3-5 linhas de raciocínio ultra-denso |
| **OUTPUT** | PT-BR padrão alto | Completo e estruturado | Código tipado, Result Monad, sem stubs |

---

## 📥 2. Fase INPUT — Compressão de Regras

### Objetivo
Comprimir regras, instruções e contexto de entrada em English Caveman, eliminando redundância e mantendo significado técnico.

### Regras de Compressão

**Substituições obrigatórias:**
- "it is necessary to" → "must"
- "in order to" → "to"
- "implement a solution for" → "fix"
- "provide assistance to" → "help"
- "conduct an analysis of" → "analyze"
- "configuration" → "cfg"
- "environment" → "env"
- "authentication" → "auth"
- "documentation" → "docs"

**Remoções (nível FULL+):**
- Artigos: the, a, an
- Filler: just, really, basically, actually, simply
- Hedge: certainly, surely, definitely, absolutely
- Redundância: very, quite, particularly, specifically

### Exemplo INPUT

**Original (148 tokens):**
```
It is necessary to implement a solution for the database connection pooling
configuration. The application must verify that all authentication tokens
are valid before establishing a connection to the production environment.
In order to ensure sufficient performance, it is important to conduct an
analysis of the current connection pool metrics and provide an explanation
of any potential bottlenecks.
```

**Comprimido — LITE (~100 tokens, -32%):**
```
Must fix database connection pooling cfg. Application verify all auth
tokens valid before connecting to prod env. To ensure sufficient
performance, must analyze current connection pool metrics and explain
potential bottlenecks.
```

**Comprimido — FULL (~75 tokens, -49%):**
```
Fix db conn pooling cfg. App verify auth tokens valid before prod env
conn. Ensure perf → analyze conn pool metrics → explain bottlenecks.
```

**Comprimido — ULTRA (~55 tokens, -63%):**
```
Fix db conn pooling cfg. App verify auth tokens→prod conn. Perf→analyze
pool metrics→explain bottlenecks.
```

---

## 🧠 3. Fase PROCESSING — Thinking Denso (CoT)

### Objetivo
Guiar o raciocínio interno do agente com template ultra-denso em 3-5 linhas.

### Formato CoT

**Nível LITE (4 linhas, frases curtas):**
```
Task: database connection pooling.
Goal: optimize pool config for production.
Steps: identify → implement → verify.
Constraints: type-safe, Result pattern, no stubs.
```

**Nível FULL (4 linhas, telegráfico):**
```
Ctx: db conn pooling.
Goal: optimize pool cfg prod.
Plan: analyze → impl → test → verify.
Rules: typed, Result monad, no stubs, PT-BR output.
```

**Nível ULTRA (3 linhas, ultra-denso):**
```
db conn pooling→optimize prod.
analyze→impl→test→verify.
typed∧Result∧¬stubs∧PT-BR.
```

### Regras do Thinking

1. **Máximo 5 linhas** para qualquer tarefa
2. **Sem prosa** — apenas substantivos, verbos e conectivos essenciais
3. **Abreviações técnicas** permitidas: cfg, env, impl, req, res, err, fix
4. **Símbolos lógicos** (ULTRA): → (então), ∧ (e), ∨ (ou), ¬ (não), ∴ (portanto)
5. **Nunca omitir**: Result Monad, type-safety, PT-BR output requirement

---

## 📤 4. Fase OUTPUT — PT-BR Padrão Alto

### Objetivo
Garantir que toda entrega final esteja em Português do Brasil com qualidade técnica máxima.

### Padrões Obrigatórios

| Aspecto | Regra |
| :--- | :--- |
| **Idioma** | PT-BR gramaticalmente correto, sem anglicismos desnecessários |
| **Código** | Completo, sem omissões, sem stubs, sem `pass # TODO` |
| **Tipagem** | Type hints obrigatórios em todas as funções públicas |
| **Resultado** | Result Monad (ok/fail) para retornos de serviço |
| **Documentação** | Docstrings em PT-BR para classes e métodos públicos |
| **Erros** | Mensagens de erro em PT-BR, códigos padronizados |
| **Formatação** | Tabelas, bullet points, passos acionáveis |

### Termos Técnicos Aceitos (não traduzir)

Mantém-se em inglês (padrão da indústria):
- Nomes de tecnologias: Python, FastAPI, SQLite, Docker
- Nomes de padrões: Result Monad, Circuit Breaker, CQRS
- Nomes de conceitos: EventBus, Webhook, MCP, OpenAPI
- Comandos e APIs: `pytest`, `git`, `curl`, `/health`

### Exemplo OUTPUT

**❌ Incorreto (stubs + inglês):**
```python
def get_user(user_id: int):
    # TODO: implement
    pass
```

**✅ Correto (PT-BR + completo + Result Monad):**
```python
def obter_usuario(user_id: int) -> Result[Usuario]:
    """Obtém usuário por ID com validação de existência."""
    usuario = repositorio.buscar_por_id(user_id)
    if usuario is None:
        return Result.fail(
            erro=f"Usuário {user_id} não encontrado",
            codigo="USUARIO_NAO_ENCONTRADO",
        )
    return Result.ok(valor=usuario)
```

---

## 🎚️ 5. Níveis de Intensidade

### Quando usar cada nível

| Nível | Quando Usar | Meta de Redução |
| :--- | :--- | :--- |
| **LITE** | Reuniões, explicações ao stakeholder, docs formais | 20-30% |
| **FULL** | Desenvolvimento diário, code review, refatoração | 35-50% |
| **ULTRA** | Sprints longas, context window apertado, batch processing | 50-65% |

### Critérios de Escalação

```
LITE → FULL: Quando contexto > 50% da janela
FULL → ULTRA: Quando contexto > 75% da janela ou batch > 10 tasks
ULTRA → FULL: Quando precisão > economia (debugging complexo)
FULL → LITE: Quando comunicação com stakeholder não-técnico
```

### Exemplos por Nível

**Pergunta:** "Por que o componente React re-renderiza?"

- **LITE:** "Seu componente re-renderiza porque cria uma nova referência de objeto a cada render. Envolva com `useMemo`."
- **FULL:** "Nova ref obj cada render. Objeto inline prop = nova ref = re-render. Wrap `useMemo`."
- **ULTRA:** "Inline obj prop, nova ref, re-render. `useMemo`."

---

## 📊 6. Métricas e Validação

### Métricas de Sucesso

| Métrica | Meta | Como Medir |
| :--- | :--- | :--- |
| Redução BPE (INPUT) | ≥ 30% (FULL) | `estimate_savings()` |
| Linhas CoT (PROCESSING) | ≤ 5 | Contagem de linhas |
| Qualidade PT-BR (OUTPUT) | 0 problemas | `_validar_idioma_output()` |
| Completude técnica | 0 stubs | `_validar_completude_tecnica()` |
| Overhead compressão | < 1ms | Timer interno |

### Validação Automática

O motor `CavemanProtocol` valida automaticamente:
1. **INPUT:** Texto não vazio, compressão aplicada
2. **PROCESSING:** Template CoT gerado com ≤ 5 linhas
3. **OUTPUT:** Idioma PT-BR, sem stubs, Result Monad presente

---

## 🔧 7. Integração com AIDD v5.1

### Uso no Pipeline de Agentes

```python
from src.core.caveman_protocol import CavemanProtocol, IntensidadeCaveman

# Inicializar com intensidade desejada
proto = CavemanProtocol(intensidade=IntensidadeCaveman.FULL)

# Fase 1: Comprimir regras de input
resultado_input = proto.format_input(regras_originais)
if resultado_input.sucesso:
    regras_comprimidas = resultado_input.valor

# Fase 2: Gerar template de thinking
resultado_thinking = proto.format_thinking(contexto_tarefa)
if resultado_thinking.sucesso:
    template_cot = resultado_thinking.valor

# Fase 3: Validar output em PT-BR
resultado_output = proto.format_output(codigo_gerado)
if resultado_output.sucesso:
    output_validado = resultado_output.valor

# Estatísticas da sessão
stats = proto.estatisticas_sessao()
```

### Integração com Result Monad

Todas as operações do protocolo retornam `Result[T]`, seguindo o padrão monádico do projeto:
- `Result.ok(valor, detalhes)` — operação bem-sucedida
- `Result.fail(erro, codigo, detalhes)` — falha com motivo e código

---

## 📋 8. Checklist de Implementação

- [ ] `CavemanProtocol` instanciado com intensidade adequada
- [ ] INPUT: regras comprimidas antes de enviar ao agente
- [ ] PROCESSING: template CoT injetado no system prompt
- [ ] OUTPUT: validação PT-BR executada antes de entregar
- [ ] Estatísticas coletadas para métricas de economia
- [ ] Result Monad utilizado em todos os retornos de serviço
