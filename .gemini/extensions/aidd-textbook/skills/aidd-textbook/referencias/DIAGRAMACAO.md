# Diagramação: o que existe e o que quebra

Abra este guia quando for montar tabela, diagrama, painel ou ficha técnica. Todas as
regras aqui vieram de defeito observado em página renderizada, não de preferência.

## 1. Blocos visuais disponíveis

O modelo visual expõe cinco construções. Use-as dentro de um bloco marcado como
conteúdo bruto de diagramação:

````markdown
```{=typst}
#painel("Título do painel")[
  Texto do painel. Serve para contexto, decisão histórica ou advertência.
]
```
````

| Construção     | Para que serve                                                      |
| :------------- | :-------------------------------------------------------------------- |
| `#painel(t)[…]` | Caixa de destaque com faixa colorida à esquerda                     |
| `#ficha(…)`    | Tabela de duas colunas: o cartão de identidade de um objeto          |
| `#esteira(…)`  | Sequência horizontal de caixas ligadas por setas                     |
| `#no(t, sub:)` | Caixa escura — representa etapa automática, sem intervenção          |
| `#no-claro(t, sub:)` | Caixa clara — representa etapa que consome modelo de IA         |
| `#chip(t)`     | Etiqueta pequena, para marcar estado dentro de um parágrafo          |

Exemplos prontos:

````markdown
```{=typst}
#ficha(
  ("Papel", "O que este objeto é, em uma linha"),
  ("Entrada", "O que consome"),
  ("Saída", "O que entrega"),
)
```
````

````markdown
```{=typst}
#esteira(
  no("1. COLETA", sub: "automática"),
  no-claro("2. ANÁLISE", sub: "usa modelo de IA"),
  no("3. ENTREGA", sub: "automática", cor: rgb("#334155")),
)
```
````

A distinção escuro/claro deve significar a mesma coisa no livro inteiro. Escolha o
significado na abertura e nunca troque no meio.

## 2. Tabelas: as duas armadilhas

**Armadilha 1 — tabela estreita.** O conversor só faz a tabela ocupar a largura da
página quando a linha de separadores passa de 72 caracteres. Abaixo disso, a tabela
encolhe para o tamanho do conteúdo e fica desalinhada no meio da página.

Errado (a tabela vai sair minúscula):

```markdown
| A | B |
|---|---|
| 1 | 2 |
```

Certo (separadores longos, tabela ocupa a página):

```markdown
| Coluna A                        | Coluna B                                          |
| :------------------------------ | :------------------------------------------------- |
| 1                               | 2                                                 |
```

**Armadilha 2 — coluna estreita demais para o conteúdo.** A largura de cada coluna é
proporcional ao comprimento do separador dela. Se a primeira coluna tem separador curto
e o conteúdo é um nome longo, o texto invade a coluna vizinha.

Regra prática: **o separador de cada coluna deve ser proporcional ao maior conteúdo
dela.** Nome técnico longo pede separador longo.

O comando `check` acusa as duas situações antes de você compilar. Rode-o sempre.

## 3. Nomes técnicos e caminhos de arquivo

Escreva nome de arquivo, comando e identificador entre crases. O modelo visual aplica
fundo claro, impede que o corretor os separe em sílabas e insere pontos de quebra
invisíveis depois de `/`, `.`, `_` e `-`, para que um caminho longo quebre dentro da
célula em vez de vazar por cima da coluna vizinha.

Em **negrito**, a separação em sílabas está desligada — nome próprio de ferramenta não
deve virar "aidd-mas-ter".

## 4. Diagramas: limite de quatro caixas por linha

Uma esteira com mais de quatro caixas deixa cada uma estreita demais, e palavras longas
começam a vazar. Quebre em duas linhas:

````markdown
```{=typst}
#esteira(
  no("1. PRIMEIRA", sub: "..."),
  no("2. SEGUNDA", sub: "..."),
  no("3. TERCEIRA", sub: "..."),
  no("4. QUARTA", sub: "..."),
)
#v(-4pt)
#esteira(
  no("5. QUINTA", sub: "..."),
  no("6. SEXTA", sub: "..."),
)
```
````

Rótulo de caixa: no máximo duas palavras curtas. O detalhe vai no `sub:`.

## 5. Títulos

Um `#` abre capítulo — e sempre começa em página nova, com faixa escura. Use-o para
capítulos e para as folhas de abertura de parte, nunca para subdivisão interna.

`##` é seção, `###` é subseção, `####` é o último nível útil. Abaixo disso, o leitor
perde a hierarquia e o sumário fica ilegível.

Código entre crases dentro de um título de capítulo é convertido para texto claro sobre
a faixa escura automaticamente — pode usar.

## 6. Acentuação

Texto em português mantém todos os acentos. Palavra sem acento é erro de revisão, e o
comando `check` acusa as ocorrências mais comuns. Isso vale também para os rótulos
dentro dos diagramas, que passam despercebidos por estarem dentro de um bloco de código.

## 7. Antes de declarar pronto

```bash
python <skill>/scripts/livro.py check <pasta>     # acusa os defeitos acima
python <skill>/scripts/livro.py build <pasta>
python <skill>/scripts/livro.py preview <pasta>   # gera uma imagem por página
```

Olhe pelo menos quatro páginas: a capa, o sumário, uma com tabela larga e uma com
diagrama. Compilar sem erro significa que o arquivo foi gerado — não que ficou legível.
