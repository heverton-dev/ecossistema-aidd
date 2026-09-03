# AGENTS — Padrão Universal para Todos os Harness

**Versão:** 1.0  
**Aplicável a:** Claude Code, Codex, Gemini CLI, OpenCode, MimoCode, Hermes, DeepSeek, etc.  
**Data:** 30/08/2026

> Este arquivo é a **fonte de verdade única** para configuração de agentes.  
> Não há duplicação: todos os harness apontam aqui via symlink.

---

## ⚖️ LEI FUNDAMENTAL: TRANSPARÊNCIA TOTAL

🔐 **INEGOCIÁVEL**

```
NADA DEVE FICAR OCULTO AO USUÁRIO
O INTUITO É DAR O PODER E CONHECIMENTO
AFINAL: CONHECIMENTO É PODER!
```

**Aplicação em tudo neste projeto:**
- ✅ Qual modelo está sendo usado (explícito no output)
- ✅ Quantos tokens foram consumidos (rastreado em JSON)
- ✅ Que decisões foram tomadas (log estruturado)
- ✅ Como reproduzir resultado (entrada + seed documentados)
- ✅ Alternativas disponíveis (educação ao usuário)

---

## Visão Geral: Metodologia AIDD

Este projeto está estruturado segundo a **metodologia AIDD (AI-Driven Development)** com as 5 Camadas de Engenharia Agêntica:

1. **Contratos e Schemas** — JSON Schema Draft 2020-12 com tipagem estrita
2. **Determinismo Primeiro** — Toda operação mecânica roda em Python local (Zero Token de LLM)
3. **Gates Mecânicos** — Validações que retornam `exit 0` (sucesso) ou `exit 1` (erro)
4. **Persistência Estruturada** — Estado em `PLANO-EXECUCAO-ESTRUTURADO.json` (banco de verdade)
5. **Bundles Modulares** — Artefatos entregues em estrutura autocontida e reproduzível

---

## 🚀 Workflow Estruturado (Obrigatório)

**Arquivo central:** `PLANO-EXECUCAO-ESTRUTURADO.json` (raiz do projeto)

**Por quê?** Sessões novas leem JSON (~5k tokens), não histórico (~50k tokens)  
→ **90% economia de tokens** + **contexto limpo** + **zero inconsistência**

**Fluxo:**
1. Leia `PLANO-EXECUCAO-ESTRUTURADO.json` (2-3 min)
2. Procure próxima etapa com status ⏳ PENDENTE
3. Implemente conforme JSON dita
4. Teste contra `criterios_sucesso`
5. Marca ✅ no JSON, commita
6. Próxima sessão lê JSON atualizado

**Detalhes completos:** Ver `AGENTS-WORKFLOW.md` (neste diretório)

---

## Princípios INEGOCIÁVEIS

### 1. Zero Alucinação
- Toda claim tem fonte (commit, arquivo, teste)
- Toda métrica é medida real (tokens via `resposta.usage`, não hardcoded)
- Nenhum número é inventado

**Check:** Se código tiver `.get('fake_valor')`, `números_fixos`, ou `pytest.skip()`, é automaticamente rejeitado.

### 2. Transparência Total
- Nada fica "apenas global" ou em artifacts
- Tudo commitado, versionado, rastreável
- Usuário e LLM têm acesso total

**Check:** `git log --oneline` mostra histórico completo.

### 3. Determinismo
- Se é Python puro = design correto (zero LLM)
- Se é LLM = tem economia tech aplicada (rtk, caveman, headroom, lean-ctx)

**Check:** Fase com 100% LLM deve estar documentada por quê (síntese, análise, etc).

### 4. Universalidade
- Funciona com qualquer harness (Claude Code, Codex, Gemini CLI, etc.)
- Funciona com qualquer LLM (Anthropic, OpenAI, Google, NVIDIA, Cerebras, Ollama)
- Zero API key forçada (protocolo delegado, fallback headless)

**Check:** Se força credencial específica, quebra universalidade.

### 5. Zero Duplicidade Desnecessária
- Um arquivo central, symlinks em todos os harness
- Não há `CLAUDE.md`, `CODEX.md`, `GEMINI.md` — todos apontam para `AGENTS.md`
- Manutenção centralizada

**Check:** Estrutura de diretórios (ver abaixo).

---

## Estrutura de Diretórios

