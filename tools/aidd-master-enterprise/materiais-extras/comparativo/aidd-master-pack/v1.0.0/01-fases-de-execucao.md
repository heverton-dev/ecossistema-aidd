# O Que Acontece Nos Bastidores — Explicação Simples (AIDD Master Pack `v1.0.0`)

> **Versão explicada:** `v1.0.0`, a versão inicial do pacote.
> Este documento não usa jargão técnico. É pensado para quem quer entender, de forma prática, o que essa ferramenta faz quando alguém a utiliza — sem precisar saber programar.

---

## Em uma frase

O AIDD Master Pack v1.0.0 é como um "molde de fábrica" que monta rapidamente o esqueleto de um pequeno sistema (um site com cadastro, um mini-CRM, um catálogo de produtos), pronto para alguém preencher com as regras específicas do negócio depois.

---

## Passo 1 — Pegar a ferramenta

Antes de tudo, alguém precisa copiar a "caixa de ferramentas" (o pacote AIDD) para o computador. Isso é feito uma única vez. Pense nisso como comprar um kit de móveis para montar: você recebe as peças e as instruções, mas ainda não tem o móvel pronto.

**O que NÃO acontece aqui:** não existe um "instalador" com botões e telas — é um processo feito por linha de comando, ou seja, digitando instruções em um terminal.

## Passo 2 — Criar o esqueleto do projeto

Quando alguém pede para "criar um novo projeto" e descreve em poucas palavras o que ele deve ser (por exemplo, "catálogo de produtos com pedido por WhatsApp"), a ferramenta:

- Cria uma pasta nova no computador com o nome do projeto.
- Prepara uma estrutura de pastas organizadas (uma para o "motor" do sistema, uma para os "módulos" de negócio, uma para os testes, uma para a parte visual).
- Copia um conjunto de peças reutilizáveis prontas: um banco de dados simples (para guardar informações), um mecanismo de "avisos internos" (para partes do sistema se comunicarem entre si) e um sistema para enviar informações para fora, como o WhatsApp ou outra ferramenta externa.

Isso é o equivalente a montar a estrutura de uma casa — paredes, encanamento básico, fiação — antes de decidir o que vai em cada cômodo.

## Passo 3 — Criar cada "módulo" do sistema

Um sistema raramente é uma coisa só; ele é feito de partes: "clientes", "produtos", "pedidos", "financeiro". Para cada uma dessas partes, a ferramenta consegue gerar automaticamente:

- Um lugar para guardar os dados daquele assunto (ex.: uma tabela de "produtos").
- As ações básicas: **listar** os itens existentes, **criar** um item novo e **apagar** um item.
- Uma tela simples (um "cartão" visual) onde esses itens podem ser vistos e adicionados.
- Um teste automático que confere se essas 3 ações continuam funcionando corretamente.

**Importante:** o que é gerado automaticamente é só o esqueleto básico dessa parte — criar, listar e apagar. Ações mais específicas do negócio (como "atualizar um pedido", "aplicar um desconto", "calcular imposto") **não vêm prontas**; alguém (uma pessoa ou um assistente de IA) precisa programá-las depois, em cima do esqueleto gerado.

## Passo 4 — Um humano (ou uma IA) completa as regras do negócio

Depois que o esqueleto de cada módulo existe, é nessa etapa que o sistema realmente ganha as regras específicas daquele negócio: como calcular um valor, como validar um cadastro, como conectar um módulo a outro. Essa parte **não é automática** nesta versão — é trabalho de programação de verdade, guiado por um pequeno conjunto de instruções escritas (regras de estilo, regras de segurança) que servem como "manual de boas práticas" para quem estiver codificando.

## Passo 5 — Conferências automáticas de qualidade ("gates")

Antes de considerar o sistema pronto para uso, a ferramenta oferece 3 conferências automáticas e rápidas, chamadas de "gates" (portões):

1. **Conferência de segredos:** varre todo o código procurando senhas, chaves de acesso ou tokens que alguém possa ter deixado escritos por engano.
2. **Conferência de qualidade básica:** verifica se todo o código escrito está gramaticalmente correto (sem erros de digitação que impeçam o programa de rodar) — mas **não** verifica se as regras de negócio estão certas, nem roda os testes automatizados.
3. **Conferência de compatibilidade:** existe na lista, mas, na prática, sempre diz "está tudo certo" sem checar nada de verdade — é uma conferência decorativa nesta versão, ainda não implementada de fato.

**Ponto de honestidade:** essas 3 conferências são úteis, mas bem básicas. Elas não garantem que o sistema funciona corretamente do ponto de vista do negócio, nem que os testes automatizados passam — isso precisa ser verificado separadamente, em outro comando.

## Passo 6 — Testes automatizados (separados da conferência de qualidade)

Existe um comando separado para rodar os testes de verdade — aqueles que simulam um usuário criando, listando e apagando itens, conferindo se tudo se comporta como esperado. Isso é uma etapa distinta da "conferência de qualidade" do Passo 5; as duas não estão amarradas uma à outra.

## Passo 7 — Colocar no ar

Por fim, existe um comando para "publicar" o sistema, com duas opções reais nesta versão:

- **Rodar localmente em um contêiner (Docker):** sobe o sistema na própria máquina, isolado, pronto para testar como se estivesse em produção.
- **Publicar em um servidor próprio (VPS):** a ferramenta apenas avisa quais comandos a pessoa deve rodar manualmente no servidor — ela não faz o envio sozinha.

Uma terceira opção (publicar em serviços de nuvem tipo Vercel) aparece como opção no menu de comandos, mas **não faz nada de verdade** nesta versão — é um espaço reservado para o futuro.

## Passo 8 — Ver o resultado final

Depois de todos esses passos, o que existe é um pequeno site/sistema rodando (tipicamente em `http://localhost:3000` no computador de quem criou), com telas simples, um banco de dados local guardando as informações, e uma documentação técnica básica das "portas de entrada" (rotas) que esse sistema aceita.

---

## Resumo para quem não é técnico

Pense na v1.0.0 como uma **fábrica de protótipos rápidos**: ela monta muito rápido a "casca" de um sistema simples — cadastro, listagem, exclusão de itens, uma telinha básica — para que alguém (pessoa ou IA) preencha o miolo com as regras reais do negócio depois. Ela não entrega, sozinha, um sistema pronto para produção em grande escala; entrega um ponto de partida sólido e organizado, com algumas conferências automáticas simples de segurança e qualidade — mas sem garantias mais profundas de que tudo está correto ou pronto para uso comercial sério.
