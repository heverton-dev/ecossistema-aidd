# Item 3: Teardown, Redeploy e Teste End-to-End

> **Iniciativa:** PLAN-0033-implementacao-arquitetural-vsa  
> **Status:** Pronto para Execução  

---

## 1. Contexto e Diagnóstico

Para assegurar conformidade total com o Protocolo de Testes de Ferramentas (`docs/protocolos/PROTOCOLO-TESTES-FERRAMENTAS.md`):
1. Fazer `git commit` e `push` de todas as alterações arquiteturais.
2. Desinstalar completamente a stack anterior na VPS (remover containers, volumes transitórios e imagens antigas).
3. Fazer novo build limpo e deploy da nova arquitetura.
4. Executar testes ponta a ponta reais com Playwright em todas as URLs.
5. Atualizar o relatório executivo em `docs/teste-end-to-end/`.

---

## 2. O que será implementado

1. **Git Commit & Push:**
   - Commit e push sincronizados em `ecossistema-aidd` e `proj_ctt/planos-ctt-app`.
2. **Teardown e Redeploy na VPS:**
   - Via SSH: `docker stack rm ctt` e limpeza de imagens/build.
   - Sincronização do novo código com repositórios dedicados.
   - `docker build` de ambos os contêineres e `docker stack deploy`.
   - Execução de seed dos 5 veículos e encomendas CTT.
3. **Validação E2E com Playwright:**
   - Testar rotas `/`, `/frotas`, `/encomendas_ctt`, `/roteirizacao`, `/webhooks`, `/mcp`, `/docs`.
4. **Atualização do Relatório:**
   - Atualizar `docs/teste-end-to-end/` com os resultados, screenshots e evidências factuais.

---

## 3. Critérios de Aceite

- [ ] Teardown e deploy limpo executados na VPS com sucesso.
- [ ] Todas as rotas respondendo HTTP 200 e renderizando Next.js com dados reais.
- [ ] Relatório E2E em `docs/teste-end-to-end/` atualizado e comitado.
