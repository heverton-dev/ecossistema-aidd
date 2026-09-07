# PROCESSO E DECISÕES — Prova Completa de Funcionamento do Ecossistema AIDD

> **Origem:** pedido do usuário, 06/09/2026, após o fechamento das Rodadas 1 (`docs/planos/evolucao-notas-auditoria/`) e 2 (`docs/planos/refinamento-notas-auditoria/`) de evolução das notas de auditoria — "gerar um teste completo para PROVAR o funcionamento completo do ecossistema, bem como de cada uma das ferramentas".
> **Propósito deste arquivo:** registro único do *processo*, igual ao das duas rodadas anteriores — o conteúdo técnico de cada bateria vive em documento próprio (ver §3).

---

## 1. O que "prova completa" significa aqui (para não virar promessa vazia)

Duas coisas diferentes já existem e **não são o que este esforço busca**:
- Suítes `pytest` unitárias/integração por ferramenta (já existem, já passam, já são rodadas por `ecossistema.py status --testes`).
- As auditorias pontuais das Rodadas 1 e 2, que provaram capacidades específicas introduzidas por cada correção.

O que falta e é o objeto deste esforço: uma bateria de **testes de ponta a ponta via CLI real** (não só `pytest`) que comprove o **caminho de ouro** de cada ferramenta — os comandos que um usuário real digitaria — de forma real, reproduzível, isolada (nunca contra o repositório real) e com evidência de execução real (exit codes reais, nunca mascarados por pipe), mais uma bateria de nível **raiz** que comprova a orquestração unificada (`ecossistema.py`) e os 6 Meta-Quality Gates.

---

## 2. Mesmo processo das rodadas anteriores, adaptado ao formato "prompt copia-e-cola"

Para cada bateria: diagnóstico rápido do que precisa ser provado → Definição de Pronto travada → **um único Prompt de Execução autocontido**, pronto para copiar e colar num agente executor (nesta sessão ou em outra) — que **gera os scripts de teste reais, executa-os de verdade e escreve o relatório da bateria**, tudo em um único ciclo (diferente das Rodadas 1/2, aqui não há decisão de arquitetura a aprovar antes, então não se justifica separar em Fase 1/Fase 2 — a única exceção é a bateria do `aidd-generator`, ver `05-testes-aidd-generator.md`, que tem uma restrição real de custo/mecanismo que exige atenção redobrada do executor).

Cada Prompt de Execução instrui o executor a salvar cada tipo de artefato no lugar certo, sempre:
- **Scripts de teste (código):** `docs/testes/testes/`
- **Prompts em linguagem natural usados como *input* dos testes** (ex.: a "ideia" passada para `/generate`, ou o texto passado para `aidd plan "..."`/`aidd prompt "..."`) — **não confundir com o Prompt de Execução deste documento**: `docs/testes/prompts/`
- **Relatório da bateria (Markdown, com tabelas/gráficos via skills `artifact-design`/`dataviz` quando fizer sentido):** `docs/testes/relatorios/`

---

## 3. Onde vive o conteúdo técnico de cada bateria

| # | Bateria | Ferramenta/Escopo | Documento |
|---|---|---|---|
| 1 | Orquestração raiz | `ecossistema.py` (status, audit, components sync/verify) + os 8 Meta-Quality Gates | `01-testes-ecossistema-raiz.md` |
| 2 | AIDD Master | `tools/aidd-master` — CLI completa (compose, add-module, inject com as 5 capacidades, plan/prompt, bench, heal, etc.) | `02-testes-aidd-master.md` |
| 3 | AIDD Enterprise | `tools/aidd-enterprise` — mesma superfície de CLI que o Master, mais as diferenças reais (5 harnesses, hook `.json`, detecção de ambiguidade) | `03-testes-aidd-enterprise.md` |
| 4 | AIDD Forge | `tools/aidd-forge` — `init`/`inject`, hook de pre-commit real, 7 gates instalados no projeto alvo | `04-testes-aidd-forge.md` |
| 5 | AIDD Generator | `tools/aidd-generator` — pipeline completo de 8 fases, incluindo o Protocolo Delegado (fases 2/3/8) | `05-testes-aidd-generator.md` |
| 6 | AIDD Ops | `tools/aidd-ops` — 5ª ferramenta (Intake, Curadoria, Sizing, SSH, MCPs, Gate Compose, Preflight e Deploy) | `06-testes-aidd-ops.md` |

