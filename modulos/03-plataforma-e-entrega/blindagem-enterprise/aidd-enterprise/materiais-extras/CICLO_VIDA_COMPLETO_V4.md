# Ciclo de Vida Completo do AIDD Master Pack v5.1 (Nível Ultra — 12 Pilares Formação.DEV)

## 1. Visão Geral do Ciclo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 0: ACESSO E INSTALAÇÃO NO AMBIENTE DO USUÁRIO                          │
│ 1. Obtenção do Pacote: git clone ou link de pasta local                     │
│ 2. Bootstrap Automático: instalação de dependências e diagnóstico           │
│ 3. Verificação de Saúde do Runtime: detecção de ORCA ADE vs Subagentes      │
│    $ python scripts/aidd.py setup                                           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1: ENTRADA DO USUÁRIO (USER INPUT - ZERO ATRITO & LINGUAGEM NATURAL)   │
│ Modo A (Linguagem Natural no Chat ou CLI):                                  │
│ $ python scripts/aidd.py "Crie uma aplicação de CRM e ERP de faturamento"   │
│                                                                             │
│ Modo B (Comando Declarativo):                                               │
│ $ python scripts/aidd.py plan "Crie um CRM e ERP"                           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 1.5: ESPECIFICAÇÃO & ALINHAMENTO ARQUITETURAL EM 3 NÍVEIS (SPEC GATE)  │
│ 1. Geração de SPEC-ARQUITETURA.md (Negócio, Backend, Frontend/UX)           │
│ 2. Geração do Manifesto PLANO-EXECUCAO-ESTRUTURADO.json                     │
│ 3. Revisão Interativa: Usuário aprova ou ajusta fatias e entidades          │
│ 4. Gatilho de Aprovação: $ python scripts/aidd.py apply --dir <pasta>       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 2: PROCESSAMENTO MECÂNICO (PROCESSING - ELITE AGENTIC ENGINE)          │
│ 1. Linter AST Anti-Acoplamento & Zero Connection Leak                       │
│ 2. Scaffolding do Shared Kernel com SQLite WAL + Soft-Delete + busy_timeout │
│ 3. Monad Result Pattern (Result.ok / Result.fail) e JobQueue em Background  │
│ 4. Controle de Migrações de Schema (_schema_migrations)                     │
│ 5. Geração Atômica de Fatias Verticais com Seed Fixtures Determinísticas    │
│ 6. EventBus Pub/Sub com Validação de Contrato de Payload e Tracing UUID     │
│ 7. Servidor Dinâmico src/server.py com Port Fallback (3000..3025) e CORS    │
│ 8. Geração de Testes com Asserção Forte de Mutação de Estado                │
│ 9. Linter de Acessibilidade & Impeccable UI (WCAG 2.1)                      │
│ 10. Snapshot SHA-256 de Contratos OpenAPI e MCP                             │
│ 11. Sincronização Multi-IDE (.cursor/rules, .claude, .agent)                │
│ 12. Grafo de Memória CONTEXTO-PROJETO.md                                    │
│ 13. Execução dos 7 Quality Gates com Limpeza Automática de Cache            │
│ 14. Benchmark Concorrente ($ python scripts/aidd.py bench -n 100)           │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FASE 3: SAÍDA ENTREGUE E OPERACIONAL (OUTPUT)                               │
│ Servidor ativo com 4 Portais e Relatório Auditado (Nota A+ 100% Blindado)   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detalhamento dos 12 Pilares Formação.DEV Implementados

| # | Pilar Estrutural | Risco Eliminado | Arquivo Principal |
| :---: | :--- | :--- | :--- |
| **1** | **Result Pattern** | Falhas 500 e exceções não tratadas por agentes. | `src/core/result.py` |
| **2** | **Value Objects Ricos** | Tipos primitivos crus e entidades anêmicas. | `src/shared/utils/validators.py` |
| **3** | **Auditoria & Soft-Delete** | Exclusão física acidental de dados. | `models.py` / `services.py` |
| **4** | **SPEC em 3 Níveis** | Alucinação e retrabalho de escopo. | `SPEC-ARQUITETURA.md` |
| **5** | **Tabela Paginada & Filtros** | Travamento de UI com listas longas. | `services.py` / Componente HTML |
| **6** | **RBAC no Kernel** | Acesso indevido a rotas administrativas. | `src/core/security.py` |
| **7** | **Templates de Subagentes** | Contextos sobrecarregados e lentidão. | `templates/agents/*.md` |
| **8** | **Multi-IDE Rules Sync** | Falta de governança em IDEs variadas. | `.cursor/`, `.claude/`, `.agent/` |
| **9** | **Busca Instantânea Local** | Queries pesadas e lentas no banco. | `services.py` (`busca`) |
| **10** | **Grafo de Memória do Projeto** | Perda de contexto em novas sessões de IA. | `CONTEXTO-PROJETO.md` |
| **11** | **Fila de Jobs Assíncronos** | Timeouts HTTP em tarefas demoradas. | `src/core/jobs.py` |
| **12** | **Cards de KPIs no Topo** | Telas cruas sem visão executiva. | `services.obter_metricas()` |
