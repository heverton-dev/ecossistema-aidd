# Item 5 — Investigação do mecanismo de descoberta de skills do `agy` (Antigravity)

> **Status:** Diagnóstico de custo zero concluído em 05/09/2026 (nenhuma chamada real ao `agy` foi gasta). Achado um mecanismo real, bem documentado, mas uma contradição real entre a documentação oficial e o teste empírico da Rodada 1 permanece — decisão do usuário necessária sobre gastar 1 chamada real para resolvê-la.
> **Origem:** `docs/planos/evolucao-notas-auditoria/06-universalidade.md` — a Rodada 1 testou `agy`/Antigravity com 2 chamadas reais de LLM (`agy --print "..."`), confirmou 0/5 skills descobertas de forma estável, mas não identificou a causa raiz e decidiu explicitamente não gastar mais chamadas investigando (regra de escopo item 3.2 daquele pacote).
> **Contribui para:** Universalidade (9→10?).

---

## As 4 perguntas de rigor

1. **É necessário?** — Sim. É o único item pendente da Rodada 1 (Pacote 6) sem explicação, e o próprio documento da Rodada 1 já registrou isso como "item de investigação futura (Fase 3)".
2. **É possível?** — Sim, e de um jeito melhor do que o previsto: **é possível investigar boa parte sem gastar nenhuma chamada de LLM**, usando técnicas gratuitas (leitura da documentação oficial pública, inspeção de strings do binário instalado, exercício dos subcomandos não-conversacionais do CLI). Isso não estava disponível/óbvio na Rodada 1.
3. **É real?** — Sim, tudo abaixo foi confirmado com comandos reais rodados agora, sem simulação.
4. **Traz ganho real?** — Depende de uma decisão do usuário (ver "Contradição não resolvida" abaixo): há um achado forte e uma explicação plausível, mas uma divergência real entre a documentação oficial e o comportamento observado na Rodada 1 que só uma chamada real (paga) resolveria com certeza.

---

## Achados (custo zero — nenhuma chamada ao `agy` foi feita)

### 1. `agy` tem, sim, um mecanismo de skills documentado — não é "mecanismo desconhecido"

Via `strings` do binário instalado (`C:\Users\trcnologia\AppData\Local\agy\bin\agy.exe`, versão `1.1.27`, confirmada via `agy --version`) e via a documentação pública oficial (`https://antigravity.google/docs/skills`, buscada agora), o mecanismo é:

- **Caminho de workspace:** `<raiz-do-workspace>/.agents/skills/<nome-da-skill>/SKILL.md` (**plural** `.agents`, não singular `.agent`).
- **Caminho global:** `~/.gemini/config/skills/<nome-da-skill>/` (confirmado também como string literal no binário: `/.gemini/config/skills/`).
- **Manifesto opcional para skills compartilhadas:** um arquivo `.agents/skills.json` na raiz do repositório, formato:
  ```json
  {
    "entries": [
      { "path": "tools/agents/skills" }
    ]
  }
  ```
  usado para apontar para um diretório compartilhado (ex.: monorepo) sem precisar duplicar os arquivos em `.agents/skills/`.
- Texto oficial da documentação (buscado agora, resposta literal): *"Antigravity now defaults to .agents/skills, but still maintains backward support for .agent/skills."*

### 2. O ecossistema hoje gera `.agent/skills/` (singular) — nunca `.agents/skills/` (plural) nem `.agents/skills.json`

Confirmado por leitura de `tools/aidd-master/src/core/profiles_registry.py` (mirrors de `skill`: `.claude/skills`, `.agent/skills`, `.gemini/skills` — 3, conforme já mapeado no Item 4) e `tools/aidd-enterprise/src/core/profiles_registry.py` (5 mirrors, incluindo `.mimocode/skills` e `.skills` flat — mas também nunca `.agents/skills`, plural). `gates/manifesto_harnesses.json` tampouco lista `.agents/skills` em nenhum lugar.

### 3. Testes gratuitos que ELIMINARAM hipóteses alternativas

