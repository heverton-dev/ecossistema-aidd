# Item 4 — Checar portoes de qualidade

> **Escopo:** Entra: confirmar que (a) as ferramentas do monorepo usadas nos itens 1-3 estao saudaveis de verdade, e (b) o projeto gerado em `proj_ctt\sistema-gerado` passa nos proprios testes e sobe de verdade. Nao entra: corrigir bugs encontrados (isso vira um item de correcao separado, fora deste plano de teste).
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** 9
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- Existem DOIS comandos de "audit" diferentes, nao confundir:
  1. `python ecossistema.py audit` (raiz, sem argumento) = Meta-Quality-Gate do MONOREPO inteiro (`ecossistema-aidd`). Testado nesta sessao: e pesado, ultrapassou 120s de execucao real — nao e instantaneo.
  2. `python -m aidd_forge.cli audit <path>` (de dentro de `tools/aidd-forge/`) = audita conformidade de um PROJETO ALVO externo (ja usado no item 2 contra `proj_ctt`).
- `python ecossistema.py status --testes` roda pytest real em cada ferramenta do monorepo e atualiza `PLANO-EXECUCAO-ESTRUTURADO.json` com a contagem medida — e a forma correta de saber se as ferramentas usadas (forge/generator) estao saudaveis antes de confiar no que elas geraram.
- Validacao real anterior (rodada de 04/09) provou que o criterio de "sistema gerado funciona" e: `pytest` real dentro da pasta gerada com testes passando, MAIS subir o servidor gerado (`subprocess`) e bater endpoints reais via `curl` — nunca so ler o codigo gerado por cima.

## Definicao de Pronto

1. `python ecossistema.py status --testes` (raiz) roda ate o fim e mostra contagem real de testes passando/falhando nas ferramentas usadas (forge, generator).
2. Dentro de `proj_ctt\sistema-gerado`, `pytest` real roda com exit 0 (ou o motivo real de falha e documentado, nunca escondido).
3. O servidor gerado sobe de verdade (`subprocess`/comando indicado pelo proprio projeto gerado) e responde a pelo menos um endpoint real via `curl`, confirmando que nao e so codigo estatico sem vida.

## Criterio de saida

- Toda alegacao de "passou" tem exit code real anexado como evidencia (nunca inferido pela leitura do codigo).
- Se algo falhar, o item registra o comando exato, a saida real e o exit code — vira insumo para um plano de correcao separado, nao e "consertado no ato" dentro deste plano de teste.

## Comandos estruturados (ordem real de execucao)

```bash
cd ecossistema-aidd
python ecossistema.py status --testes

cd "C:\Users\trcnologia\Desktop\proj_ctt\sistema-gerado"
pytest 2>&1 | tail -n 30
# subir o servidor gerado conforme instrucao do proprio README/AGENTS.md gerado, ex.:
# uvicorn main:app --port 8000 &
curl -s http://localhost:8000/<endpoint-real-do-projeto-gerado>
```

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 4: Checar portoes de qualidade.
Nao confunda os dois comandos de audit diferentes (monorepo inteiro vs projeto alvo) - use o correto pra cada caso.
Rode "status --testes" na raiz do monorepo primeiro.
Depois entre na pasta do sistema gerado e rode pytest de verdade, capturando exit code real.
Suba o servidor gerado de verdade e bata pelo menos um endpoint real via curl - nunca declarar
"funciona" so por ter lido o codigo.
Se algo falhar, registre comando, saida e exit code exatos - nao conserte aqui, isso vira insumo
pra um plano de correcao separado.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 4: Checar portoes de qualidade (check the quality gates).
Do not confuse the two different audit commands (whole monorepo vs a single target project) - use the right one for each case.
Run "status --testes" at the monorepo root first.
Then go into the generated system's folder and run pytest for real, capturing the real exit code.
Actually start the generated server and hit at least one real endpoint via curl - never claim
"it works" just from reading the code.
If anything fails, record the exact command, output, and exit code - do not fix it here, that
becomes input for a separate remediation plan.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
