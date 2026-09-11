# Item 8 — atualizar-scaffolders-master-enterprise-cookiecutter

> **Escopo:** Atualizar os geradores de código (dd_module de aidd-master, inject de aidd-enterprise e templates cookiecutter) para materializar fatias verticais já aderentes ao novo molde DDD e Clean Architecture.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- Atualmente, idd-master add-module <nome> gera o padrão antigo de models anêmicos com SQL em services.
- Os templates em 	emplates/ replicam o mesmo anti-padrão.

## Definição de Pronto

1. Atualizar o gerador dd-module para criar a nova estrutura (domain/, pplication/, infrastructure/, interfaces/).
2. Atualizar os templates Cookiecutter e Jinja em master e enterprise para o novo padrão.
3. Adicionar teste de geração que executa dd-module temp_mod e valida a saída com G_ARQUITETURA_DELIVERABLE.py.
4. Limpar artefatos temporários de teste sem deixar resíduos.

## Critério de saída

- Todo novo módulo gerado é aprovado de fábrica pelo G_ARQUITETURA_DELIVERABLE.py.
- Testes do scaffold passando 100%.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Você vai implementar o Item 8: atualizar-scaffolders-master-enterprise-cookiecutter.
1. Atualize o motor de scaffolding dd-module e os templates em 	ools/aidd-master e 	ools/aidd-enterprise.
2. Garanta que todo novo módulo scaffoldado contenha domain/, application/, infrastructure/ e interfaces/.
3. Adicione teste automatizado que gera um módulo temporário e roda G_ARQUITETURA_DELIVERABLE.py sobre ele.
4. Rode pytest tools/aidd-master/tests/ com exit 0.
`

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 8: atualizar-scaffolders-master-enterprise-cookiecutter.
1. Update dd-module scaffolding engine and templates across master and enterprise.
2. Ensure every generated module follows the 4-layer DDD layout (domain, application, infrastructure, interfaces).
3. Add automated test generating a temporary module and verifying it with G_ARQUITETURA_DELIVERABLE.py.
4. Run pytest tools/aidd-master/tests/ with exit 0.
`
