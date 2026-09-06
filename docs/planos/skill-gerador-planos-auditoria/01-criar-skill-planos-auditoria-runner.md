# Item 1 — Criar a skill compartilhada `planos-auditoria-runner`

> **Escopo:** criar, sincronizar e testar uma skill compartilhada que formaliza (sem automatizar decisão/aprovação) o padrão estrutural já usado 3 vezes neste monorepo para gerar pastas de plano de auditoria/evolução/testes.
> **Não faz parte deste item:** a skill decidir escopo, aprovar itens, enviar Prompts de Execução a agentes executores, ou fazer commit/push — essas ações continuam humanas por design (ver `00-PROCESSO-E-DECISOES.md` §4).

---

## Contexto já investigado

- Convenção real de skill compartilhada confirmada lendo `componentes/compartilhado/skills/componentes-runner/SKILL.md`: frontmatter YAML só com `name` + `description`, corpo em Markdown com protocolo determinístico do agente, vive em `componentes/compartilhado/skills/<nome>/SKILL.md` (compartilhada = útil a qualquer ferramenta/harness, distribuída via `python ecossistema.py components sync --tipo skill`).
- Padrão estrutural confirmado nos 4 exemplos reais já existentes (os 3 anteriores + esta própria pasta):
  - Um `00-PROCESSO-E-DECISOES.md` por iniciativa: origem/motivação, o processo em si, tabela "onde vive o conteúdo técnico de cada item", regras fixas, e uma tabela de registro de progresso (atualizada só depois de resultado real).
  - Um `NN-<nome-do-item>.md` por item, sempre com a mesma seção interna: Contexto já investigado → Definição de Pronto (itens numerados e checáveis) → Critério de saída → Prompt de Execução autocontido em PT-BR **e** a versão English.
- Regra fixa que nunca pode ser pulada (motivo do incidente registrado em memória — fork de levantamento fabricou uma "decisão do usuário" que nunca aconteceu): nenhum item começa a ser implementado sem essa Definição de Pronto escrita e **aprovada pelo usuário real** antes — nenhum agente/skill pode fabricar ou presumir essa aprovação.
- Checklist de higiene já obrigatório nesta sessão para qualquer Prompt de Execução gerado: contagem de marcadores de cerca de código (linhas que começam com três crases) confirmando pares isolados, nunca aninhados — reincidente 2x antes.

## Definição de Pronto

1. Skill criada em `componentes/compartilhado/skills/planos-auditoria-runner/SKILL.md` (nome sugerido — o executor pode propor um nome melhor no relatório final se achar que comunica melhor, mantendo o padrão `<algo>-runner` das skills compartilhadas existentes), com frontmatter `name`+`description` no mesmo formato das skills existentes.
2. A skill documenta um protocolo do agente (instrução em linguagem natural, como `componentes-runner` — não é um script Python) com estes passos obrigatórios, nesta ordem:
   1. **Nunca iniciar sozinha.** Só age quando o usuário pedir explicitamente para iniciar uma nova iniciativa de plano.
   2. **Confirmar escopo com o usuário antes de escrever qualquer arquivo** — nome da iniciativa (vira o nome da pasta em `docs/planos/<nome>/`), lista provisória de itens/baterias/pacotes. Usar pergunta explícita ao usuário — nunca presumir ou fabricar uma resposta.
   3. **Gerar a estrutura de pasta** em `docs/planos/<nome-da-iniciativa>/`: um `00-PROCESSO-E-DECISOES.md` e um `NN-<item>.md` por item confirmado, cada um com Contexto → Definição de Pronto (rascunho, marcado explicitamente como "aguardando aprovação") → Critério de saída → Prompt de Execução PT-BR + EN-US.
   4. **Rodar a checagem de cercas de código aninhadas** em cada arquivo gerado antes de considerar qualquer Prompt de Execução pronto.
   5. **Parar e devolver o controle.** Nunca marcar nada como "aprovado", "concluído" ou "decidido pelo usuário" por conta própria. Nunca enviar o Prompt de Execução a nenhum agente executor sozinha. Nunca fazer commit/push.