```
aidd-generator/
├── AGENTS.md                              # ⭐ Este arquivo (fonte única)
├── AGENTS-WORKFLOW.md                     # ⭐ Workflow detalhado (fonte única)
├── PLANO-EXECUCAO-ESTRUTURADO.json        # ⭐ Banco de verdade entre sessões
│
├── .claude/                               # Claude Code
│   ├── CLAUDE.md → ../AGENTS.md           # Symlink (ou cópia sincronizada)
│   ├── WORKFLOW-ESTRUTURADO.md → ../AGENTS-WORKFLOW.md
│   └── ...
│
├── .codex/ (quando criado)                # Codex
│   ├── CODEX.md → ../AGENTS.md            # Symlink
│   ├── WORKFLOW-ESTRUTURADO.md → ../AGENTS-WORKFLOW.md
│   └── ...
│
├── .gemini/ (quando criado)               # Google Gemini CLI
│   ├── GEMINI.md → ../AGENTS.md           # Symlink
│   ├── WORKFLOW-ESTRUTURADO.md → ../AGENTS-WORKFLOW.md
│   └── ...
│
├── docs/
│   ├── PRINCIPIO-UNIVERSALIDADE.md        # Protocolo delegado + headless
│   ├── AUDITORIA-PRODUCAO-2026-08-30.md   # Auditoria de produção
│   └── ...
│
├── scripts/
│   ├── pipeline_completo.py               # Orquestrador do pipeline de 8 fases
│   ├── phases/
│   │   ├── utils_delegacao.py             # Protocolo LLM universal
│   │   ├── utils_modelo.py                # Resolução e detecção de modelos
│   │   ├── 01_pesquisador.py
│   │   ├── 02_analisador.py               # ✅ Delegado ativo
│   │   ├── 03_designer.py                 # ✅ Delegado ativo
│   │   ├── 04_decisor.py
│   │   ├── 05_criador.py
│   │   ├── 06_documentador.py
│   │   ├── 07_analisador.py
│   │   └── 08_implementador.py            # ✅ Implementação funcional (opcional)
│   └── ...
│
├── .aidd/
│   └── LEI-FUNDAMENTAL-TRANSPARENCIA.md   # Lei inegociável
│
└── ...
```

---

## Como Usar Este Arquivo

### Para Usuário
```bash
# Ver configuração do projeto
cat AGENTS.md                    # Lei Fundamental + Princípios

# Ver workflow detalhado
cat AGENTS-WORKFLOW.md           # Passo-a-passo completo

# Ver plano de implementação
cat PLANO-EXECUCAO-ESTRUTURADO.json  # Todas as etapas + status
```

### Para Agente Novo (em sessão nova)
```
1. Leia PLANO-EXECUCAO-ESTRUTURADO.json (2-3 min)
2. Procure próxima etapa com status ⏳ PENDENTE
3. Leia AGENTS.md (este arquivo) — princípios são inegociáveis
4. Leia AGENTS-WORKFLOW.md — entenda workflow pós-conclusão
5. Implemente, teste, marca ✅ no JSON
```

### Para Novo Harness (Codex, Gemini, etc.)
```bash
# Criar estrutura sem duplicar:
mkdir -p .codex
ln -s ../AGENTS.md .codex/CODEX.md
ln -s ../AGENTS-WORKFLOW.md .codex/WORKFLOW-ESTRUTURADO.md

# Git rastreia symlinks nativamente:
git add .codex/
git commit -m "feat: suporte a Codex harness (symlinks centrais)"
```

---

## Workflow Pós-Conclusão de Etapa

**Após cada implementação (conforme AGENTS-WORKFLOW.md):**

1. ✅ Verificar todos `criterios_sucesso`
2. ✅ Testar (pytest, demo, import, etc.)
3. ✅ Commitar com referência ao JSON
4. ✅ Atualizar `PLANO-EXECUCAO-ESTRUTURADO.json` (status → ✅)
5. ✅ Commitar JSON
6. ✅ Gerar prompt para próxima sessão

---

## Princípio: Zero Duplicidade Desnecessária

Este padrão é AIDD Camada 5 (Bundles Modulares) aplicado a configuração:

**Antes (anti-padrão):**
```
CLAUDE.md (100 linhas)
CODEX.md (100 linhas — cópia de CLAUDE.md)
GEMINI.md (100 linhas — cópia de CLAUDE.md)
Manutenção: atualizar 3 arquivos se mudar algo
Risco: inconsistência (alguém esquece de atualizar um)
```

**Depois (padrão):**
```
AGENTS.md (100 linhas — fonte única)
.claude/CLAUDE.md → ../AGENTS.md (symlink, 0 bytes)
.codex/CODEX.md → ../AGENTS.md (symlink, 0 bytes)
.gemini/GEMINI.md → ../AGENTS.md (symlink, 0 bytes)
Manutenção: editar AGENTS.md uma vez
Risco: zero inconsistência
```

---

## Gate de Compatibilidade de Harness (G_HARNESS_COMPAT)

**O que é:** Detecção automática de capacidades de cada harness.

**Como funciona:**
```bash
python scripts/gates/G_HARNESS_COMPAT.py
# Detecta harness (Claude Code? Codex? Gemini?)
# Testa orquestração via protocolo delegado
# Testa fallback headless (litellm)
# Atualiza HARNESS-COMPAT.json com resultado REAL
```

**Resultado:** Universalidade garantida
- ✅ Funciona em qualquer harness (detecta automaticamente)
- ✅ Adapta-se: orquestração OU headless (conforme suportado)
- ✅ Transparente: arquivo HARNESS-COMPAT.json mostra status real

**Padrão Template:** Este gate é copiado para TODO projeto criado por `aidd-generator`.

---

## Próximas Referências

- **Workflow detalhado:** `AGENTS-WORKFLOW.md`
- **Plano de implementação:** `PLANO-EXECUCAO-ESTRUTURADO.json`
- **Protocolo LLM universal:** `docs/PRINCIPIO-UNIVERSALIDADE.md`
- **Compatibilidade de harness:** `HARNESS-COMPAT.json` + `scripts/gates/G_HARNESS_COMPAT.py`
- **Lei Fundamental:** `.aidd/LEI-FUNDAMENTAL-TRANSPARENCIA.md`

---

**Última atualização:** 30/08/2026  
**Aplicável a:** Todos os agentes, harness, usuários deste projeto  
**Status:** Oficial, imutável (só adiciona seções, nunca remove)
