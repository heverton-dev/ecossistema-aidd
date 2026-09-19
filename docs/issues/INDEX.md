# Índice — `docs/issues/`

> Escrito à mão em 19/09/2026 (primeira leva). Se o formato se mostrar útil, vale um
> script que gere este arquivo a partir do cabeçalho de cada ticket, igual ao que
> `docs/planos/INDEX.md` já faz.
>
> Títulos em PT-BR, corpo dos tickets em inglês telegráfico — ver `README.md`.

Origem: varredura de decisões abertas do projeto em 19/09/2026. As pendências
ligadas a **planos** (saneamento do índice, PLAN-0024, PLAN-0016, PLAN-0027/0028 e a
triagem dos 7 diagnósticos em rascunho) ficaram de fora por decisão do usuário —
serão tratadas em sessão própria.

## Frente de cobrança das leis

Os três tickets abaixo não corrigem um problema específico: corrigem o motivo pelo
qual os problemas passam. A regra que eles instalam é *toda lei precisa de um
portão, e todo portão precisa de um teste que prove que ele reprova*.

| # | Ticket | Papel |
|---|---|---|
| 0011 | [Todo portão precisa provar que morde](11-todo-portao-precisa-provar-que-morde.md) | **O que tem dente.** 8 dos 26 portões não têm teste nenhum |
| 0010 | [Cada lei declara seu portão](10-cada-lei-declara-seu-portao.md) | O inventário. Diz onde falta portão — não cobra sozinho |
| 0012 | [Gate de idioma para a Lei #4](12-gate-de-idioma-lei-4.md) | Um buraco específico, já confirmado: a Lei #4 não tem portão |

## Podem começar hoje (sem bloqueio)

| # | Ticket | Entrega |
|---|---|---|
| 0001 | [Faxina de registros desatualizados](01-faxina-registros-desatualizados.md) | Trava de honestidade religada, Lei #10 corrigida, CircuitBreaker reclassificado |
| 0002 | [Triar os 26 alertas de segredo em testes](02-triar-alertas-segredo-em-testes.md) | Ruído da trava de segredos eliminado, com justificativa individual |
| 0004 | [Zerar 18 violações de arquitetura](04-zerar-violacoes-arquitetura-e-religar-trava.md) | Banco volta para a camada certa; trava religada |
| 0006 | [Trilha de auditoria (X-Trace-Id)](06-trilha-de-auditoria-trace-id.md) | Ou a rastreabilidade LGPD passa a existir, ou a promessa sai do papel |
| 0007 | [SagaOrchestrator: ligar ou remover](07-saga-orchestrator-ligar-ou-remover.md) | Decisão registrada sobre peça sem uso |
| 0008 | [Compressor sandeco: ligar ou remover](08-compressor-sandeco-ligar-ou-remover.md) | Ou economia de tokens real, ou dependência pesada removida |
| 0009 | [Barreira contra agentes paralelos](09-barreira-agentes-paralelos.md) | O portão que hoje é fachada passa a exercitar o mecanismo |

## Dependem de outro ticket

| # | Ticket | Bloqueado por |
|---|---|---|
| 0003 | [Resolver segredos reais e religar trava](03-resolver-segredos-reais-e-religar-trava.md) | 0002 |
| 0005 | [Dividir o AGENTS.md](05-dividir-agents-md.md) | 0001 |

## Sugestão de ordem

1. **0011** primeiro, e junto com **0010**. Os dois andam de par: o inventário diz
   onde falta portão, o teste diz se o portão que existe funciona. Fazer 0010 sozinho
   produz um mapa de extintores que ninguém disparou.
2. **0006** em seguida. É o único com promessa de conformidade legal (LGPD/GDPR) sem
   implementação por trás — os outros são dívida técnica, este é risco de rótulo.
3. **0002 → 0003.** Enquanto a trava de segredos está desligada, nada impede
   automaticamente subir uma senha.
4. **0001** é barato e tira três informações erradas do registro de uma vez.
5. **0009** depois de 0011, porque 0011 define a regra que 0009 vai aplicar.
6. O resto por conveniência.

## Achado transversal desta varredura

O mesmo defeito estrutural apareceu quatro vezes, em lugares sem relação entre si:

| Onde | Forma do defeito |
|---|---|
| Lei #4 (inglês compacto) | Nenhum portão existe |
| Lei #7 (zero agente oculto) | Portão existe, mas confere texto num arquivo, não o mecanismo |
| Módulo 1.5 (trilha de auditoria) | Documentado e vendido como conformidade; sem implementação |
| `G_TESTES_REAIS` | O portão que cobra testes dos outros não tem teste próprio |

Não são quatro bugs. É um só, repetido: **regra escrita sem cobrança executável.**
É isso que os tickets 0010 a 0012 atacam.
