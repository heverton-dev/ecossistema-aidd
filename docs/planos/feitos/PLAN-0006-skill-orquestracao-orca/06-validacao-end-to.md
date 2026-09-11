# Item 6 — Validação End-to-End com Agentes Reais (Trava de Segurança)

> **Status:** 🔒 **BLOQUEADO — AGUARDANDO APROVAÇÃO EXPLÍCITA DE CUSTO DO USUÁRIO**  
> **Custo de LLM:** **Real e Não-Trivial** (disparo paralelo de CLI com tokens de LLM).  
> **Trava de Segurança:** Nenhuma chamada a binários reais com prompts de escrita será realizada sem consentimento explícito do usuário, espelhando o Protocolo Delegado do `aidd-generator`.

---

## 1. Condições de Desbloqueio

Para que este item seja iniciado, os seguintes pré-requisitos devem ser estritamente atendidos:

1. **Itens 1 a 5 100% Concluídos e Auditados:**
   - Item 1: Núcleo Mecânico (Parser, State, Worktree) ✅
   - Item 2: Gate Auditor Integrado ✅
   - Item 3: Perfis e Agent Spawner ✅
   - Item 4: Hooks Reativos e Circuit Breaker ⏳
   - Item 5: CLI e Plano de Voo ⏳
2. **Aprovação Explícita do Usuário com Declaração de Escopo:**
   - Qual plano será usado como cobaia (recomenda-se um micro-plano de 1 frente, ex.: [`docs/planos/skill-gerador-planos-auditoria/`](file:///C:/Users/trcnologia/Desktop/ecossistema-aidd/docs/planos/skill-gerador-planos-auditoria/)).
   - Qual harness/modelo específico será acionado (ex.: `mimo` com `mimo/mimo-v2.5-pro` ou `agy`).
   - Estimativa prévia de consumo de tokens/custo.

---

## 2. Escopo Planejado (Para quando for aprovado)

- Execução real ponta-a-ponta em um repositório git efêmero ou branch descartável.
- Criação de worktree real pelo `worktree_engine`.
- Disparo de um agente real em background através do comando compilado.
- Pre-hook marcando `RUNNING` e post-hook capturando a saída.
- Validação do Quality Gate local no término.
- Merge `--no-ff` automático e purga da worktree (`remove --force` + `branch -D`).
- Exibição de telemetria e custo no `memory.md` consolidado.

---

## 3. Protocolo de Bloqueio

Qualquer tentativa de executar este item sem que o usuário forneça a frase formal de autorização (ex.: `"AUTORIZO EXECUÇÃO REAL COM AGENTE <NOME> NO PLANO <CAMINHO>"`) será rejeitada pelos auditores do ecossistema.

---

## Prompt de Execução (Para quando for Desbloqueado) — PT-BR

> Use este prompt SOMENTE após aprovação explícita e desbloqueio formal.

```
Você vai realizar a validação end-to-end com agente real no monorepo
ecossistema-aidd (raiz em C:\Users\trcnologia\Desktop\ecossistema-aidd).

CONTEXTO JÁ INVESTIGADO:
- Itens 1 a 5 concluídos e auditados com sucesso.
- Motor de orquestração completo em componentes/compartilhado/skills/orca-plan-orchestrator/.
- Pré-requisito: autorização explícita de gasto de tokens fornecida pelo usuário.

DEFINIÇÃO DE PRONTO:
1. Executar a orquestração de uma única frente isolada em um repositório git temporário.
2. Confirmar que o agent_spawner disparou o binário real configurado.
3. Confirmar que os hooks gravaram o início (RUNNING) e capturaram o término.
4. Confirmar que o gate_auditor validou a entrega.
5. Confirmar que o merge e purga da worktree ocorreram com sucesso.
6. Exibir o resumo de telemetria final.

Execute o teste ponta-a-ponta e cite a saída real de cada etapa no relatório final.

CRITÉRIO DE SAÍDA:
- Orquestração completa de 1 frente executada com exit 0.
- Merge confirmado na branch principal do repositório de teste.
- Worktree efêmera purgada ao final.
- git status limpo ao final.

REGRAS DE ESCOPO - NÃO FAÇA:
- Não execute agentes reais sem autorização formal explícita do usuário.
- Não execute testes reais contra o repositório ecossistema-aidd real (usar git temporário).
- Não faça git commit nem git push no ecossistema-aidd.

ENTREGÁVEL: log de execução da frente, relatório de telemetria e saída do merge.
```

## Prompt de Execução — English version

> Use this prompt ONLY after explicit user approval and formal unlocking.

```
You are going to perform the end-to-end validation with a real agent in the
ecossistema-aidd monorepo (root at C:\Users\trcnologia\Desktop\ecossistema-aidd).

ALREADY-INVESTIGATED CONTEXT:
- Items 1 through 5 completed and audited with success.
- Complete orchestration engine in componentes/compartilhado/skills/orca-plan-orchestrator/.
- Prerequisite: explicit token expenditure authorization provided by the user.

DEFINITION OF DONE:
1. Run the orchestration of a single isolated front in a temporary git repository.
2. Confirm that agent_spawner launched the configured real binary.
3. Confirm that hooks recorded the start (RUNNING) and captured completion.
4. Confirm that gate_auditor validated the deliverable.
5. Confirm that worktree merge and purge occurred successfully.
6. Display the final telemetry summary.

Run the end-to-end test and cite the real output of each step in the final report.

EXIT CRITERIA:
- Full orchestration of 1 front completed with exit 0.
- Merge confirmed into the main branch of the test repository.
- Ephemeral worktree purged at completion.
- git status clean at the end.

SCOPE RULES - DO NOT:
- Do not launch real agents without explicit formal user authorization.
- Do not run real tests against the real ecossistema-aidd repository (use temporary git).
- Do not git commit or git push to ecossistema-aidd.

DELIVERABLE: execution log of the front, telemetry summary, and merge output.
```


