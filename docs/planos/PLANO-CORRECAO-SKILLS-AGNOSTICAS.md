# PLANO DE CORREÇÃO — AGNOSTICIDADE REAL DAS SKILLS (MULTI-HARNESS)

> **Repositório:** `https://github.com/heverton-dev/ecossistema-aidd`
> **Diretório Local:** `C:\Users\trcnologia\Desktop\ecossistema-aidd`
> **Data da Auditoria:** 05/09/2026
> **Status:** PLANEJADO — nenhuma correção aplicada ainda (apenas diagnóstico e plano, por pedido explícito do usuário)
> **Origem:** Callout "Gap de integração real" do relatório `docs/relatorios/relatorio-skills-e-comandos-aidd.html`
> **Regra de Ouro violada:** #6 do `AGENTS.md` — Supremacia Agnóstica ("skills, mcps, specs, hooks, slash commands... devem operar 100% agnóstico a harness").
> **Escopo ampliado em 05/09/2026:** por diretiva explícita do usuário, este plano deixa de cobrir só skills — a correção e, principalmente, o **protocolo permanente da Seção 5**, valem para **todo componente adicionado ao ecossistema**: skills, specs, MCPs, arquivos de configuração e arquivos de personalização. Nenhum componente novo é aceito sem ser agnóstico a stack de tecnologia, harness, ambiente de programação e sistema operacional.

---

## 1. OBJETIVO

Corrigir, de forma sistêmica (não apenas os 4 arquivos citados no relatório anterior), o motivo pelo qual **skills do ecossistema não são descobertas por todos os harnesses igualmente** — tanto na raiz do meta-repositório quanto dentro dos 4 subprojetos em `tools/*`. Toda correção deste plano será validada por comando com exit code, nunca por inspeção visual.

Além da correção pontual, este plano estabelece um **protocolo permanente** (Seção 5): daqui para frente, qualquer skill, spec, MCP, arquivo de configuração ou de personalização adicionado ao repositório — na raiz ou em qualquer `tools/*` — deve passar pelo mesmo diagnóstico aplicado na Seção 2 antes de ser considerado concluído. Agnóstico, neste plano, significa quatro independências simultâneas: **stack de tecnologia**, **harness** (Claude Code, Antigravity, OpenCode, MimoCode, Cursor, Gemini CLI, Hermes, Freebuff, DeepSeek etc.), **ambiente de programação** e **sistema operacional** (Windows/Linux/macOS).

---

## 2. DIAGNÓSTICO — EVIDÊNCIA REAL COLETADA POR ARQUIVO

### 2.1 Inventário completo de cópias por skill (levantado via `Glob **/SKILL.md`)

| Skill | Local | Cópias existentes | Cópias ausentes | Severidade |
|---|---|---|---|---|
| `aidd-forge-runner`, `aidd-generator-runner`, `aidd-master-runner`, `aidd-enterprise-runner` | raiz | `skills/`, `.agent/skills/` | **`.claude/skills/`** | **CRÍTICA** — Claude Code nunca as descobre nativamente |
| `resumo-sessao` | `tools/aidd-master`, `tools/aidd-enterprise` | `.agent`, `.claude`, `.mimocode`, `.skills` (4 cópias, sem `.gemini`) | `.gemini/skills` | Baixa (bem coberta, só falta 1 harness) |
| `seguranca-cibernetica` | `tools/aidd-master` | `.claude`, `.gemini`, `.mimocode`, `.agent`, `.skills` (5 cópias) | nenhuma | Nenhuma (referência de boa cobertura) |
| `project-spec-tracker` | `tools/aidd-generator` | **só `.claude/skills`** (1 cópia) | `.agent`, `.gemini`, `.mimocode`, `.skills` | **CRÍTICA** — só existe para Claude Code |
| `auditoria-seguranca-dependencias` | `tools/aidd-generator` | `.claude/skills`, `skills/` (bare, 2 cópias) | `.agent`, `.gemini`, `.mimocode` | Alta |
| `validador-contratos` | `tools/aidd-forge/sandbox-forge-teste` | `.agent`, `.claude` (2 cópias) | `.gemini`, `.mimocode` | Média (fixture de teste, impacto real baixo) |
| `caveman-ultra`, `orca-orchestration`, `impeccable-ui`, `open-code-review`, `post-mortem`, `cybersecurity-audit` | template `aidd-forge` → injetado em `sandbox-forge-teste` | `.agent/skills`, `skills/` (bare) | **`.claude/skills`** | **CRÍTICA** — todo projeto futuro gerado por `/forge` nasce sem suporte a Claude Code para essas 6 skills |

