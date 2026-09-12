# Item — checkpoint-persistencia-result-ops-deploy

> **Escopo:** Adicionar persistência de checkpoint por etapa no pipeline de deploy do aidd-ops, permitindo reexecução incremental apenas de tarefas pendentes.
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. .aidd/ops_deploy_state.json nao aparece em lugar nenhum do codigo.

---

## Contexto já investigado

- Falha em etapas avançadas de deploy (ex: swap) reexecuta etapas anteriores mesmo que o Ansible seja idempotente [OPS-2], consumindo tempo desnecessário.

## Definição de Pronto

1. Persistir o `Result` de cada etapa de bootstrap em `.aidd/ops_deploy_state.json`.
2. No início de cada etapa, verificar se o checkpoint já foi atingido com sucesso antes de redisparar SSH.
3. Adicionar flag `--force-redeploy` para ignorar checkpoints quando desejado.

## Critério de saída

- Re-run de deploy pós-falha executa apenas as etapas pendentes a partir do último checkpoint.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: checkpoint-persistencia-result-ops-deploy.
Siga rigorosamente a Definição de Pronto acima:
1. Persistir o `Result` de cada etapa de bootstrap em `.aidd/ops_deploy_state.json`.
2. No início de cada etapa, verificar se o checkpoint já foi atingido com sucesso antes de redisparar SSH.
3. Adicionar flag `--force-redeploy` para ignorar checkpoints quando desejado.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: checkpoint-persistencia-result-ops-deploy.
Strictly follow the Definition of Done above:
1. Persistir o `Result` de cada etapa de bootstrap em `.aidd/ops_deploy_state.json`.
2. No início de cada etapa, verificar se o checkpoint já foi atingido com sucesso antes de redisparar SSH.
3. Adicionar flag `--force-redeploy` para ignorar checkpoints quando desejado.
Ensure exit code 0 across relevant tests and gates.
```
