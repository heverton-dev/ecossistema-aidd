# Índice — `docs/planos/`

> Gerado automaticamente por `python scripts/atualizar_index_planos.py` a partir do status real de cada documento — inclusive a subpasta física (`feitos/`, `fazendo/`, `a-fazer/`), que este script também mantém sincronizada. **Não editar manualmente**: rode o script de novo depois de qualquer mudança de status.

## ✅ Concluídos

| Iniciativa | Local |
|---|---|
| Correcao Codigo Limpo | `feitos/correcao-codigo-limpo/` |
| Correcao Arquitetura Limpa | `feitos/correcao-arquitetura-limpa/` |
| Evolucao Notas Auditoria | `feitos/evolucao-notas-auditoria/` |
| Integracao Aidd Ops | `feitos/integracao-aidd-ops/` |
| Correcao Riscos Ecossistema Aidd | `feitos/PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md` |
| Refinamento Notas Auditoria | `feitos/refinamento-notas-auditoria/` |
| Skill Gerador Planos Auditoria | `feitos/skill-gerador-planos-auditoria/` |
| Skill Orquestracao Orca Ade | `feitos/skill-orquestracao-orca-ade/` |
| Testes Completos Ecossistema | `feitos/testes-completos-ecossistema/` |
| Validacao Humana Testes Reais | `feitos/validacao-humana-testes-reais/` |

## 🔶 Em execução

| Iniciativa | Local |
|---|---|
| Correcao Pos Auditoria Sem Maquiagem | `fazendo/01-correcao-pos-auditoria-sem-maquiagem/` |
| Direcionamento Estrategico Anti Nih | `fazendo/02-direcionamento-estrategico-anti-nih/` |
| Evolucao Aidd Ops Fase Completa | `fazendo/03-evolucao-aidd-ops-fase-completa/` |

---

**Convenção:** pastas com `00-PROCESSO-E-DECISOES.md` + `NN-<item>.md` são iniciativas multi-item (status = agregado da tabela "Registro de progresso"); arquivos `PLANO-<NOME>.md` soltos são planos de item único (status = linha `**Status:**` do próprio arquivo). Uma iniciativa nova criada direto na raiz de `docs/planos/` (via `plan init`) é normal — a próxima execução deste script já a move para `feitos/`, `fazendo/` ou `a-fazer/` conforme seu status real.
