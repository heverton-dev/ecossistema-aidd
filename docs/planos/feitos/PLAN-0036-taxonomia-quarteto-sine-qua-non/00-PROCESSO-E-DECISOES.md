# PROCESSO E DECISOES — taxonomia-quarteto-sine-qua-non

> **Iniciativa:** PLAN-0036-taxonomia-quarteto-sine-qua-non  
> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd  
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.  
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Implementar a nova taxonomia do **Quarteto Sine Qua Non** (Lei Inviolável #10), promovendo a convenção `/api` (OpenAPI/Swagger Studio), `/webhook` (Webhook Studio), `/mcp` (MCP Studio) e `/docs` (Guia e Documentação Central do Utilizador).

- **Objetivo Principal:** Harmonizar a definição nas Leis, nos Quality Gates (`G_QUARTETO_SINE_QUA_NON` e `G_CONTRACT_ROT`), no núcleo compartilhado, nos templates de servidores, nos projetos de referência e nos livros corporativos.
- **Limites de Escopo:** Preservar compatibilidade retroativa (redirects de `/docs` -> `/api` para Swagger e `/webhooks` -> `/webhook`), garantindo que nenhum teste ou contrato existente quebre.

### Metrica da Iniciativa (0-10)

- **Status:** CONCLUÍDO (100%)
- **Data de Conclusão:** 2026-09-21 — evidencia: Auditoria de Leis e rotas históricas [/docs, /webhooks, /mcp, /docs/guia]
- **Nota Alvo:** 10.0
- **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa]

## 2. Processo Adotado

Compilação determinística via `compilador_tickets_plano.py` → Execução em Git Worktrees isoladas com Join Barrier → Validação estrita de Quality Gates → Convergência na branch principal.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | governanca-leis-agents-memory | `01-governanca-leis-agents-memory.md` |
| 2 | quality-gates-quarteto-contract-rot | `02-quality-gates-quarteto-contract-rot.md` |
| 3 | templates-servidores-core-master-enterprise | `03-templates-servidores-core-master-enterprise.md` |
| 4 | projetos-referencia-e-exemplos | `04-projetos-referencia-e-exemplos.md` |
| 5 | livros-documentacao-e-sincronismo | `05-livros-documentacao-e-sincronismo.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho:** Rascunhos aguardam aprovação explícita.
2. **Determinismo First (Lei #1):** Comandos de validação determinísticos em todos os tickets.
3. **Zero Mocks / Zero Stubs (Lei #5):** Sem stubs, mocks ou comandos triviais.
4. **Isolamento:** Execução estrita em worktrees efêmeras.
