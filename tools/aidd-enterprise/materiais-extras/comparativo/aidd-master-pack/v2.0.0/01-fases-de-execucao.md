# O Que Acontece nos Bastidores — Explicação Simples (v2.0.0)

> **Versão documentada:** `v2.0.0` do AIDD Master Pack.
> Este texto não usa jargão técnico. O objetivo é explicar, para quem não é programador, o que essa ferramenta realmente faz quando alguém a utiliza — passo a passo, sem exagerar nem esconder o que ainda não funciona sozinho.

---

## Para que serve, em uma frase

É um conjunto de "moldes" prontos em Python que ajudam a montar mais rápido o esqueleto inicial de um sistema (tipo um pequeno ERP ou uma plataforma web), organizado em "blocos" independentes — mas essa versão específica (v2.0.0) monta as peças; ela não liga tudo sozinha para o sistema já sair funcionando na tela.

---

## Passo 1 — A pessoa "planta" um projeto novo

Alguém roda um comando dizendo o nome do projeto (por exemplo, "Plataforma de Assinaturas e Cursos"). A ferramenta então:

- Cria uma pasta organizada em "gavetas" separadas: uma para o banco de dados, uma para os módulos de negócio, uma para a parte visual (telas), uma para testes.
- Copia arquivos prontos que já sabem conversar com um banco de dados (podendo ser um banco simples salvo em arquivo, ou um banco mais robusto de produção).
- Copia os arquivos que preparam o projeto para rodar dentro de um "contêiner" (uma caixa padronizada que facilita colocar o sistema no ar em um servidor).
- Escreve um documento de instruções (`AGENTS.md`, e cópias dele com outros nomes) explicando as regras do projeto para qualquer assistente de IA que for ajudar a programar depois.
- Escreve um arquivo de "plano" (`PLANO-EXECUCAO-ESTRUTURADO.json`) que funciona como uma ficha-resumo do projeto — mas essa ficha é preenchida uma única vez, no começo, e **não é atualizada automaticamente** conforme o trabalho avança. É mais um "rótulo inicial" do que um painel de progresso ao vivo.

**Importante:** para esse primeiro passo funcionar, a ferramenta precisa encontrar, no computador de quem está usando, uma pasta de "modelos" já instalada previamente — se essa pasta não existir, alguns arquivos simplesmente não são copiados.

---

## Passo 2 — A pessoa pede um "módulo" novo (um pedaço de funcionalidade)

Depois que o projeto existe, a pessoa (ou um assistente de IA usando a ferramenta) pode pedir um novo "módulo" — por exemplo, "cupons de desconto" ou "afiliados". Com um único comando, a ferramenta cria automaticamente, para aquele módulo:

- Uma "gaveta" de banco de dados própria para guardar os itens daquele módulo.
- As regras básicas de "criar item", "listar itens" e "apagar item".
- Um pequeno bloco visual (um cartão na tela) para aquele módulo, já com um campo de texto e um botão "Adicionar" — sem usar emojis, seguindo uma regra de visual mais sério/corporativo da ferramenta.
- Um teste automático que confere se criar, listar e apagar um item realmente funciona.
- Um aviso interno para outras partes do sistema saberem que "um item novo foi criado" ou "um item foi apagado" (como um alto-falante interno que avisa o que aconteceu).

Isso pode ser repetido quantas vezes forem necessárias, um módulo de cada vez, para montar todas as áreas do sistema.

---

## Passo 3 — O elo que falta: ninguém "liga a tomada" sozinho

Aqui está o ponto mais importante para entender o estado real desta versão: depois que os módulos são criados, **ainda falta alguém escrever a peça que liga tudo e coloca o sistema para responder de verdade na internet/rede** (o "servidor" que atende quando alguém acessa o site ou chama a API). Essa peça central não é gerada automaticamente nesta versão — é um trabalho manual extra. Sem ela, os módulos existem como peças prontas em uma prateleira, mas o "motor" que as conecta e as coloca para funcionar ainda precisa ser montado à mão.

Da mesma forma, falta um arquivo que lista "quais programas auxiliares o projeto precisa instalar" — sem ele, o processo de empacotar o sistema em um contêiner para colocar no ar (Passo 5) não completa sozinho.

---

## Passo 4 — As "checagens de segurança e qualidade" automáticas

A ferramenta traz 3 verificações automáticas que podem ser rodadas a qualquer momento:

1. **Checagem de erros de digitação no código** — confere se todo o código Python está escrito corretamente (sem erros de sintaxe). Não confere se a lógica de negócio está certa, só se o código "compila".
2. **Checagem de vazamento de senhas/chaves secretas** — varre todos os arquivos do projeto procurando por padrões que parecem senhas, tokens ou chaves de API esquecidas no código, e também por textos "aleatórios demais" que possam ser segredos escondidos.
3. **Checagem de compatibilidade do ambiente** — nesta versão, essa checagem sempre diz "está tudo certo", mesmo sem checar nada de verdade. É, na prática, apenas um sinal verde automático.

Nenhuma dessas 3 checagens roda automaticamente os testes que foram criados no Passo 2 — se a pessoa quiser ter certeza de que os módulos realmente funcionam, precisa mandar rodar os testes manualmente.

---

## Passo 5 — Testes de estresse e colocação em produção

A ferramenta também prepara um teste de "carga" (simula muitas pessoas acessando o sistema ao mesmo tempo) e os arquivos para colocar o sistema dentro de um contêiner e publicá-lo em um servidor. Porém:

- O teste de carga vem com endereços de exemplo genéricos, que não são automaticamente ajustados para os módulos reais que a pessoa criou — alguém precisa editar esse teste manualmente para ele fazer sentido no projeto específico.
- Colocar o sistema realmente no ar depende de ter resolvido o Passo 3 (o "elo que falta") e o arquivo de programas auxiliares — coisas que esta versão não gera sozinha.

---

## Resumindo em uma imagem mental

Pense nesta versão da ferramenta como uma **fábrica de peças de montar de alto padrão**: ela corta, entrega e etiqueta rapidamente cada peça (banco de dados, regra de negócio, tela, teste, checagem de segredo) — mas a etapa final de encaixar todas as peças em um produto ligado e funcionando ainda depende de mãos humanas (ou de um assistente de IA) para montar o "motor" central e apertar os últimos parafusos.
