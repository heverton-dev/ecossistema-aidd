# AUDITORIA: TOKENOMICS, EFICIÊNCIA DE CONTEXTO E LATÊNCIA DE PIPELINE

> **Data:** 2026-09-09
> **Status:** ✅ PLANO FORMALIZADO — `docs/planos/a-fazer/02-otimizacao-tokenomics-latencia/`
> **Tags:** #plano-gerado #tokenomics #eficiencia-tokens #latencia #llm
> **Escopo:** Análise técnica do consumo de tokens, retenção de contexto entre fases, compressão e gargalos de latência no Ecossistema AIDD.
> **Método:** leitura direta de `utils_delegacao.py`, fases 1-8, `utils_subagente_ephemero.py`, `subagent_purger.py` (forge), skill `sandeco-token-reduce`; estimativas de tokens por heurística ~4 chars/token (a mesma usada pelo próprio forge em `subagent_purger.py:18`).

──────

## 1. Phase-by-Phase Token Consumption Breakdown

| Fase | Modo | Entrada dominante | Sair/Retorno | Densidade de desperdício |
|:--|:--|:--|:--|:--|
| 1 Pesquisador | **Zero LLM** (determinístico) | API GitHub/HF/Replit | JSON estruturado | 🟢 zero |
| 2 Analisador | LLM | `json.dumps(referencias, indent=2)` **completo** no prompt (`02_analisador.py:294,297`) | análise JSON | 🔴 alto (dump bruto) |
| 3 Designer | LLM (N subagentes paralelos, `03_designer.py:394-442`) | prompt + "CONTEXTO DA IDEIA" por subagente; **sem** referências — bom | design JSON | 🟡 médio (repetição do contexto por subagente) |
| 4 Decisor | LLM leve | design consolidado | config | 🟡 médio |
| 5 Criador | **Zero LLM** (determinístico, `05_criador.py`) | config fase 4 | projeto + arquivos | 🟢 zero |
| 6 Documentador | LLM (narrativas) | HTML/MD lidos por inteiro (`06_documentador.py:102,162`) | docs | 🔴 alto (docs gerados são verborragicos e re-entram como contexto) |
| 7 Auto-crítica | LLM | **todos os artefatos anteriores** | relatório | 🔴 alto |
| 8 Implementador | LLM pesado (1 chamada por script + loop de correção) | PROMPT_GERAR_SCRIPT ~1.2k tokens de regras fixas **por script** (`08_implementador.py:383-403`); fix-loop reenvia CODE+TEST+ERRORS completos (`08_implementador.py:405-421`) | código+teste | 🔴 **crítico** (multiplicado por N scripts × T tentativas) |

**Telemetria existente:** `estimar_tokens_tiktoken` (`utils_delegacao.py:496-517`) mede entrada/saída de **cada** chamada e é anexada à resposta (`:604,714`) — a instrumentação é boa; o que falta é *orçamento* (budget por fase) e *alerta de desvio*, não medição.

### Vazamentos de contexto entre fases (retenção indevida)
- **[TK-1] Fase 2 recebe o dump JSON bruto da fase 1 sem poda:** `referencias_json = json.dumps(referencias, indent=2)` — inclui todos os campos de metadata de cada referência (URL, descrição completa, stars etc.). Para 30+ referências, são dezenas de k tokens onde ~5k bastariam (top-N por relevância + campos seletos). Não há `pruning`, seleção top-k nem compressão: o pipeline encadeia "dados persistidos → dump integral".
- **[TK-2] Fase 7 re-recebe o mundo:** a auto-crítica consome analise+design+docs+código; nada no código indica seleção (é a fase mais cara após a 8, e roda **depois** que o código já passou em testes — o valor marginal por token é o mais baixo do pipeline).
- **[TK-3] Fase 8 fix-loop reenvia estado completo a cada tentativa:** `PROMPT_CORRIGIR_SCRIPT` inclui `CODE` + `TEST` + `ERRORS` integrais (`08_implementador.py:405-421`). Com `max_tentativas` sem decaimento de contexto, o custo é O(N×T×tamanho_total) — um script grande com 3 tentativas pode custar 6-10× a geração original.
- **[TK-4] Bloat de regras por chamada:** `PROMPT_GERAR_SCRIPT` carrega ~25 linhas de regras fixas (SQLite/FK/datas/JSON-roundtrip/CRUD/UI/Swagger/MCP) **em toda chamada**, inclusive para scripts que não tocam no assunto (ex.: script puro de cálculo recebe regras de Swagger dark-mode e webhook HMAC). Regra #1 violada: isso é seleção determinística (por palavras-chave do `script_spec`), não cognição.
- **[TK-5] Micro-ambiente `AGENTS.md` lido e mantido em memória** (`pipeline_completo.py:_carregar_micro_ambiente`) — bom mecanismo, mas o contexto lido não é contabilizado nem podado (texto integral do AGENTS.md da fase entra na composição).

