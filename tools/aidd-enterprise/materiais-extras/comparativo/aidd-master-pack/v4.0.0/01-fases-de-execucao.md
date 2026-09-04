# O Que Acontece Nos Bastidores Quando Alguém Usa Esta Versão do Projeto

> **Versão documentada:** `v4.0.0` do AIDD Master Pack
> **Para quem é este documento:** pessoas que não programam e querem entender, em linguagem simples, o que a ferramenta realmente faz por trás das telas quando alguém a usa nesta versão específica.

---

## Em uma frase

Esta versão é como um "kit de montagem de sistemas" que, com poucos comandos digitados no computador, cria automaticamente as peças básicas de um programa (um banco de dados, algumas telas, algumas regras simples) — mas, nesta fase específica do projeto, o kit ainda não vem com todas as etiquetas de instrução atualizadas, e uma de suas peças mais chamativas (uma tela de documentação bonita, em 3 colunas) só foi montada à mão em dois exemplos de demonstração, não em todos.

---

## Passo a passo do que acontece, sem jargão técnico

### 1. A pessoa "baixa" a caixa de ferramentas
Isso é feito com um comando chamado `git clone` — é como baixar uma pasta compartilhada de arquivos prontos, que contém scripts (pequenos programas auxiliares), modelos de código prontos e exemplos.

### 2. A pessoa pede para "montar" um novo projeto
Ao digitar um comando como `python scripts/aidd.py init "Minha Loja Online"`, a ferramenta:
- Cria uma pasta nova, organizada, com subpastas para cada tipo de coisa (o "miolo" do sistema, os módulos de negócio, os arquivos de tela, os testes).
- Copia para dentro dessa pasta um conjunto de peças prontas: um sistema simples de banco de dados (para guardar informações), um "quadro de avisos" interno (para que partes diferentes do sistema se avisem quando algo acontece, por exemplo "um pedido foi feito") e uma tela básica de documentação da API (uma espécie de "manual de instruções" de como outros programas podem conversar com este sistema).
- Inicializa um controle de versão (`git init`), que é como começar um "histórico de alterações" do projeto.

**Importante:** essa montagem inicial é bem básica. Ela não inclui, por si só, nenhuma funcionalidade de negócio específica — é só o alicerce vazio.

### 3. A pessoa pede para "adicionar uma funcionalidade" (um módulo)
Com um comando como `python scripts/aidd.py add-module financeiro`, a ferramenta cria automaticamente:
- Uma "gaveta" no banco de dados para guardar itens desse módulo (título, alguns dados extras, se está ativo).
- Três botões de ação básicos: listar os itens, criar um item novo, apagar um item.
- Um pequeno cartão visual na tela, com uma caixa de texto e um botão "Adicionar".
- Um teste automático simples, que confere se criar/listar/apagar continuam funcionando depois de qualquer mudança futura.

Isso é gerado de forma mecânica e repetitiva — é sempre a mesma "receita", trocando apenas o nome do módulo. Não é uma inteligência artificial pensando na regra de negócio específica; é um "carimbo" de código repetido.

### 4. A pessoa pede para "conferir a qualidade" do que foi montado
O comando `python scripts/aidd.py audit` roda três verificações automáticas, uma atrás da outra:
1. **Procura por senhas ou chaves secretas esquecidas no código** — como alguém revisando documentos em busca de números de cartão de crédito escritos à mão por engano. Se encontrar, o processo é bloqueado.
2. **Confere se o código "faz sentido" gramaticalmente** — é como um corretor ortográfico para código: garante que não há erros básicos de digitação que impediriam o programa de sequer começar a rodar.
3. **Uma terceira verificação que, nesta versão específica, apenas diz "está tudo bem" sem de fato checar nada** — é como um selo de aprovação que é carimbado automaticamente, sem inspeção real por trás. Isso é uma limitação real desta versão que vale a pena saber: essa terceira checagem ainda não faz seu trabalho de verdade aqui.

Essas checagens **não** conferem se o sistema "funciona de ponta a ponta" quando ligado — elas só olham o código parado, não o testam em ação.

### 5. A pessoa pede para "rodar os testes"
O comando `python scripts/aidd.py test` executa os testes automáticos criados no passo 3, conferindo se cada módulo continua se comportando como esperado. Existe também uma opção de "teste de carga", que simula várias pessoas usando o sistema ao mesmo tempo por alguns segundos, para ver se ele aguenta.

### 6. A pessoa liga o sistema para usar de verdade
Rodando `python src/server.py`, o computador passa a "servir" o sistema como um site local, acessível pelo navegador em um endereço como `http://localhost:3000`. A partir daí ficam disponíveis:
- A tela principal do sistema (o site em si).
- Uma tela de documentação técnica da API, para desenvolvedores.
- Em apenas dois dos doze exemplos que este pacote traz, uma versão mais bonita e sofisticada dessa tela de documentação, dividida em 3 colunas — só que, em um desses dois exemplos, essa tela mais bonita **na verdade impede o sistema inteiro de ligar**, por causa de um pequeno erro de "encaixe" entre duas peças do código que não foram ajustadas para conversarem corretamente entre si. É como uma peça de Lego de uma caixa mais nova que quase encaixa, mas não perfeitamente, travando o conjunto todo.

### 7. (Opcional) A pessoa pede para "publicar" o sistema em um servidor de verdade
O comando de "deploy" pode empacotar o sistema em um contêiner (uma espécie de caixa padronizada e portátil que roda igual em qualquer computador) e colocá-lo no ar. Nesta versão, isso funciona bem para publicar em um servidor próprio (via Docker); para publicar em um provedor de nuvem específico chamado Vercel, a opção existe no menu de comandos, mas na prática não faz nada ainda.

---

## O que vale destacar para quem decide sobre o projeto

- **A "caixa de ferramentas" em si (os scripts que montam projetos novos) está em um estágio mais simples** do que a funcionalidade mais divulgada desta versão (a tela de documentação bonita em 3 colunas). Essa tela bonita foi construída à mão como demonstração em apenas 2 de 12 exemplos guardados no pacote — ela ainda não foi "ensinada" à ferramenta de montagem automática, então quem pedir um projeto novo hoje, com os comandos desta versão, não a recebe de graça.
- **As checagens automáticas de qualidade existentes são reais, mas cobrem pouco**: elas pegam senhas esquecidas e erros de digitação no código, mas não testam se o sistema realmente liga, não verificam se há proteção de acesso (qualquer pessoa poderia, em tese, chamar as funções do sistema sem precisar de senha, nesta versão de exemplo), e uma das três checagens é apenas decorativa.
- **Não existe, nesta versão, um "documento de plano" gerado automaticamente** que diga em quais etapas o projeto está e o que falta fazer — isso, quando aparece, foi escrito manualmente por quem estava conduzindo o projeto, não pela ferramenta.

Em resumo: esta versão entrega o alicerce funcional (banco de dados, avisos entre partes do sistema, checagens básicas) de forma sólida e repetível, mas a "vitrine" mais impressionante do release (a documentação de API em 3 colunas) ainda é uma peça de demonstração isolada, não uma funcionalidade pronta para todo mundo usar automaticamente.
