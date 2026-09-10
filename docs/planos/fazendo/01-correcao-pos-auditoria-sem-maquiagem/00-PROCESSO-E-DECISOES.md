# PROCESSO E DECISOES — correcao-pos-auditoria-sem-maquiagem

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Objetivo Principal:** Fechar os achados críticos e de atenção da auditoria "sem maquiagem" de 2026-09-07 (`docs/relatorios/relatorio-auditoria-ecossistema-aidd-sem-maquiagem.html`), reduzir custo de token onde o núcleo de cada ferramenta já é determinístico, e elevar as notas por dimensão (engenharia agêntica, economia de tokens, facilidade de uso, universalidade/anti-lock-in, entrega, determinismo real) ao máximo alcançável de forma honesta.
- **Regra inegociável desta iniciativa:** nenhuma correção pode ser fake/cosmética — cada item tem critério de verificação real (comando, teste ou execução reproduzível) antes de ser marcado como concluído. Subir uma nota "maquiando" telemetria ou rótulo sem mudar o comportamento real invalida o item.
- **Limites de Escopo:** Não inclui decisões não aprovadas por humano; não inclui reescrever ferramentas do zero — é trabalho de correção/hardening sobre o que já existe.

### Modelo/harness sugerido por item

Calibração de partida (não é regra rígida): tarefas mecânicas/determinísticas vão para a camada mais barata do harness escolhido; tarefas que exigem decisão de arquitetura ou de escopo vão para a camada mais forte.

| # | Item | Complexidade | Claude | Antigravity | MiMo |
|---|---|---|---|---|---|
| 1 | Gates rodarem pytest de verdade | Mecânica | Haiku | Gemini 3.1 pro | mimo-v2.5 |
| 2 | Telemetria sempre remedida | Mecânica | Haiku | Gemini 3.1 pro | mimo-v2.5 |
| 3 | G_ZERO_HEADLESS: enforcement real | Arquitetural | Opus | Gemini 3.8 | mimo-v2.5-pro |
| 4 | Reverter CSP relaxado | Moderada | Sonnet | Gemini 3.7 | mimo-v2.5-pro |
| 5 | Remover seed de demo | Mecânica | Haiku | Gemini 3.1 pro | mimo-v2.5 |
| 6 | `enterprise inject` dry-run por padrão | Moderada | Sonnet | Gemini 3.7 | mimo-v2.5-pro |
| 7 | Corrigir gate "blindagem militar" | Decisão de escopo | Opus | Gemini 3.8 | mimo-v2.5-pro |
| 8 | Sincronizar CLI do ops com testes | Moderada | Sonnet | Gemini 3.7 | mimo-v2.5-pro |
| 9 | Porta duplicada + dashboard fabricando resultado | Moderada | Sonnet | Gemini 3.7 | mimo-v2.5-pro |
| 10 | Corrigir CORS inseguro no app gerado | Mecânica | Haiku | Gemini 3.1 pro | mimo-v2.5 |
| 11 | Corrigir deploy Docker do módulo gerado | Moderada | Sonnet | Gemini 3.7 | mimo-v2.5-pro |
| 12 | Prova real de integração multi-ferramenta | Arquitetural | Opus | Gemini 3.8 | mimo-v2.5-pro |
| 13 | Reduzir custo de token no núcleo determinístico | Arquitetural | Opus | Gemini 3.8 | mimo-v2.5-pro |
| 14 | Remover ou ligar código morto de resiliência no enterprise | Decisão de escopo | Opus | Gemini 3.8 | mimo-v2.5-pro |
| 15 | requirements.txt do app gerado pelo generator dessincronizado do código real | Mecânica | Haiku | Gemini 3.1 pro | mimo-v2.5 |

## 1.1 Dependência com `docs/planos/a-fazer/direcionamento-estrategico-anti-nih/`

Revisão feita em 2026-09-07, respondendo à pergunta direta do usuário ("com o estratégico completo, o tático continua útil?"): **sim, a maior parte continua necessária de qualquer forma** — o estratégico troca qual motor sustenta um subsistema (biblioteca madura em vez de código próprio), não corrige comportamento/governança que independe disso. Só alguns itens têm relação real com a Fase 2 (troca de motor) do estratégico:

