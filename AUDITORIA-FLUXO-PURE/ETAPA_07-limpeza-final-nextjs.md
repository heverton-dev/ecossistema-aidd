# Auditoria de Etapa: Limpeza final do Next.js (passo 5, Ticket R5 da ETAPA_06)

### [RECURSO]: Guarda `tests/test_sem_nextjs_vivo.py` (TDD Red-Green)
- **Ordem de Execução:** após o passo 4 (Docker). Escrito **antes** de qualquer limpeza.
- **Ação Executada:** teste que varre `git ls-files -co --exclude-standard` e reprova qualquer rastro vivo: `next.js`, `next/link|navigation|image|font|router`, `NEXT_PUBLIC`, `eslint-config-next`, `next.config`, `NextJSExporter`, `nextjs_exporter`, `nextjs_app_router`, `nextjs_typescript`, `nextjs-on-cloudflare` e a dependência `"next": "<versão>"`. Linhas que declaram a abolição ("abolido", "abolição") são aceitas.
- **Critério (decidido e registrado):** fora da varredura: documentos históricos datados (`docs/auditoria`, `melhorias`, `reports`, `relatorios`, `teste-end-to-end`, `issues`, `explicacoes`, `testes`, `oficiais`, `secoes`, `features`, `livros`, `mapas-visuais`, `secoes/`, `AUDITORIA-FLUXO-PURE/`, `projetos/`, `.mimocode/plans/`) e as listas defensivas de pasta de build `.next` (inertes; no fluxo `freedom` servem para analisar projetos externos). Permitidos por serem produtos de terceiros que são apps Next.js: `ninerouter-stack.yml` (9Router) e os textos do `aidd-ops` sobre Cal.com/ERPNext. Permitidos por provarem a rejeição: o próprio guarda, `test_forge_templates_padrao_ouro`, `test_g_stack_padrao_ouro`, `test_tanstack_exporter`, `test_frontend_stack_tanstack`.
- **Entrega / Artefato Gerado:** guarda.
  - *Caminho Exato (100% concluído):* `tests/test_sem_nextjs_vivo.py`.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Red: **225 rastros** em 39+ arquivos (exit 1). Green: exit 0 depois da limpeza.
  - *Falhas / Anomalias:* nenhuma no guarda.

### [RECURSO]: Limpeza
- **Ação Executada:** removidos `nextjs_exporter.py` (3 cópias) e `test_nextjs_exporter.py`; `MANIFEST.json`, `CATALOGO.json` (128 peças) e baseline do drift atualizados; selos re-calculados só nas 5 peças que alterei (`G_CONTRACTS`, `G_STACK_PADRAO_OURO`, os 2 schemas de handoff, `design_catalog`); `G_CONTRACTS` reescrito (rejeita a dependência `next` e exige o frontend TanStack completo: `vite.config.ts`, `tsconfig.json`, `index.html`, `src/main.tsx`, `src/router.tsx`); schemas de handoff só aceitam `tanstack_router` e `tanstack_router_typescript_tailwind`; prompt da fase 08 do `aidd-pure` (`BLOCO_REGRA_UI`) e o `AGENTS.md` da fase passam de Next.js para TanStack Router + Vite; `AGENTS.md`, `README.md`, `MEMORY.md`, protocolos vivos, manual do usuário, 3 skills (`aidd-frontend-forms`, `aidd-open`, `aidd-pure`) e seus testes; skill externa `nextjs-on-cloudflare` removida do manifesto de dependências e do `.gitignore`.
- **Entrega / Artefato Gerado:** repositório vivo sem Next.js.
  - *Caminho Exato (100% concluído):* ver `git diff --stat` do clone.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim.
  - *Falhas / Anomalias:*
    - *Ocorrência (erro meu):* a substituição em lote trocou "Next.js" por "TanStack Router" **também nas frases que declaram a abolição**, invertendo o sentido ("TanStack Router foi formalmente abolido"). Isso atingiu a mensagem de rejeição do `G_STACK_PADRAO_OURO` (3 cópias), a do `G_NOVE_CAMADAS_MERCADO`, `README.md` (2 linhas), `AGENTS.md:110`, um comentário de teste e um docstring meu em `test_provision_project`. Foi pego pelo teste `test_stack_morde_quando_usa_next_abolido` (falhou) e por uma varredura de linhas com "abol" e "TanStack Router". As 18+ linhas foram restauradas e o selo do catálogo recalculado.
    - *Localização Exata do Erro:* `G_STACK_PADRAO_OURO.py:11,135,137` (componentes, `fluxo-01-pure` e template do forge), `G_NOVE_CAMADAS_MERCADO.py:100`, `README.md:17,200`, `AGENTS.md:110`.
  - *Ação Corretiva Cirúrgica:* restauração por frase, mais teste e varredura de conferência.
  - *Os espelhos das 3 skills* (18 arquivos, 6 por skill) foram atualizados por cópia direta, só depois de confirmar que cada um era byte-idêntico à fonte antiga; o `components sync` completo não foi usado porque `components verify` já acusa 103 problemas de espelhos neste clone (arquivos locais dos harnesses que o clone não tem) que não são desta mudança.

