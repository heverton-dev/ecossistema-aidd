# Pacote 7 — Agnosticismo de Distribuição de Componentes (Supremacia Agnóstica)

> **Status:** Definição de Pronto travada — as 4 decisões e a arquitetura (diretório canônico `componentes/` + sync por cópia + camada híbrida CLI/skill) estão confirmadas. Aguardando sua aprovação final para eu gerar os prompts de execução (2 prompts sequenciais sugeridos — ver seção "Nota sobre o tamanho deste pacote").
> **Origem:** análise feita por outro agente a seu pedido explícito, entregue em `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` + `docs/relatorios/relatorio-skills-e-comandos-aidd.html`. Registrado aqui por instrução sua para entrar no mesmo processo dos demais pacotes.
> **Regra de Ouro violada:** #6 do `AGENTS.md` — *Supremacia Agnóstica*: "Absolutamente TUDO (skills, mcps, specs, hooks, slash commands, fluxos, configurações) deve operar de forma 100% agnóstica a ambiente de execução, sistema operacional, harness [...] e provedor de LLM."

---

## Por que isto é um pacote separado do Pacote 6 (Universalidade)

O Pacote 6 já registrado (`00-PROCESSO-E-DECISOES.md` §5) é sobre uma coisa diferente: **execução** real testada em múltiplos harnesses (Codex, Gemini CLI etc.) — travado porque só há Claude Code instalado nesta máquina, um teto estrutural genuíno que nenhuma quantidade de trabalho remove agora.

Este Pacote 7 é sobre **distribuição de arquivos**: um componente (skill/MCP/spec/config/hook) precisa existir fisicamente na pasta que cada harness lê para descobri-lo. Isso é 100% verificável e corrigível **nesta máquina, agora**, sem precisar instalar mais nenhum harness — não é bloqueado pelo mesmo teto do Pacote 6. Por isso ganha um número próprio em vez de ser misturado ao 6.

---

## Verificação independente que já fiz (antes de aceitar o diagnóstico do outro agente às cegas)

Não aceitei o relatório do outro agente de olhos fechados — conferi os dois achados mais importantes eu mesmo:

1. **Confirmado via checagem direta do disco:** as 4 skills-runner da raiz (`aidd-forge-runner`, `aidd-generator-runner`, `aidd-master-runner`, `aidd-enterprise-runner`) existem em `skills/` e `.agent/skills/`, mas **nenhuma delas existe em `.claude/skills/`** — ou seja, o Claude Code (o harness que estou rodando agora, nesta própria sessão) não descobre nativamente nenhuma das 4 skills-runner do projeto.
2. **Confirmado via `grep` em `gates/G_HARNESS_COMPAT.py`:** o gate nunca menciona `.claude/skills`, `.gemini` ou `.mimocode` em nenhuma linha — por isso `python ecossistema.py audit` passa com exit 0 mesmo com o gap do item 1 presente. O ponto cego é real, não hipotético.

O restante da tabela de diagnóstico (`PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` §2.1-2.5) ainda não foi reverificado item a item por mim — isso entra como parte da Definição de Pronto deste pacote, antes de qualquer implementação (mesma disciplina dos Pacotes 1 e 2: nunca implementar sobre um diagnóstico que eu mesmo não conferi de ponta a ponta).

---

## Decisões — todas resolvidas em 05/09/2026

1. **`.mimocode/skills`: redundante, elimina-se.** Confirmado por citação direta de `AGENTS.md §5`: *"Antigravity / MimoCode / OpenCode: Carrega definições em .agent/commands/ e .agent/skills/"*. Não existe convenção própria documentada para MimoCode — a pasta separada contradiz a regra escrita do próprio ecossistema. MimoCode passa a ser servido por `.agent/skills/`, igual Antigravity/OpenCode. Conteúdo de `.mimocode/skills/` é diffado contra `.agent/skills/` antes de removido (nunca apagar sem checar divergência silenciosa).
   - **Achado adicional nesta verificação:** `AGENTS.md` não menciona Gemini CLI em nenhuma linha, mas `.gemini/skills/` existe e está em uso real (ex.: skill `seguranca-cibernetica`). Diferente do caso do MimoCode, isso é uma **omissão de documentação**, não uma contradição — não há indício de que `.gemini/skills/` seja redundante. Tratamento: mantido como convenção legítima e documentado agora em `AGENTS.md §5` (fecha de vez a causa-raiz nº4 do diagnóstico original, que apontava exatamente essa lacuna).

