# Protocolo de Ingestão e Harmonização Externa (aidd-ingest)

> **Governança:** Ingestão de repositórios externos sob isolamento estrito, triagem de integrabilidade perante as 13 Leis, Auditoria 4F e evolução em Git Worktrees efêmeras.
> **Referências:** [`PIPELINE-AUDITORIA-4F.md`](PIPELINE-AUDITORIA-4F.md), [`CONVENCAO-AUTORIA-SKILLS.md`](CONVENCAO-AUTORIA-SKILLS.md), [`CONVENCAO-AUTORIA-GATES.md`](CONVENCAO-AUTORIA-GATES.md).

---

## 1. Visão Geral do Pipeline Unificado

O pipeline `aidd-ingest` permite absorver repositórios externos (ferramentas, MCPs, skills, utilitários e processos) de forma segura, garantindo que nenhum código externo seja inserido no ecossistema sem triagem determinística, auditoria de conformidade e adaptação aos padrões canônicos.

```
[Repositório Externo (Git/URL)]
           │
           ▼
[Fase 1: Triagem & Isolamento Efêmero] ──► Rejeita stubs, mocks, lock-in, violações das 13 Leis
           │
           ▼
[Fase 2: Auditoria 4F (Inspetor 15-D)] ──► Emite Laudo Técnico e Matriz de Riscos
           │
           ▼
[Fase 3: Plano de Evolução (Arquiteto)] ──► Compila PLANO-EVOLUCAO.json com tickets atômicos
           │
           ▼
[Fase 4: Execução em Worktrees (Construtor)] ──► Implementa em componentes/ com Gates e Barreira Humana
```

---

## 2. As 4 Fases Canônicas

### Fase 1: Triagem de Integrabilidade e Isolamento Efêmero
- **Isolamento de Sandbox:** O repositório externo é clonado exclusivamente no diretório efêmero `.tmp/ingest/<slug>/` (ignorado pelo Git).
- **Varredura Estática:** O analisador inspeciona a árvore do repositório procurando:
  - Componentes aproveitáveis: servidores MCP, definições de ferramentas, prompts/skills procedurais, clientes de API agnósticos.
  - Incompatibilidades e bloqueios: SDKs proprietários acoplados (violação da Lei #6), stubs ou mocks de teste (Lei #5), subagentes invisíveis sem harness auditável (Lei #7), código sem testes reais (Lei #1 e Lei #13).
- **Entregável:** `MANIFESTO-TRIAGEM.json` contendo o inventário de peças elegíveis, peças descartadas e o motivo formal de cada veto.

### Fase 2: Auditoria 4F (Inspetor nas 15 Dimensões)
- **Execução:** Disparo do motor de auditoria (`aidd-audit-4f`) focado nas peças elegíveis listadas no manifesto.
- **Avaliação:** Análise profunda de segurança, tipagem, dependências limpas e ausência de chamadas maliciosas.
- **Entregável:** `docs/auditoria/<alvo>/ciclo-01/RELATORIO-AUDITORIA.md` com nota atual e requisitos de conformidade.

### Fase 3: Arquiteto e Plano de Evolução
- **Decomposição em Peças Canônicas:** Mapeia cada componente aprovado para seu destino de fonte única:
  - Skills procedurais ➔ `componentes/compartilhado/skills/aidd-<nome>/`
  - Servidores MCP ➔ `componentes/compartilhado/mcps/<nome>/`
  - Quality Gates complementares ➔ `gates/G_<NOME>.py`
- **Geração de Tickets:** Compilação de `PLANO-EVOLUCAO.json` com fatias verticais, critérios de aceitação binários (DoD) e scripts de verificação.

### Fase 4: Execução em Worktrees e Barreira Humana (Join Barrier)
- **Execução Atômica:** Cada ticket do plano é executado em Git Worktree efêmera (`aidd-evolution` ou `aidd-orca`).
- **Verificação Contínua:** Nenhum commit é realizado sem passar pela auditoria binária (`python ecossistema.py audit`).
- **Sincronização:** Após aprovação e merge da worktree, as peças em `componentes/` são sincronizadas para todos os harnesses via `python ecossistema.py components sync --tipo todos`.
- **Limpeza do Sandbox:** O diretório efêmero `.tmp/ingest/<slug>/` é purgado automaticamente ao término da migração.

---

## 3. Invariáveis Inegociáveis

1. **Proibição de Poluição do Repositório:** O repositório externo clonado NUNCA deve ser commitado diretamente ou mantido permanentemente na árvore de código do ecossistema.
2. **Adaptação às Convenções de Peças:**
   - Toda skill ingerida deve ser renomeada com prefixo `aidd-` e adotar a convenção de [`CONVENCAO-AUTORIA-SKILLS.md`](CONVENCAO-AUTORIA-SKILLS.md).
   - Todo gate criado deve cumprir a Lei #13 comprovando que morde via teste (`G_PORTAO_PROVA_QUE_MORDE.py`).
3. **Soberania do Desenvolvedor:** O manifesto de triagem e o plano de evolução requerem revisão e aprovação antes do início da execução em worktrees.
