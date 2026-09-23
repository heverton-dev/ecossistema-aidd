# Definition of Done: aidd-melhoria (Readequação Arquitetural)

## Metas e Critérios Binários de Aceitação

1. **D3 (Fallback CLI):**
   A ferramenta `aidd-melhoria` deverá poder ser acionada integralmente por terminal local via `ecossistema.py melhoria --manifest <json>`.

2. **D4 (Handoff CLI):**
   A ferramenta deverá emitir um arquivo de Handoff JSON em `./handoff-melhoria.json` detalhando a avaliação (exit 0) ou falha (exit 1).

3. **D8 (Quality Gate Spec):**
   Deverá ser criado `gates/G_amelhoria.py` que valide o contrato do Handoff da ferramenta e seja incluído no ecossistema e no pipeline.

4. **D11 (Schema JSON e Determinismo):**
   A resposta LLM deve ser envelopada em JSON limpo (ex: `{"relatorio": "..."}`).

5. **D12 (Isolamento de Worktree):**
   A ferramenta não poderá ler/escrever fora de seu diretório de trabalho designado ou de `docs/`.

6. **D13 (Rótulo Honesto):**
   Não poderá afirmar "Refatoração concluída", mas sim "Sugestão de refatoração aprovada/reprovada".

7. **D14 (Testes E2E):**
   O ciclo de 5 passos deve ser completado com `docs/teste-end-to-end/aidd-melhoria.md` atualizado.

8. **D15 (Quarteto):**
   N/A (Justificativa técnica obrigatória no PR informando que a ferramenta não possui UI Web ou rotas de servidor vivo).
