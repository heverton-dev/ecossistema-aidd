# RELATÓRIO DE ACHADOS — TESTE DE USABILIDADE DO ECOSSISTEMA-AIDD

> **Prefixo de data:** 22-09-2026
> **Projeto analisado:** `C:\Users\trcnologia\Desktop\proj_app-frotas`
> **Escopo:** Jornada completa `git clone` → entrega do projeto (Fluxo 02 / `aidd-open`)
> **Insumos:** `RELATORIO-SESSAO-AIDD-FROTAS.md`, estrutura física do workspace, `AGENTS.md`, `MEMORY.md`, `ecossistema.py`, `docs/livros/` (propósito canônico)
> **Propósito de referência:** “meta-repositório de engenharia de software assistida por agentes que transforma uma intenção em linguagem natural em um sistema completo, testado, auditado e implantado”, com saída “PT-BR de padrão alto”, dupla fala “Na Festa / Na Casa” e anti-jargão (`docs/livros/partes/01-macro.md`, `MINI-LIVRO-DO-ZERO-AO-APP-PRONTO.md`, `A-CASA-COMPLETA-DO-ECOSSISTEMA.md`)

---

## 0. Sumário executivo

A sessão de usabilidade **entregou tecnicamente** o que a Tríade promete: em 59 minutos, de clone a app rodando, com gates em 100%, testes reais, Quarteto Sine Qua Non ativo e desmantelamento do lock-in Lovable. O **modo como a entrega chega e se apresenta ao usuário final** fracassou em 4 eixos declarados no teste e em mais 5 achados colaterais desta auditoria:

| # | Achado | Severidade |
|---|---|---|
| A1 | Comando de sincronização informado ao usuário está incompleto e a “correção” em circulação também não existe no parser | **Crítica** |
| A2 | Linguagem dos outputs é técnica e jargônica; regra de saída simples não vale para CLI/docs e está desligada no harness testado | **Crítica** |
| A3 | Repositório clonado inflado: 221 MB, 8.186 arquivos, ~80% de peso dev-only do ecossistema | **Alta** |
| A4 | Projeto gerado nasce aninhado e avulso (3–4 raízes coexistindo; backend soterrado em 4 níveis) | **Crítica** |
| A5 | Entrega fragmentada: legado e gerado sem ponto de entrada único | **Alta** |
| A6 | Divergência raiz entre livro (projeto irmão via `--pasta ../proj`) e comportamento real (`ecossistema-aidd/projetos/`) | **Alta** |
| A7 | Remoção de lock-in parcial (Supabase e `.lovable/` residuais) | **Média** |
| A8 | Fronteiras Git confusas: 3 repositórios internos, zero versionamento no workspace de entrega | **Média** |
| A9 | Artefatos de auditoria verbosamente jargônicos: o usuário leigo não consegue auditar a própria entrega | **Média** |

---

## 1. Propósito declarado (baseline dos achados)

Dos livros canônicos, extraem-se 5 critérios que este relatório usa como régua:

1. **Resultado:** sistema completo, testado, auditado e implantado — não “código que parece pronto”.
2. **Idioma:** PT-BR de padrão alto, dupla fala (metáfora simples no chat, comando real na “Casa”), proibição de jargão não explicado.
3. **Comandos:** cadeia curta e copiável — clone → `preflight-host` → entrevista → spec → planner → fluxo → audit → rodar.
4. **Topologia:** o projeto do usuário nasce **fora** do clone, em pasta irmã (`--pasta ../proj_x`); o monorepo do ecossistema é ferramenta, não o produto.
5. **Peso do repositório:** o clone deve trazer o núcleo funcional — o restante é responsabilidade de quem mantém o ecossistema.

---

## 2. Achados

### A1 — Comando de sincronização informado ao usuário está incompleto

**Análise completa.**
O usuário tentou sincronizar componentes e recebeu orientação incompleta. O dispatch real de `ecossistema.py` (linhas ~1149–1191) aceita o subcomando `components`, **não** aceita `sync` solto e **não possui** a flag `--tipos`. O único caminho funcional é:

