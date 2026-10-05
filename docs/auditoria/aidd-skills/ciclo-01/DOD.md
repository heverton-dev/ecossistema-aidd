# Definition of Done: aidd-skills (Auditoria 15-D)

## Metas e Critérios Binários de Aceitação

1. **D1 (Contratos e Regras):**
   A ferramenta `aidd-skills` deve impor convenções de autoria descritas em `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md`.

2. **D3 (Raio de Impacto e Isolamento):**
   Skills devem ser criadas exclusivamente dentro de `componentes/<escopo>/skills/<nome>/SKILL.md`.

3. **D12 (Frugalidade de Contexto):**
   O corpo de cada skill não pode ultrapassar 450 linhas, tendo como alvo ideal ~150 linhas em inglês conciso.

4. **D13 (Quality Gate de Repositório):**
   Os gates determinísticos `gates/G_SKILL_FORMATO.py` e `gates/G_SKILL_ROT.py` devem aprovar as skills com exit 0.
