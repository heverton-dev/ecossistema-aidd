# Índice — `docs/issues/`

> Títulos em PT-BR, corpo dos tickets em inglês telegráfico — ver `README.md`.
> Escrito à mão. Se o formato se firmar, vale um script que gere este arquivo a partir
> do cabeçalho de cada ticket, igual ao que `docs/planos/INDEX.md` já faz.

## ✅ Fechados

| # | Ticket |
|---|---|
| 0010 | [Cada lei declara seu portão](10-cada-lei-declara-seu-portao.md) |
| 0011 | [Todo portão precisa provar que morde](11-todo-portao-precisa-provar-que-morde.md) |
| 0019 | [Endurecer o cobrador da Lei #13](19-endurecer-cobrador-da-lei-13.md) |

## 🔴 Prioridade — a cobrança está frouxa

| # | Ticket | Por quê |
|---|---|---|
| 0006 | [Trilha de auditoria (X-Trace-Id)](06-trilha-de-auditoria-trace-id.md) | Único caso de promessa de conformidade legal sem implementação |
| 0002 → 0003 | [Segredos em testes](02-triar-alertas-segredo-em-testes.md) → [segredos reais](03-resolver-segredos-reais-e-religar-trava.md) | Trava desligada; nada impede subir senha automaticamente |

## 🟡 Dívida concreta

| # | Ticket |
|---|---|
| 0001 | [Faxina de registros desatualizados](01-faxina-registros-desatualizados.md) |
| 0004 | [Zerar 18 violações de arquitetura](04-zerar-violacoes-arquitetura-e-religar-trava.md) |
| 0007 | [SagaOrchestrator: ligar ou remover](07-saga-orchestrator-ligar-ou-remover.md) |
| 0008 | [Compressor sandeco: ligar ou remover](08-compressor-sandeco-ligar-ou-remover.md) |
| 0009 | [Barreira contra agentes paralelos](09-barreira-agentes-paralelos.md) |
| 0005 | [Dividir o AGENTS.md](05-dividir-agents-md.md) — bloqueado por 0001 |

## 🔵 Portões novos (vindos da taxonomia de ROT)

| # | Ticket | Nota |
|---|---|---|
| 0018 | [Reconciliar as 6 categorias duplicadas](18-reconciliar-taxonomia-rot.md) | **Fazer primeiro.** 6 dos 10 portões propostos já existem; o documento tem 4 erros a corrigir |
| 0014 | [Contract Rot](14-contract-rot-gate.md) | Rotas reais vs. contrato escrito |
| 0015 | [Env Rot](15-env-rot-gate.md) | Variáveis exigidas vs. `.env.example` |
| 0016 | [Skill Rot](16-skill-rot-gate.md) | Teria pego o caso da `sandeco` sozinho |
| 0017 | [Migration Rot](17-migration-rot-gate.md) | Migração que não volta atrás |

## 🟢 Disciplina de saída

| # | Ticket |
|---|---|
| 0012 | [Gate de idioma para a Lei #4](12-gate-de-idioma-lei-4.md) |
| 0013 | [Formato de resposta em todo harness](13-formato-de-resposta-agnostico.md) |

## Ordem sugerida

1. **0019** — todo portão escrito daqui pra frente herda a rigidez dele.
2. **0018** — evita construir 6 portões que já existem.
3. **0006**, depois **0002 → 0003**.
4. **0014 a 0017** — os portões novos, já sob a regra endurecida.
5. **0012 + 0013** — disciplina de saída, juntos.
6. **0001**, **0004**, **0007**, **0008**, **0009**, **0005** por conveniência.

## Achado transversal

O mesmo defeito apareceu cinco vezes, em lugares sem relação entre si:

| Onde | Forma |
|---|---|
| Lei #4 (inglês compacto) | Nenhum portão existia |
| Lei #7 (zero agente oculto) | Portão conferia texto, não mecanismo |
| Módulo 1.5 (trilha de auditoria) | Vendido como conformidade; sem implementação |
| `G_TESTES_REAIS` | Cobrava testes que ele próprio não tinha |
| Lei #13 (prove que morde) | O cobrador procura a frase certa, não roda o teste |

Não são cinco bugs. É um só, repetido: **regra escrita sem cobrança executável** — e
duas vezes seguidas o remédio nasceu com a mesma doença.
