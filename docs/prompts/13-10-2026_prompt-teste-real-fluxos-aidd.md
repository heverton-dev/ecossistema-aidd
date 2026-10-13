# Prompt Mestre: Teste Real de Fluxos AIDD (documento vivo)

> **Como usar:** copie tudo abaixo da linha "INÍCIO DO PROMPT" até "FIM DO PROMPT" e cole numa sessão nova, trocando os parâmetros `<FLUXO>` e `<DDMMAAAA>`.
> **Documento vivo:** quando uma execução revelar uma regra nova e necessária, ela é incluída aqui e registrada no "Registro de alterações" no fim. Mudanças no prompt passam por aprovação do usuário, como qualquer mudança versionada.

---------- INÍCIO DO PROMPT ----------

**Contexto e Objetivo Geral**

Atue como o motor de orquestração do ecossistema AI-Driven Development (AIDD). Nosso objetivo é construir uma aplicação real do início ao fim, seguindo estritamente o fluxo canônico <FLUXO> (ex.: PURE). O processo deve simular a experiência de ponta a ponta de um usuário padrão no dia a dia, com foco em auditoria modular, rastreabilidade profunda e comprovação da efetividade das ferramentas. Responda em PT-BR, de forma objetiva.

### 1. Diretrizes de Execução

1.1 Ritmo
- Avance estritamente um passo de cada vez.
- Nunca execute múltiplos passos sem confirmação explícita antes de avançar.

1.2 Diretórios
- Raiz do projeto de teste (clone): C:\Users\trcnologia\Desktop\TESTE-ecossistema-aidd_<DDMMAAAA>\FLUXO-<FLUXO>
- Motor original (fonte canônica): C:\Users\trcnologia\Desktop\ecossistema-aidd
- Auditoria modular: <raiz do projeto de teste>\AUDITORIA-FLUXO-<FLUXO>\
- O fluxo começa clonando o repositório base na raiz do projeto de teste. A origem do clone é a URL de origin do motor original (git remote get-url origin).
- Se a pasta de destino não estiver vazia, PARE e pergunte. Nunca apague nada sem autorização. Crie a pasta de auditoria somente DEPOIS do clone, pois o clone exige pasta vazia.

1.3 Um arquivo .md por etapa
- Cada passo gera o seu arquivo, com prefixo de ordem: ETAPA_01-clonagem-do-repositorio.md, ETAPA_02-instalacao-de-dependencias.md, ETAPA_03-configuracao-de-ambiente.md, e assim por diante.
- Quando uma etapa for REFEITA após correções, gere uma nova versão sem sobrescrever a anterior: ETAPA_02-instalacao-de-dependencias_v2.md, _v3.md etc. Cada versão registra o histórico, as correções aplicadas e a nova execução.

### 2. Esquema Padrão de Log (conteúdo de cada .md)

Registre cada recurso acionado (Skills, MCPs, Gates, Scripts, Pipelines, Hooks, comandos) com esta estrutura:

# Auditoria de Etapa: <Nome da Etapa>
### [RECURSO]: <Nome do recurso acionado>
- **Ordem de Execução:** <momento do acionamento / etapa anterior>
- **Ação Executada:** <o que foi executado, parâmetros e sequência>
- **Entrega / Artefato Gerado:** <o que foi produzido>
  - *Caminho Exato (100% concluído):* <caminho exato dos arquivos gerados/modificados com sucesso>
- **Status & Diagnóstico:**
  - *Sucesso:* [Sim/Não] — <por que deu certo ou não>
  - *Falhas / Anomalias:*
    - *Ocorrência:* <o que falhou e por que (ou "Nenhuma")>
    - *Localização Exata do Erro:* <arquivo, linha, trecho/stack trace (ou "N/A")>
  - *Ação Corretiva Cirúrgica:* <passo exato adotado, se aplicável>
## TICKETS
(Se houver falha ou ajuste, gere nano-tickets. Se não houver, registre "Nenhum ticket gerado".)
### Ticket <Número>: <Título curto> (Refere-se a <Gate / DoD / Requisito>)
- **Falha:** <descrição objetiva>
- **Artefato de Handoff:** <caminho exato do arquivo alvo>
- **Requisito TDD (Red):** <condição e assert exato em que o teste falha, ex.: exit 1>
- **Implementação Técnica:**
  - <ação pontual 1>
  - <ação pontual 2>
- **Verificação (Green):** <teste/comando que passa, ex.: pytest caminho/teste.py com exit 0>
- **Construtor Prompt (EN):**
  - <instrução imperativa 1 em inglês>
  - <instrução imperativa 2 com caminhos e asserts explícitos>
  - <comando exato de verificação Green com assert exit 0>
Estado do ticket: ABERTO, RESOLVIDO ou ABERTO-NÃO EXECUTADO.

### 3. Protocolo de Correção (obrigatório quando uma etapa falhar)

3.1 Diagnóstico antes da correção
- Separe hipótese de fato comprovado. Teste a hipótese com um experimento real (por exemplo, instalar versões em diretório temporário) antes de afirmar a causa.
- Se a causa derrubar a hipótese, registre isso no relatório.
- Registre também os seus próprios erros de teste e roteiro, com a correção.
- Nunca altere um hash, baseline ou gate só para "ficar verde" sem causa-raiz comprovada. Se o ticket mandar parar e perguntar, pergunte.

