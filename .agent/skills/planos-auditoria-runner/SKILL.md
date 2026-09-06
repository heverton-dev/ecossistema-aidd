---
name: planos-auditoria-runner
description: Gera a estrutura padrão e rascunhos de planos de auditoria, evolução ou testes (00-PROCESSO-E-DECISOES.md e NN-<item>.md) sem fabricar decisões ou aprovações.
---

# Planos Auditoria Runner — Gerador Estrutural de Planos

Esta skill formaliza e padroniza a criação de iniciativas de plano em `docs/planos/<nome-da-iniciativa>/` seguindo a arquitetura documental canônica do monorepo ecossistema-aidd.

## Princípio Fundamental e Regras Inegociáveis (Guarda de Segurança)

1. **A skill nunca decide, nem aprova sozinha:** Todo arquivo gerado é entregue estritamente como **RASCUNHO** com status explícito "aguardando aprovação". Nenhuma decisão de escopo, escolha arquitetural ou aprovação de item pode ser fabricada pelo agente.
2. **A skill nunca envia prompts a agentes executores sozinha:** A execução, cópia/colagem de prompts ou disparo de subagentes depende de comando e ação expressa do usuário humano.
3. **Sem Git Commit / Push Automático:** A skill não executa comandos git de commit ou push.
4. **Isolamento em Testes:** Qualquer teste ou validação estrutural deve ser executado em diretório temporário isolado, jamais alterando ou criando lixo em `docs/planos/` em tempo de teste.

---

## Referências Canônicas no Repositório

Consulte a estrutura e tom dos 4 exemplos reais já estabelecidos no ecossistema:
- `docs/planos/evolucao-notas-auditoria/00-PROCESSO-E-DECISOES.md`
- `docs/planos/refinamento-notas-auditoria/00-PROCESSO-E-DECISOES.md`
- `docs/planos/testes-completos-ecossistema/00-PROCESSO-E-DECISOES.md`
- `docs/planos/skill-gerador-planos-auditoria/00-PROCESSO-E-DECISOES.md`

---

## Protocolo Obrigatório do Agente

Quando esta skill for acionada:

### Passo 1: Não Iniciar Sozinha
Apenas atue sob demanda expressa do usuário para iniciar ou estruturar uma nova iniciativa de plano.

### Passo 2: Alinhamento Prévio de Escopo com o Usuário
Antes de criar ou gravar qualquer arquivo em disco, pergunte e confirme explicitamente com o usuário:
- Nome identificador da iniciativa (ex: `refatoracao-modulo-auth`), que se tornará a pasta `docs/planos/<nome-da-iniciativa>/`.
- Objetivo e motivação central da iniciativa.
- Lista preliminar de itens/tarefas que comporão as frentes de trabalho.
*Nota:* Jamais assuma nomes ou liste itens por inferência silenciosa sem validação interativa.

### Passo 3: Geração Estruturada dos Arquivos
Após confirmação do escopo pelo usuário, crie a pasta da iniciativa e os arquivos essenciais:

1. **`00-PROCESSO-E-DECISOES.md`:**
   - **Cabeçalho:** Título da iniciativa e metadados (origem, data, propósito).
   - **§1 O que este esforço busca:** Objetivos claros e limites de escopo.
   - **§2 Processo Adotado:** Diagnóstico → Definição de Pronto → Prompt de Execução autocontido → Auditoria por reprodução real.
   - **§3 Mapeamento de Itens:** Tabela `# | Item | Documento`.
   - **§4 Regras Fixas:** Vedações, critérios de aprovação humana e não fabricação de consenso.
   - **§5 Registro de Progresso:** Tabela `# | Item | Status | Documento`, marcando os itens inicialmente como `⏳ Prompt gerado, aguardando aprovação`.

2. **`NN-<nome-do-item>.md`** (um para cada item acordado, ex: `01-preparacao.md`):
   - **Título e Escopo:** Descrição concisa do que entra e do que não entra.
   - **Contexto já investigado:** Fatos técnicos verificados e arquivos-chave.
   - **Definição de Pronto:** Itens numerados e checáveis, marcados como `[RASCUNHO — Aguardando Aprovação Humana]`.
   - **Critério de Saída:** Condições observáveis e determinísticas de encerramento.
   - **Prompt de Execução (PT-BR):** Prompt autocontido com instruções completas para um agente executor.
   - **Prompt de Execução — English version:** Versão equivalente em inglês para agentes multilíngues.

### Passo 4: Verificação Determinística de Cercas de Código (Anti-Nesting)
Em cada arquivo Markdown gerado, execute uma inspeção das linhas que iniciam com três crases (```):
- As cercas devem sempre ocorrer em pares isolados (abertura e fechamento).
- Nunca aninhe blocos de código markdown que quebrem a renderização do prompt ou arquivo.

### Passo 5: Parada Estrita e Devolução de Controle
- Apresente ao usuário os caminhos dos arquivos criados.
- Devolva o controle imediatamente para que o usuário revise, ajuste ou aprove a Definição de Pronto antes de qualquer implementação.
- **NUNCA** marque tarefas como aprovadas ou concluídas sem veredito real do usuário.
