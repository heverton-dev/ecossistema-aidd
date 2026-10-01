# Papéis das 8 Ferramentas do Ecossistema AIDD

> Registro documental. Fonte: `AGENTS.md` §3 (Tríade Canônica) e §4 (Context Dispatch), README de cada ferramenta e diff real entre `tools/aidd-master` e `tools/aidd-enterprise` (01/10/2026).

## Ordem de execução

```text
[FORGE -> PLANNER] -> {GENERATOR | FACTORY | BRIDGE} -> [MASTER -> ENTERPRISE -> OPS]
```

Os 3 fluxos têm o mesmo começo e o mesmo fim. Só muda a etapa de construção do meio.

## Papel de cada ferramenta

| # | Etapa | Ferramenta | Papel |
|---|-------|-----------|-------|
| 1 | PREPARAÇÃO DO TERRENO | `aidd-forge` | Prepara o ambiente e fixa as regras do jogo: templates, blindagem do ambiente, governança e economia de tokens |
| 2 | PLANTA BAIXA | `aidd-planner` | Transforma a ideia em plano: recebe a especificação (SDD/BDD) e gera o `PLANNER.json`, que alimenta o fluxo escolhido |
| 3a | CONSTRUÇÃO — do zero | `aidd-generator` | Fluxo 01 (`/pure`). Constrói o app do zero num pipeline de 8 fases com TDD (teste antes do código) |
| 3b | CONSTRUÇÃO — peças prontas | `aidd-factory` | Fluxo 02 (`/open`). Constrói usando motores open-source escolhidos e integrados como fatias |
| 3c | CONSTRUÇÃO — reforma | `aidd-bridge` | Fluxo 03 (`/freedom`). Pega um app feito em low-code (Lovable/v0/Bolt), remove a dependência da plataforma e empacota para VPS própria, mantendo a interface |
| 4 | INTEGRAÇÃO | `aidd-master` | Junta as fatias geradas por generator/factory/bridge num monólito modular |
| 5 | BLINDAGEM | `aidd-enterprise` | Injeta componentes aprovados com selo SHA-256, registro e auditoria |
| 6 | ENTREGA / INFRA PRÓPRIA | `aidd-ops` | Publica na VPS: segredos cifrados (sops+age), monitoramento (Uptime Kuma) e entrega do Quarteto (`/api`, `/webhook`, `/mcp`, `/docs`) |

## Resumo em uma linha cada

- **aidd-forge** = TERRENO: prepara o ambiente e impõe as regras antes de qualquer coisa
- **aidd-planner** = PLANTA: converte a especificação no plano que guia a construção
- **aidd-generator** = OBRA DO ZERO: constrói o app inteiro com TDD em 8 fases
- **aidd-factory** = OBRA COM PEÇAS PRONTAS: monta o app integrando motores open-source
- **aidd-bridge** = REFORMA: tira o app do low-code e o deixa pronto para servidor próprio
- **aidd-master** = INTEGRAÇÃO: junta as fatias num monólito modular
- **aidd-enterprise** = BLINDAGEM: injeta componentes aprovados com selo SHA-256, registro e auditoria
- **aidd-ops** = ENTREGA: coloca no ar na VPS, com segredos protegidos e monitoramento

## Observação

Hoje `aidd-master` e `aidd-enterprise` compartilham 86% dos arquivos (346 de 404 são idênticos). Os papéis acima são o **alvo**. A separação real está em `docs/auditoria/meus-prompts/PROMPT-FRONTEIRAS-E-DEDUP-FERRAMENTAS.txt`.
