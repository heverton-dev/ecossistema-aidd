# Item 3 — Gerar sistema a partir da ideia

> **Escopo:** Entra: rodar o pipeline de 8 fases do `aidd-generator` usando o relatorio de frotas/roteirizacao/CTT como a ideia de entrada, com o agente ativo (esta sessao) respondendo o protocolo delegado. Nao entra: os portoes de qualidade pos-geracao (item 4) e divisao entre multiplos agentes (item 5, so se este item mostrar necessidade real).
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** 9
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- `python ecossistema.py generate --help` (rodado da raiz) confirma a assinatura real: `generate IDEIA --pasta PASTA [--interativo] [--implementar-codigo] [--resume] [--orquestrador legado|prefect]`. `--implementar-codigo` liga a Fase 8 (codigo funcional real, com testes).
- **Protocolo Delegado (ja validado em rodada anterior real, nao suposicao):** as Fases 2, 3 e 8 nao usam nenhuma chave de API. Elas escrevem um pedido em `tools/aidd-generator/scripts/.aidd/cache/_llm_request_{id}.json` e esperam uma resposta em `_llm_response_{id}.json` no mesmo diretorio, com timeout de 30-60s. Isso e o design real do produto ("Zero API Key" quando um agente de IA como esta sessao esta ativo) — nao e gambiarra.
- A Fase 3 dispara 5 pedidos concorrentes (`especialista_tokens`, `arquiteto_ferramentas`, `arquiteto_camadas`, `engenheiro_scripts`, `especialista_gates`). A Fase 8 e sequencial (schema -> cada script -> teste de integracao) e todo pedido de Fase 8 traz `"fase": "phase_08"` — para saber qual script esta sendo pedido, ler o campo `"prompt"` procurando o texto `"SCRIPT: {nome}"`.
- **Tecnica que ja funcionou numa rodada real anterior:** rodar o pipeline em background (`&`) e, em paralelo, um script "watcher" em loop `while` monitorando a pasta de cache, respondendo cada pedido com conteudo genuino assim que ele aparece — nunca por chamadas de ferramenta sequenciais indo e voltando (o vai-e-vem estoura o timeout de 30s da Fase 2). Resultado provado numa rodada anterior com outra ideia: pipeline completo, auto-critica final 91-100, servidor real respondendo aos 4 verbos REST via curl.
- Esta rodada e mais pesada que uma checagem rapida: pode levar bastante tempo real (varios ciclos de pedido/resposta). Antes de disparar, confirmar com o usuario se roda agora ou em sessao dedicada.

## Definicao de Pronto

1. A ideia de entrada usada e extraida de verdade do conteudo de `proj_ctt\relatorio_frotas_roteirizacao_ctt.md` (nao uma frase generica inventada pelo agente).
2. `python ecossistema.py generate "<ideia>" --pasta "C:\Users\trcnologia\Desktop\proj_ctt\sistema-gerado" --implementar-codigo` roda ate o fim (Fases 1-8) com exit 0, ou para de forma limpa e diagnosticavel numa fase especifica (gate bloqueando com motivo real).
3. Cada pedido do protocolo delegado (`_llm_request_*.json`) foi respondido com conteudo genuino, gerado de verdade pelo agente que le o pedido (nunca uma resposta fixa/copiada entre pedidos diferentes).
4. O resultado final tem `PLANO-EXECUCAO-ESTRUTURADO.json` com status COMPLETO nas 8 fases, dentro da pasta de saida.

## Criterio de saida

- Pasta `sistema-gerado/` criada com codigo real (nao stub, nao `pass`).
- Nenhuma tabela ou nome hardcoded de projeto-exemplo anterior vazou pro projeto novo (achado ja corrigido em rodada anterior — confirmar que nao regrediu).
- Testes reais existem e sao executaveis dentro da pasta gerada.

## Comandos estruturados (ordem real de execucao)

```bash
cd ecossistema-aidd
python ecossistema.py generate "Sistema de gestao de frotas, roteirizacao inteligente (VRP) e integracao com pick-up/tracking dos CTT Portugal, com painel de KPIs de custo por km e SLA de entrega" \
  --pasta "C:\Users\trcnologia\Desktop\proj_ctt\sistema-gerado" \
  --implementar-codigo &
# em paralelo, um watcher (script Python) monitora:
#   tools/aidd-generator/scripts/.aidd/cache/_llm_request_*.json
# e responde escrevendo:
#   tools/aidd-generator/scripts/.aidd/cache/_llm_response_{mesmo_id}.json
# com conteudo real gerado pelo agente que le cada pedido (campo "prompt").
```

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 3: Gerar sistema a partir da ideia.
Extraia a ideia de entrada de verdade do relatorio real em proj_ctt\relatorio_frotas_roteirizacao_ctt.md.
Rode o "generate" em background e, ao mesmo tempo, monitore a pasta
tools/aidd-generator/scripts/.aidd/cache/ (nao ".aidd/cache/" direto - tem "scripts/" no meio).
Cada arquivo "_llm_request_{id}.json" que aparecer, leia o campo "prompt" e responda de verdade
escrevendo "_llm_response_{id}.json" com conteudo genuino (nunca copiar a mesma resposta pra pedidos diferentes).
Isso NAO e simular uma API - e voce, agente ativo, respondendo o protocolo delegado real do produto.
Confirme ao final que PLANO-EXECUCAO-ESTRUTURADO.json mostra as 8 fases como COMPLETO.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 3: Gerar sistema a partir da ideia (generate the system from the idea).
Extract the input idea for real from the actual report at proj_ctt\relatorio_frotas_roteirizacao_ctt.md.
Run "generate" in the background and, at the same time, watch the folder
tools/aidd-generator/scripts/.aidd/cache/ (note the "scripts/" in the middle of the path).
For every "_llm_request_{id}.json" that appears, read its "prompt" field and answer for real by
writing "_llm_response_{id}.json" with genuine content (never copy the same answer across requests).
This is NOT faking an API - you, the active agent, are genuinely fulfilling the product's real delegated protocol.
At the end, confirm PLANO-EXECUCAO-ESTRUTURADO.json shows all 8 phases as COMPLETE.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