3. A skill inclui, no próprio corpo, uma referência textual aos 4 exemplos reais (`docs/planos/evolucao-notas-auditoria/`, `docs/planos/refinamento-notas-auditoria/`, `docs/planos/testes-completos-ecossistema/`, `docs/planos/skill-gerador-planos-auditoria/` — esta própria pasta) como referência de formato.
4. Sincronização real: `python ecossistema.py components sync --tipo skill --ferramenta compartilhado` executado com exit 0, e `python ecossistema.py audit` continua exit 0 depois.
5. Teste manual real (não hipotético): pedir para a skill gerar uma iniciativa de exemplo dentro de um diretório temporário isolado (nunca escrever direto em `docs/planos/` real durante o teste) e confirmar que a estrutura gerada bate item a item com o padrão dos 4 exemplos reais.

## Critério de saída

- `SKILL.md` criado no caminho correto, sincronizado com exit 0, `ecossistema.py audit` limpo.
- Teste manual de geração de uma iniciativa de exemplo (em diretório temporário isolado) confirmando fidelidade ao padrão real.
- Nenhum arquivo dentro de `docs/planos/` real criado ou alterado pelo próprio teste da skill.
- `git status` da raiz limpo ao final, exceto os arquivos reais desta tarefa (a skill nova e os destinos sincronizados pelo `components sync`).

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai criar uma nova skill compartilhada no monorepo ecossistema-aidd
(raiz em C:\Users\trcnologia\Desktop\ecossistema-aidd) que formaliza um
processo que hoje é feito manualmente: gerar pastas de "plano de
auditoria/evolução/testes" com uma estrutura padrão. Esta skill NÃO deve
tomar decisões sozinha nem fabricar aprovações — ela só organiza
estrutura e rascunhos, sempre devolvendo o controle para uma pessoa
real decidir e aprovar.

CONTEXTO JÁ INVESTIGADO (leia os 4 exemplos reais abaixo antes de
escrever qualquer coisa — não invente a convenção, copie o padrão real):
- docs/planos/evolucao-notas-auditoria/00-PROCESSO-E-DECISOES.md
- docs/planos/refinamento-notas-auditoria/00-PROCESSO-E-DECISOES.md
- docs/planos/testes-completos-ecossistema/00-PROCESSO-E-DECISOES.md
- docs/planos/skill-gerador-planos-auditoria/00-PROCESSO-E-DECISOES.md
  (esta própria pasta — feita seguindo o mesmo padrão, serve de
  exemplo adicional)
- Cada um desses tem, dentro da mesma pasta, um ou mais arquivos
  NN-<nome>.md com a estrutura: Contexto já investigado -> Definição de
  Pronto -> Critério de saída -> Prompt de Execução (em PT-BR e depois
  a versão English, ambos autocontidos, prontos para copiar e colar
  para um agente executor externo que não viu a conversa original).
- Convenção real de skill compartilhada: leia
  componentes/compartilhado/skills/componentes-runner/SKILL.md como
  referência de formato (frontmatter YAML com só "name" e "description",
  corpo em Markdown com um protocolo determinístico do agente).

DEFINIÇÃO DE PRONTO:
1. Criar componentes/compartilhado/skills/planos-auditoria-runner/SKILL.md
   (pode propor nome melhor no relatório final se achar que comunica
   mais claro, mantendo o padrão "<algo>-runner" das skills
   compartilhadas existentes), com frontmatter name+description no
   mesmo formato das skills existentes.
