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
| 3a | CONSTRUÇÃO — do zero | `aidd-pure` | Fluxo 01 (`/pure`). Constrói o app do zero num pipeline de 8 fases com TDD (teste antes do código) |
| 3b | CONSTRUÇÃO — peças prontas | `aidd-open` | Fluxo 02 (`/open`). Constrói usando motores open-source escolhidos e integrados como fatias |
| 3c | CONSTRUÇÃO — reforma | `aidd-freedom` | Fluxo 03 (`/freedom`). Pega um app feito em low-code (Lovable/v0/Bolt), remove a dependência da plataforma e empacota para VPS própria, mantendo a interface |
| 4 | INTEGRAÇÃO | `aidd-master` | Junta as fatias geradas por generator/factory/bridge num monólito modular |
| 5 | BLINDAGEM | `aidd-enterprise` | Injeta componentes aprovados com selo SHA-256, registro e auditoria |
| 6 | ENTREGA / INFRA PRÓPRIA | `aidd-ops` | Publica na VPS: segredos cifrados (sops+age), monitoramento (Uptime Kuma) e entrega do Quarteto (`/api`, `/webhook`, `/mcp`, `/docs`) |

## Resumo em uma linha cada

- **aidd-forge** = TERRENO: prepara o ambiente e impõe as regras antes de qualquer coisa
- **aidd-planner** = PLANTA: converte a especificação no plano que guia a construção
- **aidd-pure** = OBRA DO ZERO: constrói o app inteiro com TDD em 8 fases
- **aidd-open** = OBRA COM PEÇAS PRONTAS: monta o app integrando motores open-source
- **aidd-freedom** = REFORMA: tira o app do low-code e o deixa pronto para servidor próprio
- **aidd-master** = INTEGRAÇÃO: junta as fatias num monólito modular
- **aidd-enterprise** = BLINDAGEM: injeta componentes aprovados com selo SHA-256, registro e auditoria
- **aidd-ops** = ENTREGA: coloca no ar na VPS, com segredos protegidos e monitoramento

## Observação e Fronteiras Canônicas

Para a especificação formal, delimitação estrita de código, responsabilidades, catálogo e zonas de escrita de cada uma das 8 ferramentas, consulte o documento oficial canônico consolidado no Ciclo 01:
- [FRONTEIRAS-POR-FERRAMENTA.md](FRONTEIRAS-POR-FERRAMENTA.md) (derivado diretamente de `componentes/compartilhado/specs/MAPA-DONOS-FERRAMENTAS.json` e fiscalizado pelo gate `G_FRONTEIRA_FERRAMENTAS.py`).

A dedup histórica entre `aidd-master` e `aidd-enterprise` foi concluída nos Blocos 3 e 4 do Ciclo 01, consolidando as frentes canônicas.