### 2.2 Causa-raiz nº1 — o gate que deveria pegar isso tem ponto cego

`gates/G_HARNESS_COMPAT.py` (linhas 34-79) só compara **2 vias**: `skills/<runner>/SKILL.md` vs `.agent/skills/<runner>/SKILL.md`, e só para as 4 skills-runner da raiz. Nunca checa `.claude/skills/` (nem na raiz, nem em `tools/*`), nunca checa `.gemini`/`.mimocode`, e nunca varre skills de subprojeto. Por isso `python ecossistema.py audit` passa com exit 0 mesmo com o estado real do item 2.1.

### 2.3 Causa-raiz nº2 — o sincronizador automático do `aidd-forge` só espelha o que já existe

`tools/aidd-forge/aidd_forge/core/harness_sync.py`:
```python
CANONICAL_SKILLS_DIR = ".agent/skills"
MIRROR_HARNESS_DIRS: tuple[str, ...] = (".claude", ".gemini", ".mimocode")
...
for harness in MIRROR_HARNESS_DIRS:
    harness_root = target_root / harness
    if not harness_root.exists():
        result.skipped_harnesses.append(harness)
        continue          # <- nunca cria o harness ausente
```
`universal_injector.py:67` **chama esse sincronizador automaticamente** após materializar uma skill — o mecanismo existe e roda sozinho, mas por design só espelha em pastas de harness que o usuário já provisionou manualmente. Nenhuma verificação depois checa `result.skipped_harnesses` nem falha o processo. Bare `skills/` (usado pela própria raiz do ecossistema e por `aidd-generator`) nunca entra no `MIRROR_HARNESS_DIRS` — está fora do alcance do sincronizador mesmo quando existe.

### 2.4 Causa-raiz nº3 — dois injetores independentes, dois destinos diferentes

- `tools/aidd-forge/aidd_forge/core/injector_profiles.py` grava skill em `.agent/skills/{nome}/SKILL.md` (`FORGE_PROFILE`).
- `tools/aidd-generator/scripts/core/injector/` (citado no próprio `SKILL.md` de `auditoria-seguranca-dependencias`) grava em `skills/{nome}` + `.claude/skills/{nome}`, **sem `.agent/skills`** — ou seja, fora do alcance de `harness_sync.py`, que só lê de `.agent/skills` como fonte.

Dois injetores decidindo destino de forma independente é a razão estrutural de toda a divergência do item 2.1 — não foi descuido pontual, é o comportamento esperado do código atual.

### 2.5 Causa-raiz nº4 — `AGENTS.md §5` não documenta o que o código realmente faz

`AGENTS.md` só lista 3 grupos de harness (Antigravity/MimoCode/OpenCode → `.agent/`; Claude Code → `.claude/`; Cursor → `.cursor/rules/`). O código e o disco mostram **5 convenções físicas distintas** em uso: `.agent/skills`, `.claude/skills`, `.gemini/skills`, `.mimocode/skills` (separado de `.agent`, contrariando o próprio AGENTS.md) e bare `skills/`. Não há hoje uma fonte de verdade única que diga qual convenção é oficial para qual harness.

---

## 3. PLANO DE CORREÇÃO EM 7 FASES