- **Item 14 original removido** (`Sequenciar as 4 frentes de evolucao-aidd-ops-fase-completa`) — era 100% duplicado da própria Fase 2 do plano estratégico (que já decide "avaliar Coolify/CapRover antes de aprovar as 4 frentes"). Essa decisão vive lá agora, não aqui. **O número 14 foi reaproveitado em 2026-09-07** para um achado novo e não relacionado (código morto de resiliência no enterprise, achado rodando `code-review-graph dead-code` de verdade) — não é o mesmo item, só a mesma numeração livre.
- **Itens 4, 5, 7, 9, 11 — prováveis subprodutos da Fase 2, não garantidos:** se a Fase 2 (segurança → scaffolding → infra do ops) for concluída ANTES destes itens, cada um deve primeiro ser **reproduzido** contra o estado pós-troca — se já estiver corrigido de verdade (não por acidente), o item fecha rápido como "verificado, sem trabalho adicional"; se a migração não cobriu o caso, o item continua sendo a rede de segurança e é implementado normalmente. Nunca marcar como concluído só porque "a Fase 2 deveria ter resolvido" sem reprodução real:
  - Item 4 (CSP): resolve se `secure.py` substituir `templates/core/security.py` com defaults seguros — verificar, não assumir.
  - Item 5 (seed de demo): só resolve se quem migrar pra Cookiecutter lembrar de não carregar o seed — não é automático.
  - Item 7 (gate "blindagem militar"): a Regra de Ouro anti-marketing (item 2 do estratégico) resolve a metade do rótulo; a decisão de aumentar cobertura funcional real do gate continua em aberto de qualquer forma.
  - Item 9 (porta duplicada + dashboard): só resolve se a decisão do estratégico for "adotar Coolify/CapRover". Se for "manter infra própria", este item continua 100% necessário sem alteração.
  - Item 11 (deploy Docker): mesmo caso do item 5 — resolve se a reescrita via Cookiecutter for cuidadosa, não é garantia automática.
