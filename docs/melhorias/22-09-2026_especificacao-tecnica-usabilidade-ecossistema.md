# Especificação Técnica — Melhorias de Usabilidade do Ecossistema-AIDD

> **Origem (Passo 1):** `docs/melhorias/22-09-2026_RELATORIO-ACHADOS-USABILIDADE-ECOSSISTEMA-AIDD.md` (A1–A9, confirmados em 22-09-2026).
> **Papel (Passo 3):** especificação executável para decomposição atômica (`/aidd-tickets`).
> **Destino (Passo 4):** `docs/issues/usabilidade-ecossistema/`.
> **Governança:** Lei #1 determinismo, #2 saída binária, #7 controle do desenvolvedor, #8 honestidade de rótulo, #13 todo portão prova que morde.

---

## 1. Contexto e Non-Goals Explícitos

### Contexto

O Fluxo 02 (`aidd-open`) entrega engenharia correta em ~59 min (gates 100%, Quarteto ativo, deslock-in Lovable), mas falha na camada de **distribuição e comunicação** ao usuário final. A especificação corrige 9 achados (A1–A9) sem reescrever os motores da Tríade.

### Non-Goals (fora de escopo)

1. Alterar arquitetura VSA / fatias / worktrees / Join Barrier.
2. Mudar stack Padrão-Ouro (Next.js + TS + Tailwind / Python + SQLite WAL / OpenAPI 3.1).
3. Reescrever livros canônicos inteiros — apenas trechos que ensinam comando ou topologia errados.
4. Implementar deploy VPS / `aidd-ops` / `aidd-enterprise` novos.
5. Traduzir todo o código-fonte do núcleo para PT-BR (Lei #4: núcleo agent-facing segue compact English).
6. Alterar contratos imutáveis de entrada de planos de infraestrutura.

---

## 2. Contratos e Interfaces Tipadas

### 2.1 Contrato CLI de sincronização (A1)

```text
Canônico:  python ecossistema.py components sync --tipo todos
           python ecossistema.py components verify --tipo todos

Aceitar:   python ecossistema.py sync [--tipo|--tipos <t>]
           python ecossistema.py components sync          # default implícito: todos
           python ecossistema.py components sync --tipos todos  # sinônimo

Default:   --tipo ausente => "todos" + aviso de 1 linha.
Erro:      mensagem didática já copiável:
           Erro: use "python ecossistema.py components sync --tipo todos".
```

### 2.2 Helper determinístico de posicionamento (A4, A6)

```python
def resolve_pasta_entrega(
    cwd: Path,
    nome_projeto: str,
    pasta_arg: str | None = None,
) -> Path:
    """Retorna a pasta de entrega do app do usuário.

    Regras:
    1. Se pasta_arg explícita (--pasta): respeitar (absoluta ou relativa a cwd).
    2. Se cwd NÃO é exclusivamente o ecossistema (há legado irmão:
       package.json | src/ | app/ | backend/ fora de tools/|gates/|componentes/):
       default = raiz do workspace do usuário (pai do clone se clone aninhado,
       senão cwd), NUNCA <clone>/projetos/.
    3. Se cwd é exclusivamente o ecossistema: default = <clone>/projetos/<slug>.
    4. Ambiguidade (2+ candidatos): NÃO decidir em silêncio — retornar erro
       estruturado com as 2 opções em PT-BR simples (Lei #7).
    """
```

Saída de ambiguidade (contrato de erro):

```json
{
  "erro": "pasta_entrega_ambigua",
  "opcoes": [
    {"rotulo": "Na pasta atual (junto ao projeto antigo)", "caminho": "..."},
    {"rotulo": "Dentro da ferramenta ecossistema-aidd/projetos/", "caminho": "..."}
  ],
  "instrucao": "Escolha com --pasta <caminho> e rode de novo."
}
```

### 2.3 Achatamento de aninhamento (A4)

```text
PROIBIDO:  .../ecossistema-aidd/projetos/<app>/proj_<app>/{src,frontend}
PADRÃO:    <pasta_entrega>/<app>/{src,frontend,tests,docker}
           (eliminar prefixo proj_ e camada extra)
```

### 2.4 Card de entrega (A4, A5)

```text
=== SEU APP ESTÁ PRONTO ===
Onde está:  <caminho_absoluto>
Como subir:  <um_comando_copiavel>
Abrir:       http://localhost:<porta>
Guia:        <caminho>/README-USUARIO.md
```

### 2.5 Artefatos de encerramento (A5, A9)

| Artefato | Local | Limite | Público |
|---|---|---|---|
| `README-USUARIO.md` | raiz da entrega | ≤30 linhas, zero sigla | leigo |
| `RESUMO-USUARIO.md` | raiz da entrega | ≤20 linhas, zero sigla | leigo |
| `RELATORIO-TECNICO.md` | raiz da entrega | atual (jargão ok) | auditor técnico |
| `docker-compose.yml` ou `make run` | raiz da entrega | 1 comando sobe tudo | leigo |

`RESUMO-USUARIO.md` — 3 perguntas obrigatórias: o que mudou / como abro / como verifico.

### 2.6 Perfil de linguagem (A2)

```python
# preflight-host --perfil leigo | tecnico  (default: tecnico)
PERFIL_LEIGO = {
    "max_bullets": 5,
    "siglas_traduzidas_na_primeira_ocorrencia": True,
    "comandos_completos_copiaveis": True,
    "proibido_jargao_sem_traducao": [
        "harness", "quality gate", "drift", "handoff", "worktree",
        "VSA", "fatia vertical", "pipeline", "orquestrador",
        "preflight", "E2E", "BDD", "SDD", "Quarteto Sine Qua Non",
    ],
}
```

Nomenclatura de governança (desambiguar):

| Rótulo correto | Proibido sozinho | Conteúdo |
|---|---|---|
| `Rule 10 (Formato de Resposta)` | "Lei #10" p/ idioma | forma da resposta |
| `Lei #10 (Quarteto)` | "Rule 10" p/ Quarteto | `/api` `/webhook` `/mcp` `/docs` |
| `Lei #4 (Idioma)` | — | PT-BR usuário / EN núcleo |

### 2.7 Pacote de distribuição (A3)

```text
python ecossistema.py package --perfil usuario
# ou: git archive / sparse-checkout documentado

INCLUSO:   ecossistema.py, gates/, core/, componentes/, scripts/, tools/,
           requirements.txt, README.md, LICENSE, docs/protocolos/, schemas/
EXCLUÍDO:  tests/, testes/, *.db, requirements-dev*, pytest.ini,
           .pre-commit-config.yaml, .secrets.baseline, __pycache__/,
           .pytest_cache/, .worktrees/, .ade_tmp/, docs/relatorios/,
           docs/reports/, docs/livros/ (PDFs/imagens), PLANO-EXECUCAO-ESTRUTURADO.json
```

`.gitattributes`: `export-ignore` para a lista EXCLUÍDO.

### 2.8 Checklist anti-lock-in (A7)

```text
grep -rniE 'lovable|supabase|firebase' <raiz_entrega> --include='*.{json,ts,tsx,js,py,toml,yml,yaml,md}'
dirs residuais: .lovable/, supabase/  → remover ou justificar em RESUMO-USUARIO.md
```

### 2.9 Topologia Git padrão (A8)

```text
<workspace-usuario>/     ← git init AQUI (raiz de entrega versionável)
├── proj_legado/         ← subárvore OU repo próprio (documentar qual)
├── <app_gerado>/        ← subárvore do mesmo repo (default)
└── (ecossistema-aidd/)  ← ferramenta FORA da entrega ideal; se presente,
                            sparse/shallow e nunca misturar histórico
```

### 2.10 Portões novos (Lei #13)

| Gate | Arquivo | Detecta | Bite test (exit 1) |
|---|---|---|---|
| `G_SYNC_CMD_ROT` | `gates/G_SYNC_CMD_ROT.py` | `components sync` sem `--tipo` em doc canônico; `--tipos` não mapeado; `ecossistema.py sync` sem alias | fixture doc com forma errada |
| `G_LAYOUT_ENTREGA` | `gates/G_LAYOUT_ENTREGA.py` | app gerado sob `<clone>/projetos/` havendo legado irmão | fixture layout aninhado |
| `G_PACOTE_CORE` | `gates/G_PACOTE_CORE.py` | release contém `*.db`, `requirements-dev*`, `docs/relatorios/` | fixture release suja |
| `G_USER_FACING_PTBR` | `gates/G_USER_FACING_PTBR.py` | README/`--help` com jargão da lista proibida sem tradução | fixture README jargão |
| `G_ANT_LOCKIN_LEGADO` | `gates/G_ANT_LOCKIN_LEGADO.py` | resíduo `lovable\|supabase\|firebase` em entrega | fixture com resíduo |
| `G_RESUMO_USUARIO` | `gates/G_RESUMO_USUARIO.py` | encerramento sem `RESUMO-USUARIO.md` ≤20 linhas / 3 perguntas | fixture sem resumo |

---

## 3. Invariantes e Regras de Negócio

1. **I1 — Forma canônica única de sync:** toda doc canônica e mensagem de erro citam `components sync --tipo todos` (ou alias equivalente funcional). Duas formas erradas em circulação são bug.
2. **I2 — Projeto do usuário nunca nasce dentro da ferramenta por default** quando existe legado irmão. O monorepo é ferramenta; o produto vive fora.
3. **I3 — Ambiguidade nunca resolve em silêncio (Lei #7).** Layout incerto ⇒ parar e perguntar em PT-BR simples.
4. **I4 — Superfície lida pelo leigo é PT-BR simples:** `README-USUARIO.md`, `RESUMO-USUARIO.md`, card de entrega, `--help` de comandos de usuário, `GEMINI.md`. Sigla traduzida na 1ª ocorrência.
5. **I5 — Dupla fala:** “Na Festa” (frase simples) + “Na Casa” (comando real completo e copiável). Nunca só jargão.
6. **I6 — Entrega = 1 comando, 1 URL principal.** Demais URLs no guia, não na primeira linha.
7. **I7 — Clone enxuto traz núcleo funcional.** Histórico/livros/relatórios/dev-only não entram no pacote `--perfil usuario`.
8. **I8 — Lock-in zero residual** em qualquer fluxo que toque projeto existente: varredura determinística + gate.
9. **I9 — Raiz de entrega é versionável** (Git init documentado/automático). Fronteiras de repo declaradas em ≤5 linhas no mini-livro.
10. **I10 — Todo gate novo prova que morde (Lei #13).** Caminho feliz (exit 0) não basta; teste com violação sintética asserta exit 1.
11. **I11 — Rule 10 ≠ Lei #10.** Nenhum documento cita “Lei #10” para idioma nem “Rule 10” para Quarteto.
12. **I12 — Honestidade (Lei #8).** Nenhuma nota/certificação sem evidência real de teste rodado.

---

## 4. Critérios Binários de Aceitação

Por ticket (detalhe em `docs/issues/usabilidade-ecossistema/`). Globais:

- [ ] `python ecossistema.py audit` ⇒ exit 0 após cada ticket.
- [ ] Todo gate novo tem teste de violação assertando exit 1 (I10).
- [ ] Nenhum ticket afeta `tools/*` engines além dos pontos de CLI/preflight/packaging explicitados.
- [ ] `components sync --tipo todos` continua exit 0 (91 componentes, SHA-256 estável) após A1.
- [ ] Nenhuma forma errada de sync sobra em `MEMORY.md`, `docs/protocolos/AGENTS-REFERENCIA-COMPLETA.md`, `docs/livros/**` (A1).
- [ ] Fixture “clonou dentro de projeto existente” gera entrega na raiz do workspace, não em `projetos/` (A4/A6).
- [ ] `GEMINI.md` 100% PT-BR simples; nenhuma “Mandatory Answer Shape” em inglês (A2).
- [ ] Encerramento de fluxo emite card + `README-USUARIO.md` + `RESUMO-USUARIO.md` + `RELATORIO-TECNICO.md` (A4/A5/A9).
- [ ] Pacote `--perfil usuario` (ou `git archive` equivalente) sem `*.db` / `requirements-dev*` / `docs/relatorios/` (A3).
- [ ] Varredura anti-lock-in exit 1 com fixture contendo `supabase`/`.lovable` (A7).
- [ ] `git init` na raiz de entrega documentado e exercitado no teste E2E de usabilidade (A8).

---

## 5. Modos de Falha e Degradação

| Falha | Comportamento exigido |
|---|---|
| `--tipo`/`--tipos` ausente | Default `todos` + aviso 1 linha; **não** abortar. |
| Subcomando desconhecido (`ecossistema.py sync` sem alias ainda) | Erro didático com comando canônico copiável; exit 1. |
| Ambiguidade de pasta de entrega | Erro estruturado com 2 opções + `--pasta`; exit 1; zero escrita em disco. |
| Legado detectado e `--pasta` não informado | Default raiz do workspace + aviso; nunca `<clone>/projetos/`. |
| Ausência de Docker/ports no umbrella run | `README-USUARIO.md` degrada para 2 comandos (backend + frontend) + URLs; card não mente “1 comando” (Lei #8). |
| Hook `regra10_check` indisponível (Gemini/Antigravity) | Gate `G_USER_FACING_PTBR` + checklist de encerramento cobrem superfícies leigas; status explícito “hook off — convenção + gate no fim do fluxo”. |
| Resíduo lock-in encontrado | Gate exit 1; lista arquivos/dirs; remoção só com confirmação humana (Lei #7) se for projeto do usuário. |
| Release suja (dev-only) | `G_PACOTE_CORE` exit 1; build do pacote abortado. |
| Falha de `git init` (repo já existe / permissão) | Mensagem com comando manual; entrega não é marcada “pronta” sem versão ou aviso explícito no card. |

---

## 6. Rastreabilidade Achado → Ticket → Gate

| Achado | Severidade | Ticket | Gate |
|---|---|---|---|
| A1 | Crítica | ISSUE-USA-0001 | `G_SYNC_CMD_ROT` |
| A6 | Alta | ISSUE-USA-0002 | `G_LAYOUT_ENTREGA` |
| A4 | Crítica | ISSUE-USA-0003 | `G_LAYOUT_ENTREGA` |
| A2 | Crítica | ISSUE-USA-0004 | `G_USER_FACING_PTBR` |
| A5 | Alta | ISSUE-USA-0005 | (golden path + `G_RESUMO_USUARIO`) |
| A3 | Alta | ISSUE-USA-0006 | `G_PACOTE_CORE` |
| A9 | Média | ISSUE-USA-0007 | `G_RESUMO_USUARIO` |
| A7 | Média | ISSUE-USA-0008 | `G_ANT_LOCKIN_LEGADO` |
| A8 | Média | ISSUE-USA-0009 | (topologia Git + E2E usabilidade) |

---

*Especificação gerada em 22-09-2026 (Passo 3 — `/aidd-spec`) a partir do diagnóstico A1–A9 aprovado pelo desenvolvedor (Lei #7).*