2. **Auto-criação de pasta de harness ausente: sempre criar (opção A), confirmado.** Coerente com Determinismo Primeiro — com fonte canônica única e comando de sync determinístico, o comportamento correto é completo e previsível, não condicional ao estado prévio do disco.

3. **Unificação dos dois injetores: entra neste mesmo ciclo.** Resolvida pela própria decisão de arquitetura abaixo — com um diretório canônico único, os dois injetores (`aidd-forge`, `aidd-generator`) passam a escrever no mesmo lugar por definição, não é mais uma escolha entre "agora ou depois".

4. **Amplitude do rollout: TODOS os tipos de componente, confirmado.** Skills, specs, MCPs, hooks, arquivos de configuração, comandos, sub-agentes e scripts — não só `skill` como prova de conceito.

---

## Arquitetura confirmada

Por proposta do usuário + reflexão conjunta registrada nesta conversa:

- **Diretório canônico único na raiz:** `componentes/` (nome escolhido por mim, sem conflito confirmado com nenhum diretório existente).
  ```
  componentes/
    aidd-forge/        {skills, mcps, specs, hooks, config, comandos, subagentes, scripts}/
    aidd-master/        (mesma estrutura)
    aidd-enterprise/     (mesma estrutura)
    aidd-generator/      (mesma estrutura)
    compartilhado/      {skills, comandos}/   ← componentes de escopo ecossistema, não de 1 ferramenta
                                                  (aqui vivem as 4 skills-runner e os slash-commands raiz)
  ```
- **Mecanismo de propagação: cópia física sincronizada por comando determinístico — não symlink.** Motivo (já registrado nesta conversa): symlink no Windows exige Admin ou Modo de Desenvolvedor, e o Git não lida bem com symlink sem configuração extra — trava específica de SO que a própria Regra de Ouro #6 proíbe. Mesma decisão já tomada antes neste projeto (`PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md`).
- **Camada híbrida:** um comando real e único (`python ecossistema.py components sync|verify --tipo <tipo> [--ferramenta <nome>]`), auditável e testável por exit code — e uma skill/slash-command fina por cima, que só invoca esse mesmo comando e apresenta o resultado de forma amigável para quem não conhece a estrutura de pastas. Zero lógica duplicada entre as duas camadas.
- **Fonte única do manifesto:** `gates/manifesto_harnesses.json` (mesmo diretório dos outros arquivos de referência dos gates — `baseline_nucleo_compartilhado.json`, `allowlist_segredos.json`, `allowlist_cli_help.json`), declarando harness × tipo de componente × pasta de destino física.

---

## Definição de Pronto

**Fase 1 — Manifesto + estrutura canônica**
1.1. Criar `gates/manifesto_harnesses.json`: harnesses (Claude Code, Antigravity, MimoCode, OpenCode, Gemini CLI, Cursor) × tipos de componente (skill, mcp, spec, hook, config, comando, subagente, script) × pasta física de destino — já refletindo as decisões 1-2 acima.
1.2. Criar a árvore vazia `componentes/<ferramenta>/<tipo>/` para as 4 ferramentas + `componentes/compartilhado/`.
1.3. Atualizar `AGENTS.md §5` para documentar `.claude/skills/` e `.gemini/skills/` (hoje usados na prática, nunca escritos no documento) e remover qualquer menção a `.mimocode/skills` como pasta própria.

**Fase 2 — Comando único de sync/verify**
2.1. Implementar `scripts/gestor_componentes.py` (raiz) com as funções `sync(tipo, ferramenta=None, dry_run=False)` e `verify(tipo, ferramenta=None)`, lendo `gates/manifesto_harnesses.json`.
2.2. Registrar `python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>] [--dry-run]` e `python ecossistema.py components verify --tipo <tipo> [--ferramenta <nome>]` em `ecossistema.py`.
2.3. `sync` sempre cria as pastas de harness declaradas no manifesto (decisão 2), nunca usa symlink, sobrescreve destino com cópia byte-idêntica da fonte canônica.