### O que já está correto (mérito)
- Fases 1 e 5 são 100% determinísticas — o maior princípio Zero-Token já aplicado onde dava.
- `ContextPurgeEngine` + `_modulo_cache` descartam a fase anterior da memória do orquestrador (`pipeline_completo.py:89-115`) — sem acúmulo entre fases no lado Python.
- Fase 3 não injeta o dump de referências nos subagentes (só a ideia) — o vazamento da fase 2 **não** se propaga adiante.
- `SubagentPurger` do forge limita prompt a ~1000 tokens por design (`subagent_purger.py:18,59-63`) e valida AST antes de persistir — o melhor contrato custo/qualidade do repositório.

---

## 2. Identified Waste & Inefficiencies (locais concretos)

| # | Local | Desperdício | Correção determinística possível? |
|:--|:--|:--|:--|
| TK-1 | `02_analisador.py:294` | dump integral das referências | Sim: top-k + campos seletos + truncagem por orçamento (script puro) |
| TK-4 | `08_implementador.py:383-403` | regras fixas em toda chamada | Sim: montar prompt por features do script_spec (FK? UI? API?) |
| TK-3 | `08_implementador.py:405-421` | fix-loop reenvia tudo | Parcial: diff mínimo + erros recortados por parser de traceback (o `PostMortemAnalyzer._isolar_traceback` **já existe** em `:232` — só não é usado no prompt!) |
| TK-2 | `07_analisador.py` | fase crítica re-recebe tudo | Sim: crítica sobre índices/diffs, não sobre artefatos integrais |
| — | `utils_delegacao.py:119-248` | `extrair_json_resposta` + `_validar_pydantic_com_retry(max_retries=3)`: quando o LLM quebra o JSON, a resposta crua volta inteira ao modelo até 3× | Sim: reparo de JSON é 100% mecânico (o `_extrair_json_manual:145-177` já faz 80% do trabalho — os retries restantes gastam chamada de LLM em erros que `jsonrepair`-style resolve) |
| — | Fase 6 → 7 | docs HTML verborragicos viram contexto | Sim: mapa de seções (títulos+resumos) em vez de HTML integral |

**Conclusão da área 2:** o pipeline já tem os instrumentos de medição (tiktoken) e já tem dois reparos mecânicos (AST no purge, extração manual de JSON) — o desperdício está em (a) não podar handoffs, (b) não fragmentar regras por script, (c) não usar os recortes mecânicos que já existem no prompt de correção.

## 3. Compressão (LLMLingua-2 / sandeco-token-reduce) — por que não está integrada

- A skill existe e está sincronizada em 6 harnesses (`componentes/compartilhado/skills/sandeco-token-reduce/`), com `scripts/setup.py` (cria .venv próprio) e `scripts/compress.py` (XLM-RoBERTa local).
- **Nenhuma referência a `llmlingua` em `tools/`** — confirmado por busca. Ela é skill *conversacional* (acionada por humano/agente no chat), não middleware de engine.
- **Por que não integrada hoje:** (1) latência de cold-start — o setup baixa modelo e cria venv na primeira execução, inaceitável dentro de uma fase de pipeline sem pré-aquecimento; (2) custo computacional local vs. economia de tokens precisa de política (não comprimir código gerado — compressão destrói sintaxe; só comprimir prosa: referências, docs, AGENTS.md); (3) o `dependencias_externas.json` do ecossistema ainda não a declara como dependência de pipeline.

