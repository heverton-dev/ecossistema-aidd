# Ficha de Auditoria Bit a Bit: Micro-Ferramentas de Engenharia Procedural (`aidd-grill`, `aidd-spec`, `aidd-tickets`, `aidd-tdd`)

> **Micro-Ferramentas:** `componentes/compartilhado/skills/` (`aidd-grill`, `aidd-spec`, `aidd-tickets`, `aidd-tdd`)  
> **Data da Auditoria:** 2026-09-22  
> **Status:** AUDITADO / ÍNTEGRO  
> **Responsável:** Antigravity / Eco-AIDD Agent

---

## SESSÃO I: ESTADO ATUAL (Diagnóstico Pré-Implementação)

### 1. Matriz Contratual das 11 Dimensões

| Micro-Ferramenta | 1. RECEBE (Input) | 2. CRIA / PROCESSA | 3. ENTREGA (Output) | 4. CONFIGS | 5. GATES | 6. SCRIPTS 0 LLM | 7. HOOKS | 8. AGENTS | 9. SKILLS | 10. MCPS | 11. RULES |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **`aidd-grill`** | Ideia bruta ou pedido de refatoração do usuário | Protocolo socrático estrito de 1 pergunta por vez; esgota branches de decisão e edge cases | Bloco estruturado de premissas alinhadas e critérios não-funcionais | Modo interativo (chat) ou headless (síntese determinística) | `G_QUALIDADE` | Parser de invariantes | Interrupção imediata em ambiguidade crítica | Persona Entrevistador Socrático | `aidd-grill`, `aidd-grill-docs` | `code-review-graph` para contexto | Encadeamento obrigatório para `/aidd-spec` |
| **`aidd-spec`** | Premissas validadas pelo `aidd-grill` | Estruturação de escopo, contratos tipados (JSON Schema, TypeScript, Python) | Especificação técnica executável em `docs/planos/` | N/A (formato canônico universal) | `G_CONTRACTS`, `G_ESTRUTURA` | Validação de schemas tipados | Rejeição de especificação sem critérios de aceitação binários | Persona Engenheiro de Requisitos | `aidd-spec` | N/A | Zero conversação vazia; encadeamento para `/aidd-tickets` ou `/aidd-planner` |
| **`aidd-tickets`** | Especificação técnica formal de `aidd-spec` | Decomposição atômica com blast radius delimitado (Tracer Bullets) | Sequência ordenada de tickets atômicos TDD com dependências | `--modo <linear\|dag>` | `G_DETERMINISMO_LEI_1` | Algoritmo DAG de ordenação de tickets | Bloqueio de tickets com blast radius > 3 arquivos | Persona Planejador Atômico | `aidd-tickets` | N/A | Proibição de tarefas genéricas ou sem teste associado |
| **`aidd-tdd`** | Ticket atômico de implementação | Ciclo estrito Red-Green-Refactor com asserções reais | Código funcional tipado e teste correspondente com `exit 0` | `--polyglot <python\|ts\|go\|rust>` | `G_TESTES_REAIS`, `G_SAIDA_BINARIA` | Runner local de testes (`pytest`, `npm test`) | Bloqueio de código sem teste que falha no Red | Persona Desenvolvedor TDD | `aidd-tdd` | N/A | Lei Inviolável #5: Zero stubs, zero mocks vazios |

### 2. Evidência de Testes e Sincronização
- **Comando executado:** `python ecossistema.py components verify --tipo todos`
- **Resultado:** 91/91 componentes verificados e sincronizados com SHA-256 idêntico em todos os harnesses (`.agents/`, `.claude/`, `.gemini/`, `.cursor/`, `.windsurf/`).

---

## SESSÃO II: PLANO DE CORREÇÃO & TICKETS DE MELHORIA

*(Nenhum ticket impeditivo aberto. Micro-ferramentas canônicas sincronizadas sem drift).*

---

## SESSÃO III: ESTADO PÓS-IMPLEMENTAÇÃO (Certificação)

- **Status:** APROVADO & CERTIFICADO
- **Nível de Autonomia:** Protocolo canônico agnóstico multi-harness com integridade criptográfica.
