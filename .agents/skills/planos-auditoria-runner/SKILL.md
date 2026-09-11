---
name: planos-auditoria-runner
description: Gera a estrutura padrao e rascunhos de planos de auditoria, evolucao ou testes (00-PROCESSO-E-DECISOES.md e NN-<item>.md) sem fabricar decisoes ou aprovacoes.
---

# Planos Auditoria Runner — Gerador Estrutural de Planos

Esta skill formaliza e padroniza a criacao de iniciativas de plano em `docs/planos/<nome-da-iniciativa>/` seguindo a arquitetura documental canonica do monorepo ecossistema-aidd.

## Principio Fundamental e Regras Inegociaveis (Guarda de Seguranca)

1. **A skill nunca decide, nem aprova sozinha:** Todo arquivo gerado e entregue estritamente como **RASCUNHO** com status explicito "aguardando aprovacao". Nenhuma decisao de escopo, escolha arquitetural ou aprovacao de item pode ser fabricada pelo agente.
2. **Determinismo Primeiro (Zero Token Fallacy):** A geracao do esqueleto estrutural e a checagem de cercas markdown devem utilizar o comando deterministico CLI oficial `python ecossistema.py plan ...` sempre que possivel, evitando geracao manual suscetivel a erros.
3. **A skill nunca envia prompts a agentes executores sozinha:** A execucao, copia/colagem de prompts ou disparo de subagentes depende de comando e acao expressa do usuario humano.
4. **Sem Git Commit / Push Automatico:** A skill nao executa comandos git de commit ou push.
5. **Isolamento em Testes:** Qualquer teste ou validacao estrutural deve ser executado em diretorio temporario isolado, jamais alterando ou criando lixo em `docs/planos/` em tempo de teste.

---

## Referencias Canonicas no Repositorio

Consulte a estrutura e tom dos 4 exemplos reais ja estabelecidos no ecossistema:
- `docs/planos/feitos/evolucao-notas-auditoria/00-PROCESSO-E-DECISOES.md`
- `docs/planos/feitos/refinamento-notas-auditoria/00-PROCESSO-E-DECISOES.md`
- `docs/planos/feitos/testes-completos-ecossistema/00-PROCESSO-E-DECISOES.md`
- `docs/planos/feitos/skill-gerador-planos-auditoria/00-PROCESSO-E-DECISOES.md`

## Onde a iniciativa nasce vs onde ela vive

`python ecossistema.py plan init <nome>` sempre cria a pasta nova direto em
`docs/planos/<nome>/` (raiz) — isso é esperado e correto. O ecossistema
organiza `docs/planos/` em 3 subpastas por status real (`feitos/`,
`fazendo/`, `a-fazer/`), mas quem move a iniciativa pra lá é
`python scripts/atualizar_index_planos.py`, rodado depois (manualmente ou
pelo hook de pre-commit) — nunca decida você mesmo em qual subpasta uma
iniciativa nova deveria começar.

---

## Protocolo Obrigatorio do Agente

Quando esta skill for acionada (ou via `/plan`):

### Passo 1: Nao Iniciar Sozinha
Apenas atue sob demanda expressa do usuario para iniciar ou estruturar uma nova iniciativa de plano.

### Passo 2: Alinhamento Previo de Escopo com o Usuario
Antes de criar ou gravar qualquer arquivo em disco, pergunte e confirme explicitamente com o usuario:
- Nome identificador da iniciativa (ex: `refatoracao-modulo-auth`), que se tornara a pasta `docs/planos/<nome-da-iniciativa>/`.
- Objetivo e motivacao central da iniciativa.
- Lista preliminar de itens/tarefas que comporao as frentes de trabalho.
- **Nota Atual, Nota Alvo (0-10) e evidencia real** — para a iniciativa como um todo E para cada item. A evidencia e um relatorio ja existente (ex: um relatorio gerado pela skill `melhoria`), um comando ou teste rodado agora. **Nunca aceite ou invente um numero sem evidencia real** — se o usuario nao tiver evidencia ainda, o campo fica `NAO AUDITADO`, nunca uma estimativa do agente.
*Nota:* Jamais assuma nomes ou liste itens por inferencia silenciosa sem validacao interativa.