```bash
python ecossistema.py components sync --tipo todos
```

(`--tipo` é `required=True` em `ecossistema.py:436` e `scripts/gestor_componentes.py:841`.) A mesma exigência vale para `components verify --tipo todos`. A própria sessão de teste confirma o comando que funcionou: `components sync --tipo todos` (relatório da sessão, Etapa 0).

A forma abreviada e quebrada está gravada nas fontes que o agente lê como verdade:

- `MEMORY.md:33` → ``python ecossistema.py components sync`` **sem `--tipo`**
- `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md:181` → idem
- `docs/livros/21-09-2026_LIVRO-…:429,1576,2812`, `docs/livros/partes/05-transversais.md:17`, `docs/melhorias/…venture-os.md:196` (`componentes sync` — subcomando inexistente)

**Observação de honestidade (Lei #8):** a correção circularmente informada neste teste, `python ecossistema.py --tipos todos`, **também não existe** no parser (`--tipos`: 0 ocorrências no repositório). Existem, portanto, **duas formas erradas em circulação** e apenas uma forma canônica.

**O que está correto.**
- O motor `components sync --tipo todos` funciona: 91 componentes sincronizados com SHA-256 idêntico.
- Existem skills corretas (`componentes-runner/SKILL.md:30,43`, `aidd-skills`, `aidd-mcp`) que já ensinam `--tipo todos`.
- O manifesto e a arquitetura fonte→destino estão bem definidos (`componentes/` é fonte; `.claude/`, `.gemini/` etc. são destinos gerados).

**O que está errado.**
- Documentação canônica (MEMORY + referência de protocolo + livros) ensina a forma sem `--tipo`; o agente colapsa para `ecossistema.py sync` e o usuário recebe erro.
- Não há alias `sync` nem flag `--tipos`, nem mensagem de erro que sugira o comando certo.
- Nenhum gate captura a forma abreviada (`G_DOCS_ROT` / consistência de CLI não varrem esse padrão).

**Como corrigir.**
1. Aliasing no parser: `sync` → atalho de `components sync`; aceitar `--tipos` como sinônimo de `--tipo`; quando `--tipo` vier ausente, **default implícito `todos`** com aviso de 1 linha (em vez de erro).
2. Mensagem de erro didática: `Erro: use "python ecossistema.py components sync --tipo todos".` (a própria dica já é a correção).
3. Corrigir de imediato `MEMORY.md:33` e `AGENTS-REFERENCIA-COMPLETA.md:181` + livros/planos com a forma completa.
4. Novo gate determinístico (ex.: `G_SYNC_CMD_ROT`): falha se qualquer doc canônico contiver `components sync` sem `--tipo`/`todos`, ou `ecossistema.py sync`/`--tipos` não mapeado.

---

### A2 — Linguagem técnica e jargão nos outputs violam a regra de saída simples

**Análise completa.**
O teste declara fricção: os outputs de chat são “extremamente técnicos, cheios de jargões”. A auditoria confirma três causas estruturais:

1. **Escopo da regra.** No `AGENTS.md`, a regra de formato de saída é a **Rule 10** (linhas 13–18: “One top sentence… Forbidden: … unexplained jargon”), enquanto a **Lei #10** (linha 59) é o *Quarteto Sine Qua Non* (`/api`, `/webhook`, `/mcp`, `/docs`) — nada de idioma. A **Lei #4** é a de idioma (“dense PT-BR user responses only when requested”). Há, portanto, **confusão de nomenclatura** que já por si só desorienta quem tenta cumprir a regra.
2. **Cobertura parcial.** O hook `.claude/hooks/regra10_check.py` audita **apenas a última resposta do assistente** (chat). CLI, `README.md`, mensagens dos gates, relatórios de sessão e docs **não são cobertos** por nenhuma regra de linguagem simples.
3. **Harness desligado.** O teste rodou no **Antigravity IDE (Gemini)**. O `GEMINI.md:4–8` redige a “Mandatory Answer Shape (Rule 10 / Law #4)” **em inglês técnico** e `GEMINI.md:10` declara o hook **indisponível** — “compliance is maintained by convention”. Ou seja: no harness exato do teste, **nada fiscaliza** a linguagem.

Jargão real de superfície ao usuário final: `README.md:79` (“Universal Convergence Funnel… Quarteto Sine Qua Non”), `README.md:87` (“context-purge… Quality Gates”), `README.md:91–92` (“SHA-256… drift… Zero-Trust… Hardening SSH/Ansible”), `ecossistema.py:131` (“Meta-Orquestrador Unificado de Engenharia Agêntica”), saídas de gates (`G_QUARTETO_SINE_QUA_NON.py:205`). Termos dominantes: harness, quality gates, drift, handoff, worktree, VSA/fatias verticais, pipeline, orquestrador, preflight/E2E, BDD/SDD.

**O que está correto.**
- A Rule 10 existe, é objetiva e proíbe explicitamente jargão não explicado.
- O livro prevê a dupla fala “Na Festa / Na Casa” — conceito certo para usuário leigo.
- A sessão em PT-BR foi conduzida e os artefatos foram gerados (funcionalidade ≠ clareza).
- O gate `G_IDIOMA_LEI_4` prova que mordem quando o alvo é o certo (`docs/issues/*.md`).

**O que está errado.**
- Usuário leigo recebe prompts e docs em jargão de engenharia (VSA, handoff, drift, Quarteto Sine Qua Non) sem tradução.
- Regra de saída simples **não se aplica** a CLI, README, gates e relatórios — justamente as superfícies que o leigo lê.
- No Antigravity/Gemini o hook está off e a forma de resposta está em inglês → o teste de usabilidade mediu o pior cenário de conformidade.
- “Lei #10” virou sinônimo ambíguo (formato × Quarteto), gerando instrução contraditória.

**Como corrigir.**
1. **Renomear/rotular sem ambiguidade:** `Rule 10 (Formato de Resposta)` e `Lei #10 (Quarteto)` em todos os harness files; nunca citar só “Lei #10” quando o assunto for idioma.
2. **Modo “usuário leigo”:** variável/preflight (`python ecossistema.py preflight-host` com perfil `leigo`) que instrui o agente a: (a) uma frase simples; (b) no máximo N bullets sem sigla; (c) toda sigla traduzida na primeira ocorrência; (d) comandos sempre completos e copiáveis.
3. **Reescrever `GEMINI.md` em PT-BR simples** (hoje o harness do teste recebe a regra em inglês) e implementar equivalente leve do `regra10_check` para Gemini (ou checagem via gate no fim do fluxo, quando o hook não existe).
4. **Estender a regra de idioma às superfícies lidas pelo usuário:** README, `--help` da CLI e saída dos gates em PT-BR simples; gate `G_USER_FACING_PTBR` varrendo README/help.
5. Glossário obrigatório no `/docs` gerado (Quarteto já entrega a página — usar `docs/glossario` com termo → frase do dia a dia).

---

### A3 — Repositório clonado inflado com arquivos e diretórios dev-only

**Análise completa.**
O clone em `proj_app-frotas\ecossistema-aidd` tem **221 MB e 8.186 arquivos**. O núcleo funcional necessário ao usuário final (`ecossistema.py`, `gates/`, `core/`, `componentes/`, `scripts/`, `tools/` dos motores, `requirements.txt`, `README.md`, `LICENSE`) convive com peso claramente de **desenvolvimento interno do ecossistema**:

| Artefato no clone | Tamanho/peso | natureza |
|---|---|---|
| `.git/` (histórico completo do meta-repo) | 27 MB | manutenção |
| `docs/` (livros, `relatorios/`, `reports/`, `explicacoes/` com imagens, manuais PDF, `teste-end-to-end/`, `planos/`) | 20 MB | conteúdo interno/histórico |
| `componentes/` | 20 MB | **core** (fonte do sync — manter) |
| `tools/` (8 motores) | 17 MB | **core** dos fluxos — manter |
| `tests/`, `testes/`, `test_verify.db` (69 KB), `verify_check.db` (65 KB) | — | teste do próprio ecossistema + **bancos de teste commitados** |
| `requirements-dev.txt/.lock`, `pytest.ini`, `.pre-commit-config.yaml`, `.secrets.baseline` | — | toolchain dev |
| `__pycache__/`, `.pytest_cache/`, `.worktrees/`, `.ade_tmp/` | — | resíduo de execução |
| `PLANO-EXECUCAO-ESTRUTURADO.json`, `MEMORY.md` (memória do ecossistema) | — | estado interno |
| Configs multi-harness na raiz (`CLAUDE.md`, `GEMINI.md`, `CODEX.md`, `MIMOCODE.md`, `OPENCODE.md`, `mimocode.jsonc` + 9 diretórios `.*`) | — | **regeneráveis** pelo próprio `components sync` (livros: “destinos gerados, nunca fontes”) |

**O que está correto.**
- O núcleo funcional **está todo presente** — o fluxo rodou de ponta a ponta a partir do clone (prova: sessão completa bem-sucedida).
- `componentes/` e `tools/` são de fato necessários (sync + motores da Tríade) — não são “peso morto”.
- Nenhum segredo privado vazado (`chaves/` contém apenas chave pública `ed25519_public.json`, 290 B).
- `pc_final.log` e artefatos sujos óbvios não foram versionados.

**O que está errado.**
- Bancos de teste (`*.db`), `requirements-dev*`, `pytest.ini`, planos executores e `__pycache__` **não têm lugar** em distribuição ao usuário final.
- `docs/` carrega históricos, relatórios e livros ilustrados (20 MB) — viola a própria Lei #12/Docs Rot no espírito de “docs vivos canônicos”, e infla o clone.
- Histórico Git completo (27 MB) via `git clone` padrão para quem só quer usar a ferramenta.
- Diretórios de harness regeneráveis são entregues como se fossem fonte — o próprio livro diz que não são.

**Como corrigir.**
1. **`.gitattributes` com `export-ignore`** para artefatos dev-only (`tests/`, `testes/`, `*.db`, `requirements-dev*`, `pytest.ini`, `__pycache__`, `.worktrees`, `.ade_tmp`, planos executores) + documentar `git archive`/release.
2. **Perfil de distribuição `core`:** `python ecossistema.py package --perfil usuario` gera pacote/zip ou instrução de `git clone --depth 1` + sparse-checkout só com `ecossistema.py gates/ core/ componentes/ scripts/ tools/ requirements.txt README.md LICENSE`.
3. Mover `docs/relatorios`, `docs/reports`, `docs/livros` (PDFs/imagens) para release assets ou site de documentação — no clone, só `docs/protocolos/` + schemas ativos (coerente com Lei #12).
4. `.gitignore` explícito para `*.db`, `__pycache__/`, `.pytest_cache/`, `.worktrees/`, `.ade_tmp/`; remover da árvore os resíduos já commitados.
5. Gate `G_PACOTE_CORE` (Lei #13): falha se a release contiver `*.db`, `requirements-dev*` ou `docs/relatorios/`.

---

### A4 — Projeto gerado nasce aninhado e avulso ao projeto legado

**Análise completa.**
O teste clonou **dentro** do workspace do projeto existente e a execução do fluxo produziu a topologia observada:

```
proj_app-frotas/                          ← raiz do workspace do usuário (SEM git)
├── RELATORIO-SESSAO-AIDD-FROTAS.md
├── proj_app/                             ← projeto legado (SEM git; ~571 MB)
└── ecossistema-aidd/                     ← clone da ferramenta (COM git, 221 MB)
    └── projetos/
        └── logistica-frotas-ctt/         ← “projeto” (COM git, interno)
            └── proj_logistica-frotas-ctt/ ← backend real (COM git)
                ├── src/server.py, src/modules/, frontend/ (Next.js), tests/, Docker
```

Resultado: **três projetos num único local** e o backend enterrado em **4 níveis de profundidade**. O usuário leigo não tem como saber onde “está o meu app”. Os comandos de auditoria do próprio relatório da sessão exigem `cd .../ecossistema-aidd/projetos/logistica-frotas-ctt` — o produto final fica dentro da ferramenta, ao contrário do cósmo dos livros.

**O que está correto.**
- O gerador **funciona**: backend FastAPI com fatias VSA, frontend Next.js, Docker e Quarteto foram criados e validados (notas 9–10 no `PLAN-0037`).
- Há separação lógica `projetos/<nome>` dentro do ecossistema — modelo aceitável para quem usa o ecossistema como IDE de fábrica (caso o usuário *queira* monorepo de fábrica).
- O relatório da sessão documentou os caminhos (auditável por quem lê com calma).

**O que está errado.**
- Contradiz os livros: o projeto deve nascer **irmão** do clone (`--pasta ../proj_x`, `02-fluxos.md:143–154`), não **dentro** dele.
- Quando o clone é feito *dentro* de um projeto já existente, o fluxo **não detecta** o legado nem devolve a entrega para a raiz do workspace — cria a ilha `ecossistema-aidd/projetos/…` ao lado do legado intocado.
- O usuário final recebe **3 raízes + 2 Git internos + 0 Git na raiz de entrega** — impossível entregar/empacotar como um artefato só.
- Nome duplo `logistica-frotas-ctt/proj_logistica-frotas-ctt` acrescenta ruído sem valor.

**Como corrigir.**
1. **Detecção de layout no preflight/forge:** se existir projeto legado na raiz onde o clone foi feito (ou `package.json`/`src` no pai), `--pasta` padrão passa a ser a **raiz do workspace do usuário**, nunca `ecossistema-aidd/projetos/`.
2. Regra de ouro: **`projetos/` só é default quando o CWD é exclusivamente o ecossistema**; caso contrário, exibir (PT-BR simples) as 2 opções e perguntar — leigo não escolhe sozinho em silêncio.
3. Ao final do fluxo, imprimir **um card de entrega** com: caminho do app, comando para subir, URL — na primeira linha, sem jargão.
4. Achatar o aninhamento: `projetos/<app>/` com `src/` e `frontend/` dentro (eliminar o prefixo `proj_` redundante).
5. Incluir no fluxo `git init` na raiz do workspace de entrega (ou instrução única), fechando A8.

---

### A5 — Entrega fragmentada: legado e backend gerado sem ponto de entrada único

**Análise completa.**
A solução prometida era “Gestão de Frotas… & Picking CTT”. Na prática entregou-se:

- **Frontend legado** (`proj_app/`, porta 5173) — Torre de Controle, deslock-inizado;
- **Backend conector** (`ecossistema-aidd/projetos/.../proj_...`, porta 8000) — separado, outro repositório;
- **Infra Docker** (Fleetbase 8001, Traccar 8082, VROOM 3000, OSRM 5000) — dentro da pasta aninhada.

Não existe um **último comando** (“suba tudo e abra o navegador”) nem documentação única do usuário no topo do workspace. O leigo precisa orquestrar 2 árvores de diretório, 2 stacks e 6 portas.

**O que está correto.**
- Cada peça isolada está correta e testada (pytest 100%, gates aprovados).
- O desacoplamento do lock-in preservou a UI existente (regra de “papel da aplicação” definida no grill).
- URLs de auditoria mapeadas no relatório da sessão.

**O que está errado.**
- A promessa do livro é “app pronto com `python server.py` + `npm run dev`” — aqui a receita é dispersa e implícita.
- Nenhum `docker-compose`/script umbrella na **raiz do workspace** unindo legado + conector + motores.
- Sem “Guia do Utilizador” acessível no nível que o usuário realmente está.

**Como corrigir.**
1. Gerar na **raiz da entrega** um `README-USUARIO.md` (PT-BR simples, ≤30 linhas): 1) instalar; 2) um comando para subir tudo; 3) 1 URL principal; 4) onde estão as outras.
2. `docker-compose.yml` ou `make run` umbrella na raiz, referenciando legado + conector + infra.
3. Verificação final do fluxo: “golden path do leigo” — a partir da raiz, em 1 comando, o app abre (gate de aceite de usabilidade).

