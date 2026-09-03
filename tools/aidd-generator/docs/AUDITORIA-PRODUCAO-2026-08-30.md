# AUDITORIA DE PRONTIDÃO PARA PRODUÇÃO — aidd-generator

**Data:** 2026-08-30
**Escopo:** Análise completa para publicação no GitHub
**Método:** Leitura de código, execução real de testes, grep por segredos, revisão de documentação

---

## 1) Status das Etapas no PLANO-EXECUCAO-ESTRUTURADO.json

### Etapas CONCLUÍDAS (✅): 20 etapas

Fases 0-7 completas, incluindo múltiplas correções pós-auditoria. A Fase 8 teve múltiplas sub-etapas resolvidas (schema compartilhado, fence embutido, validação AST, sincronia de contrato, economia de tokens, reordenação do pipeline, validação de FK, correção de fabricação de referência).

### Etapas PENDENTES (⏳): 2 etapas

| ID | Resumo |
|---|---|
| `fase-8-delegado-sem-fallback-headless` | Quando o modo delegado dá timeout (ADE não responde), o pipeline falha direto em vez de cair automaticamente para o modo headless que já está configurado no `.env`. Viola o princípio de universalidade. |
| `fase-8-sem-teste-integracao-entre-scripts` | A Fase 8 só gera testes isolados por script — nenhum teste verifica se os scripts funcionam compostos entre si (ex: `coletar_habitos()` não retornava `lastrowid`, mas os testes unitários passavam porque nunca usavam o valor de retorno). |

### Etapas com status especial (🔶)

| ID | Status | Resumo |
|---|---|---|
| `fase-8-inicio` | MECÂNICA PROVADA COM LLM REAL — RESULTADO REAL FOI FALHA (11/20 testes, 55%) | A ferramenta relatou a falha corretamente; foi o commit de documentação que maquiou o resultado. Números e status corrigidos para bater com o `_phase_08_index.json` real. |
| `fase-8-generalizacao` | TESTADO — GATE I3 REPROVOU NAS 2 IDEIAS | Pipeline generaliza para domínios diferentes mas tem 2 gaps sistêmicos (contrato cross-script e tipos JSON). |

---

## 2) Resultado Real dos Testes

```
============================= 204 passed in 5.10s ==============================
```

**204 testes, 0 falhas, 0 skips, 5.10 segundos.** Resultado real obtido com `python -m pytest tests/ -v`.

---

## 3) Segredos/Credenciais Hardcoded

**Nenhum segredo encontrado.** Grep por `sk-`, `API_KEY="..."`, `token="..."` em `.py` e `.json` retornou zero matches com valores reais. As únicas ocorrências de "hardcoded" são em:

- `G_BLOQUEAR_SEGREDOS.py` — é o próprio gate que **bloqueia** commits com segredos
- `AUDITAR_COMPARATIVO_HARNESS.py` — comentário documentando um achado histórico

O `.env` **não está tracked pelo git** (verificado com `git ls-files`).

---

## 4) .gitignore vs .env

**Cobertura adequada.** Linhas 44-46 do `.gitignore`:

```
.env
.env.*
!.env.example
```

Cobre `.env`, qualquer variação (`.env.local`, `.env.production`), e exclui explicitamente `.env.example` para que seja versionado. Correto.

---

## 5) Análise de 08_implementador.py e utils_delegacao.py — Falhas do LLM escondidas?

**NÃO. O código é honesto sobre falhas.** Pontos específicos:

- **`08_implementador.py:387-398`**: Se o LLM não responde (`resposta is None`), retorna `None` e a fase falha. Se o JSON não tem `codigo`/`teste`, imprime aviso e retorna `None`. Não maquia.
- **`08_implementador.py:410-467`**: Loop de correção — se esgota `MAX_TENTATIVAS_POR_SCRIPT`, marca `falhou_apos_tentativas = True` e retorna. Não finge sucesso.
- **`08_implementador.py:262-264`**: Se gates falham, imprime "FASE FALHOU" e retorna `None`. O `_gerar_index()` registra `status: 'FALHOU'` e `requer_intervencao_manual: true`.
- **`utils_delegacao.py:257-259`**: Timeout delegado retorna `None` explicitamente.
- **`utils_delegacao.py:342-347`**: Erro no headless loga o erro real e retorna `None` após esgotar tentativas.

