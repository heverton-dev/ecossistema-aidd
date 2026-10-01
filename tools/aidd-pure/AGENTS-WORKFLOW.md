# Workflow Estruturado — Modelo AIDD com JSON Persistente

**Data:** 30/08/2026  
**Status:** Padrão oficial para todo e qualquer trabalho neste projeto  
**Aplicável a:** Todos os agentes (Claude Code, novos agentes em sessões diferentes, etc.)

---

## O Conceito

Este projeto usa um **arquivo JSON como banco de verdade** entre sessões. Isso evita:
- ❌ Recarregar contexto histórico (economia 90% tokens)
- ❌ Re-explicar decisões já tomadas
- ❌ Risco de inconsistência (o JSON é a fonte, não o histórico)

**Resultado:** novo agente lê JSON (2min), sabe TUDO, implementa direto.

---

## Arquivo Central: `PLANO-EXECUCAO-ESTRUTURADO.json`

Este arquivo é:
- ✅ **Obrigatório** — sempre está no projeto
- ✅ **Atualizado** — após cada etapa, flageado ✅
- ✅ **Referência** — agentes novos começam aqui
- ✅ **Histórico** — `git log PLANO-EXECUCAO-ESTRUTURADO.json` mostra evolução

---

## Workflow Padrão (para toda implementação)

### Sessão N (começando)

**1. Cole/Leia o JSON**
```bash
cat PLANO-EXECUCAO-ESTRUTURADO.json | head -100
```

**2. Identifique próxima etapa**
```json
{
  "id": "fase-0-correcao-2",
  "status": "⏳ PENDENTE",
  "criterios_sucesso": ["✓ input() real", "✓ Gate C2 falha"]
}
```

**3. Implemente conforme JSON dita**
- Siga `decisoes` do JSON
- Teste contra `criterios_sucesso` (não achismo, não "acho que ficou bom")
- Sem desvios — o JSON é a especificação

---

### Após implementação (ainda Sessão N)

**1. Verificar Criterios Sucesso**
```python
# Exemplo para Correção 2/5
✓ input() retorna valor real (testado com stdin simulado)
✓ Gate C2 verifica Path.resolve().exists() (pode falhar)
✓ --nao-interativo usa heurística coerente (não dict fixo)
```

Se algum falhar → voltar para código, não "flagear de qualquer forma".

**2. Testar**
```bash
pytest tests/test_phase_04.py -v  # todos passam?
python scripts/phases/04_decisor.py "ideia" < <<< "resposta"  # funciona com stdin?
```

**3. Commitar com padrão estruturado**
```bash
git commit -m "fix(fase-0/correcao-2): modal real em 04_decisor.py

**Etapa:** fase-0-correcao-2 (conforme PLANO-EXECUCAO-ESTRUTURADO.json)
**Criterios Sucesso:** 
  ✓ input() de verdade
  ✓ Gate C2 pode falhar realmente
  ✓ --nao-interativo heurística coerente

**Testes:** pytest test_phase_04.py [PASSOU 4/4]
**Próxima Etapa:** fase-0-correcao-3

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"
```

**4. Atualizar JSON**
```json
{
  "id": "fase-0-correcao-2",
  "status": "✅ COMPLETO",           // ← Mudou aqui
  "data_conclusao": "2026-08-30",   // ← Adicionou data
  "commit": "a1b2c3d"               // ← Adicionou hash
}
```

**5. Commitar JSON atualizado**
```bash
git add PLANO-EXECUCAO-ESTRUTURADO.json
git commit -m "docs(fase-0): marca correcao-2 como concluida (commit a1b2c3d)"
```

---

### Comunicar próxima sessão (OBRIGATÓRIO SEMPRE)

**⚠️ ANTES DE FECHAR SESSÃO: Você DEVE fazer isto:**

```bash
# 1. Commitar implementação
git add scripts/phases/*.py [outros arquivos]
git commit -m "fix(fase-0/correcao-N): [descrição]

**Etapa:** fase-0-correcao-N
**Criterios Sucesso:** ✓ ... ✓ ... ✓ ...
**Próxima Etapa:** fase-0-correcao-{N+1}

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>"

# 2. Commitar JSON
git add PLANO-EXECUCAO-ESTRUTURADO.json
git commit -m "docs(fase-0): marca correcao-N como concluida (commit HASH)"

# 3. Verificar commits
git log --oneline | head -2
```

**Depois, comunique assim:**

```markdown
## ✅ Fase 0 - Correção 2/5 COMPLETO

**Commit:** a1b2c3d — fix(fase-0/correcao-2): modal real  
**Criterios Sucesso:** Todos passaram ✓  
**Próxima Etapa:** Fase 0 - Correção 3/5 (06_documentador.py)

---

### Prompt para próxima sessão (copie/cole para nova janela):

# Sessão Nova — Implementar Fase 0 - Correção 3/5

Leia primeiro:
```
PLANO-EXECUCAO-ESTRUTURADO.json (seções: metadata, decisoes_arquiteturais, etapas com id="fase-0-correcao-3")
```

**Objetivo:** Escrever HTML, Markdown, PDF reais em 06_documentador.py

**Criterios Sucesso (do JSON):**
- ✓ Arquivos escritos em disco (verificável com os.path.exists)
- ✓ HTML renderiza no navegador
- ✓ MD é válido (parseable)
- ✓ PDF pode ser aberto

Implemente, teste contra criterios acima, commita, marca ✅ no JSON, repete para próxima.
```

Usuário copia esse prompt, abre nova sessão, cola, e próximo agente sabe EXATAMENTE o que fazer.

---

