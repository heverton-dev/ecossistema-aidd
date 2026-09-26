# Atualizar um livro-texto existente

Abra este guia quando a obra já existe. Atualizar é cirurgia, não reescrita.

## 1. Primeiro, situe-se

```bash
python <skill>/scripts/livro.py status <pasta>
```

A saída diz quantas partes existem, quantas palavras, se o PDF está em dia com o texto
e quantas revisões já aconteceram. O manifesto (`livro.json`) guarda o histórico: data,
impressão digital do texto, palavras e a nota de cada revisão.

Três respostas possíveis:

| Resultado          | O que significa                                    | O que fazer                        |
| :----------------- | :--------------------------------------------------- | :--------------------------------- |
| `PDF em dia`       | Ninguém mexeu no texto desde a última compilação    | Siga para a seção 2                |
| `DESATUALIZADO`    | Alguém editou o texto e não recompilou              | Entenda o que mudou antes de mexer |
| `PENDENTE`         | Nunca foi compilado                                 | Trate como obra nova               |

Se o resultado for `DESATUALIZADO`, **não recompile por reflexo.** Veja primeiro o que
foi editado: pode ser trabalho de outra pessoa pela metade.

## 2. Classifique a mudança antes de tocar no texto

| Tipo de mudança                                  | Alcance                                                  |
| :----------------------------------------------- | :--------------------------------------------------------- |
| Um fato mudou (número, versão, estado, caminho)  | As frases que citam aquele fato — em todas as partes       |
| Uma peça nova apareceu                           | Um capítulo novo + a tabela de inventário + o glossário    |
| Uma peça saiu                                    | O capítulo sai + as menções a ela nos outros capítulos     |
| Um processo mudou de forma                       | O capítulo do processo + os diagramas afetados             |
| Algo pendente foi resolvido                      | O apêndice de estado honesto + o capítulo correspondente   |
| A obra ganhou um nível ou eixo novo              | Estrutural: converse com quem pediu antes de reorganizar   |

A última linha é a regra de segurança: **mudança estrutural não se faz por conta
própria.** Reorganizar partes invalida referências cruzadas, números de capítulo e o
índice — avise antes.

## 3. Ache tudo que fala do fato antigo

O maior risco de uma atualização não é errar o texto novo: é **deixar o texto velho
vivo em outro capítulo**. Um livro que diz duas coisas diferentes sobre o mesmo assunto
perde a autoridade inteira.

```bash
grep -rn "termo antigo" <pasta>/partes/     # todas as ocorrências, em todas as partes
```

Confira também as menções indiretas: tabela de inventário, glossário, apêndice de
arquivos-chave, apêndice de estado honesto e os rótulos dentro dos diagramas.

## 4. Edite só o que precisa

Altere as frases afetadas, não o arquivo inteiro. Reescrever uma parte inteira para
trocar um número gasta muito e costuma introduzir defeito onde não havia.

Ao acrescentar capítulo novo:

```bash
python <skill>/scripts/livro.py add-parte <pasta> --nome 07-nova --titulo "Capítulo 7 — ..."
```

Para inserir no meio, use `--depois-de <nome-da-parte-anterior>`; a ordem no manifesto é
a ordem do livro.

## 5. Atualize a evidência, não só a prosa

Quando o fato muda, a seção *Rastreabilidade* daquele capítulo muda junto: arquivo que
deixou de existir sai, arquivo novo entra. Livro que aponta para fonte inexistente é
pior que livro sem fonte, porque promete auditoria e entrega engano.

```bash
python <skill>/scripts/livro.py check <pasta> --raiz-evidencia <raiz-do-projeto>
```

Esse comando confere se cada arquivo citado existe de verdade.

## 6. Recompile e registre

```bash
python <skill>/scripts/livro.py update <pasta> --nota "o que mudou nesta revisão"
```

O `update` compara a impressão digital do texto, roda a auditoria, recompila **só se
algo mudou** e grava a revisão no manifesto. A nota não é burocracia: é o que permite,
meses depois, saber por que o capítulo 12 mudou.

Se a auditoria reprovar, corrija os achados. Existe uma saída de emergência
(`--pular-check`), mas usá-la significa publicar um livro com defeito conhecido — só
com decisão explícita de quem pediu a obra.

## 7. Confira o resultado

```bash
python <skill>/scripts/livro.py preview <pasta>
```

Olhe as páginas que você mudou e as duas vizinhas — o texto novo empurra o anterior e
pode ter quebrado uma tabela ou deixado um título sozinho no fim da página.

## 8. O que nunca fazer numa atualização

- Rodar `init` sobre uma obra existente: apaga o manifesto e o histórico de revisões.
- Editar o arquivo consolidado (`<nome-base>.md`): ele é gerado, e some na próxima
  compilação. O conteúdo vive em `partes/`.
- Apagar o apêndice de estado honesto porque "agora está tudo funcionando": atualize as
  linhas, registrando o que foi resolvido e quando.
- Trocar o título da obra ou o nome-base sem avisar: muda o nome do arquivo entregue e
  quebra todo link externo que apontava para ele.
