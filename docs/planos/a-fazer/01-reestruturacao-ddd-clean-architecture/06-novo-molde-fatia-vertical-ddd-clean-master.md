# Item 6 — novo-molde-fatia-vertical-ddd-clean-master

> **Escopo:** Redesenhar a fatia canônica modulo1 em aidd-master sob os conceitos estritos de Clean Architecture e DDD (Domain com Entities/Value Objects/Events/Repositories, Application com Use Cases, Infrastructure com SQLiteRepository, Interfaces com rotas finas).
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- src/modules/modulo1 atual usa modelo anêmico (DDL cru em models.py), SQL concatenado direto dentro de services.py e rotas manipulando cache de read-model.
- Violação direta do DDD tático e da Dependency Rule de Clean Architecture.

## Definição de Pronto

1. Refatorar src/modules/modulo1/ na estrutura canônica:
   - domain/entities.py, alue_objects.py, events.py, 
epositories.py (Protocol puro).
   - pplication/use_cases.py, dtos.py (orquestração sem SQL nem HTTP).
   - infrastructure/sqlite_repository.py, schema.py (SQL isolado exclusivamente aqui).
   - interfaces/routes.py (apenas mapeamento HTTP -> Use Case -> DTO).
2. Preservar o Outbox transacional e CQRS como adapters de infraestrutura disparados por Domain Events.
3. Atualizar e expandir a suíte de testes unitários e de integração de modulo1.

## Critério de saída

- Zero SQL fora de infrastructure/.
- Zero dependência externa ou de banco dentro de domain/.
- Testes de modulo1 passando 100% com exit 0.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Você vai implementar o Item 6: novo-molde-fatia-vertical-ddd-clean-master.
1. Redesenhe a fatia canônica 	ools/aidd-master/src/modules/modulo1/ conforme o blueprint de Clean Architecture & DDD:
   - domain/ (entities ricas com invariantes, value objects imutáveis, domain events, interface de repositório)
   - application/ (use cases e DTOs tipados)
   - infrastructure/ (sqlite_repository com SQL isolado, schema DDL, outbox adapter)
   - interfaces/ (routes finas)
2. Garanta que domain não importe nada de infraestrutura ou sqlite.
3. Execute pytest tools/aidd-master/tests/ e comprove exit 0.
`

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 6: novo-molde-fatia-vertical-ddd-clean-master.
1. Redesign canonical vertical slice 	ools/aidd-master/src/modules/modulo1/ following Clean Architecture & DDD blueprint:
   - domain/ (rich entities, immutable value objects, domain events, repository Protocol)
   - application/ (use cases and typed DTOs)
   - infrastructure/ (sqlite_repository with all raw SQL, DDL schema, outbox adapter)
   - interfaces/ (thin routes adapter)
2. Ensure domain package has zero dependencies on infrastructure or database.
3. Run pytest tools/aidd-master/tests/ and verify exit 0.
`