**Estimativa de economia (heurística 4 chars/token):**
| Handoff | Tamanho atual típico | Com LLMLingua-2 (rate 0.5, prosa) | Economia por execução |
|:--|:--|:--|:--|
| Fase 1→2 referências | 30 refs × ~600 chars ≈ 18k chars ≈ 4.5k tokens | ~2.3k tokens | ~2.2k tokens |
| Fase 6→7 docs | ~40k chars ≈ 10k tokens | ~5k | ~5k |
| Micro-AGENTS.md por fase | ~3k tokens/fase × 4 fases LLM | ~1.7k | ~5k |
| **Total por execução de pipeline** | | | **~10-12k tokens de entrada** (~15-25% do custo total de pipeline típico, dominado pela fase 8) |

Veredicto honesto: a compressão vale a pena **nos handoffs de prosa** (1→2, 6→7, AGENTS.md), mas o maior ganho absoluto é arquitetural (podar, fragmentar regras, diff no fix-loop) — compressão é segundo passo, não primeiro.

## 4. Subagent & Harness Context Purging — hermeticidade real

- **Forge (`subagent_purger.py`):** ciclo Spawn→Executa→AST→Purge é hermético de verdade (session_active como janela única, AST valida antes de salvar, purge imediato). Limite de 4.000 chars evita prompt inflado. 🟢
- **Generator (`utils_subagente_ephemero.py` + `pipeline_completo.py`):** o orquestrador Python não acumula estado entre fases (módulos descartados, cache de 1 fase). Porém a **hermeticidade do harness alvo é declarativa, não imposta**: o subagente real (Claude/Codex headless) é invocado por CLI (`solicitar_llm_modo_headless`) — se o harness mantiver sessão entre invocações (ex.: `claude --continue` ou contexto de repositório carregado automaticamente), o purge do lado Python não limpa o lado do harness. Não há verificação de que cada invocação nasce sem histórico (nem flag `--no-session-persistence` auditada por gate). 🟡
- **Risco residual [TK-6]:** `solicitar_llm_modo_delegado` escreve prompt em arquivo e aguarda resposta em arquivo (`utils_delegacao.py:360-390`) — no modo delegado, quem responde é a sessão ADE ativa, **que carrega todo o contexto acumulado da conversa do usuário**. Ou seja: no modo default, o "prompt limpo de ~1000 tokens" chega ao modelo montado sobre uma sessão que já viu tudo. O orçamento de tokens da fase é ilusório nesse modo.

## 5. Target Token-Optimization Architecture (receitas)

### 5.1 `Orçador de Contexto` (context budgeter) — entre todas as fases
```
orcador.montar_handoff(fase_atual, dados_anteriores, budget_tokens):
    1. schema da fase define campos obrigatórios (fonte única: scripts/phases/schemas/)
    2. seleção determinística: top-k por score já calculado na fase anterior
       (fase 1 já tem gates R1-R4 de relevância — reaproveitar o ranking)
    3. truncagem por orçamento: campos longos → resumo determinístico
       (primeiras N linhas / chaves do dict), nunca silencioso: registra o que cortou
    4. header de handoff: "<resumo do que foi podado>" para a fase seguinte saber
    5. telemetria: tokens_enviados vs budget por fase → _pipeline_state.json
```
### 5.2 `Prompt por Composição` (fase 8)
- `PROMPT_GERAR_SCRIPT` vira base + blocos condicionais montados por `script_spec`: `tem_fk → bloco FK`, `tem_api → bloco Swagger/MCP`, `tem_ui → bloco design`. Economia típica: 30-50% do prompt fixo por script.
- `PROMPT_CORRIGIR_SCRIPT`: substituir CODE/TEST integrais pelo **diff falho + traceback isolado** (o `PostMortemAnalyzer._isolar_traceback` já existe — ligá-lo ao prompt) e o trecho do código sob suspeita (funções citadas no traceback via AST). Fix-loop cai de O(total) para O(local).

