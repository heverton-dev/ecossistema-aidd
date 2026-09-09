# Item 3 — extrair-camada-aplicacao-dos-clis-master-enterprise

> **Escopo:** Decompor o monolito CLI scripts/aidd.py (1.162 linhas) em master e enterprise, separando a camada de entrada (CLI fina com parsing e help) da camada de aplicação (Use Cases de comando).
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- 	ools/aidd-master/scripts/aidd.py e 	ools/aidd-enterprise/scripts/aidd.py contêm 1.162 linhas misturando parsing argparse, I/O de disco, lógica de scaffolding e execução de subprocessos.
- Violação direta de Clean Architecture (Interface Adapters misturados com Application Use Cases).

## Definição de Pronto

1. Extrair comandos de negócio para classes/funções de Use Case em pplication/commands/ (ex: AddModuleCommand, InjectComponentCommand, InitProjectCommand).
2. Reduzir scripts/aidd.py para um adapter fino (apenas parsing de argumentos e delegação aos Use Cases).
3. Utilizar o padrão Result para retornos de erros e sucessos.
4. Validar que nenhuma flag ou comportamento existente de CLI foi quebrado via G_CLI_HELP_CONSISTENCIA.py.

## Critério de saída

- scripts/aidd.py menor que 300 linhas em master e enterprise.
- Gate G_CLI_HELP_CONSISTENCIA.py com exit 0.
- Testes de CLI e integração de master/enterprise aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Você vai implementar o Item 3: extrair-camada-aplicacao-dos-clis-master-enterprise.
1. Crie a estrutura pplication/commands/ em aidd-master e aidd-enterprise.
2. Migre a lógica de execução de cada comando de scripts/aidd.py para seu respectivo Use Case.
3. Reduza scripts/aidd.py para uma casca fina de parsing argparse (<= 300 linhas).
4. Verifique:
   - python gates/G_CLI_HELP_CONSISTENCIA.py
   - pytest tools/aidd-master/tests/
   - pytest tools/aidd-enterprise/tests/
Garanta exit 0.
`

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 3: extrair-camada-aplicacao-dos-clis-master-enterprise.
1. Create pplication/commands/ in aidd-master and aidd-enterprise.
2. Extract business commands from monolithic scripts/aidd.py into distinct Use Cases.
3. Keep scripts/aidd.py as a thin CLI adapter (<= 300 lines).
4. Run:
   - python gates/G_CLI_HELP_CONSISTENCIA.py
   - pytest tools/aidd-master/tests/
   - pytest tools/aidd-enterprise/tests/
Ensure exit 0.
`