### FASE 1 — Fechar a contradição de convenção (pré-requisito, decisão do usuário)
Criar `gates/manifesto_harnesses.json` como fonte única, listando cada harness suportado (Claude Code, Antigravity, OpenCode, MimoCode, Gemini CLI, Cursor, Hermes, Freebuff, DeepSeek, etc.) e, **para cada tipo de componente** já reconhecido por `injector_profiles.py` (`skill`, `mcp`, `rule`, `spec`, `roteiro` — mais o tipo `config`, hoje sem perfil próprio), seu diretório físico de destino por harness — resolvendo a contradição do item 2.5 e generalizando o que hoje só existe para `skill`. Depende da Decisão 1 (Seção 4).
**Saída:** manifesto versionado, referenciado por `AGENTS.md §5` (atualizado) e por todo script das fases seguintes.

### FASE 2 — Construir o sincronizador único (`ecossistema.py components sync|verify --tipo <tipo>`)
Substituir a lógica fragmentada (`harness_sync.py` isolado, só para `skill` + injetor duplicado do `aidd-generator`) por um único comando **por tipo de componente**, orientado pelo manifesto da Fase 1 — não só skills:
- `python ecossistema.py components verify --tipo <skill|mcp|rule|spec|roteiro|config> [--root <caminho>]`: somente leitura, compara todas as cópias contra a fonte canônica, `exit 1` se houver divergência de conteúdo ou harness ausente declarado no manifesto como obrigatório para aquele projeto.
- `python ecossistema.py components sync --tipo <...> [--root <caminho>]`: materializa/atualiza as cópias ausentes ou divergentes a partir da fonte canônica (cópia física byte-idêntica, não symlink — mesma técnica já usada e validada por `G_HARNESS_COMPAT.py`, evita reabrir a decisão de symlink no Windows já pendente em `PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md`).
**Saída:** os dois comandos funcionam sobre a raiz do ecossistema-aidd em modo `--dry-run` sem alterar nada ainda, para `--tipo skill` no mínimo (demais tipos podem ser incrementais, ver Decisão 4).

### FASE 3 — Aplicar na raiz do ecossistema-aidd (fecha o gap originalmente reportado)
3.1. Rodar `components sync --tipo skill` para as 4 skills-runner: cria `.claude/skills/{4 skills}/SKILL.md`.
3.2. Estender `G_HARNESS_COMPAT.py` para chamar `components verify --tipo skill` em vez da checagem manual de 2 vias hoje hardcoded (linhas 34-79).
3.3. Atualizar `AGENTS.md §5` para declarar `.claude/skills/` como path oficial (hoje só cita `.claude/commands/`).
**Critério de saída:** `python ecossistema.py audit` cobre as 3 vias (`skills/`, `.agent/skills/`, `.claude/skills/`) para as 4 skills-runner, exit 0.

### FASE 4 — Aplicar em cada `tools/*` (fecha o gap mais amplo relatado pelo usuário)
4.1. Para cada skill órfã/divergente do item 2.1, **antes de sincronizar automaticamente**: diff manual entre as cópias existentes para descartar que já divergiram silenciosamente (regra de ouro "nunca sobrescrever sem revisar diff").
4.2. Promover fonte canônica por skill:
   - `project-spec-tracker`: única cópia existente (`.claude/skills`) vira fonte; `components sync --tipo skill` cria as demais.
   - `auditoria-seguranca-dependencias`: comparar `.claude/skills` vs `skills/` (bare) antes de escolher fonte.
4.3. Rodar `components sync --tipo skill` nos 4 subprojetos.
**Critério de saída:** `python ecossistema.py components verify --tipo skill --root tools/aidd-master --root tools/aidd-generator --root tools/aidd-enterprise --root tools/aidd-forge` retorna exit 0.

### FASE 5 — Corrigir o `aidd-forge` para não repetir o bug em projetos futuros
5.1. `harness_sync.py`: incluir bare `skills/` no `MIRROR_HARNESS_DIRS` e remover (ou tornar opt-out explícito) a regra "só espelha harness que já existe" — hoje é a causa direta do item 2.1 (6 skills de template sem `.claude/skills`).
5.2. Unificar `injector_profiles.py` (aidd-forge) e `scripts/core/injector/` (aidd-generator) para consumirem o mesmo manifesto da Fase 1, ou no mínimo ambos chamarem `components sync` (Fase 2) ao final da materialização, em vez de decidirem destino de forma independente (causa-raiz nº3). Isso vale para os 5 tipos hoje suportados (`skill`, `mcp`, `rule`, `spec`, `roteiro`), não só `skill`.
**Critério de saída:** rodar `/forge` do zero em um projeto de teste (`sandbox-forge-teste` recriado) produz as 6 skills de template já com `.claude/skills` presente, sem passo manual.

