# Estrutura canônica de um livro-texto

Abra este guia quando for definir o índice da obra ou escrever qualquer capítulo.

## 1. A matriz: três níveis, eixos fixos

A obra desce do geral para o particular em três níveis, e em cada nível faz **sempre as
mesmas perguntas**. É isso que permite ao leitor comparar dois objetos lendo a mesma
seção de cada capítulo, em vez de reler o livro inteiro.

| Nível     | O que descreve                                              | Parte do livro |
| :-------- | :----------------------------------------------------------- | :------------- |
| **Macro** | O todo como organismo único: propósito, leis, topologia      | Parte I        |
| **Meso**  | Os processos: as esteiras que levam da intenção ao resultado | Parte II       |
| **Micro** | As peças: cada componente, um capítulo                       | Parte III      |
| Transversal | O que atravessa todos os níveis (padrões, qualidade)       | Parte IV       |
| Apêndices | Referência de consulta, glossário, estado honesto            | Apêndices      |

Os eixos fixos — as perguntas repetidas em todo nível — são três. Adapte os nomes ao
domínio da obra, mas mantenha a repetição:

1. **Como foi pensado e construído** (a intenção e a engenharia por trás).
2. **Como está hoje** (a arquitetura real, não a desejada).
3. **O eixo próprio do domínio** (custo, desempenho, segurança, economia — escolha o
   que mais importa naquele sistema e mantenha-o em todos os níveis).

## 2. O gabarito de cada capítulo da Parte III

Todo capítulo de peça segue oito seções, na mesma ordem:

```
X.1  O que é
X.2  Papel dentro do processo (nível meso)
X.3  Papel dentro do todo (nível macro)
X.4  Como foi pensada, está estruturada e configurada
X.5  Como funciona individualmente        ─┐
X.6  Como funciona dentro do processo      ├─ os sete itens abaixo, em cada uma
X.7  Como funciona dentro do todo         ─┘
X.8  Rastreabilidade
```

As seções X.5, X.6 e X.7 respondem **sempre aos mesmos sete itens**:

| Item | Pergunta                                                                  |
| ---: | :------------------------------------------------------------------------- |
| 1    | Passo a passo de execução — o que acontece, em ordem                      |
| 2    | Verificações de qualidade — o que bloqueia, e com qual critério           |
| 3    | Habilidades — o que é acionado nessa camada                               |
| 4    | Automação — quais scripts fazem o trabalho sem intervenção                |
| 5    | Ferramentas acessadas — programas, serviços e dados externos              |
| 6    | Disparos automáticos e regras — o que roda sozinho e quais normas valem   |
| 7    | Entrega — o que entrega, como entrega e para quem entrega                 |

Abrir o capítulo com uma **ficha técnica** (`#ficha(...)`) economiza páginas: papel,
posição no processo, forma de acionamento, entrada, saída, natureza.

## 3. As quatro seções obrigatórias da obra

**Como ler este livro** (abertura). A quem se destina, a matriz da obra, as convenções
visuais e o que a obra deliberadamente não é.

**Rastreabilidade** (fim de cada capítulo). Os arquivos ou fontes que sustentam as
afirmações daquele capítulo. É o que separa um livro auditável de um texto de opinião.
Quem lê deve conseguir conferir sozinho.

**Glossário** (apêndice). Todo termo do domínio definido em uma ou duas frases. Se o
termo apareceu no corpo sem explicação, ele precisa estar aqui.

**Estado honesto** (apêndice final). Tabela consolidada do que está incompleto, do que
está falhando e do que aguarda decisão humana — com data, motivo e onde isso está
registrado. Um livro que só mostra o que funciona é folheto de vendas, e a perda de
confiança contamina o resto do texto.

## 4. Como escrever cada capítulo

**Evidência primeiro, prosa depois.** Leia o material real antes de escrever. Números
vêm de medição, nunca de estimativa; quando for estimativa, diga que é.

**Uma afirmação, uma fonte.** Se você não consegue apontar onde aquilo está, ou a
afirmação sai, ou entra marcada como hipótese.

**Explique o porquê, não só o quê.** A decisão técnica interessante é a que tem motivo
documentado — especialmente quando nasceu de um problema real. Registre o problema.

**Contradição é conteúdo.** Quando a documentação diz uma coisa e o código faz outra,
o livro registra as duas e diz qual vale.

**Comprimento segue a complexidade.** Capítulo de peça simples pode ter três páginas;
não infle para igualar ao vizinho.

## 5. Ordem de escrita recomendada

1. Levantar a evidência e montar o índice (nomes dos capítulos e o que cada um cobre).
2. Escrever a Parte III (as peças) — é onde está a evidência mais concreta.
3. Escrever a Parte II (os processos) — já sabendo como as peças funcionam.
4. Escrever a Parte I (o todo) — que sintetiza o que as duas anteriores mostraram.
5. Escrever a Parte IV e os apêndices — que consolidam o que se repetiu.
6. Escrever a abertura por último: só aí você sabe o que o livro realmente ficou sendo.

Escrever o macro primeiro leva a prometer no início o que o micro depois desmente.
