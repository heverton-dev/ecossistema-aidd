# PROCESSO E DECISOES — seguranca-zero-trust-e-supply-chain

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Origem:** Auditoria de Segurança em Profundidade, Zero-Trust e Supply Chain registrada em `docs/relatorios/SEGURANCA-SUPPLY-CHAIN-BASELINE.md` (2026-09-09).
- **Objetivo Principal:** Fechar vetores críticos de RCE e vazamento de credenciais na execução de código gerado por LLM (Fase 8), introduzir sandbox com variáveis de ambiente restritas e isolamento de processo, corrigir vulnerabilidade de SQL Injection na policy PostgreSQL de RLS, elevar o mecanismo SHA-256 do aidd-enterprise para manifestos assinados com Ed25519 (Zero-Trust autêntico), e blindar a cadeia de suprimentos com hashes criptográficos estritos (`--require-hashes` / `uv.lock`).
- **Limites de Escopo:**
  - Não bloqueia fluxos legítimos de desenvolvimento local; implementa defesas em camadas proporcionais ao risco.
  - Toda regra é auditada por Quality Gates binários determinísticos.
  - Zero tolerância para termos de marketing ("blindagem militar") que não correspondam à cobertura real testada.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | sandbox-nivel-1-subprocess-env-minimo-fase-08 | `01-sandbox-nivel-1.md` |
| 2 | gate-owasp-sobre-output-fase-08 | `02-gate-owasp-sobre.md` |
| 3 | corrigir-interpolacao-sql-set-tenant-pg | `03-corrigir-interpolacao-sql.md` |
| 4 | pin-exato-e-hashes-requirements-lockfile | `04-pin-exato-hashes.md` |
| 5 | manifest-assinado-ed25519-componentes-enterprise | `05-manifest-assinado-ed25519.md` |
| 6 | jwt-hardening-segredo-prod-exp-obrigatorio | `06-jwt-hardening-segredo.md` |
| 7 | hash-artefatos-skills-mcps-dependencias-externas | `07-hash-artefatos-skills.md` |
| 8 | mcp-defensivo-cap-limite-e-env-denylist | `08-mcp-defensivo-cap.md` |
| 9 | rls-fail-closed-auditoria-tabelas-desprotegidas | `09-rls-fail-closed.md` |
| 10 | sandbox-nivel-2-container-modo-isolado | `10-sandbox-nivel-2.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | sandbox-nivel-1-subprocess-env-minimo-fase-08 | ⏳ Rascunho gerado, aguardando aprovacao | `01-sandbox-nivel-1.md` |
| 2 | gate-owasp-sobre-output-fase-08 | ⏳ Rascunho — parte ja implementada (ver auditoria) | `02-gate-owasp-sobre.md` |
| 3 | corrigir-interpolacao-sql-set-tenant-pg | ⏳ Rascunho gerado, aguardando aprovacao | `03-corrigir-interpolacao-sql.md` |
| 4 | pin-exato-e-hashes-requirements-lockfile | ⏳ Rascunho gerado, aguardando aprovacao | `04-pin-exato-hashes.md` |
| 5 | manifest-assinado-ed25519-componentes-enterprise | ⏳ Rascunho gerado, aguardando aprovacao | `05-manifest-assinado-ed25519.md` |
| 6 | jwt-hardening-segredo-prod-exp-obrigatorio | ⏳ Rascunho gerado, aguardando aprovacao | `06-jwt-hardening-segredo.md` |
| 7 | hash-artefatos-skills-mcps-dependencias-externas | ⏳ Rascunho gerado, aguardando aprovacao | `07-hash-artefatos-skills.md` |
| 8 | mcp-defensivo-cap-limite-e-env-denylist | ⏳ Rascunho gerado, aguardando aprovacao | `08-mcp-defensivo-cap.md` |
| 9 | rls-fail-closed-auditoria-tabelas-desprotegidas | ⏳ Rascunho gerado, aguardando aprovacao | `09-rls-fail-closed.md` |
| 10 | sandbox-nivel-2-container-modo-isolado | ⏳ Rascunho gerado, aguardando aprovacao | `10-sandbox-nivel-2.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
