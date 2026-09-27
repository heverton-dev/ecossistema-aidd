# Anatomia Técnica: pipeline-melhoria

## Cartão de Identidade
- **Nome do Alvo:** pipeline-melhoria (Tríade /melhoria -> /plan -> /orchestrate)
- **Finalidade:** Investigar fatos e notas no código real, compilar planos de melhoria com notas de maturidade (0-10) ancoradas em evidências e orquestrar a execução multiamplo (ORCA app, Subagentes ou Git Worktrees nativos) com paradas humanas obrigatórias.
- **Nível de Maturidade:** Produção / Blindado (Estrutura canônica de ciclo de vida em 3 estágios independentes).
- **Trava Principal:** Paradas humanas compulsórias entre estágios (Lei #7 - Developer in Control), proibição de notas estimadas sem medição real (`NAO AUDITADO`) e barreira de sincronização antes de qualquer merge.
- **Comando Acionador:** `python ecossistema.py melhoria ...` (ou `/melhoria`), `python ecossistema.py plan ...` (ou `/plan`), `python ecossistema.py orchestrate ...` (ou `/orchestrate`).
- **Localização:** `scripts/gerenciador_melhorias.py`, `scripts/gerenciador_planos.py`, `componentes/compartilhado/skills/aidd-orca/scripts/` e as skills `aidd-improvement`, `aidd-plan`, `aidd-orchestrate`.

---

## Fluxo de Execução
- **Etapa 1 — Investiga (Estágio /melhoria):** **Dispara** a análise profunda acionada exclusivamente por pedido explícito em linguagem natural:
  - **Consulta** o grafo de conhecimento via `code-review-graph` e complementa com inspeção direta via CLI/Grep.
  - **Mede** a nota atual (0-10) baseada em evidência factual verificável; na ausência de prova real, **atribui** compulsoriamente `NAO AUDITADO`.
  - **Gera** deterministicamente o par de artefatos `<data>_melhoria-<3-palavras>.html` e `.json` em `docs/melhorias/` via `scripts/gerenciador_melhorias.py`.
  - **Interrompe** o fluxo e **devolve** o controle ao usuário com pergunta de confirmação antes de avançar para planejamento.
- **Etapa 2 — Modela (Estágio /plan):** **Estrutura** a pasta da iniciativa em `docs/planos/PLAN-<NNNN>-<nome>/`:
  - **Valida** escopo, itens previstos, notas atuais e notas-alvo junto ao usuário antes da escrita.
  - **Compila** deterministicamente os arquivos `00-PROCESSO-E-DECISOES.md` e `NN-<item>.md` através de `python ecossistema.py plan init`.
  - **Audita** a integridade dos blocos de código markdown via `python ecossistema.py plan check-fences`.
  - **Mantém** todos os itens em estado `DRAFT` até aprovação expressa do usuário.
  - **Aprova** e **move** a pasta do plano para `docs/planos/a-fazer/` via `python ecossistema.py plan aprovar` somente sob comando explícito.
- **Etapa 3 — Roteia (Estágio /orchestrate - Pré-voo):** **Seleciona** o ambiente de execução sem presunção autônoma:
  - **Interroga** o usuário sobre o ambiente pretendido: ORCA app real (`orca-cli`), Subagentes da sessão, ou Git Worktrees nativos.
  - **Compila** o manifesto mecânico `.orca-flight-plan.json` em modo seco (`--dry-run`) via `componentes/compartilhado/skills/aidd-orca/scripts/`.
  - **Exibe** o plano de voo e **aguarda** validação/edição manual de harnesses, modelos e parâmetros.
- **Etapa 4 — Executa (Estágio /orchestrate - Voo):** **Inicia** a implementação controlada dos tickets:
  - **Marca** o plano em andamento movendo a pasta para `docs/planos/fazendo/` via `python ecossistema.py plan iniciar-execucao`.
  - **Isola** as frentes em árvores de trabalho Git efêmeras (`git worktree`) ou despacha tarefas isoladas para subagentes conforme o ambiente eleito.
  - **Executa** o ciclo de implementação assegurando passagens por gates locais e verificação de handoff.
- **Etapa 5 — Conclui (Estágio /orchestrate - Pós-voo):** **Consolida** o ciclo e **arquiva** a iniciativa:
  - **Revalida** a suíte de testes e o contrato do ecossistema antes de qualquer integração na branch base.
  - **Move** a pasta do plano para `docs/planos/concluidos/` após validação humana.

---

## Esteira Visual com Blocos

| Bloco | Descrição do Fluxo |
| :--- | :--- |
| **Entrada** | Pedido em linguagem natural do usuário, relatório de auditoria ou plano existente para reanálise comparativa. |
| **Processo** | Triangulação investigativa no código real ➔ Escopo e compilação de pastas de plano ➔ Geração do Flight Plan multiamplo ➔ Execução isolada por frentes. |
| **Trava** | Portão humano obrigatório entre cada estágio (Lei #7), proibição estrita de notas estimadas sem teste real e checagem rígida de markdown fences. |
| **Saída** | Relatórios auditados em `docs/melhorias/`, planos versionados em `docs/planos/` e código testado integrado à branch principal com histórico limpo. |

---

## Defeitos e Limitações
- **Fragmenta** a orquestração em scripts heterogêneos entre `scripts/gerenciador_*` e `componentes/compartilhado/skills/aidd-orca/scripts/`.
- **Depende** de formatação estrita de nomes de pastas (`PLAN-<NNNN>-<3-palavras>`), falhando deterministicamente se pastas forem manipuladas manualmente.
- **Limita** o modo Subagentes ao mesmo contexto de arquivos da sessão, gerando risco de concorrência se frentes paralelas tocarem nos mesmos arquivos sem worktree.
- **Impede** qualquer transição contínua autônoma (zero pipeline unattended), exigindo presença humana a cada mudança de estágio (`melhoria` -> `plan` -> `orchestrate`).

> [!WARNING]
> **Ponto Crítico:** Nunca execute comandos de atualização de nota (`plan atualizar-nota`) ou início de orquestração de forma autônoma. A atualização sobrescreve a nota permanentemente no plano e o início de execução move pastas físicas no disco, quebrando a rastreabilidade se disparados sem autorização do desenvolvedor.

> [!TIP]
> **Recomendação Prática:** Ao reanalisar um plano com `/melhoria`, sempre passe `--plano-existente <caminho>` e `--itens-avaliados` para produzir a tabela comparativa visual de avanço (nota anterior vs nova nota com status `feito`, `parcial` ou `nao-feito`).