**Fase 3 — Reverificação completa do diagnóstico + migração do conteúdo existente**
3.1. Reverificar item a item a tabela §2.1 de `PLANO-CORRECAO-SKILLS-AGNOSTICAS.md` (só 2 dos vários achados foram checados por mim até agora) — confirmar cada divergência antes de migrar.
3.2. Para cada componente hoje espalhado: `diff` manual entre cópias divergentes antes de escolher qual vira a fonte canônica dentro de `componentes/` (nunca sobrescrever sem essa checagem — regra de ouro já usada nesta sessão).
3.3. Mover o conteúdo escolhido para `componentes/<ferramenta ou compartilhado>/<tipo>/`; rodar `components sync --tipo <todos>` para regenerar todas as cópias-destino a partir da nova fonte única.
3.4. Remover `.mimocode/skills/` (decisão 1) depois do diff de segurança do item 3.2.
**Critério de saída:** `python ecossistema.py components verify --tipo <todos>` exit 0 na raiz.

**Fase 4 — Unificar os dois injetores**
4.1. `tools/aidd-forge/aidd_forge/core/injector_profiles.py` e `tools/aidd-generator/scripts/core/injector/` passam a gravar em `componentes/<ferramenta>/<tipo>/` (ou chamar `components sync` ao final da materialização) em vez de decidirem destino cada um por conta própria.
**Critério de saída:** rodar `/forge` do zero produz um projeto cujos componentes de template já nascem espelhados em todas as pastas de harness declaradas, sem passo manual.

**Fase 5 — Camada híbrida para leigos**
5.1. Criar a skill/slash-command fina (nome sugerido: `componentes-runner`) cujo conteúdo é só invocar `ecossistema.py components sync/verify` com os parâmetros certos e reportar o resultado — cobrindo todos os tipos de componente da decisão 4.
**Critério de saída:** pedir em linguagem natural "crie uma skill nova chamada X para a ferramenta Y" resulta na skill aparecendo fisicamente em todas as pastas de harness declaradas, sem o usuário tocar em nenhuma pasta manualmente.

**Fase 6 — Estender o gate existente**
6.1. `gates/G_HARNESS_COMPAT.py` passa a chamar `components verify --tipo <todos>` em vez da checagem manual hardcoded de 2 vias (linhas 34-79 atuais).

**Fase 7 — Gate novo, protocolo permanente**
7.1. Criar `gates/G_COMPONENTE_AGNOSTICO.py`: via `git diff --name-only` contra a base, identifica componentes tocados no commit e falha (exit 1) se algum não tiver a cobertura de harness exigida pelo manifesto.
7.2. Registrar em `ecossistema.py audit` (6º gate raiz).
7.3. Extrair o protocolo permanente (Seção 5 de `PLANO-CORRECAO-SKILLS-AGNOSTICAS.md`) para `docs/protocolos/PROTOCOLO-AGNOSTICIDADE-COMPONENTES.md`, referenciado a partir de `AGENTS.md` (Regra de Ouro #6).

**Validação final (todas as fases)**
- `python ecossistema.py audit` (com `G_HARNESS_COMPAT` estendido + `G_COMPONENTE_AGNOSTICO` novo) → exit 0.
- `python ecossistema.py components verify --tipo <todos>` → exit 0 na raiz e nos 4 `tools/*`.
- Suítes completas das 4 ferramentas sem regressão.
- Teste real de ponta a ponta: criar uma skill nova via a camada híbrida (Fase 5), confirmar por comando (não inspeção visual) que ela existe fisicamente em toda pasta de harness declarada no manifesto.
- Teste real de reprodução: um commit de teste que adicione um componente só em 1 harness precisa ser reprovado por `ecossistema.py audit` (prova que o protocolo da Fase 7 não depende de disciplina manual).

---

## Nota sobre o tamanho deste pacote

É o maior dos 7 pacotes — cobre migração de conteúdo real, uma ferramenta nova (`components sync/verify`), unificação de 2 injetores em 2 ferramentas diferentes, uma camada de UX nova e um gate permanente novo. Antes de gerar o prompt de execução, minha recomendação é dividir em **2 prompts sequenciais para o agente executor** (não um só): Prompt A = Fases 1-3 (manifesto, comando, migração — fecha o gap relatado originalmente) e Prompt B = Fases 4-7 (injetores, camada híbrida, gates) só depois do Prompt A auditado e confirmado. Isso reduz o raio de impacto de qualquer desvio e mantém a mesma disciplina de validação incremental já usada nos Pacotes 1 e 2.

---

## Veredito

*(pendente — aguardando você confirmar a Definição de Pronto acima, e a divisão em 2 prompts sugerida)*
