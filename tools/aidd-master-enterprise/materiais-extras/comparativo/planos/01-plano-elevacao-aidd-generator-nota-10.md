# Plano de Ação: Elevação do aidd-generator para Nota 10.0 em Todas as Camadas

> **Projeto:** `aidd-generator` (Versão Atual: 2.1 / Tag: `7d63085`)  
> **Nota Atual Consolidada:** 8.74 / 10.0  
> **Meta:** Atingir 10.0+ em todas as 5 dimensões técnicas de engenharia agêntica.  
> **Inovações Integradas:** Orquestração de Subagentes com Descarte Imediato de Contexto + Auto-Descoberta de Frota Orca + Modularização Granular por Fase + Interface Zero Fricção (/generate) + Protocolo Caveman Ultra.

---

## 1. Diagnóstico das Lacunas Atuais (Por que não é 10.0 hoje?)

| Dimensão | Nota Atual | Meta | Principal Lacuna Identificada |
| :--- | :---: | :---: | :--- |
| **Engenharia Agêntica** | 9.2 | **10.0+** | Execução sequencial pesada que acumula histórico de conversas; falta de subagentes concorrentes descartáveis e risco de erro se o usuário não tiver agentes específicos instalados. |
| **Conceitos de AIDD** | 9.5 | **10.0+** | Schemas Draft 2020-12 gerados sem tipagem estática (Pydantic / Dataclasses) automática para os scripts funcionais. |
| **Economia de Tokens** | 9.7 | **10.0+** | Falta de descarte atômico de contexto: o pipeline acumula tokens de fases anteriores ao chegar na Fase 8. |
| **Qualidade do Output** | 7.5 | **10.0+** | A Fase 8 varia entre 55% e 91% de acerto; falta interface gráfica interativa, OpenAPI viva e testes cruzados de integração. |
| **Eficácia Factual** | 7.8 | **10.0+** | Falhas de compilação intermitentes, carência de auto-descoberta dinâmica de frota e ausência do Gate I3. |

---

## 2. Orquestração de Subagentes com Descarte Imediato de Contexto (Context-Purge Engine)

Para garantir máxima velocidade e eliminar o inchaço de contexto (Context Bloat), o `aidd-generator` adota a separação estrita entre **Mecânica Determinística** e **Cognição Descartável**:

```
                  ORQUESTRADOR DO PIPELINE
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   ONDE ENTRA O PYTHON               ONDE ENTRAM OS SUBAGENTES
  (Zero Token / Mecânico)           (Cognição / Trabalho Criativo)
  ───────────────────────           ──────────────────────────────
  • Criação de pastas e arquivos.   • Síntese da lógica de negócio.
  • Parsing e linter estático AST.  • Geração do código Python real.
  • Execução do `pytest` local.     • Investigação 5-Porquês (post-mortem).
  • Validação binária de Gates.     • Revisão cega de arquitetura.
  • Mata e inicializa processos.    • MORRE ASSIM QUE GERA O ARTEFATO.
```

- **Mecânica de Descarte Imediato:**
  1. O script Python detecta a necessidade de cognição (ex: escrever a função de serviço da Fase 8).
  2. Ele instancia um **Subagente Efêmero** com um prompt limpo contendo unicamente: o schema JSON da entidade, as regras da fase e a meta de código (~1.000 tokens).
  3. O subagente gera o código e o salva no disco.
  4. O orquestrador valida o código via AST (`ast.parse`) e **destrói imediatamente a sessão do subagente**.
  5. **Ganho:** Zero acúmulo de memória. O pipeline chega ao fim gastando uma fração ínfima do custo de um agente monolítico.

---

## 3. Auto-Descoberta de Frota & Fallback em Cascata no ORCA ADE

Para evitar qualquer erro de execução caso o usuário não possua ferramentas específicas instaladas (ex: se não tiver `codex` ou `opencode`):

