# Definição de Pronto (Definition of Done - DoD) — skills-ddd (Ciclo 01)

> Critérios de aceite para a extração, criação e integração de Manuais Canônicos e Skills derivadas de `skills-ddd-clean`.  
> Fonte canônica das skills: `componentes/compartilhado/skills/<skill>/SKILL.md`.  
> Fonte canônica dos manuais: `docs/protocolos/<manual>.md`.  

---

## Critérios Obrigatórios de Aceite

1. **DoD 1: Manual Canônico de DDD Tático & Invariantes no Monólito VSA (D1 / D8)**
   - O arquivo `docs/protocolos/PADRAO-DDD-CLEAN-VSA.md` existe e define as regras para Entidades, Value Objects, Aggregates, Domain Services e Repositórios dentro de fatias verticais VSA.
   - Fornece exemplos desacoplados e tipados em Python (backend) e TypeScript (frontend), sem dependências proprietárias externas.
   - Testado e validado por `tests/test_manual_ddd_clean_vsa.py` (exit 0).

2. **DoD 2: Manual Canônico de Leitura Otimizada e CQRS (D8 / D14)**
   - O arquivo `docs/protocolos/PADRAO-CONSULTAS-LEITURA-CQRS.md` existe e define a segregação entre operações de comando (invariantes de escrita) e operações de consulta (leitura direta otimizada em SQL).
   - Testado e validado por `tests/test_manual_cqrs_leitura.py` (exit 0).

3. **DoD 3: Atualização de Nomenclatura Frontend na Stack Ouro (D1 / D3)**
   - O arquivo `docs/protocolos/PADRAO-OURO-STACK-TECNOLOGICA.md` é atualizado incorporando a convenção padronizada de sufixos de arquivo para o frontend Next.js (`.component.tsx`, `.page.tsx`, `.context.tsx`, `.hook.ts`, `.schema.ts`).
   - Testado e validado por `tests/test_convencao_nomenclatura_frontend.py` (exit 0).

4. **DoD 4: Nova Skill Canônica `aidd-frontend-forms` (D2 / D3)**
   - A pasta `componentes/compartilhado/skills/aidd-frontend-forms/` existe com `SKILL.md` em conformidade estrita com `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md`.
   - Contém instruções e templates determinísticos para formulários Next.js com Zod e React Hook Form.
   - Testada e validada por `tests/test_skill_frontend_forms.py` (exit 0).

5. **DoD 5: Sincronização Universal e Verificação Multi-Harness (D15)**
   - Comando `python ecossistema.py components sync --tipo todos` executado com sucesso.
   - Verificação `python ecossistema.py components verify` retorna exit 0 sem drifts entre harnesses.

6. **DoD 6: Quality Gate Final do Ecossistema**
   - Execução de `python ecossistema.py audit` retorna exit code 0 sem quebra de portas de integridade (`G_DOCS_ROT.py`, `G_SKILL_FORMATO.py`, `G_SKILL_ROT.py`, `G_STACK_PADRAO_OURO.py`).
