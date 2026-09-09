# Item 7 — gate-g-arquitetura-deliverable

> **Escopo:** Criar Quality Gate estático via AST (gates/G_ARQUITETURA_DELIVERABLE.py) que valida a conformidade com Clean Architecture e DDD nos templates e módulos de software gerados.
> **Status:** [RASCUNHO — Aguardando Aprovação Humana]

---

## Contexto já investigado

- O ecossistema possui gates para integridade e sintaxe, mas nenhum gate estático valida se o código gerado nos módulos respeita as camadas de Clean Architecture.
- Sem um gate automático, violações como SQL em rotas ou services voltam a ocorrer silenciosamente.

## Definição de Pronto

1. Criar gates/G_ARQUITETURA_DELIVERABLE.py usando parsing AST (Zero Token Fallacy).
2. Regras de verificação do gate:
   - Proibir import sqlite3 e chamadas execute( fora da pasta infrastructure/.
   - Proibir domain/ de importar qualquer submódulo de infrastructure/, interfaces/ ou bibliotecas de banco.
   - Proibir 
outes.py de importar repositórios concretos ou executar lógica de cache diretamente.
3. Integrar o gate no .pre-commit-config.yaml e no comando python ecossistema.py audit.
4. Testar o gate contra modulo1 novo (passando) e contra uma fixture violadora (reprovando com exit 1).

## Critério de saída

- Gate G_ARQUITETURA_DELIVERABLE.py funcional com saída binária (exit 0 / exit 1).
- Integrado na auditoria padrão do ecossistema.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

`
Você vai implementar o Item 7: gate-g-arquitetura-deliverable.
1. Crie o gate determinístico gates/G_ARQUITETURA_DELIVERABLE.py com análise AST.
2. Bloqueie:
   - SQL cru/sqlite3 fora de infrastructure/
   - Imports de infraestrutura dentro de domain/
   - Acoplamentos diretos de banco/cache dentro de rotas
3. Adicione o hook no .pre-commit-config.yaml.
4. Valide a execução com python gates/G_ARQUITETURA_DELIVERABLE.py.
`

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

`
You are going to implement Item 7: gate-g-arquitetura-deliverable.
1. Create deterministic AST-based gate gates/G_ARQUITETURA_DELIVERABLE.py.
2. Enforce:
   - Raw SQL/database imports forbidden outside infrastructure/
   - Infrastructure imports forbidden inside domain/
   - Direct database/cache coupling forbidden inside routes/
3. Register hook in .pre-commit-config.yaml.
4. Verify with python gates/G_ARQUITETURA_DELIVERABLE.py.
`
