# PROMPT OPERACIONAL DE AUDITORIA EM MASSA (MODO /GOAL)

Copie e execute o bloco de instruções abaixo como o objetivo do comando `/goal` no terminal ou harness:

```markdown
Você atuará como o Orquestrador Mestre Autônomo de Auditoria e Evolução do Ecossistema AIDD.
Sua missão inegociável é zerar a lista de pendências do Plano Mestre de Auditoria com 100% de conformidade técnica e aprovação binária em todos os Quality Gates.

================================================================================
META FINAL
================================================================================
100% dos itens listados em `docs/auditoria/PLANO-MESTRE-AUDITORIA.md` marcados como concluídos `[x]`, com todos os relatórios factuais 15-D emitidos, códigos evoluídos sem mocks nem stubs, suíte de testes passando e nenhum portão quebrado (tudo verde).

================================================================================
CONFIGURAÇÕES E INVARIANTES OBRIGATÓRIAS
================================================================================
1. Configuração de Execução:
   - Siga estritamente `docs/auditoria/CONFIG-EXECUCAO-USUARIO.json`.
   - O comando de terminal padrão para os agentes de todas as fases e worktrees é:
     `claude-9router --dangerously-skip-permissions --chrome --model sonnet`

2. Gestão Estrita de Git Worktrees:
   - Cada ciclo e ticket de implementação DEVE rodar em uma Git Worktree isolada temporária (ex: `.worktrees/audit-<alvo>-ciclo-<N>`).
   - Imediatamente após a conclusão com sucesso de um ciclo (ou término do item), execute nesta ordem:
     a) `git add -A` e `git commit -m "audit(<alvo>): conclusao do ciclo <N>"`
     b) Merge da branch da worktree na branch `main`
     c) Push das alterações para o repositório remoto
     d) Remoção total e forçada da worktree e de sua pasta temporária (`git worktree remove --force <caminho>` e deleção do diretório efêmero).
   - NUNCA deixe pastas temporárias de worktrees acumuladas no disco.

3. Protocolo de Resiliência e Auto-Recuperação (Crash Recovery):
   - Se o agente orquestrador ou qualquer subagente travar, produzir erro irrecuperável de contexto ou falhar na execução:
     a) Encerre/feche imediatamente a aba/processo com erro.
     b) Abra uma nova aba/sessão invocando o agente limpo via `claude-9router`.
     c) Leia o último artefato factual persistido no diretório da auditoria (`01-RELATORIO-INSPETOR.md`, `02-PLANO-EVOLUCAO.md` ou `03-RELATORIO-CONSTRUTOR.md`).
     d) Retome o trabalho exatamente do ponto onde parou sem perder o estado.
   - A mesma regra de descarte e reabertura limpa com `claude-9router` se aplica para worktrees que apresentarem falhas de ambiente, terminal ou concorrência.

================================================================================
FLUXO DE EXECUÇÃO PASSO A PASSO
================================================================================

Para CADA item pendente `[ ]` em `docs/auditoria/PLANO-MESTRE-AUDITORIA.md` (seguindo a ordem Bottom-Up: Fundações ➔ Gestão ➔ Utilitários ➔ Middlewares ➔ Tools ➔ Tríade):

1. INICIALIZAÇÃO DO ALVO:
   - Identifique o componente ou ferramenta alvo.
   - Verifique o histórico em `docs/auditoria/<alvo>/` para identificar o próximo ciclo a executar (`ciclo-01`, `ciclo-02` ou `ciclo-03`).
   - Crie a pasta do ciclo: `docs/auditoria/<alvo>/ciclo-NN/`.

2. EXECUÇÃO DO PAR [AUDIT-4F + EVOLUCAO] (MÁXIMO DE 3 CICLOS POR ALVO):
   Para cada ciclo (limite de 3 tentativas por ferramenta):

   - FASE 1 (INSPETOR 15-D):
     * Crie o `PROMPT-INSPETOR.txt` fechado com os caminhos dos arquivos do alvo.
     * Execute o Inspetor via `claude-9router` gerando `01-RELATORIO-INSPETOR.md`.
     * Valide deterministicamente com o script de portão local `python docs/auditoria/<alvo>/G_auditoria_15D.py` (ou `gates/G_auditoria_15D.py`).
     * Se todas as 15 dimensões estiverem em conformidade (EXIT 0), o alvo é considerado aprovado e pode avançar direto para a finalização.

   - FASE 2 (ARQUITETO):
     * Se houver dimensões falhas ou notas abaixo do DoD, invoque o Arquiteto via `claude-9router`.
     * Gere `02-PLANO-EVOLUCAO.md` contendo os tickets de evolução atômicos e prompts executáveis.

   - FASE 3 (CONSTRUTOR EM WORKTREE):
     * Crie a Git Worktree efêmera para o alvo.
     * Invoque o Construtor via `claude-9router` dentro da worktree.
     * Aplique TDD rigoroso (Red-Green-Refactor) e implemente as correções de código reais (Zero Mocks / Zero Stubs).
     * Emita o `03-RELATORIO-CONSTRUTOR.md` documentando todas as alterações e testes comprovados.

   - FASE 4 (INSPETOR DE RETORNO):
     * Re-execute a validação 15-D sob a mesma régua inicial gerando `04-RELATORIO-RETORNO.md`.
     * Rode os testes e portões locais.
     * Se EXIT 0:
       - Faça o commit dos arquivos.
       - Faça merge na `main`.
       - Execute o push.
       - Remova e limpe a pasta da worktree.
       - Atualize a linha do alvo em `docs/auditoria/PLANO-MESTRE-AUDITORIA.md` de `[ ]` para `[x]` com o link para o relatório de retorno.
       - Encerre o processamento desta ferramenta e siga para a próxima da lista.
     * Se EXIT 1 e o número de ciclos for menor que 3:
       - Avance para o próximo ciclo (`ciclo-(N+1)`) repetindo o fluxo a partir da Fase 1 para atacar os débitos remanescentes.
     * Se atingir 3 ciclos sem EXIT 0:
       - Registre a trava em `04-RELATORIO-RETORNO.md`, documente os bloqueios técnicos e acione a recuperação antes de interromper.

3. AUDITORIA GERAL DE INTEGRIDADE:
   - A cada 3 ferramentas concluídas e ao término de toda a fila, execute a validação global:
     `python ecossistema.py audit`
     `python gates/G_DOCS_ROT.py`
   - Garanta que nenhum portão geral foi quebrado no processo.

4. CRITÉRIO DE CONCLUSÃO DO GOAL:
   - O goal só é considerado concluído quando 100% dos checkboxes de `docs/auditoria/PLANO-MESTRE-AUDITORIA.md` estiverem preenchidos com `[x]`, com todas as pastas temporárias de worktrees deletadas do disco e o repositório sincronizado na `main`.
```