Cada documento segue a mesma estrutura interna: Contexto já investigado → Definição de Pronto → Prompt de Execução (autocontido, PT-BR) → Regras de escopo.

---

## 4. Regras fixas que valem para todas as bateiras

1. **Nunca testar contra o repositório real.** Todo teste roda num diretório temporário isolado (`tmp`/`mktemp -d`), nunca dentro de `C:\Users\trcnologia\Desktop\ecossistema-aidd` como alvo de escrita — a única exceção é ler os arquivos-fonte das próprias ferramentas (o que é normal e esperado) e escrever os artefatos de teste (scripts/prompts/relatórios) nas 3 pastas de `docs/testes/`.
2. **Reprodução real, nunca simulada.** Nenhum passo do relatório pode se basear em "deveria funcionar" — todo comando roda de verdade, exit code real capturado, saída real citada.
3. **Honestidade sobre limites de ambiente.** Se um comando depender de algo não disponível nesta máquina (ex.: Docker não instalado para `deploy docker`, `locust` para teste de carga, `node`/`npm` para `export-frontend`), o relatório documenta isso explicitamente como limitação de ambiente — nunca finge que rodou, nunca pula em silêncio.
4. **Efeitos colaterais reais devem ser desfeitos.** Qualquer comando que suba um processo/servidor/container (`docker compose up`, servidor de teste, etc.) precisa ser derrubado (`docker compose down`, `kill`, etc.) ao final do teste — nunca deixar processos ou containers órfãos rodando.
5. **Sem git commit/push** feito pelos scripts de teste em nenhum repositório (nem no ecossistema real, nem nos projetos temporários gerados) — a menos que o próprio comando testado exija um repositório git local para funcionar (ex.: o hook de pre-commit do `aidd-forge`), caso em que o `git init`/commit acontece só dentro do diretório temporário isolado, nunca no repositório real.
6. **Sem gastar chamada real de LLM sem aprovação explícita.** Válido principalmente para a bateria do `aidd-generator` (Protocolo Delegado) — ver regras específicas em `05-testes-aidd-generator.md`.

---

## 5. Registro de progresso

| # | Bateria | Status | Documento |
|---|---|---|---|
| 1 | Orquestração raiz | ✅ Concluído (auditado 2026-09-06, 100% aprovado) | `01-testes-ecossistema-raiz.md` |
| 2 | AIDD Master | ✅ Concluído (executado 2026-09-06, PASSOU COM RESSALVAS — ver `docs/testes/relatorios/02_aidd_master.md`) | `02-testes-aidd-master.md` |
| 3 | AIDD Enterprise | ✅ Concluído (executado 2026-09-06, PASSOU COM RESSALVAS — 1 achado grave, ver `docs/testes/relatorios/03_aidd_enterprise.md`) | `03-testes-aidd-enterprise.md` |
| 4 | AIDD Forge | ✅ Concluído (executado 2026-09-06, APROVADO 11/11 — ver `docs/testes/relatorios/04_aidd_forge.md`) | `04-testes-aidd-forge.md` |
| 5 | AIDD Generator | ✅ Concluído (executado 2026-09-06, PASSOU — score auto-crítica 88/100, ver `docs/testes/relatorios/05_aidd_generator.md`) | `05-testes-aidd-generator.md` |
| 6 | AIDD Ops | ✅ Concluído (executado 2026-09-06, APROVADO 7/7 — ver `docs/testes/relatorios/06_aidd_ops.md`) | `06-testes-aidd-ops.md` |

Esta tabela é atualizada para ✅ Concluído só depois que o relatório real da bateria existir em `docs/testes/relatorios/` com evidência de execução real.
