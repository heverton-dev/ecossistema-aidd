# Item 8 — Integracao comprovada multi-ferramenta

> **Escopo:** Entra: implementar e provar UM elo real de composição entre duas ferramentas (ex.: ops→enterprise), onde a saída de uma é de fato consumida pela outra, com evidência verificável. Não entra: implementar orquestração completa das 5 ferramentas — isso fica documentado como trabalho futuro, não fabricado como pronto.
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** NAO AUDITADO
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- Confirmado por fork de auditoria: `teste-integrado-ecossistema-aidd/orca/02_routing_rules.json` mostra `harness_count: 0`, `mode: "unconfigured"` — a orquestração multi-harness nunca rodou nesse projeto. `pipeline_phases/phase_0{0-4}_*` contêm só `AGENTS.md` + `mcp_config.json` por fase, sem artefato de trabalho real.
- Comparando com `teste-isolado-aidd-enterprise`: é o mesmo projeto aidd-enterprise (mesmo `scripts/aidd.py`, `src/core/*`, mesmo `docker-compose.yml` byte-a-byte) com 1 módulo a mais — "integrado" é rótulo, não arquitetura.
- Generator (fase 1) e Ops rodaram de fato nesse projeto e deixaram evidência real (`.aidd/cache/data/insights_phase1.json`, `PLANO-INFRAESTRUTURA.json` com nicho classificado a partir do texto real do projeto), mas nenhum dos dois resultados foi aplicado ao projeto final — o compose final continua sendo o template genérico do enterprise. As saídas coexistem na mesma pasta sem se compor.

## Definicao de Pronto

1. Escolher com o usuário qual elo de composição é o alvo mínimo viável (ex.: o compose final do projeto gerado reflete o sizing real do `PLANO-INFRAESTRUTURA.json` do ops).
2. Rodar o fluxo escolhido do zero e mostrar via diff que a saída da ferramenta B mudou por causa da saída real da ferramenta A (não é coincidência de template).
3. Documentar esse elo como "integração comprovada nº1" no README/AGENTS.md, deixando claro que os demais elos (forge→generator→master etc.) permanecem trabalho futuro não implementado — sem alegar mais do que foi provado.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 8: Integracao comprovada multi-ferramenta.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 8: Integracao comprovada multi-ferramenta.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