**Única ressalva**: o `utils_delegacao.py` não faz fallback automático de delegado→headless no timeout (justamente a etapa `fase-8-delegado-sem-fallback-headless` que está PENDENTE). Mas isso não é "esconder" — é uma feature não implementada.

---

## 6) README/AGENTS.md documentam como configurar credenciais?

**Parcialmente — com problemas reais:**

- **`.env.example`** existe e está bem documentado (26 linhas, com provedores Groq, NVIDIA, OpenRouter, TogetherAI, OpenAI compatível). Isso é bom.
- **README.md** descreve o projeto ORIGINAL (análise de listas YouTube), NÃO o aidd-generator. O README inteiro é sobre `proj_yt-list` com gates G0/G1/G2, YouTube API, `yt-dlp`, etc. Alguém que clone o repo vai ler o README e não vai entender que a ferramenta é um gerador de projetos AIDD.
- **AGENTS.md** documenta a estrutura e workflow, mas **não tem seção "Getting Started" ou "Como configurar"** para um clonador externo. Não menciona `.env.example`, `requirements-dev.txt`, ou como rodar os testes.
- **`requirements.txt`** não existe na raiz (só `requirements-dev.txt`). O README menciona um `requirements.txt` que não está no repo.

---

## 7) Veredito

# APTO COM RESSALVAS

### O que está BOM (não bloqueia)

- 204 testes passando, 0 skips, cobertura ~93%
- Zero segredos hardcoded, `.env` gitignoreado corretamente
- Falhas do LLM reportadas honestamente (não maquiadas)
- Pipeline Fases 0-7 sólido e provado com múltiplos harnesses
- Fase 8 mecanicamente funcional (gates I1-I4, validação AST, schema compartilhado)
- `.env.example` existe e documenta provedores
- Gate de pre-commit (`G_BLOQUEAR_SEGREDOS`) impede commits com credenciais

### Bloqueadores REAIS para publicar no GitHub hoje

| # | Bloqueador | Severidade | Esforço |
|---|---|---|---|
| 1 | **README.md descreve projeto errado** (YouTube analysis, não aidd-generator). Qualquer clonador vai ficar confuso. | ALTA | Médio |
| 2 | **2 etapas PENDENTES** no PLANO — fallback delegado→headless e testes de integração entre scripts. Não são bloqueadores técnicos para publicar, mas são gaps documentados que reduzem a confiabilidade da Fase 8. | MÉDIA | Baixo-Médio |
| 3 | **Sem LICENSE file** — o README diz "projeto privado" mas quer publicar no GitHub. Precisa de uma licença explícita (MIT, Apache 2.0, etc). | ALTA | Mínimo |
| 4 | **Sem instruções de setup para contribuidor externo** — não documenta como instalar dependências (`pip install -r requirements-dev.txt`), rodar testes (`pytest tests/ -v`), ou configurar `.env` a partir do `.env.example`. | MÉDIA | Baixo |
| 5 | **`requirements.txt` referenciado no README mas não existe** — só existe `requirements-dev.txt`. | BAIXA | Mínimo |
| 6 | **Fase 8 com taxa de sucesso real de ~55-91%** dependendo da ideia — o gerador de código funcional não é 100% confiável ainda. OK para beta público, mas precisa de disclaimer honesto. | MÉDIA | N/A (documentar) |

### Resumo final

A **infraestrutura** (testes, gates, transparência, segurança) está sólida. O que falta para GitHub é basicamente **embalagem**: README correto, licença, instruções de setup, e um disclaimer sobre a maturidade da Fase 8. Nenhum desses é difícil — é trabalho de 1-2 horas.