### Passo 3: Geracao Deterministica Estruturada dos Arquivos
Apos confirmacao do escopo pelo usuario, utilize o CLI deterministico:
```bash
python ecossistema.py plan init <nome-da-iniciativa> --itens "Item 1" "Item 2" \
  --notas-atuais "6" "5" --notas-alvo "9" "8" --evidencias "docs/melhorias/<relatorio>.html" "" \
  --nota-atual-geral "6" --nota-alvo-geral "9" --evidencia-geral "docs/melhorias/<relatorio>.html"
```
As flags de nota sao opcionais e posicionais (mesma ordem de `--itens`). Se
`--evidencias` vier vazio para um item, a nota atual daquele item e forcada
para `NAO AUDITADO` automaticamente pelo proprio gerador — o script nunca
grava um numero sem evidencia, mesmo que um seja passado por engano.

O comando criara automaticamente com integridade garantida:
1. **`00-PROCESSO-E-DECISOES.md`:**
   - Origem, proposito e aviso de governanca.
   - Secoes canonicas: O que este esforco busca (com a Metrica da Iniciativa —
     Nota Atual/Alvo/Real), Processo Adotado, Onde vive o conteudo tecnico,
     Regras Fixas e Registro de Progresso (itens marcados como
     `⏳ Rascunho gerado, aguardando aprovacao`, com colunas de Nota Atual,
     Nota Alvo e Nota Real por item).
2. **`NN-<nome-do-item>.md`** (um para cada item acordado):
   - Escopo, Status `[RASCUNHO — Aguardando Aprovacao Humana]` e o bloco de
     Nota Atual/Alvo/Real (com evidencia) daquele item.
   - Contexto investigado, Definicao de Pronto checavel, Criterio de saida.
   - Prompt de Execucao (PT-BR) e versao em ingles autocontidos.
3. **Nota Real:** so e preenchida no fechamento de cada item/iniciativa, e
   somente rodando o MESMO mecanismo real que mediu a Nota Atual (nunca um
   comando "parecido") — mesma regra que ja vale para os planos de auditoria
   de notas existentes em `docs/planos/feitos/`.

### Passo 4: Verificacao Deterministica de Cercas de Codigo (Anti-Nesting)
Valide a integridade sintatica de todas as cercas de codigo markdown atraves do comando CLI:
```bash
python ecossistema.py plan check-fences docs/planos/<nome-da-iniciativa>/
```
Garante que todas as cercas ocorram em pares isolados (abertura e fechamento), sem quebra de formatacao.

### Passo 5: Parada Estrita e Devolucao de Controle
- Apresente ao usuario os caminhos dos arquivos criados.
- Devolva o controle imediatamente para que o usuario revise, ajuste ou aprove a Definicao de Pronto antes de qualquer implementacao.
- **NUNCA** marque tarefas como aprovadas ou concluidas sem veredito real do usuario.
- Depois que o usuario aprovar o plano (nunca antes disso), pergunte explicitamente
  se ele quer que o `/orchestrate` seja iniciado a partir desta iniciativa. **Nunca
  dispare o `/orchestrate` sozinho** — ele tem seu proprio gate (ORCA vs Subagentes)
  que exige decisao humana explicita antes de qualquer execucao.

---

## Comandos CLI Equivalentes

```bash
# Inicializar nova iniciativa de plano
python ecossistema.py plan init <nome-da-iniciativa> --itens "Item 1" "Item 2"

# Verificar balanceamento de cercas markdown
python ecossistema.py plan check-fences <caminho-ou-pasta>
```