---

### A6 — Divergência raiz: livros × comportamento real de posicionamento

**Análise completa.**
Este achado é a **causa de A4**. Os livros ensinam clone em diretório próprio e projeto irmão (`--pasta ../proj_clinica`; “Forge cria a pasta, inicializa git”). O runtime, quando invocado com defaults a partir de clone situado dentro de um projeto existente, grava em `<clone>/projetos/<app>`. Documentação e código caminham em sentidos opostos — e o usuário do teste recebeu o resultado do código, não o do livro.

**O que está correto.** A regra documentada nos livros é boa e deve ser mantida como norma.
**O que está errado.** O default do código não a implementa; não há guarda (gate) de divergência doc×runtime; não há aviso ao usuário quando o layout gerado difere do documentado.
**Como corrigir.**
1. Centralizar a regra de path num único helper determinístico (`resolve_pasta_entrega()`), usado por todos os fluxos, com testes que **quebram** se o projeto sair da raiz esperada (Lei #13).
2. Gate `G_LAYOUT_ENTREGA`: valida que o projeto gerado não está sob `<clone>/projetos/` quando existe projeto legado irmão.
3. Atualizar mini-livro/fluxos com o caso real “clonou dentro do projeto existente → o que acontece” (cenário do teste).

---

### A7 — Remoção de lock-in parcial

**Análise completa.**
O fluxo removeu com sucesso `@lovable.dev/*` e apontou o registry para o npmjs.org (`package.json`, `bunfig.toml`, `vite.config.ts` alterados em 22/09 07:55 — janela da sessão). Restam **2 referências a `supabase`** em `package.json` e os diretórios `.lovable/` e `supabase/` ainda existem em `proj_app/`.

**O que está correto.** O bloqueio real (403 do Artifact Registry) foi resolvido; Vite 7 + React 19 + Tailwind v4 + TanStack 100% open-source; 255 pacotes oficiais instalados.
**O que está errado.** Fluxo Bridge/Freedom não foi aplicado ao legado de forma completa (Fluxo 02 não obriga varredura total); resíduos eixo “Vendor lock-in” da promessa.
**Como corrigir.** Checklist determinístico anti-lockin no fim de qualquer fluxo que toque projeto existente: `grep` por `lovable|supabase|firebase` + remoção de dirs residuais, com gate `G_ANT_LOCKIN_LEGADO` (mordendo: fixture com resíduo → exit 1).

---

### A8 — Fronteiras Git confusas na entrega

**Análise completa.**
Três repositórios Git aninhados (`ecossistema-aidd/`, `projetos/logistica-frotas-ctt/`, `proj_logistica-frotas-ctt/`) e **nenhum** na raiz `proj_app-frotas/` nem em `proj_app/`. O workspace que o usuário efetivamente entrega não é versionável; o histórico que existe é o da ferramenta e de cópias internas.

**O que está correto.** O Forge inicializa Git nos artefatos que cria (comportamento documentado); worktrees do dispatch convergiram para `main`.
**O que está errado.** Raiz de entrega sem Git; legado sem Git; histórico da ferramenta (27 MB) misturado à experiência do usuário.
**Como corrigir.** Padronizar a topologia: Git **na raiz da entrega** (workspace), legado como subárvore ou repo próprio, ecossistema como ferramenta externa (idealmente instalada fora ou via sparse/shallow); documentar o padrão em 5 linhas no mini-livro.

---

### A9 — Artefatos de auditoria verbosamente jargônicos

**Análise completa.**
O próprio `RELATORIO-SESSAO-AIDD-FROTAS.md` — peça que o usuário leigo usaria para entender o que recebeu — está em PT-BR técnico denso: “Tríade Canônica”, “VSA Topological Dispatch”, “Quality Gates”, “injeção de regra de integridade SHA-256”, “auditoria de drift zerada”, “Non-Goals”, “Intake BDD/SDD”. A seção “Como Auditar” exige rodar pytest, gates individuais e 6 serviços Docker.

**O que está correto.** O relatório é factual, tem telemetria, comandos copiáveis e URLs — excelente para um auditor técnico; nota 9.0/10 autoavaliada com itens rastreáveis.
**O que está errado.** Não existe versão “Na Festa” do relatório (o que mudou no meu negócio, o que eu abro no navegador, o que eu faço amanhã). A régua da Rule 10 (sem jargão não explicado) não foi aplicada ao artefato entregue.
**Como corrigir.** Template duplo obrigatório no encerramento de todo fluxo: `RESUMO-USUARIO.md` (≤20 linhas, zero sigla, 3 perguntas: o que mudou / como abro / como verifico) + `RELATORIO-TECNICO.md` (atual). Gate `G_RESUMO_USUARIO` na auditoria final.

---

## 3. Conformidade global vs. propósito (placar)

| Critério do propósito (livros) | Status no teste | Achado |
|---|---|---|
| Sistema completo, testado, auditado, implantado | **Cumpre** — fluxo 100%, gates OK, app nas 4 URLs | — |
| Desmantelar lock-in | **Parcial** — Lovable ok, Supabase/.lovable residuais | A7 |
| PT-BR simples, sem jargão, dupla fala | **Falha** — jargão em chat/CLI/docs/relatório; hook off no harness | A2, A9 |
| Comandos curtos e copiáveis | **Falha** — sync informado errado (duas formas erradas em circulação) | A1 |
| Projeto irmão do clone (topologia) | **Falha** — gerado aninhado em 4 níveis, avulso do legado | A4, A6 |
| Clone enxuto / núcleo | **Falha** — 221 MB / 8.186 arquivos, ~80% peso dev-only | A3 |
| Entrega pronta “1 comando, 1 URL” | **Falha** — 2 árvores, 2 stacks, 6 portas, sem guia no topo | A5, A8 |

---

## 4. Plano de correção priorizado

| Prioridade | Ação | Achados | Esforço |
|---|---|---|---|
| **P0** | Alias `sync`/`--tipos` + default `--tipo todos` + mensagem de erro que já ensina; corrigir `MEMORY.md:33` e `AGENTS-REFERENCIA:181` | A1 | Baixo |
| **P0** | Regra de posicionamento única + preflight que detecta projeto legado e devolve entrega à raiz do workspace | A4, A6 | Médio |
| **P0** | `GEMINI.md` em PT-BR simples + modo “usuário leigo” no preflight (perfil de linguagem) | A2 | Baixo |
| **P1** | `README-USUARIO.md` + comando umbrella na raiz da entrega | A5, A9 | Baixo |
| **P1** | `export-ignore`/perfil `package --perfil usuario` + gitignore de `*.db` e caches | A3 | Médio |
| **P1** | Template duplo de encerramento (usuário + técnico) | A9 | Baixo |
| **P2** | Gates: `G_SYNC_CMD_ROT`, `G_LAYOUT_ENTREGA`, `G_PACOTE_CORE`, `G_ANT_LOCKIN_LEGADO`, `G_RESUMO_USUARIO` — todos com teste que prova mordida (Lei #13) | A1–A9 | Médio |
| **P2** | Varredura anti-lockin completa + remoção de resíduos Supabase/.lovable | A7 | Baixo |
| **P2** | Topologia Git padrão documentada no mini-livro | A8 | Baixo |

---

## 5. Conclusão

A **engenharia de geração cumpriu o propósito**: da intenção ao sistema testado e auditado em uma hora, sem stubs, com Quarteto e gates reais. O **produto de distribuição e a camada de comunicação não cumprem**: repositório inflado, entrega aninhada em quatro níveis ao lado do projeto do usuário, comando-chave documentado errado na fonte canônica, linguagem de engenharia nas superfícies que o leigo lê e regra de simplicidade desligada justamente no harness testado. Corrigir P0 já elimina as três maiores fontes de fricção apontadas pelo teste de usabilidade.

---

*Relatório gerado em 22-09-2026 a partir da auditoria física do workspace `proj_app-frotas`, dos livros canônicos do ecossistema e das fontes de comando (`ecossistema.py`, `MEMORY.md`, `AGENTS.md`, `GEMINI.md`).*