- **Item 13 (reduzir custo de token):** a parte de *implementar* pelo menos 2 trocas continua aqui; a parte de *medir antes/depois formalmente* é absorvida pela Fase 3 (reauditoria) do plano estratégico, que já remede tudo depois da troca de motor — não duplicar a remedição nos dois lugares.
- **Itens 1, 2, 3, 6, 8, 10, 12 — sem sobreposição, seguem exatamente como estão.**

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Gates rodarem pytest de verdade (nao so estrutura) | `01-gates-rodarem-pytest-de-verdade-nao-so-estrutura.md` |
| 2 | Telemetria de testes sempre remedida, nunca gravada estatica | `02-telemetria-de-testes-sempre-remedida-nunca-gravada-estatica.md` |
| 3 | G_ZERO_HEADLESS: enforcement real, nao so grep de string | `03-g-zero-headless-enforcement-real-nao-so-grep-de-string.md` |
| 4 | Reverter CSP relaxado no template compartilhado (unsafe-inline/CDN) | `04-reverter-csp-relaxado-no-template-compartilhado-unsafe-inlinecdn.md` |
| 5 | Remover seed de demo (webhook.site + secret hardcoded) da geracao padrao | `05-remover-seed-de-demo-webhooksite-secret-hardcoded-da-geracao-padrao.md` |
| 6 | enterprise inject: dry-run real por padrao antes de gravar no working tree | `06-enterprise-inject-dry-run-real-por-padrao-antes-de-gravar-no-working-tree.md` |
| 7 | Corrigir gate de seguranca rotulado blindagem militar (rotulo ou cobertura real) | `07-corrigir-gate-de-seguranca-rotulado-blindagem-militar-rotulo-ou-cobertura-real.md` |
| 8 | Sincronizar CLI do aidd-ops com a suite de testes | `08-sincronizar-cli-do-aidd-ops-com-a-suite-de-testes.md` |
| 9 | Corrigir porta duplicada no compose gerado e parar dashboard de fabricar resultado de preflight | `09-corrigir-porta-duplicada-no-compose-gerado-e-parar-dashboard-de-fabricar-resultado-de-preflight.md` |
| 10 | Corrigir CORS inseguro (allow_origins=* + allow_credentials=True) no app gerado pelo generator | `10-corrigir-cors-inseguro-allow-origins-allow-credentialstrue-no-app-gerado-pelo-generator.md` |
| 11 | Corrigir deploy Docker do modulo gerado (pip install ausente, nginx/ inexistente, secret em texto plano) | `11-corrigir-deploy-docker-do-modulo-gerado-pip-install-ausente-nginx-inexistente-secret-em-texto-plano.md` |
| 12 | Prova real de integracao multi-ferramenta no teste integrado | `12-prova-real-de-integracao-multi-ferramenta-no-teste-integrado.md` |
| 13 | Reduzir custo de token nas ferramentas de nucleo deterministico (master/enterprise/ops/CLI) | `13-reduzir-custo-de-token-nas-ferramentas-de-nucleo-deterministico-masterenterpriseopscli.md` |
| 14 | Remover ou ligar codigo morto de resiliencia no enterprise | `14-remover-ou-ligar-codigo-morto-de-resiliencia-no-enterprise.md` |
| 15 | requirements.txt do app gerado pelo generator dessincronizado do codigo real | `15-requirementstxt-do-app-gerado-pelo-generator-dessincronizado-do-codigo-real.md` |
| 16 | XSS armazenado real em `get_studio_html` (núcleo compartilhado) | `16-xss-armazenado-real-em-get_studio_html-nucleo-compartilhado.md` |
| 17 | CLI aidd_inject convertida de argparse para click pela metade | `17-cli-aidd-inject-convertida-argparse-para-click-pela-metade.md` |
| 18 | CLI do aidd-forge convertida de argparse para click pela metade (suíte quebrada) | `18-cli-forge-argparse-para-click-pela-metade-suite-quebrada.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Gates rodarem pytest de verdade (nao so estrutura) | ✅ Concluído e auditado | `01-gates-rodarem-pytest-de-verdade-nao-so-estrutura.md` |
| 2 | Telemetria de testes sempre remedida, nunca gravada estatica | ⏳ Rascunho gerado, aguardando aprovacao | `02-telemetria-de-testes-sempre-remedida-nunca-gravada-estatica.md` |
| 3 | G_ZERO_HEADLESS: enforcement real, nao so grep de string | ⏳ Rascunho gerado, aguardando aprovacao | `03-g-zero-headless-enforcement-real-nao-so-grep-de-string.md` |
| 4 | Reverter CSP relaxado no template compartilhado (unsafe-inline/CDN) | ⏳ Rascunho gerado, aguardando aprovacao | `04-reverter-csp-relaxado-no-template-compartilhado-unsafe-inlinecdn.md` |
| 5 | Remover seed de demo (webhook.site + secret hardcoded) da geracao padrao | ⏳ Rascunho gerado, aguardando aprovacao | `05-remover-seed-de-demo-webhooksite-secret-hardcoded-da-geracao-padrao.md` |
| 6 | enterprise inject: dry-run real por padrao antes de gravar no working tree | ⏳ Rascunho gerado, aguardando aprovacao | `06-enterprise-inject-dry-run-real-por-padrao-antes-de-gravar-no-working-tree.md` |
| 7 | Corrigir gate de seguranca rotulado blindagem militar (rotulo ou cobertura real) | ⏳ Rascunho gerado, aguardando aprovacao | `07-corrigir-gate-de-seguranca-rotulado-blindagem-militar-rotulo-ou-cobertura-real.md` |
| 8 | Sincronizar CLI do aidd-ops com a suite de testes | ⏳ Rascunho gerado, aguardando aprovacao | `08-sincronizar-cli-do-aidd-ops-com-a-suite-de-testes.md` |
| 9 | Corrigir porta duplicada no compose gerado e parar dashboard de fabricar resultado de preflight | ⏳ Rascunho gerado, aguardando aprovacao | `09-corrigir-porta-duplicada-no-compose-gerado-e-parar-dashboard-de-fabricar-resultado-de-preflight.md` |
| 10 | Corrigir CORS inseguro (allow_origins=* + allow_credentials=True) no app gerado pelo generator | ⏳ Rascunho gerado, aguardando aprovacao | `10-corrigir-cors-inseguro-allow-origins-allow-credentialstrue-no-app-gerado-pelo-generator.md` |
| 11 | Corrigir deploy Docker do modulo gerado (pip install ausente, nginx/ inexistente, secret em texto plano) | ⏳ Rascunho gerado, aguardando aprovacao | `11-corrigir-deploy-docker-do-modulo-gerado-pip-install-ausente-nginx-inexistente-secret-em-texto-plano.md` |
| 12 | Prova real de integracao multi-ferramenta no teste integrado | ⏳ Rascunho gerado, aguardando aprovacao | `12-prova-real-de-integracao-multi-ferramenta-no-teste-integrado.md` |
| 13 | Reduzir custo de token nas ferramentas de nucleo deterministico (master/enterprise/ops/CLI) | ⏳ Rascunho gerado, aguardando aprovacao | `13-reduzir-custo-de-token-nas-ferramentas-de-nucleo-deterministico-masterenterpriseopscli.md` |
| 14 | Remover ou ligar codigo morto de resiliencia no enterprise | ⏳ Rascunho gerado, aguardando aprovacao | `14-remover-ou-ligar-codigo-morto-de-resiliencia-no-enterprise.md` |
| 15 | requirements.txt do app gerado pelo generator dessincronizado do codigo real | ⏳ Rascunho gerado, aguardando aprovacao | `15-requirementstxt-do-app-gerado-pelo-generator-dessincronizado-do-codigo-real.md` |
| 16 | XSS armazenado real em `get_studio_html` (núcleo compartilhado) | ✅ Concluído e auditado (2026-09-09) | `16-xss-armazenado-real-em-get_studio_html-nucleo-compartilhado.md` |
| 17 | CLI aidd_inject convertida de argparse para click pela metade | ✅ Concluído — decisão revista na mesma data: MANTER CLICK (migração completa pelo item 10 do plano estratégico anti-NIH, 929 testes verdes, `click` declarado em requirements.txt) (2026-09-09) | `17-cli-aidd-inject-convertida-argparse-para-click-pela-metade.md` |
| 18 | CLI do aidd-forge convertida de argparse para click pela metade (suíte quebrada) | ✅ Concluído — decisão revista na mesma data: MANTER CLICK (migração completa pelo item 10 do plano estratégico anti-NIH, 196 testes verdes, `click` declarado em setup.py) (2026-09-09) | `18-cli-forge-argparse-para-click-pela-metade-suite-quebrada.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real. Item 14 removido em 2026-09-07 por duplicidade confirmada com a Fase 2 de `docs/planos/a-fazer/direcionamento-estrategico-anti-nih/` (ver §1.1). Item 15 adicionado em 2026-09-07, achado real investigando o item 7 do plano `direcionamento-estrategico-anti-nih`.