- `agy plugin list` / `agy plugin import` → "No claude extensions found." / "No gemini extensions found." — confirma que o subsistema `plugin` do `agy` é um conceito **diferente** de skill (exige `plugin.json`, não `SKILL.md`); não é por aí que skills são importadas.
- `agy plugin validate tools/aidd-master/.agent/skills/aidd-master-runner` → `Error: missing plugin.json` — confirma que "plugin" e "skill" são formatos distintos no `agy`, eliminando de vez a hipótese de que `agy plugin import claude` seria o caminho certo para os `.claude/skills/` existentes.
- Não existe nenhum subcomando `agy skills` exposto no `--help` nem documentado (`agy help skills` → `unknown subcommand`) — não há como listar skills descobertas sem uma sessão real (interativa ou `--print`), que tem custo.

### 4. Contradição não resolvida — decisão do usuário necessária

A documentação oficial afirma que `.agent/skills` (singular, formato que o ecossistema já gera hoje) tem **suporte retroativo** ("backward support"). Se isso for literalmente verdade e estivesse ativo no momento do teste da Rodada 1, o `agy` deveria ter encontrado pelo menos algumas das 5 skills via `.agent/skills/` — mas o teste real da Rodada 1 (2 chamadas reais de LLM, mesma versão `1.1.27` instalada, mesmo dia) encontrou **0/5**, de forma estável.

Duas explicações plausíveis, nenhuma confirmável sem uma chamada real:
- **(a)** O "backward support" documentado tem alguma condição não documentada (ex.: só ativa se `.agents/` não existir *de jeito nenhum* na árvore, ou exige alguma flag/config adicional) que não se aplicou neste repositório.
- **(b)** O teste da Rodada 1 aconteceu **antes** da correção do bug de BOM UTF-8 em `componentes-runner/SKILL.md` (Pacote 6, Fase 1) — mas isso não explica sozinho o 0/5, porque só 1 dos 5 arquivos-fonte tinha BOM; um resultado de "falha total" é mais consistente com "diretório errado" do que com "1 arquivo corrompido entre 5".

Não tentei resolver isso com uma chamada real ainda — meu diagnóstico ficou 100% dentro do orçamento gratuito, meio a mais do que a Rodada 1 conseguiu sem gastar chamada nenhuma.

---

## Opções para o usuário

**Opção A — Fechar aqui, documentar o achado como está (custo zero, recomendo como piso).** Registrar em `AGENTS.md`/onde for apropriado: "`agy`/Antigravity descobre skills via `.agents/skills/` (plural) ou `~/.gemini/config/skills/` (global); o ecossistema gera `.agent/skills/` (singular), que a documentação oficial do `agy` alega ter suporte retroativo mas que o teste real da Rodada 1 (0/5) contradiz — causa exata da divergência não confirmada." Honesto, ganho real (de "mecanismo desconhecido" para "mecanismo identificado com uma contradição documentada"), zero risco.

**Opção B — 1 chamada real para fechar a contradição (custo real, pequeno).** Rodar `agy --print` (1 única chamada, mesmo padrão de rigor da Rodada 1 — "aprovada explicitamente pelo usuário") num diretório de teste **isolado** (não no repo real) contendo uma cópia de `.agents/skills/<nome>/SKILL.md` (plural, convenção correta) baseada num dos componentes já existentes, perguntando se a skill é vista. Se `agy` a encontrar, confirma 100% que a causa raiz da Rodada 1 é só o nome da pasta (singular vs. plural) — e aí caberia decidir, num item futuro, se vale a pena o ecossistema passar a gerar TAMBÉM `.agents/skills/` (plural) como mais um mirror (mesmo padrão de "adicionar mirror" já usado para MimoCode no Item 4).

**Opção C — 1 chamada real, mas testando o cenário exato que a Rodada 1 já rodou (`.agent/skills`, singular) de novo, agora pós-fix do BOM.** Mais barato em termos de decisão (não cria fixture nova), mas resolve só a hipótese (b) acima, não a (a).

Qual você prefere? Se for B ou C, preciso da sua aprovação explícita antes de rodar a chamada (mesma regra da Rodada 1 — cada chamada tem custo real na sua conta).
