# Ficha de Auditoria Bit a Bit: Micro-Ferramentas de Análise, Evolução e Diagnóstico (`aidd-melhoria`, `aidd-plan`, `aidd-diagnose`, `aidd-handoff`)

> **Micro-Ferramentas:** `componentes/compartilhado/skills/` (`aidd-melhoria`, `aidd-plan`, `aidd-diagnose`, `aidd-handoff`)  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Micro-Ferramenta | 1. RECEBE (Input) | 2. CRIA / PROCESSA | 3. ENTREGA (Output) | 4. CONFIGS | 5. GATES | 6. SCRIPTS 0 LLM | 7. HOOKS | 8. AGENTS | 9. SKILLS | 10. MCPS | 11. RULES |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **`aidd-melhoria`** | Pedido em linguagem natural ou código existente | Avaliação heurística e diagnóstica de arquitetura, débitos e vulnerabilidades | Relatório estruturado em `docs/melhorias/` com Nota Atual e evidências | `--pedido`, `--nome` | `G_QUALIDADE` | Parser de relatório e métricas | Parada obrigatória: "Deseja que eu gere o plano a partir disto?" | Persona Auditor de Qualidade | `aidd-melhoria`, `melhoria` | `code-review-graph` | Proibido modificar código diretamente sem plano gerado |
| **`aidd-plan`** | Relatório de `aidd-melhoria` ou especificação aprovada | Decomposição formal em fases, fatias e critérios de validação | Pasta estruturada em `docs/planos/<nome>/` com todos os itens | `--formato <markdown\|json>` | `G_ESTRUTURA_ESTADO` | Template generator estático | Parada obrigatória: "Aprova este plano?" antes da orquestração | Persona Arquiteto de Software | `aidd-plan`, `aidd-planos`, `plan` | N/A | Plano deve ser auto-contido e auditável |
| **`aidd-diagnose`** | Sintoma de falha, stacktrace ou regressão de teste | Triagem científica em 5 fases: isolamento de hipóteses, reprodução mínima, inspeção de impacto | Teste de regressão determinístico e relatório de causa-raiz | `--fase <1-5>` | `G_PORTAO_PROVA_QUE_MORDE` | Script de teste mínimo isolado | Interrupção imediata caso a regressão não seja reproduzível deterministicamente | Persona Investigador Científico de Falhas | `aidd-diagnose`, `debug-issue` | `code-review-graph` (`get_impact_radius_tool`) | Proibido aplicar correções baseadas em "achismos" ou sem teste que falhe antes |
| **`aidd-handoff`** | Estado volátil da sessão ativa de chat | Serialização e compactação de contexto de memória e variáveis | Artefato compacto de handoff em `secoes/` ou `docs/handoff/` | `--compact` | `G_IDIOMA_LEI_4` | Serializador estruturado | Alerta de saturação de contexto (>150k tokens) recomendando rotação de sessão | Persona Operador de Contexto | `aidd-handoff`, `resumo-sessao` | N/A | Lei Inviolável #4: Economia extrema de tokens (<2000 tokens de contexto ativo) |

### 2. Evidência de Testes e Sincronização
- **Comando executado:** `python ecossistema.py components verify --tipo todos`
- **Resultado:** 91/91 componentes verificados e sincronizados com SHA-256 idêntico em todos os harnesses (`.agents/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`).

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Micro-ferramentas canônicas sincronizadas sem drift).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Conjunto completo de micro-ferramentas integradas e sincronizadas.
