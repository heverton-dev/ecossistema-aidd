# Item 2: Fatias Verticais e Repositórios Isolados na Aplicação

> **Iniciativa:** PLAN-0033-implementacao-arquitetural-vsa  
> **Status:** Pronto para Execução  

---

## 1. Contexto e Diagnóstico

Na aplicação `proj_ctt/planos-ctt-app`, os módulos `frotas`, `encomendas_ctt` e `roteirizacao` estão em `src/modules/`, mas as operações de banco de dados e regras precisam ser segregadas em arquivos `repository.py` dedicados para cada fatia, eliminando qualquer dependência acoplada direta e preparando a aplicação para eventual extração autônoma.

---

## 2. O que será implementado

1. **Repositório de Frotas (`src/modules/frotas/repository.py`):**
   - Extrair persistência e queries da tabela `frotas`.
2. **Repositório de Encomendas (`src/modules/encomendas_ctt/repository.py`):**
   - Extrair persistência e queries da tabela `encomendas_ctt`.
3. **Repositório de Roteirização (`src/modules/roteirizacao/repository.py`):**
   - Extrair persistência e queries da tabela `rotas`.
4. **Atualização dos Services:**
   - Injetar os repositórios nos services de cada fatia.
5. **Frontend Next.js (`web/src/`):**
   - Garantir paridade das fatias com hooks e DTOs tipados.

---

## 3. Critérios de Aceite

- [ ] Arquivos `repository.py` criados em `src/modules/frotas/`, `src/modules/encomendas_ctt/` e `src/modules/roteirizacao/`.
- [ ] Testes unitários da aplicação (`pytest`) passando 100%.
- [ ] Sem queries SQL cruzadas entre módulos.