```
                              INÍCIO DO RUNNER ORCA
                                        │
                                        ▼
                      ┌────────────────────────────────────┐
                      │ 1. Auto-Descoberta de Ferramentas  │
                      │    (which claude, codex, agy, etc) │
                      └─────────────────┬──────────────────┘
                                        │
             ┌──────────────────────────┴──────────────────────────┐
             ▼                                                     ▼
   DETECTOU MÚLTIPLOS AGENTES                             DETECTOU APENAS 1 AGENTE
(Ex: Tem Claude e Codex no host)                        (Ex: Usuário só tem Antigravity)
             │                                                     │
             ▼                                                     ▼
ROTEIA POR ESPECIALIDADE                               MODO "AGENTE ÚNICO ISOLADO"
• Arquiteto  ➔ Claude                                  • Todos os workers usam Antigravity!
• Database   ➔ Codex                                   • MAS rodam em Worktrees separadas
                                                       • Mantém o ganho de contexto limpo!
```

- **Configuração Customizável pelo Usuário (`.env`):**
  ```env
  # Opcional: forçar um único agente para toda a frota
  ORCA_DEFAULT_HARNESS=antigravity   # ou claude, codex, cursor, ollama
  ```
- Se não customizado, o script detecta as ferramentas instaladas automaticamente. Se houver apenas uma ferramenta, todos os workers operam nela em worktrees separadas sem falhar.

---

## 4. Modularização Granular por Fase (Phase-Level Agentic Fencing)

O pipeline do `aidd-generator` organiza cada etapa em micro-ambientes isolados:
* `phase_01_pesquisa/`: apenas regras de escopo e Filesystem MCP.
* `phase_03_designer/`: apenas regras de modelagem e Schemas Draft 2020-12.
* `phase_05_criador/`: apenas regras de Impeccable UI Tailwind e AST linter.
* `phase_08_implementador/`: apenas regras de Result Monad, pytest e Database MCP.

---

## 5. Interface Humana Zero Fricção (Zero Terminal Barrier)

* **Slash Command Nativo:** `/generate <ideia>` ou `/aidd-gen <ideia>` no chat.
* **Linguagem Natural:** Intent router no `AGENTS.md` detecta frases como *"crie um sistema de..."* e aciona o pipeline.
* **1-Clique Desktop:** `iniciar.bat` (Windows) / `iniciar.sh` (Linux/Mac) abrindo a interface local em `localhost:5000`.

---

## 6. Protocolo Tríplice de Economia Severa de Tokens (Caveman Ultra)

1. **ENTRADA (System Prompts em Inglês):** Economia de 30% a 50% de tokens de BPE.
2. **PROCESSAMENTO (Internal Thinking em English Caveman):** CoT telegráfico de 3 a 5 linhas sem artigos (*"check schemas, fix FK, impl CRUD"*).
3. **SAÍDA / OUTPUT (Português do Brasil - PT-BR de Alta Precisão):** Respostas diretas, sem enrolação, com código completo e testado.

---

## 7. Cronograma de Execução

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   CRONOGRAMA DE ELEVAÇÃO: aidd-generator ➔ NOTA 10.0+            │
├──────────────────────────────────────────────────────────────────────────────────┤
│ SPRINT 1: Engine de Subagentes Efêmeros com Descarte Imediato de Contexto        │
│ SPRINT 2: Auto-Descoberta de Frota & Fallback Universal no ORCA ADE              │
│ SPRINT 3: Reestruturação Granular por Fase (Micro-Ambientes com AGENTS/MCPs)    │
│ SPRINT 4: Camada Zero Fricção (Slash Commands /generate + Intent Router)         │
│ SPRINT 5: Protocolo Tríplice Caveman Ultra nos Prompts (Input EN / CoT / PT-BR)  │
│ SPRINT 6: Reestruturação da Fase 8 em Micro-Tasks AST com Result Pattern         │
│ SPRINT 7: Implementação do Gate I3 e Gate de Cibersegurança OWASP                │
└──────────────────────────────────────────────────────────────────────────────────┘
```
