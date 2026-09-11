---
name: plan
description: Etapa 2 do fluxo /melhoria -> /plan -> /orchestrate. Transforma um relatorio de analise (ou um pedido direto do usuario) na estrutura de plano em docs/planos/, sempre como rascunho, e para para aprovacao humana.
---

# /plan — Gerador de Planos (Etapa 2 de 3)

Contrato executavel universal do slash command `/plan <nome>`.

## Posicao no Fluxo (leia antes de agir)

O ecossistema tem **um unico fluxo de trabalho de 3 etapas**, e cada etapa
termina com uma **parada obrigatoria** onde quem decide e o usuario:

| Etapa | Comando | Entra | Sai | Parada obrigatoria no fim |
|---|---|---|---|---|
| 1 | `/melhoria <pedido em linguagem natural>` | pedido do usuario, ou um plano existente pra reanalisar | relatorio em `docs/melhorias/` com Nota Atual e evidencia | "quer que eu gere o plano a partir disto?" |
| 2 | **`/plan <nome>`** | o relatorio da etapa 1 (ou o pedido direto) | pasta em `docs/planos/<nome>/` com todos os itens em rascunho | "aprova este plano?" |
| 3 | `/orchestrate <plano>` | plano aprovado | execucao real das frentes | escolha de ambiente + aprovacao do Plano de Voo |

**Nenhuma etapa dispara a seguinte sozinha.** Ao terminar, esta skill
*pergunta* se o usuario quer seguir pro `/orchestrate` e para ali. Encadear
automatico removeria exatamente o ponto de controle humano que o processo
existe pra garantir (Regra de Ouro #7 do `AGENTS.md`).

Se o usuario chegou aqui sem passar pela etapa 1, isso e valido — so confirme
de onde vem a evidencia das notas (ver Passo 2). Sem evidencia real, a nota e
`NAO AUDITADO`, nunca um numero estimado pelo agente.

## Convencao de Nome das Iniciativas (obrigatoria)

Toda iniciativa de plano vive numa pasta nomeada assim:

```
PLAN-<NNNN>_<dd-mm-aaaa>-<nome-curto-3-palavras>
```

Exemplo real: `PLAN-0016_09-09-2026-qualidade-testes-mutacao`.

- **`NNNN` e um identificador global e permanente.** Nao reinicia em cada
  subpasta (`a-fazer/`, `fazendo/`, `feitos/`) e nunca e reaproveitado, mesmo
  quando o plano muda de pasta ou some. Antes disso as tres subpastas tinham,
  cada uma, um "01, 02, 03" diferente — falar de "plano 03" era ambiguo.
- **A data e a de criacao da iniciativa**, nao a de hoje nem a da ultima edicao.
- **O nome curto tem 3 palavras significativas** (artigos e preposicoes fora).
- **Nunca monte esse nome a mao:** `python ecossistema.py plan init <nome>` ja
  gera o numero, a data e o nome curto sozinho. Numerar a mao e como escrever
  seu proprio numero de senha na fila do banco — cedo ou tarde dois planos
  recebem o mesmo.
- O prefixo aparece no caminho fisico; o `INDEX.md` exibe so o titulo limpo.

## Protocolo

O protocolo detalhado desta etapa (passos, flags do CLI, checagem de cercas
markdown, regras de nao-fabricacao de aprovacao) vive em um unico lugar:
**`skills/planos-auditoria-runner/SKILL.md`**. Leia e siga aquele arquivo — ele
e o motor desta etapa. Esta skill e so a porta de entrada do comando `/plan`;
`planos-auditoria-runner` nao tem slash command proprio, pra nunca existirem
dois donos do mesmo comando.

Resumo do que o motor faz, na ordem:

1. Nao inicia sozinha — so sob pedido expresso.
2. **Gate de escopo com o usuario** — nome da iniciativa, objetivo, lista de
   itens, e Nota Atual/Alvo com evidencia real de cada um.
3. Geracao deterministica via `python ecossistema.py plan init ...` (nunca
   escrevendo os arquivos a mao).
4. `python ecossistema.py plan check-fences docs/planos/<nome>/`.
5. **Parada:** mostra os caminhos criados e devolve o controle. So depois de
   aprovacao explicita do usuario roda `python ecossistema.py plan aprovar`.

## Onde a iniciativa nasce vs. onde ela vive

`plan init` sempre cria em `docs/planos/<nome>/` (raiz). Quem move pra
`a-fazer/`, `fazendo/` ou `feitos/` e `python scripts/atualizar_index_planos.py`,
a partir do status real da tabela de progresso. **Nunca mova uma pasta de plano
a mao** — foi assim que um plano com 10 itens ainda em rascunho apareceu em
`feitos/` como se estivesse concluido.

## Quando NAO usar esta skill

- Investigar o codigo e medir uma nota antes de existir plano → `/melhoria`.
- Executar um plano ja aprovado → `/orchestrate`.
- Editar o conteudo tecnico de um item ja criado → edite o `NN-<item>.md`
  direto; esta skill so gera e valida estrutura.

## CLI equivalente

```bash
python ecossistema.py plan init <nome-da-iniciativa> --itens "Item 1" "Item 2"
python ecossistema.py plan check-fences docs/planos/<nome-da-iniciativa>/
python ecossistema.py plan aprovar docs/planos/<nome-da-iniciativa>/
python ecossistema.py plan ler-nota <caminho> [--item <NN>]
python ecossistema.py plan atualizar-nota <caminho> [--item <NN>] --nota-atual <n> --evidencia <caminho>
```
