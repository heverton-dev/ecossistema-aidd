# Item 4 — remover-hacks-syspath-no-generator

> **Escopo:** Substituir manipulações manuais de sys.path e carregamento dinâmico via importlib.machinery no aidd-generator por um pacote Python estruturado com carregamento lazy tipado.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- 	ools/aidd-generator/scripts/pipeline_completo.py usa sys.path.insert e spec_from_file_location para carregar scripts das fases.
- Dificulta testes unitários das fases, polui o namespace global do Python e impede análise estática de tipos.

## Definição de Pronto

1. Estruturar as 8 fases dentro de um pacote formal importável (ex: idd_generator.phases).
2. Implementar registro de fases via lazy import controlado sem mutação de sys.path.
3. Manter a compatibilidade com o isolamento de micro-ambientes da governança.
4. Executar os testes do generator e comprovar ausência de sys.path.insert.

## Critério de saída

- Zero sys.path.insert em código de produção do generator.
- Testes de pipeline do aidd-generator aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Você vai implementar o Item 4: remover-hacks-syspath-no-generator.
1. Refatore o carregamento das fases em aidd-generator para um pacote Python estruturado (idd_generator/phases/ ou registry lazy).
2. Elimine todos os sys.path.insert e carregamentos dinâmicos frágeis.
3. Assegure que as 8 fases continuem executando com seus contratos de entrada e saída.
4. Rode pytest tools/aidd-generator/tests/ com exit 0.
`

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 4: remover-hacks-syspath-no-generator.
1. Refactor phase loading in aidd-generator into a structured package/registry.
2. Eliminate sys.path.insert and fragile dynamic imports.
3. Validate that all 8 phases execute seamlessly with typed input/output contracts.
4. Run pytest tools/aidd-generator/tests/ with exit 0.
`
