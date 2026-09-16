# Item 2 — Plugar factory bridge

> **Escopo:** Integrar os comandos de `aidd-factory` e `aidd-bridge` no despachante CLI unificado `ecossistema.py` e atualizar a verificação estática no gate `gates/G_ECOSSISTEMA_INTEGRIDADE.py`.
> **Status:** [CONCLUÍDO]
> **Nota Atual (0-10):** 5.0 — evidencia: python ecossistema.py factory e bridge nao estavam documentados no topo nem validados em G_ECOSSISTEMA_INTEGRIDADE.py.
> **Nota Alvo (0-10):** 10.0
> **Nota Real (pos-implementacao):** 10.0 — evidencia: tools/aidd-factory/README.md criado; comandos factory sincronizados em 6 harnesses via components sync; G_ECOSSISTEMA_INTEGRIDADE.py aprovado com 7 ferramentas.

---

## Contexto ja investigado

- As ferramentas `aidd-factory` e `aidd-bridge` existem fisicamente no diretório `tools/`, com testes próprios e documentações `AGENTS.md` / `README.md`.
- No entanto, `ecossistema.py` lista no banner e no parser apenas as 5 ferramentas originais (`forge`, `generate`, `master`, `enterprise`, `aidd-ops`).
- É necessário unificar a experiência do desenvolvedor para que todas as 7 ferramentas sejam acessíveis a partir da raiz.

## Definicao de Pronto

1. Adicionar comandos `factory` e `bridge` ao despachante `ecossistema.py` com suporte a `--help` e delegação para seus respectivos pontos de entrada em `tools/`.
2. Atualizar o gate `gates/G_ECOSSISTEMA_INTEGRIDADE.py` para incluir `aidd-factory` e `aidd-bridge` na matriz oficial de integridade.
3. Executar `python ecossistema.py factory --help` e `python ecossistema.py bridge --help` validando saída correta.
4. Executar `python gates/G_ECOSSISTEMA_INTEGRIDADE.py` com exit code 0.

## Criterio de saida

- Roteamento completo das 7 ferramentas no monorepo.
- Gate de integridade cobrindo as 7 ferramentas.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 2: Plugar factory bridge.
1. Atualize ecossistema.py para rotear os comandos 'factory' e 'bridge' para as ferramentas correspondentes em tools/.
2. Atualize gates/G_ECOSSISTEMA_INTEGRIDADE.py para auditar as 7 ferramentas.
3. Teste ecossistema.py factory --help e ecossistema.py bridge --help.
4. Valide a conformidade executando python gates/G_ECOSSISTEMA_INTEGRIDADE.py.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: Plugar factory bridge.
1. Update ecossistema.py to route 'factory' and 'bridge' commands to tools/aidd-factory and tools/aidd-bridge.
2. Update gates/G_ECOSSISTEMA_INTEGRIDADE.py to cover all 7 tools.
3. Test ecossistema.py factory --help and ecossistema.py bridge --help.
4. Validate compliance by running python gates/G_ECOSSISTEMA_INTEGRIDADE.py.
```
