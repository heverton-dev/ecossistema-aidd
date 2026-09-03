# Princípio da Universalidade — Correção 1/5, Fase 0

**Data:** 30/08/2026  
**Status:** Implementado em Correção 1/5 (commit 50865c5+)  
**Escopo:** Fase 0 — Núcleo determinístico universal

---

## O Problema

Quando forçamos o usuário a inserir uma chave de API **diferente da que usa no seu harness**, quebramos a regra de **ser fácil e replicável em qualquer ambiente**:

```
Claude Code (Haiku/Sonnet/Opus/Fable)
     ↓
Codex, Gemini CLI, OpenCode, MimoCode, Hermes, DeepSeek Harness
     ↓
Todos querem rodar o MESMO projeto
     ↓
❌ Pedir chave API nova = quebra a universalidade
```

---

## A Solução: Protocolo Delegado Agnóstico

### Modo Delegado (default — recomendado, universal)

```
Fase (02_analisador, 03_designer, etc.) escreve um arquivo JSON:
  .aidd/cache/_llm_request_{uuid}.json
  {
    "id": "abc12345",
    "fase": "phase_02",
    "modelo_sugerido": "claude-opus-5",
    "prompt": "Analise esta ideia..."
  }

                           ↓ (exit code 2 = aguardando orquestrador)

Orquestrador ATIVO (Claude Code, Codex, qualquer ADE) detecta isso.
Usa SEUS PRÓPRIOS acessos (já configurados, já pagos).
Responde escrevendo:
  .aidd/cache/_llm_response_{uuid}.json
  {
    "conteudo": "resposta LLM",
    "tokens_consumidos": 1234,
    "modelo_usado": "claude-opus-5",
    "timestamp_resposta": "2026-08-30T..."
  }

                           ↓

Fase re-executa, lê resposta, continua.

RESULTADO: Zero credencial nova necessária. Usa a ADE que já está ativa.
```

**Vantagens:**
- ✅ Funciona com QUALQUER ADE (Claude Code, Codex, Gemini, OpenCode, etc.)
- ✅ Funciona com QUALQUER LLM (Anthropic, OpenAI, Google, NVIDIA, Cerebras, Ollama)
- ✅ Zero API key nova
- ✅ Não quebra universalidade

**Como funciona tecnicamente:**
- O protocolo é baseado em **arquivos JSON**, nada mais
- Toda ADE consegue ler/escrever arquivos no projeto
- A fase aguarda de forma inteligente (`time.sleep(0.5)` com timeout), não bloqueia

---

### Modo Headless (fallback — para CI/CD, scripts standalone)

Se **nenhuma ADE está orquestrando** (ex: rodando num container CI/CD):

```
Fase detecta que não há orquestrador ativo (env vars de harness = vazios).

Chama litellm.completion() DIRETO com a credencial do LLM_MODEL env var.

Requer: uma chave de API configurada (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.)
```

**Vantagens:**
- ✅ Continua funcionando mesmo sem ADE
- ✅ CI/CD pode usar qualquer LLM via LLM_MODEL + chave
- ✅ Fallback gracioso, não quebra tudo

**Requisitos:**
- Configure `LLM_MODEL` env var (ex: `anthropic/claude-opus-5`, `openai/gpt-4o`)
- Configure a chave de API do provedor (ex: `ANTHROPIC_API_KEY`)

---

## Implementação Técnica

### Arquivo novo: `scripts/phases/utils_delegacao.py`

Define a interface unificada:

```python
def solicitar_llm(
    prompt: str,
    contexto: str,
    fase: str,
    modo: Optional[str] = None,  # Auto-detecta se None
    modelo: Optional[str] = None,
    timeout_delegacao: int = 30
) -> Optional[Dict]:
    """
    Interface unificada. Escolhe automaticamente:
    - Modo Delegado se ADE detectada (CLAUDECODE=1, etc.)
    - Modo Headless se nenhuma ADE
    """
```

### Modificações em Fases

**02_analisador.py:**
```python
# Antes:
import litellm
resposta = litellm.completion(...)

# Depois:
from utils_delegacao import solicitar_llm
resposta = solicitar_llm(prompt, contexto, "phase_02")
```

**03_designer.py:**
```python
# Antes: 5x litellm.completion() em ThreadPoolExecutor

# Depois: 5x solicitar_llm() em ThreadPoolExecutor (idêntico, via protocolo)
```