2. O corpo da skill documenta um protocolo do agente, nesta ordem
   obrigatória:
   a. Nunca iniciar sozinha - só age quando o usuário pedir
      explicitamente para iniciar uma nova iniciativa de plano.
   b. Confirmar com o usuário, ANTES de escrever qualquer arquivo: nome
      da iniciativa (vira o nome da pasta em docs/planos/<nome>/),
      lista provisória de itens/baterias/pacotes. Fazer isso via
      pergunta explícita ao usuário real - nunca presumir ou inventar
      a resposta.
   c. Gerar a estrutura: um 00-PROCESSO-E-DECISOES.md (seguindo o
      template dos 4 exemplos reais acima) e um NN-<item>.md por item
      confirmado, cada um com Contexto -> Definição de Pronto (rascunho,
      marcado explicitamente como "aguardando aprovação", nunca como
      aprovado) -> Critério de saída -> Prompt de Execução PT-BR e
      EN-US.
   d. Rodar checagem de cercas de código aninhadas (contar
      ocorrências de linhas que comecam com tres crases seguidas em
      cada arquivo gerado, confirmar que formam pares isolados, nunca
      aninhados) antes de considerar qualquer Prompt de Execução
      pronto.
   e. Parar e devolver o controle. A skill entrega os arquivos como
      RASCUNHO - nunca marca nada como "aprovado", "concluído" ou
      "decidido pelo usuário" por conta própria. Nunca envia o Prompt
      de Execução a nenhum agente executor sozinha. Nunca faz git
      commit nem git push.
3. Incluir no corpo da skill uma referência textual aos 4 exemplos
   reais acima, para quem a executar não precisar adivinhar a
   convenção.
4. Rodar de verdade:
   python ecossistema.py components sync --tipo skill --ferramenta compartilhado
   confirmar exit 0. Depois rodar:
   python ecossistema.py audit
   confirmar exit 0 (prova que o frontmatter da skill nova passa no
   gate G_ECOSSISTEMA_INTEGRIDADE).
5. Teste manual real: invoque a skill de verdade (ou simule seguindo o
   protocolo dela manualmente, se a invocação automática não for
   possível neste ambiente) pedindo para gerar uma iniciativa de
   EXEMPLO dentro de um diretório temporário isolado (mktemp -d ou
   equivalente) - nunca escrever dentro de docs/planos/ real durante
   este teste. Confirme que a estrutura gerada (pastas, nomes de
   arquivo, seções internas) bate item a item com o padrão dos 4
   exemplos reais.

CRITÉRIO DE SAÍDA:
- SKILL.md criado no caminho correto, sync com exit 0, audit com exit 0.
- Teste manual de geração de uma iniciativa de exemplo em diretório
  temporário isolado, com evidência real (caminho dos arquivos
  gerados, conteúdo consistente com o padrão).
- Nenhum arquivo dentro de docs/planos/ real criado ou alterado pelo
  teste.
- git status da raiz do repositório limpo ao final, exceto os arquivos
  reais desta tarefa (a skill nova e os destinos sincronizados pelo
  components sync).

REGRAS DE ESCOPO - NÃO FAÇA:
- Não escreva a skill de forma que ela decida sozinha escopo, aprove
  itens ou invente respostas do usuário - isso é a regra mais
  importante desta tarefa.
- Não faça a skill enviar o Prompt de Execução para nenhum agente
  executor sozinha, nem fazer commit/push sozinha - isso continua
  sendo ação humana.
- Não gere nenhum arquivo dentro de docs/planos/ real durante o teste
  desta própria tarefa - use diretório temporário isolado.
- Não faça git commit nem git push desta tarefa.

ENTREGÁVEL: caminho do SKILL.md criado, saída real dos 2 comandos
(sync e audit) com exit code, caminho dos arquivos gerados no teste
manual em diretório temporário, e um resumo de 3-5 linhas confirmando
que a trava de "nunca decidir/aprovar sozinha" está clara no texto da
skill.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to create a new shared skill in the ecossistema-aidd
monorepo (root at C:\Users\trcnologia\Desktop\ecossistema-aidd) that
formalizes a process done manually today: generating "audit/evolution/
test plan" folders with a standard structure. This skill must NOT make
decisions on its own or fabricate approvals - it only organizes
structure and drafts, always handing control back to a real person to
decide and approve.

ALREADY-INVESTIGATED CONTEXT (read the 4 real examples below before
writing anything - do not invent the convention, copy the real
pattern):
- docs/planos/evolucao-notas-auditoria/00-PROCESSO-E-DECISOES.md
- docs/planos/refinamento-notas-auditoria/00-PROCESSO-E-DECISOES.md
- docs/planos/testes-completos-ecossistema/00-PROCESSO-E-DECISOES.md
- docs/planos/skill-gerador-planos-auditoria/00-PROCESSO-E-DECISOES.md
  (this very folder - built following the same pattern, serves as an
  extra example)