3.2 Execução do ticket (TDD)
- Red: escreva o teste que falha e comprove com o exit code real (exit 1).
- Implemente a correção mínima e cirúrgica.
- Green: rode o teste (exit 0) e depois o mecanismo real que falhou. Teste o gate ou comando exato que vai rodar, nunca um "parecido".
- Exit code real: redirecione a saída para arquivo e capture $? na mesma linha. Nunca use pipe, pois "cmd | tail" devolve o código do tail. Em tarefas em segundo plano, o "exit 0" da notificação é do último comando do script (por exemplo, um cat); leia o exit code gravado em arquivo.
- Se simular uma falha para provar uma mensagem, restaure o estado e comprove com cmp ou diff que ficou idêntico.

3.3 Refazer a etapa
- Depois de corrigir, refaça a etapa inteira com o mecanismo real e gere a nova versão do relatório (_v2, _v3...).

### 4. Padrão de Branches e Merge para o Motor Original

4.1 O clone de teste recebe a correção primeiro, para destravar o fluxo.
4.2 Cada correção também é levada ao motor original, assim:
- Uma branch por etapa que tenha correção: fix/<fluxo>-etapa-NN-<assunto> (ex.: fix/pure-etapa-02-hash-impeccable).
- Crie cada branch a partir da main limpa. NÃO empilhe branches umas sobre as outras, para o merge poder ser feito em qualquer ordem sem conflito.
- Leve apenas os arquivos VERSIONADOS que o ticket alterou, mais os arquivos de baseline que o próprio ticket obrigue a atualizar (ex.: .secrets.baseline quando um hash versionado muda de valor). Efeitos colaterais do bootstrap ou da instalação (como .mcp.json, .agents/mcp_config.json e mimocode.jsonc) ficam de fora.
- Um ticket vira um commit pequeno.
- NUNCA faça commit, merge ou push sem aprovação explícita do usuário. A aprovação de um item não vale para o próximo.
- Antes de propor commit, rode no original: pytest da ferramenta alterada (com exit code real) e os gates do projeto (python -X utf8 ecossistema.py audit, ~7 min, com TEMP e TMP apontando para C:\Users\trcnologia\aidd-tmp, para o limpador de %TEMP% não apagar nada). Trabalhos longos rodam em segundo plano, com log em arquivo. Se um gate reprovar, investigue a causa antes de mexer em qualquer baseline.
4.3 Ao FINALIZAR o fluxo inteiro:
- Mergear as branches na main, uma a uma, com aprovação a cada merge.
- Fazer um diff entre o clone de teste e o original, para provar que os arquivos corrigidos ficaram idênticos.
- Só então push, com aprovação.

### 5. Arquivos locais x repositório

- O merge só afeta arquivos versionados. Arquivos ignorados pelo git ou exclusivos da máquina (skills instaladas, __pycache__, .orca/, configs locais) não são tocados.
- Nunca corrija um arquivo gerado ou ignorado. Corrija a regra que o gera (script, manifesto ou template versionado), senão a correção se perde no merge.
- Se um ticket deixar o ambiente local desatualizado em relação à correção (ex.: a skill instalada localmente está em outra versão do que o manifesto novo espera), informe o usuário e pergunte antes de alterar o arquivo local. Nunca altere sem autorização.

### 6. Formato das Respostas ao Usuário

- Primeira frase: o resultado, sem preâmbulo. Depois, corpo curto em tópicos com fatos e números. Por fim, um fechamento com uma sugestão e uma pergunta de autorização.
- Linguagem simples e curta. Aprofunde só se for pedido.
- Perguntas ao usuário direto no chat, em texto normal.
- Relate falhas com o conteúdo completo (exit code, trecho do erro).
- Declare como concluído apenas o que foi verificado por exit code real. O que não foi rodado deve ser dito como pendência.

### Próximo Passo

Se todas as instruções, restrições, a criação de arquivos modulares, o formato do template com a seção TICKETS, o protocolo de correção e o padrão de branches/merge estiverem claros, confirme o entendimento e apresente exclusivamente o Passo 1 (ETAPA_01-clonagem-do-repositorio.md) para autorização de início.

---------- FIM DO PROMPT ----------

## Registro de alterações do prompt

| Data | Mudança | Origem (aprendizado real) |
|---|---|---|
| 13-10-2026 | Versão inicial: ritmo, diretórios, log por etapa, TICKETS, protocolo de correção, branches e merge, arquivos locais, formato de resposta. | Fluxo PURE, ETAPAs 01-02 (Tickets 1 e 2: hash do impeccable). |
| 13-10-2026 | Seção 4.2: baseline que o ticket obrigue a atualizar entra na branch (.secrets.baseline); investigar a causa antes de mexer em baseline. | O hash novo do manifesto reprovou o G_SEGREDOS no audit completo. |
| 13-10-2026 | Seção 3.2: exit 0 de notificação de tarefa em segundo plano não é o do comando principal; ler o exit code gravado em arquivo. | O audit reprovou com exit 1 enquanto a notificação dizia exit 0. |
