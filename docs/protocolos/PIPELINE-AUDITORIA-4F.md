# Pipeline Linear de Auditoria 4F (4 Fases)

> **Governança:** Execução estritamente linear em Git Worktrees. Controle manual de Harness/Model pelo usuário. Convergência submetida à aprovação humana.

## As 4 Fases do Pipeline

1. **Fase 1: Inspetor (Auditoria)**
   - Lançamento da Lens 15-D ou Quality Gate específico.
   - Gera o laudo base (ex: `aidd-melhoria-15D.md`).
2. **Fase 2: Arquiteto (Plano de Evolução)**
   - Lê o laudo e as Definições de Pronto (DoD).
   - Gera o `PLANO-EVOLUCAO.md` na pasta da ferramenta com os tickets de correção e prompts de delegação.
3. **Fase 3: Construtor (Implementação)**
   - Executa os tickets gerados.
   - Altera o código da ferramenta em Worktree isolada.
4. **Fase 4: Inspetor de Retorno (Re-Auditoria)**
   - Re-executa o prompt exato da Fase 1.
   - Assertividade rigorosa: deve atingir `EXIT 0` sem dimensões falhas perante o DoD.

## Invariáveis do Sistema (Regras Inegociáveis)

1. **Input e Soberania do Usuário:** O Harness e o Modelo de cada fase **não são decididos pela IA**. Eles devem ser preenchidos manualmente pelo usuário no manifesto JSON de orquestração antes do disparo do pipeline.
2. **Definition of Done (DoD):** Para evitar loops infinitos, cada execução obrigatoriamente aponta para um "Norte de Pronto" estático (DoD). Se o critério for atingido (EXIT 0 no script de Gate final), o pipeline avança para a aprovação humana.
3. **Aprovação Humana (Join Barrier):** Sob nenhuma circunstância a worktree é mergeada de forma autônoma. Após a Fase 4, a execução é suspensa. O usuário revisará os documentos e códigos para julgar se o DoD foi cumprido na vida real. Só então ocorre o merge e o `[x]` automático no Plano Mestre de Auditoria.