### 5.3 `Middleware de Compressão` (sandeco-token-reduce como engine, não skill)
- Empacotar `compress.py` como serviço local com pré-aquecimento no bootstrap do pipeline (`preflight_llm` já é o ponto natural: adicionar `verificar_compressor_pronto()`).
- Política declarativa por handoff: `compressivel: true` apenas para prosa (referências, docs, AGENTS.md); **nunca** para código/JSON de schema.
- Fallback determinístico se o compressor não estiver inicializado: envia sem comprimir + registra em telemetria (nunca bloquear pipeline por economia).
- Registrar a dependência em `gates/dependencias_externas.json` (opcional, com flag).

### 5.4 `Hermeticidade Verificável` (fecha TK-6)
- Modo headless: exigir/auditar flags de sessão limpa do harness alvo (ex.: `--no-continue`, sessão efêmera) — gate AST no comando montado em `solicitar_llm_modo_headless`.
- Modo delegado: rotular a medição de tokens como "contexto de sessão contaminado" (a telemetria já tem a categoria `autodeclarado` — adicionar `sessao_compartilhada`) para honestidade de rótulo (Regra #9), ou exigir resposta via subagente efêmero sempre que a fase exigir orçamento controlado.

### 5.5 `Reparo JSON Zero-LLM` (fecha o desperdício de `_validar_pydantic_com_retry`)
- Escada determinística antes de gastar LLM: extração manual (já existe) → `jsonrepair`/regras de fence → pydantic. Só depois de esgotar a escada, 1 retry LLM com o erro estruturado — não 3 retries com texto cru.

---

## 6. Actionable Roadmap (priorizado, pronto para planos-auditoria-runner)

| # | Prioridade | Ação | Resolve | Critério de pronto (gate/teste) |
|:--|:--:|:--|:--|:--|
| 1 | **P0** | `Prompt por Composição` na fase 8 + fix-loop com diff/traceback isolado (ligar `PostMortemAnalyzer` ao prompt) | [TK-3/4] | Teste: prompt montado para script sem UI/API não contém blocos Swagger/MCP; fix-loop 2ª tentativa envia < 40% dos tokens da 1ª (medido por tiktoken) |
| 2 | **P0** | `Orçador de Contexto` no handoff 1→2 (top-k referências com campos seletos) | [TK-1] | Teste: handoff fase 2 ≤ N tokens para entrada de 30 referências; campos não essenciais ausentes; ranking preservado |
| 3 | **P1** | Escada de reparo JSON determinística antes de retry LLM | desperdício `utils_delegacao:248` | Teste: 10 respostas quebradas sinteticamente → ≥8 reparadas sem chamada LLM |
| 4 | **P1** | `Hermeticidade Verificável`: gate no comando headless + rótulo `sessao_compartilhada` no modo delegado | [TK-6] | Gate AST rejeita comando headless sem flag de sessão limpa; telemetria distingue origens |
| 5 | **P2** | Middleware sandeco-token-reduce com preflight + política declarativa + fallback | seção 3 | Teste: pipeline roda sem compressor (fallback registrado); com compressor, handoff 1→2 reduz ≥40% chars sem perder campos obrigatórios do schema |
| 6 | **P2** | Orçador no handoff 6→7 (mapa de seções em vez de HTML integral) | [TK-2] | Teste: tokens fase 7 ≤ 50% do baseline atual com mesma nota de crítica (amostra) |
| 7 | **P3** | Orçamento por fase no `_pipeline_state.json` + alerta de desvio >20% | telemetria | Gate: execução de pipeline com desvio produz aviso estruturado no estado |

**Sequência:** 1→2→3 atacam o custo direto; 4 fecha o buraco de honestidade de medição; 5-6 são otimizações incrementais mensuráveis pelos instrumentos que já existem.

> **Nota de rótulo (Regra #9):** a alegação "Redução de >65% no consumo de tokens vs carregamento eager" (`pipeline_completo.py:110-115`) não tem medição auditável anexada — ou vira métrica com baseline medido pelo `estimar_tokens_tiktoken`, ou é reescrita como objetivo de design.
