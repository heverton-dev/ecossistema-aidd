# Resumo — fronteiras-ferramentas ciclo-01

> **Status:** diagnóstico e plano prontos (versão 2, com a visão do usuário), **aguardando aprovação**. Nada foi corrigido, movido, apagado ou commitado.

## A visão
- **forge** prepara o terreno inteiro: dependências, configurações, leis e guardas, e um **almoxarifado** com todas as peças. Só passa o bastão depois de provar que está tudo pronto.
- **planner** desenha a planta baixa completa, com cada micro-etapa (ticket) endereçada à ferramenta certa.
- **Construtores e acabamento** pegam as peças no almoxarifado quando precisam. Ninguém guarda cópia.

## Onde estamos hoje
- Os 3 fluxos param na etapa da construção, e cada parada é uma falha de passagem de bastão:
  - fluxo 01: o terreno foi entregue sem IA disponível;
  - fluxo 02: a planta não trouxe a entrada da factory;
  - fluxo 03: o terreno foi entregue sem o primeiro commit.
- A "etiqueta" de cada passagem é escrita pelo orquestrador, e não por quem fez o trabalho: em modo simulação, ela diz "100%" sem nada feito.
- Cada ferramenta guarda as próprias cópias: 249 arquivos repetidos (727 cópias) e 126 cópias de gate.

## Nada do que foi feito certo se perde
1. Uma tag no git guarda o estado de hoje para sempre.
2. Um inventário lista cada função, teste, gate e molde de cada cópia.
3. O que só existe numa cópia é juntado à peça do almoxarifado antes de qualquer remoção.
4. Uma verificação automática precisa dar "zero capacidade perdida", e o número de testes passando não pode cair de 2352.
5. Os 3 fluxos rodam de novo depois de cada passo e não podem piorar.
6. Você confirma cada remoção.

## O plano (23 tickets em 5 blocos, com a sua aprovação no fim de cada bloco)
**Bloco 1** Fundação: gate próprio por ticket, foto E2E automática, inventário, nomes, mapa, fiscal e validador · **Bloco 2** Almoxarifado · **Bloco 3** Cada ferramenta no seu lugar, com E2E depois de cada ticket · **Bloco 4** Remoção das cópias, com você · **Bloco 5** Fiscal bloqueando, foto "depois", READMEs, mapas visuais e livros.

Inventário → nomes padronizados (generator→**aidd-pure**, factory→**aidd-open**, bridge→**aidd-freedom**) → mapa → almoxarifado único → forge com prontidão e planner com tickets → cada ferramenta passa a consumir do almoxarifado, uma por vez → remoção das cópias com prova de zero perda → fiscal bloqueando → foto "depois" → README de cada ferramenta.

## O que preciso de você
- Aprovar `ESPEC-CONTRATOS-E-GATE.md` e `PLANO-EVOLUCAO.md`.
- Decisões D1–D5 já respondidas (D1, D4 e D5 pelo usuário em 01/10/2026; D2 e D3 pela visão).
