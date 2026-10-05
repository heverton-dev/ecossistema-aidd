---
name: open-code-review
description: Linter de acoplamento e grafo de dependencias de Clean Architecture — detecta violacoes de camada (dominio importando infra, etc).
---

# Open Code Review — Linter de Acoplamento

## Objetivo

Revisar a fatia implementada quanto a acoplamento indevido entre
camadas, usando um grafo de dependencias derivado dos imports reais do
codigo (nao opiniao subjetiva).

## Camadas de Clean Architecture

1. **Dominio** (entidades, regras de negocio puras) — nao importa nada
   das camadas abaixo.
2. **Aplicacao** (casos de uso) — importa Dominio, nunca Infra/UI.
3. **Infraestrutura** (banco, MCPs, HTTP) — implementa interfaces do
   Dominio/Aplicacao.
4. **UI/Apresentacao** — depende de Aplicacao, nunca acessa Infra
   diretamente.

## Verificacoes do Linter

- Construir grafo de imports por arquivo/modulo.
- Sinalizar toda aresta que aponta de uma camada interna para uma
  camada externa (ex: Dominio importando Infraestrutura).
- Sinalizar ciclos de dependencia entre modulos.
- Sinalizar imports concretos onde deveria existir uma interface/porta
  (Dependency Inversion violada).

## Relatorio

- Gerar `review_report.md` listando cada violacao com: arquivo, linha,
  camada de origem, camada de destino, sugestao de correcao.
- Nao corrigir automaticamente — apenas reportar (revisao, nao
  refatoracao).

## Gate de Saida

`exit 0` somente se `review_report.md` existir e nenhuma violacao de
camada (Dominio -> Infra/UI) estiver marcada como critica sem
justificativa documentada.
