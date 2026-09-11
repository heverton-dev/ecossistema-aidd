# Item 10 — teste-integracao-helm-aidd-ops

> **Escopo:** Adicionar verificação de deployabilidade real do Helm chart e Docker Compose gerados pelo aidd-ops, substituindo lint puramente textual por validação com dry-run/template real e integração com cluster de teste.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- G_INFRA_COMPOSE e G_HADOLINT validam sintaxe e segurança de compose/dockerfiles, mas o Helm gerado pelo ops não tem teste de integração contra template/dry-run do binário Helm.
- O rótulo 'deployável' precisa de validação técnica comprovada sem fabricar garantias.

## Definição de Pronto

1. Adicionar teste automatizado que executa helm template e helm lint sobre os charts gerados pelo aidd-ops.
2. Configurar teste opcional de integração com cluster de desenvolvimento local (kind ou minikube quando disponível via flag --cluster).
3. Validar que os resources definidos no PLANO-INFRAESTRUTURA.json são corretamente renderizados nos manifests do Kubernetes gerados.
4. Assegurar exit 0 no teste de validação de infraestrutura.

## Critério de saída

- Helm gerado aprovado em helm lint e helm template.
- Rótulo de deployabilidade apoiado em verificação real.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Você vai implementar o Item 10: teste-integracao-helm-aidd-ops.
1. Adicione suite de teste em 	ools/aidd-ops/tests/ que executa validação do Helm chart gerado via helm lint e helm template.
2. Verifique se os resources calculados no sizing real são injetados sem erro nos manifests renderizados.
3. Execute pytest tools/aidd-ops/tests/ e garanta exit 0.
`

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 10: teste-integracao-helm-aidd-ops.
1. Add test suite in 	ools/aidd-ops/tests/ running helm lint and helm template against generated charts.
2. Verify that sizing resources are accurately propagated into rendered manifests.
3. Run pytest tools/aidd-ops/tests/ and ensure exit 0.
`