---

## Como Rodar

### Cenário 1: No Claude Code (Modo Delegado — recomendado)

```bash
# Zero config necessário
python scripts/phases/02_analisador.py "Minha ideia de projeto"
```

**O que acontece:**
1. Script detecta `CLAUDECODE=1` (env var do harness)
2. Escreve requisição em `.aidd/cache/_llm_request_*.json`
3. Aguarda resposta (máx. 30s)
4. Claude Code responde automaticamente (se ativo)
5. Script lê resposta e continua

✅ Zero credencial nova.

### Cenário 2: Em outro ADE (Codex, Gemini CLI, etc.)

```bash
# Zero config necessário (princípio: o que funciona em Claude Code funciona everywhere)
python scripts/phases/02_analisador.py "Minha ideia de projeto"
```

✅ Mesmo protocolo, mesmo resultado. Universalidade funcionando.

### Cenário 3: CI/CD ou headless local (Modo Headless)

```bash
export LLM_MODEL=anthropic/claude-opus-5
export ANTHROPIC_API_KEY=sk-ant-...

# Força modo headless explicitamente:
python scripts/phases/02_analisador.py "Minha ideia" --modo headless
```

✅ Funciona sem ADE. Requer credencial, mas é esperado em CI/CD.

---

## Detecção Automática de Modo

Prioridade (em ordem):

1. **Argumento explícito:** `--modo delegado|headless` → usa aquele
2. **Env var de ADE:** `CLAUDECODE=1` → delegado; nada → headless
3. **Fallback:** sem ADE detectada → headless com aviso

```
Detectado: Claude Code (CLAUDECODE=1)
→ Usando Modo Delegado

vs.

⚠️  Nenhuma ADE detectada — usando Modo Headless
   (Configure LLM_MODEL e credencial para usar este modo)
```

---

## Vantagens Frente ao Design Anterior (litellm sempre)

| Aspecto | Antes (litellm) | Agora (Delegado+Headless) |
|---|---|---|
| Credencial necessária em Claude Code? | ✅ SIM | ❌ NÃO |
| Funciona em qualquer ADE? | ❌ Só testado em Claude Code | ✅ SIM |
| Funciona em headless/CI? | ✅ SIM (com chave) | ✅ SIM (com chave) |
| Princípio: "fácil + replicável"? | ❌ Força chave nova | ✅ Zero chave nova se ADE ativa |
| Universalidade? | ⚠️ Parcial | ✅ Total |

---

## Próximos Passos (Fases 0 Correção 2-5)

Após Correção 1/5 estar estável e testada:

- **Correção 2/5:** `04_decisor.py` — modal genuinamente interativo
- **Correção 3/5:** `06_documentador.py` — escrever arquivos reais (HTML, MD, PDF)
- **Correção 4/5:** `07_analisador.py` — auto-crítica de verdade
- **Correção 5/5:** Testes reais (6 fases, >70% coverage)

Todas as fases usarão o mesmo protocolo delegado — zero mudanças em princípio.

---

## FAQ

**P: E se rodar em outro harness (Codex, Gemini CLI) — como o Codex "sabe" responder?**

R: O protocolo não é específico do Claude Code. Qualquer ferramenta que:
1. Execute subprocessos Python
2. Tenha acesso ao sistema de arquivos do projeto
3. Tenha um LLM configurado

...consegue monitorar `.aidd/cache/` e responder. Isso requer um pequeno addon por ADE (ler arquivo, chamar LLM, escrever resposta), mas é **simples e universal** — não depende de APIs específicas.

---

**P: E se o timeout passar — o que acontece?**

R: Fase falha com:
```
✗ Timeout ao aguardar resposta delegada (ID: abc12345)
```

Significa: nenhuma ADE respondeu em 30s. Usuário pode:
1. Certificar que o ADE ainda está ativo
2. Tentar novamente
3. Usar `--modo headless` com LLM_MODEL configurado

---

**P: O protocolo delegado é suficiente para passar dados grandes (ex: 50MB)?**

R: Arquivos JSON no disco **não têm limite de tamanho** (além do HD). Sim, funciona para 50MB.

Contudo: Phase 1 (Pesquisa) coleta metadados, não arquivos. Não esperamos dados > 1MB em práticas comuns.

---

**Última atualização:** 30/08/2026  
**Próxima revisão:** Após Correção 1/5 ser testada com sucesso
