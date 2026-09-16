# Item 1: Governança e Blueprint VSA no Ecossistema

> **Iniciativa:** PLAN-0033-implementacao-arquitetural-vsa  
> **Status:** Pronto para Execução  

---

## 1. Contexto e Diagnóstico

O ecossistema AIDD prescreve arquitetura modular, mas a separação estrita de Fatias Verticais (Vertical Slice Architecture) com paridade obrigatória entre Frontend e Backend e Repositórios segregados precisa estar formalizada na governança de `tools/aidd-master/` e nos blueprints em `componentes/compartilhado/`.

---

## 2. O que será implementado

1. **Atualização em `tools/aidd-master/AGENTS.md`:**
   - Formalizar o padrão canônico VSA: cada módulo de negócio DEVE possuir `router.py`, `service.py`, `repository.py`, `dtos.py` e `events.py`.
   - Proibição de dependência circular e importações diretas entre fatias no nível de dados.
2. **Atualização do Blueprint em `componentes/compartilhado/`:**
   - Adicionar template de scaffold para novos módulos contendo a árvore canônica de arquivos.

---

## 3. Critérios de Aceite

- [ ] `tools/aidd-master/AGENTS.md` documenta a regra de fatias verticais e repositórios isolados.
- [ ] `python ecossistema.py audit` executa e passa 100% dos gates sem quebras.
