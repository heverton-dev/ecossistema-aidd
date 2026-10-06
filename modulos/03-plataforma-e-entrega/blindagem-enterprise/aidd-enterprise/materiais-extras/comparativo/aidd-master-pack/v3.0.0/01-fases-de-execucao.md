# O Que Acontece nos Bastidores — Explicação em Linguagem Simples (v3.0.0)

> **Versão explicada:** `v3.0.0` do AIDD Master Pack.
> **Para quem é este documento:** pessoas que não programam, mas querem entender, em termos práticos, o que acontece "por baixo dos panos" quando alguém usa esta versão do projeto para montar um sistema (um CRM, um financeiro, um catálogo, etc.).

---

## Pense nisto como uma linha de montagem

Imagine uma fábrica que monta pequenos sistemas de software sob encomenda. Nesta versão (v3.0.0), a fábrica tem algumas máquinas automáticas e algumas etapas que ainda precisam de um "operário" (que pode ser uma pessoa ou um assistente de IA trabalhando junto) para terminar o serviço à mão. Veja o passo a passo.

---

## Etapa 1 — Buscar a "caixa de ferramentas"

Antes de qualquer coisa, é preciso baixar o pacote de arquivos do projeto (usando o programa `git`, que é como baixar uma pasta compartilhada) e selecionar especificamente a "edição" v3.0.0 dessa caixa de ferramentas. Isso não instala nada sozinho — apenas coloca os arquivos no computador, prontos para uso.

## Etapa 2 — Pedir um projeto novo (a "planta baixa")

Quando alguém pede "monte uma plataforma de assinaturas" (ou qualquer outra ideia), a ferramenta cria, em segundos, uma pasta nova já organizada com "gavetas" separadas: uma para o banco de dados, uma para as regras de negócio, uma para a parte visual (telas), uma para os testes automáticos e uma para os "fiscais de qualidade" (explicados na Etapa 4). É como montar o esqueleto de uma casa antes de decorar os cômodos — paredes, encanamento e fiação básicos já vêm prontos e copiados de um modelo padrão.

*Detalhe importante:* nesta versão, o endereço da pasta onde o projeto novo é salvo vem fixo no próprio programa (aponta para uma pasta específica do computador do autor original). Ou seja, quem usa esta versão em outro computador precisa saber que talvez tenha que ajustar isso manualmente — não é um campo que se escolhe livremente na hora.

## Etapa 3 — Adicionar "módulos" (pedaços funcionais) sob encomenda

Depois que a "casa" está de pé, é possível pedir, um de cada vez, um "cômodo" novo — por exemplo, "módulo de cupons de desconto" ou "módulo de tickets de suporte". Cada pedido desses gera automaticamente:
- uma tabela de banco de dados para guardar aquele tipo de informação;
- as regras básicas de "listar", "criar" e "apagar" itens;
- as portas de entrada (endpoints) que permitem essas ações pela internet;
- um pedacinho de tela pronta para mostrar aquilo;
- um teste automático simples que confere se criar/listar/apagar funciona.

*Detalhe importante:* a ação de "editar" um item já criado não vem pronta automaticamente — só criar, listar e apagar. Editar precisa ser programado à mão quando necessário. Além disso, depois que o "cômodo" é gerado, alguém ainda precisa "ligar a energia" dele — ou seja, conectar manualmente esse novo pedaço ao restante do sistema (não acontece sozinho).

## Etapa 4 — Passar pelos "fiscais de qualidade" (auditoria automática)

Antes de considerar o trabalho pronto, existem três verificações automáticas e rápidas, sem custo e sem depender de internet:

1. **Fiscal de vazamento de segredos:** varre todo o código procurando senhas, chaves de acesso ou tokens que alguém possa ter esquecido escritos "a céu aberto" no código — o que seria um risco grave de segurança.
2. **Fiscal de qualidade básica:** confere se todo o código Python escrito está com a "gramática" correta (sem erros de sintaxe que impediriam o programa de rodar).
3. **Fiscal de compatibilidade do ambiente:** nesta versão, este fiscal é apenas simbólico — ele sempre aprova, sem checar nada de verdade ainda.

Se o primeiro ou o segundo fiscal encontrar um problema, o processo é interrompido e avisa o que precisa ser corrigido antes de seguir.

*Importante para gestão de expectativas:* esta versão ainda **não tem** fiscais para verificar se as telas seguem o padrão visual da empresa, se os dados sensíveis de cada cliente estão isolados uns dos outros (isso é assunto de versões futuras), nem um fiscal que force a existência de testes automáticos suficientes. São apenas 3 fiscais básicos.

## Etapa 5 — Testar antes de entregar

O sistema pode ser testado de duas formas simples:
- **Teste funcional:** confirma que cada pedacinho (módulo) funciona como esperado (criar, listar, apagar).
- **Teste de carga:** simula várias pessoas usando o sistema ao mesmo tempo, por alguns segundos, para ver se ele aguenta uso simultâneo sem travar.

*Detalhe importante:* o teste de carga desta versão vem com um roteiro genérico (criado para um exemplo de "loja"), então em outros tipos de sistema (um financeiro, por exemplo) ele pode estar testando um endereço que nem existe naquele projeto específico — precisa de ajuste manual para ser realmente útil.

## Etapa 6 — Colocar no ar (deploy)

Existem dois caminhos possíveis: subir o sistema localmente usando um "contêiner" (uma caixa padronizada que empacota tudo que o programa precisa para rodar) ou publicar em um servidor remoto (VPS) através de um script de atualização.

*Detalhe importante e honesto:* nesta versão específica, faltam dois arquivos que o processo de empacotamento em contêiner espera encontrar (a lista de "ingredientes" — bibliotecas necessárias — e o "arquivo principal" de arranque do programa, que tem um nome diferente do que o empacotador procura). Ou seja, tentar colocar em produção usando o caminho automático de contêiner, exatamente como a ferramenta está nesta versão, vai falhar até alguém completar esses dois arquivos manualmente. Rodar o sistema diretamente com Python (sem contêiner) funciona normalmente.

## Etapa 7 — Consultar a "situação" do projeto e a documentação

Existe um comando simples para perguntar "como está esse projeto?", que mostra o nome, a versão e quais módulos estão ativos — desde que exista um arquivo de "resumo do plano" na pasta do projeto. Esse arquivo de resumo, porém, **não é criado automaticamente** por nenhuma ferramenta desta versão — ele só aparece se alguém (pessoa ou assistente de IA) o escrever manualmente ao final do trabalho, como uma espécie de "ata de reunião" registrando o que foi feito.

Em três dos seis projetos de demonstração incluídos nesta versão, existe também uma página de documentação com visual bonito, parecido com um manual de produto (sidebar de navegação, títulos, blocos de código com botão "copiar"), acessível por um endereço específico do sistema. É bem feita e funcional, mas foi construída manualmente para aqueles três exemplos — não existe um botão ou comando que gere essa documentação automaticamente para um projeto novo.

---

## Resumo em uma frase

Nesta versão, o AIDD Master Pack já automatiza bem a criação do "esqueleto" do sistema e de módulos individuais, e já tem 2 verificações automáticas de qualidade que funcionam de verdade (segurança de segredos e sintaxe do código) — mas a ligação final das peças, a criação das telas, a montagem da documentação e a preparação completa para produção ainda dependem de trabalho manual complementar.
