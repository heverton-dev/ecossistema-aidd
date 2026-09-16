# Item 1 — Preparar terreno e ambiente

> **Escopo:** Entra: clonar o repo e rodar os comandos que checam/instalam dependencias externas e o diagnostico rapido de binarios do sistema. Nao entra: qualquer comando dentro de `tools/*` (isso e item 2 em diante).
> **Status:** [APROVADO — Aguardando Execucao]
> **Nota Atual (0-10):** NAO AUDITADO — evidencia: (nota pendente de medicao real - nao preencher com estimativa)
> **Nota Alvo (0-10):** 9
> **Nota Real (pos-implementacao):** [Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]

---

## Contexto ja investigado

- `python ecossistema.py dependencia verify` ja foi rodado nesta sessao a partir da raiz do monorepo e retornou `[SUCESSO] Todas as dependencias externas declaradas estao instaladas/registradas.` (40 dependencias declaradas) — baseline real, nao suposicao.
- `python ecossistema.py --help` lista todos os comandos de topo (`dependencia`, `orchestrate`, `melhoria`, `plan`, `audit`, `harness`, `preflight-host`, `status`, `help`).
- `python ecossistema.py audit` (sem argumento) roda o Meta-Quality-Gate do monorepo inteiro — ficou mais de 120s rodando nesta sessao, ou seja, e uma operacao pesada e real, nao instantanea. Nao confundir com `forge audit <path>` (item 2), que audita um projeto alvo especifico.

## Definicao de Pronto

1. `git clone https://github.com/heverton-dev/ecossistema-aidd.git` termina com exit 0 e a pasta `ecossistema-aidd/` existe.
2. `python ecossistema.py dependencia verify` roda a partir da raiz e retorna exit 0 com a mensagem `[SUCESSO]`. Se retornar `[FALHA]`, rodar `python ecossistema.py dependencia bootstrap` e repetir o `verify` ate exit 0 real (nunca assumir sucesso sem rodar de novo).
3. `python ecossistema.py preflight-host` roda em menos de 2s e reporta o estado real dos binarios do sistema (Git, Node, Docker, Hadolint, Checkov).

## Criterio de saida

- Os 3 comandos abaixo foram executados de verdade nesta maquina (nao lidos, nao inferidos) e o exit code de cada um foi capturado.
- Nenhum comando rodou com `--no-verify`, `--force` ou qualquer flag que pule validacao.

## Comandos estruturados (ordem real de execucao)

```bash
git clone https://github.com/heverton-dev/ecossistema-aidd.git
cd ecossistema-aidd
python ecossistema.py dependencia verify
# se a linha acima nao terminar com [SUCESSO], rodar e repetir o verify:
python ecossistema.py dependencia bootstrap
python ecossistema.py preflight-host
python ecossistema.py help
```

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 1: Preparar terreno e ambiente.
Rode os comandos da secao "Comandos estruturados" nesta ordem exata, um de cada vez.
Depois de cada comando, capture o exit code real (nao suponha sucesso pelo texto de saida).
Se "dependencia verify" falhar, rode "dependencia bootstrap" e repita o verify ate exit 0 real.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 1: Preparar terreno e ambiente (prepare ground and environment).
Run the commands in "Comandos estruturados" in this exact order, one at a time.
After each command, capture the real exit code (do not assume success from the printed text).
If "dependencia verify" fails, run "dependencia bootstrap" and repeat verify until it exits 0 for real.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