- Each of these has, inside the same folder, one or more NN-<name>.md
  files with the structure: Already-investigated context -> Definition
  of Done -> Exit criteria -> Execution Prompt (in PT-BR then the
  English version, both self-contained, ready to copy-paste to an
  external executor agent that has not seen the original conversation).
- Real shared-skill convention: read
  componentes/compartilhado/skills/componentes-runner/SKILL.md as the
  format reference (YAML frontmatter with only "name" and
  "description", Markdown body with a deterministic agent protocol).

DEFINITION OF DONE:
1. Create componentes/compartilhado/skills/planos-auditoria-runner/SKILL.md
   (may propose a better name in the final report if it communicates
   more clearly, keeping the "<something>-runner" pattern of existing
   shared skills), with name+description frontmatter in the same
   format as existing skills.
2. The skill body documents an agent protocol, in this mandatory order:
   a. Never start on its own - only acts when the user explicitly asks
      to start a new plan initiative.
   b. Confirm with the user, BEFORE writing any file: the initiative
      name (becomes the folder name in docs/planos/<name>/), a
      provisional list of items/batteries/packages. Do this via an
      explicit question to the real user - never assume or invent the
      answer.
   c. Generate the structure: a 00-PROCESSO-E-DECISOES.md (following
      the template of the 4 real examples above) and one NN-<item>.md
      per confirmed item, each with Context -> Definition of Done
      (draft, explicitly marked as "awaiting approval", never as
      approved) -> Exit criteria -> Execution Prompt in PT-BR and
      EN-US.
   d. Run a nested-code-fence check (count lines that start with three
      backticks in a row in each generated file, confirm they form
      isolated pairs, never nested) before considering any Execution
      Prompt ready.
   e. Stop and hand control back. The skill delivers the files as a
      DRAFT - never marks anything as "approved", "completed", or
      "decided by the user" on its own. Never sends the Execution
      Prompt to any executor agent by itself. Never runs git commit or
      git push.
3. Include in the skill body a textual reference to the 4 real
   examples above, so whoever runs it doesn't have to guess the
   convention.
4. Actually run:
   python ecossistema.py components sync --tipo skill --ferramenta compartilhado
   confirm exit 0. Then run:
   python ecossistema.py audit
   confirm exit 0 (proves the new skill's frontmatter passes the
   G_ECOSSISTEMA_INTEGRIDADE gate).
5. Real manual test: actually invoke the skill (or manually simulate
   following its protocol, if automatic invocation is not possible in
   this environment) asking it to generate a SAMPLE initiative inside
   an isolated temporary directory (mktemp -d or equivalent) - never
   write inside the real docs/planos/ during this test. Confirm the
   generated structure (folders, file names, internal sections)
   matches the 4 real examples item by item.

EXIT CRITERIA:
- SKILL.md created at the correct path, sync exits 0, audit exits 0.
- Manual test of generating a sample initiative in an isolated
  temporary directory, with real evidence (path of generated files,
  content consistent with the pattern).
- No file inside the real docs/planos/ created or changed by the test.
- Root repository git status clean at the end, except the real files
  of this task (the new skill and the destinations synced by
  components sync).

SCOPE RULES - DO NOT:
- Do not write the skill so that it decides scope on its own, approves
  items, or invents user answers - this is the single most important
  rule of this task.
- Do not make the skill send the Execution Prompt to any executor
  agent by itself, nor commit/push by itself - this remains a human
  action.
- Do not generate any file inside the real docs/planos/ during this
  task's own test - use an isolated temporary directory.
- Do not git commit or git push for this task.

DELIVERABLE: path of the created SKILL.md, real output of both
commands (sync and audit) with exit code, path of the files generated
in the manual test inside the temporary directory, and a 3-5 line
summary confirming that the "never decide/approve alone" guardrail is
clear in the skill's text.
```
