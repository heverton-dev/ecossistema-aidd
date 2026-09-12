# Item — preflight-ops-antecipado-ansible-sops-docker

> **Escopo:** Antecipar a verificação de ferramentas de infraestrutura (ansible, sops, docker) no pipeline do aidd-ops para antes do pre-voo SSH e da geração de inventários efêmeros.
> **Status:** [EM EXECUCAO]
> **Auditoria por reproducao real (11-09-2026):** NAO-FEITO. pipeline_ops_deploy.py nao valida ansible-playbook nem sops no inicio.

---

## Contexto já investigado

- Ausência de ansible-playbook só é detectada após estabelecer conexão SSH [BP-5], gerando perda de tempo e resíduos temporários no host.

## Definição de Pronto

1. No início de `pipeline_ops_deploy.py`, validar presença de `ansible-playbook` e `sops`.
2. Abortar imediatamente com mensagem instrutiva em < 1s se faltar algum binário essencial.
3. Evitar criação de arquivos de inventário ou tentativas de rede quando o host não estiver apto.

## Critério de saída

- Falha rápida (fast-fail) determinística em deploys com binários ausentes.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: preflight-ops-antecipado-ansible-sops-docker.
Siga rigorosamente a Definição de Pronto acima:
1. No início de `pipeline_ops_deploy.py`, validar presença de `ansible-playbook` e `sops`.
2. Abortar imediatamente com mensagem instrutiva em < 1s se faltar algum binário essencial.
3. Evitar criação de arquivos de inventário ou tentativas de rede quando o host não estiver apto.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: preflight-ops-antecipado-ansible-sops-docker.
Strictly follow the Definition of Done above:
1. No início de `pipeline_ops_deploy.py`, validar presença de `ansible-playbook` e `sops`.
2. Abortar imediatamente com mensagem instrutiva em < 1s se faltar algum binário essencial.
3. Evitar criação de arquivos de inventário ou tentativas de rede quando o host não estiver apto.
Ensure exit code 0 across relevant tests and gates.
```