### FASE 6 — Validação final e re-auditoria completa
6.1. `python ecossistema.py audit` (com `G_HARNESS_COMPAT` estendido) → exit 0.
6.2. `python ecossistema.py components verify --tipo skill` na raiz e nos 4 `tools/*` → exit 0.
6.3. Atualizar o relatório `docs/relatorios/relatorio-skills-e-comandos-aidd.html`: trocar os status `gap`/`templated` da Camada 1 e 3 para `wired` onde corrigido, republicar o artifact.
**Critério de saída (Definition of Done):** nenhuma skill do repositório com menos cópias que o exigido pelo manifesto da Fase 1; `components verify` roda em CI (mesmo pipeline citado em `PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md §4.2`).

### FASE 7 — Institucionalizar o protocolo permanente (fecha o loop para componentes futuros)
7.1. Extrair o checklist da Seção 5 para um documento canônico e durável, independente do ciclo de vida deste plano de correção: `docs/protocolos/PROTOCOLO-AGNOSTICIDADE-COMPONENTES.md`.
7.2. Referenciar esse documento a partir de `AGENTS.md` (Regra de Ouro #6), para que sobreviva ao encerramento/arquivamento deste plano.
7.3. Criar `gates/G_COMPONENTE_AGNOSTICO.py`: roda `components verify --tipo <todos>` para todo componente novo/alterado no diff do commit (via `git diff --name-only` contra a base), e falha (`exit 1`) se algum caminho tocado sob `skills/`, `.claude/skills/`, `.agent/skills/`, `docs/mcps/`, `docs/specs/`, `docs/rules/` ou pastas de config equivalentes não tiver a cobertura de harness exigida pelo manifesto.
7.4. Registrar `G_COMPONENTE_AGNOSTICO` em `ecossistema.py audit` (`cmd_audit`), na mesma lista de gates sequenciais.
**Critério de saída:** um commit de teste que adicione uma skill nova só em 1 harness é **reprovado** por `python ecossistema.py audit` até rodar `components sync`; isso prova que o protocolo deixou de depender de disciplina manual.

---

## 4. DECISÕES QUE PRECISAM DO USUÁRIO ANTES DE EXECUTAR

1. **`.mimocode/skills` é redundante ou obrigatório?** `AGENTS.md §5` diz que MimoCode lê `.agent/skills/`, mas o disco mantém `.mimocode/skills/` como pasta separada e idêntica em 2 subprojetos. Confirmar: MimoCode realmente precisa de pasta própria (então documentar oficialmente no manifesto da Fase 1), ou é cópia redundante herdada de um convenção antiga (então eliminar e apontar MimoCode só para `.agent/skills/`)?
2. **Política de auto-criação de harness ausente (Fase 5.1):** mudar `harness_sync.py` para sempre criar `.claude/`, `.gemini/`, `.mimocode/` mesmo quando o projeto-alvo não os provisionou pode "sujar" projetos gerados por `/forge` com pastas de harness que o usuário-final nunca vai usar. Decidir entre: (a) sempre criar todos os harnesses do manifesto incondicionalmente; (b) criar todos só na raiz do próprio ecossistema-aidd (que já declara suportar todos) e manter opt-in (só espelha o que já existe) em projetos-alvo de terceiros gerados via `/forge`.
3. **Unificação dos dois injetores (Fase 5.2)** é mudança estrutural maior (toca `aidd-forge` e `aidd-generator`). Confirmar se entra neste plano ou vira item separado — pode ser adiado sem bloquear as Fases 1-4 (que já fecham o gap relatado, mesmo com os dois injetores ainda desacoplados).
4. **Amplitude do rollout por tipo de componente (Fases 1-2):** o manifesto e o `components sync|verify` generalizados cobrem `skill` primeiro (prova de conceito no gap já diagnosticado). Confirmar se `mcp`, `rule`, `spec`, `roteiro` e `config` entram no mesmo ciclo de correção ou em um ciclo incremental separado, já usando a ferramenta pronta — sem isso, o gate da Fase 7 (7.3) fica sem critério de quando declarar cada tipo "coberto".

---

## 5. PROTOCOLO PERMANENTE DE AGNOSTICIDADE — TODO COMPONENTE NOVO

> Válido a partir da conclusão da Fase 7. Escopo: **qualquer skill, spec, MCP, arquivo de configuração ou de personalização** adicionado ou modificado neste monorepo, na raiz ou em qualquer `tools/*` — não só skills. "Agnóstico" = independente de stack de tecnologia, de harness, de ambiente de programação e de sistema operacional.

### 5.1 Definição de "agnóstico" para efeito deste protocolo
- **Stack de tecnologia:** a mecânica de descoberta/injeção do componente (onde ele é procurado, como é lido) não pode presumir uma linguagem/framework específico. Conteúdo de negócio de uma spec pode ser stack-specific por natureza — a forma como ela é localizada e versionada, não.
- **Harness:** o componente deve existir, fisicamente, em todo diretório de harness que o manifesto da Fase 1 declarar como aplicável ao tipo daquele componente.
- **Ambiente de programação:** nenhuma dependência de IDE/editor específico para o componente ser descoberto ou executado.
- **Sistema operacional:** nenhum caminho hardcoded com separador de um único SO, nenhuma dependência de symlink real sem fallback (Windows sem privilégio elevado precisa funcionar), nenhum comando de shell específico de um SO sem alternativa.

### 5.2 Protocolo de diagnóstico obrigatório (mesma lógica da Seção 2, aplicada a qualquer componente novo)
1. **Identificar o tipo** do componente (`skill`, `mcp`, `rule`, `spec`, `roteiro`, `config`) e resolver seu `ComponentProfile` no manifesto único da Fase 1.
2. **Enumerar todos os harnesses** que o manifesto declara para esse tipo — nunca presumir que só o harness em uso localmente importa.
3. **Confirmar cópia física** do componente em cada harness enumerado; se ausente, rodar `python ecossistema.py components sync --tipo <tipo> --nome <nome>` antes de considerar a tarefa concluída.
4. **Rodar `python ecossistema.py components verify --tipo <tipo>`** — exit 0 obrigatório antes de qualquer commit que toque o componente.
5. **Checar hardcodes que quebram agnosticidade:** caminho de SO literal (usar `os.path.join`/`pathlib`), nome de harness como pré-condição de funcionamento, ou stack específica na camada de descoberta/injeção (não no conteúdo de negócio da spec, quando aplicável).
6. **Nenhum PR/commit é aceito** sem os passos 1-5 executados e referenciados (ex: no corpo do commit ou da descrição do PR, citando este protocolo).

### 5.3 Onde isso fica de pé mesmo após este plano ser arquivado
O checklist acima é extraído para `docs/protocolos/PROTOCOLO-AGNOSTICIDADE-COMPONENTES.md` (Fase 7.1) e referenciado a partir de `AGENTS.md` (Fase 7.2) — este plano de correção documenta o diagnóstico e a implementação pontual, mas a regra permanente não pode depender de um plano que um dia será marcado como concluído e arquivado.

---

## 6. RISCOS RESIDUAIS (fora do escopo deste plano)

- Não foi auditado se `.cursor/rules/` precisa de um equivalente por-skill (hoje Cursor usa 1 arquivo de regra apontando para `AGENTS.md`, mecanismo diferente de skill-por-pasta — não é o mesmo tipo de gap).
- `materiais-extras/SKILL.md` (`tools/aidd-enterprise`) não foi classificado em nenhuma das 4 camadas do relatório anterior nem neste plano — precisa de triagem própria antes de entrar em qualquer sync automático.
- Não foi verificado se skills geradas por `aidd-master`/`aidd-enterprise` para clientes finais (fora deste monorepo) também sofrem do mesmo bug — este plano cobre só o que está fisicamente neste repositório.