## Estrutura do JSON (para agentes novos)

```json
{
  "metadata": {
    "versao": "1.0",
    "objetivo_geral": "Implementar 8 Fases AIDD reais",
    "principios_inegociaveis": [
      "Transparência Total",
      "Zero Alucinação",
      "Universalidade"
    ]
  },

  "decisoes_arquiteturais": {
    "protocolo_llm": {
      "decisao": "Delegado (default) + Headless (fallback)",
      "status": "✅ IMPLEMENTADO EM 02_analisador.py, 03_designer.py"
    }
  },

  "etapas": [
    {
      "id": "fase-0-correcao-1",
      "status": "✅ COMPLETO",
      "commit": "6806bad",
      "criterios_sucesso": ["✓ Imports funcionam", "✓ Modo delegado cria arquivo"]
    },
    {
      "id": "fase-0-correcao-2",
      "status": "⏳ PENDENTE",
      "criterios_sucesso": ["✓ input() real", "✓ Gate C2 pode falhar"]
    }
  ]
}
```

**Para agente novo:**
1. Procure por status `⏳ PENDENTE` ou `🔄 PARCIALMENTE`
2. Leia `criterios_sucesso` — isso é o seu "Definition of Done"
3. Implemente, teste, marca ✅
4. Atualiza JSON, commita

---

## Exemplo Real (você pode ver isso agora)

**Correção 1/5 já completa:**
```bash
git show HEAD:PLANO-EXECUCAO-ESTRUTURADO.json | grep -A 10 '"fase-0-correcao-1"'
```

Output:
```json
{
  "id": "fase-0-correcao-1",
  "nome": "Correção 1/5: Protocolo Delegado Universal",
  "status": "✅ COMPLETO",
  "data_conclusao": "2026-08-30",
  "commit": "6806bad"
}
```

Você consegue rastrear exatamente o quê, quando e por quê.

---

## FAQ

**P: E se mudar de ideia durante implementação?**  
R: Atualize o JSON e commita a mudança. O histórico git mostra o quê mudou.  
`git log PLANO-EXECUCAO-ESTRUTURADO.json` é seu audit trail.

**P: O que se não passar em um criterios_sucesso?**  
R: Não flagueia ✅ ainda. Volta para código, arruma, testa novamente.  
O status fica `⏳ PENDENTE` até todos os criterios passarem.

**P: Se perdi a sessão no meio da implementação?**  
R: Sem problema. O JSON ainda diz "próxima_etapa": "fase-0-correcao-2".  
Novo agente abre projeto, lê JSON, retoma de onde parou.

**P: Posso fazer mais de uma etapa por sessão?**  
R: Sim. Basta atualizar JSON e commitar após cada uma.

---

## Principios AIDD Aplicados Aqui

| Camada AIDD | Aplicação |
|---|---|
| **1: Contratos** | JSON é o schema (JSON Schema Draft 2020-12) |
| **2: Determinismo** | Nenhuma decisão é "contexto carregado", é arquivo estruturado |
| **3: Gates** | Cada etapa tem criterios_sucesso testáveis |
| **4: Persistência** | JSON é SQLite equivalente (mas em texto, versionável) |
| **5: Bundles** | Cada conclusão = bundle (commit + JSON atualizado) |

---

## Economia de Tokens (Prova)

**Antes (contexto carregado):**
- Sessão 1: Ler 200KB contexto (50k tokens) + implementar
- Sessão 2: Ler NOVAMENTE 200KB contexto (50k tokens) + implementar  
- Sessão 3: Idem
- **Total:** ~150k tokens de contexto puro

**Depois (JSON estruturado):**
- Sessão 1: Ler 200KB contexto (50k tokens) + implementar + escrever JSON (20KB)
- Sessão 2: Ler JSON (20KB = 5k tokens) + implementar
- Sessão 3: Ler JSON (5k tokens) + implementar
- **Total:** ~60k tokens de contexto puro

**Economia:** ~90k tokens = 60% menos. Para 8 fases: ~360k economizados.

---

## Resumo para Agentes Novos

1. ✓ Cole `PLANO-EXECUCAO-ESTRUTURADO.json` no topo da sessão
2. ✓ Procure por próxima etapa com status ⏳ PENDENTE
3. ✓ Implemente conforme `decisoes` do JSON
4. ✓ Teste contra `criterios_sucesso`
5. ✓ Commita com referência ao JSON
6. ✓ Atualiza JSON (status → ✅, data, commit)
7. ✓ Commita JSON atualizado
8. ✓ Gera prompt para próxima sessão

Pronto. Zero contexto histórico re-carregado. Máxima eficiência.

---

## ⚠️ CHECKLIST FINAL OBRIGATÓRIO

Antes de comunicar que terminou, verifique:

- [ ] **COMMITS FEITOS?**
  - `git log --oneline | head -2` mostra seus commits?
  - Mensagem de commit referencia etapa ID?
  
- [ ] **JSON ATUALIZADO?**
  - `grep "fase-0-correcao-N" PLANO-EXECUCAO-ESTRUTURADO.json` mostra status ✅ COMPLETO?
  - Commit hash está no JSON?

- [ ] **PROMPT PARA PRÓXIMA SESSÃO?**
  - Extraiu "id": "fase-0-correcao-{N+1}" do JSON?
  - Gerou prompt estruturado (use template acima)?
  - **ENVIE O PROMPT JUNTO com a comunicação de conclusão**

**Se algum item estiver ❌, VOLTE e corrija antes de sinalizar!**

---

**Última atualização:** 30/08/2026  
**Aplicável a:** Toda sessão, agente, ou usuário consultando este projeto