### [RECURSO]: Verificação
- **Ação Executada:** suítes após a limpeza; depois da correção das frases, repetidos os gates e os testes afetados.
- **Status & Diagnóstico:**
  - *Sucesso:* Sim. Master **457 passed, 3 skipped**; enterprise **389 passed, 3 skipped**; `aidd-open` **28 passed**; raiz (guarda, forge, skill de forms, orquestrador, livro) **35 passed**; gates do `fluxo-01-pure` **24 passed** (após a correção); `G_DRIFT_NUCLEO_COMPARTILHADO` exit 0.
  - *Falhas / Anomalias:* rodar `tests/` e `fluxo-01-pure/gates` **na mesma sessão** do pytest dá erro de coleta (dois arquivos com o mesmo nome em pastas diferentes: `test_g_nove_camadas_mercado.py` e `test_g_template_tanstack_offline.py`); não é desta mudança, rodam separados (Ticket 5-C).

## TICKETS

### Ticket R5: Resíduos de Next.js ainda vivos — RESOLVIDO NO CLONE
- **Falha:** 225 rastros vivos em ~68 arquivos.
- **Artefato de Handoff:** os arquivos listados no relatório.
- **Requisito TDD (Red):** `pytest tests/test_sem_nextjs_vivo.py` → exit 1 (225 rastros).
- **Implementação Técnica:**
  - Remoções, reescrita do `G_CONTRACTS`, schemas, prompt da fase 08, docs, skills e testes.
- **Verificação (Green):** o guarda com exit 0; suítes e gate de drift com exit 0.
- **Construtor Prompt (EN):**
  - Run `python -m pytest tests/test_sem_nextjs_vivo.py -q` and assert exit 0; never replace framework names inside abolition statements.

### Ticket 5-A: Skill local `nextjs-on-cloudflare` instalada no original — ABERTO
- **Falha:** o manifesto não a declara mais, mas as cópias locais instaladas (`.agents/`, `.claude/`, `.codebuddy/skills/nextjs-on-cloudflare`) continuam no motor original e passam a aparecer como não rastreadas (a regra do `.gitignore` foi removida). No clone já foram apagadas.
- **Artefato de Handoff:** diretórios acima, no original.
- **Requisito TDD (Red):** `git status` do original lista essas pastas como não rastreadas depois do merge.
- **Implementação Técnica:** apagar as cópias locais no original (decisão do usuário).
- **Verificação (Green):** `git status` limpo.
- **Construtor Prompt (EN):**
  - After merging, delete the three local `nextjs-on-cloudflare` skill folders in the original checkout and confirm `git status` is clean.

### Ticket 5-B: `components verify` com 103 problemas de espelhos neste clone — ABERTO (pré-existente)
- **Falha:** o clone não tem os arquivos locais dos harnesses (hooks e outros), então `components verify` reprova.
- **Artefato de Handoff:** `ecossistema.py components`.
- **Requisito TDD (Red):** `python ecossistema.py components verify` num clone novo → exit 1.
- **Implementação Técnica:** decidir se o `bootstrap` deve gerar esses espelhos ou se o `verify` deve ignorar o que é local.
- **Verificação (Green):** `verify` com exit 0 num clone novo.
- **Construtor Prompt (EN):**
  - Reproduce `components verify` failing in a fresh clone and decide whether bootstrap should create the local mirrors or verify should skip local-only files; assert exit 0 afterwards.

### Ticket 5-C: Nomes de teste repetidos entre `tests/` e `gates/` (Refere-se à coleta do pytest) — ABERTO (pré-existente)
- **Falha:** `test_g_nove_camadas_mercado.py` e `test_g_template_tanstack_offline.py` existem em `tests/` e em `fluxo-01-pure/gates/`; na mesma sessão o pytest erra na coleta.
- **Artefato de Handoff:** os 4 arquivos.
- **Requisito TDD (Red):** `pytest tests modulos/02-triade-motores/fluxo-01-pure/gates` → exit 2.
- **Implementação Técnica:** renomear um de cada par ou isolar por pacote.
- **Verificação (Green):** o mesmo comando com exit 0.
- **Construtor Prompt (EN):**
  - Rename one file of each duplicated pair (or package them) so a single pytest session collects both folders; assert exit 0.
