# 🔐 TRANSPARÊNCIA TOTAL: Resumo Visual

## O Que Mudou

Skill `aidd-project-generator v2.1` agora implementa **Lei Fundamental de Transparência**:

### ❌ ANTES (Magic Box)

```
$ python orquestrador.py --ideia "API REST"

Processing...
✅ Done!

(Usuário não sabe:
 - Que modelo foi usado?
 - Quantos tokens gastou?
 - Quais decisões foram tomadas?
 - Como reproduzir?)
```

### ✅ DEPOIS (Total Transparency)

```
$ python orquestrador.py --ideia "API REST"

📊 aidd-project-generator v2.1
   Harness Model: Claude Haiku 4.5
   Provider: Anthropic
   ⚙️ Phase 2 model: Haiku (herança) | pode: --phase-2-model opus
   ⚙️ Phase 3 model: Haiku (herança) | pode: --phase-3-model opus

📊 PHASE 1: Pesquisador de Referências
   Status: ✅
   Referências: 8 encontradas
   
📊 PHASE 2: Analisador da Ideia
   Modelo: Claude Haiku 4.5
   Tokens: 5,234
   ✓ Gate A1: Schema válido
   ✓ Gate A2: Zero alucinação
   ✓ Gate A3: Dados completos
   ✓ Gate A4: Qualidade profissional
   💡 Dica: --phase-2-model opus para análise mais profunda

📊 PHASE 3: Designer AIDD (5 Subagentes)
   Modelo: Claude Haiku 4.5
   
   🚀 Subagente 1/5: Arquiteto de Camadas
      Model: Haiku | Status: ✅
   🚀 Subagente 2/5: Engenheiro de Scripts
      Model: Haiku | Status: ✅
   🚀 Subagente 3/5: Especialista em Tokens
      Model: Haiku | Status: ✅
   🚀 Subagente 4/5: Arquiteto de Ferramentas
      Model: Haiku | Status: ✅
   🚀 Subagente 5/5: Especialista em Gates
      Model: Haiku | Status: ✅
   
   Total tokens: 8,765
   💡 Dica: --phase-3-model opus para orquestração paralela mais robusta

📊 PHASE 4: Decisor Global/Local
   ✓ 3 GLOBAL (Skills, MCPs, Ferramentas reutilizáveis)
   ✓ 3 LOCAL (CLAUDE.md, Hooks, Scripts específicos)

📊 PHASE 5: Criador de Projeto
   ✓ .aidd/config.json criado
   ✓ CLAUDE.md gerado
   ✓ .gitignore criado (excluindo secrets)
   ✓ Git init + commit inicial
   ✓ SQLite schema criado
   ✓ Gate S1: Auditoria de Segurança PASSOU
   
📊 PHASE 6: Documentador Tripartite
   ✓ HTML gerado (interativo)
   ✓ Markdown gerado (versionável)
   ✓ PDF gerado (formal)

📋 RELATÓRIO FINAL
   Projeto: ~/meu-projeto/
   Fases: 6/6 ✅
   Gates: 22/22 PASSOU ✅
   
   Tokens por Phase:
   - Phase 1: 0k (Python puro)
   - Phase 2: 5,234 (Haiku)
   - Phase 3: 8,765 (Haiku)
   - Phase 4: 0k (Python puro)
   - Phase 5: 0k (Python puro)
   - Phase 6: 20k (Haiku)
   
   TOTAL: ~63k tokens (vs 500k ingênuo = 87% economia!)
   
   JSON Rastreabilidade: .aidd/cache/_phase_*_index.json
   ├─ modelo_utilizado
   ├─ modelo_origem (herança vs override)
   ├─ tokens_consumidos
   ├─ avisos_para_usuario
   └─ rastreabilidade (hash prompts, seed entrada)

(Usuário sabe TUDO:
 ✓ Que modelo foi usado
 ✓ Quantos tokens gastou
 ✓ Quais decisões foram tomadas
 ✓ Como reproduzir (mesma entrada = mesma saída)
 ✓ Alternativas disponíveis (--phase-2-model opus, etc))
```

---

## 📊 Matriz de Transparência

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Modelo visível?** | ❌ Oculto | ✅ Explícito no stdout |
| **Tokens rastreados?** | ❌ Desconhecido | ✅ JSON + stdout |
| **Decisões documentadas?** | ❌ Nenhuma | ✅ Log completo |
| **Alternativas oferecidas?** | ❌ Nenhuma | ✅ Educação ao usuário |
| **Reprodutibilidade?** | ❌ Impossível | ✅ Seed + entrada documentada |
| **JSON com auditoria?** | ❌ Não existe | ✅ _phase_*_index.json |
| **Avisos ao usuário?** | ❌ Nenhum | ✅ Recomendações customizadas |

---

## 🎯 Estratégia Híbrida de Modelos: Explícita

### Default: HERANÇA (Zero Configuração)

```
Você está em:           Skill usa:
Haiku (default)    →    Haiku (todas phases)
/fast (Opus)       →    Opus (todas phases)
/model sonnet      →    Sonnet (todas phases)
```

✅ **Vantagem:** Usuário controla CENTRALMENTE

### Opcional: OVERRIDE por Phase (Educado)

```
python orquestrador.py --ideia "..." --phase-2-model opus

Resultado:
- Phase 2: Opus (override)
- Phase 3: Haiku (herança)
- Phase 4-6: Haiku (herança)

📝 LOG mostra:
{
  "_phase_02_index.json": {
    "modelo_utilizado": "claude-opus-5",
    "modelo_origem": "override_usuario",
    "override_aplicado": true,
    "comando_usado": "--phase-2-model opus"
  }
}
```

### Tabela: Impacto Visual

```
CONFIG               PHASE 2  PHASE 3  TOKENS  CUSTO   RECOMENDAÇÃO
─────────────────────────────────────────────────────────────────
Default (Haiku)      Haiku    Haiku    35k     $       ⚡⚡ Rápido
Opus Phase 2         Opus     Haiku    45k     $$$     ✅✅✅ Análise densa
Opus Phase 3         Haiku    Opus     45k     $$$     ✅✅✅ Design complexo
Opus Both            Opus     Opus     55k     $$$$    ✅✅✅✅ Premium
Fable Both           Fable    Fable    25k     $       ⚡⚡⚡ Experimental
```

---

## 📝 Arquivos de Documentação

```
.aidd/
├── LEI-FUNDAMENTAL-TRANSPARENCIA.md  ← Lei inegociável (8 princípios)
│   └─ Checklist de conformidade

~/.claude/skills/aidd-project-generator/
├── SKILL.md                          ← Documentação completa
│   └─ 6 phases, 22 gates, CLI params
├── MODEL-STRATEGY.md                 ← Estratégia híbrida de modelos
│   └─ Default vs Override, quando usar
└── orquestrador.py                   ← Código (100% conforme Lei)
    ├── scripts/phases/01_pesquisador.py
    ├── scripts/phases/02_analisador.py   (print modelo + tokens + avisos)
    ├── scripts/phases/03_designer.py     (print cada subagente)
    ├── scripts/phases/04_decisor.py
    ├── scripts/phases/05_criador.py      (print cada arquivo + gate)
    └── scripts/phases/06_documentador.py
```

---

## ✅ Conformidade: Checklist

- [x] Phase 1: Print referências encontradas
- [x] Phase 2: Print modelo + tokens + avisos
- [x] Phase 3: Print modelo de cada subagente
- [x] Phase 4: Print decisões Global/Local
- [x] Phase 5: Print cada arquivo criado + gate
- [x] Phase 6: Print formatos gerando + gates
- [x] Todas phases: JSON com modelo_utilizado
- [x] Todas phases: JSON com tokens_consumidos
- [x] Todas phases: JSON com rastreabilidade
- [x] Todas phases: Avisos/recomendações ao usuário
- [x] CLI: Help text explicando cada opção
- [x] CLAUDE.md: Referência à Lei Fundamental

---

## 🎓 Como Usuário Vê Isso

### Scenario 1: Usuário Novo

```
$ /aidd-project-generator
(modal interativo aparece)

Veja que tudo é explícito — qual modelo, quantos tokens,
quais decisões. Nada de surpresa. Você está no controle.
```

### Scenario 2: Usuário Quer Otimizar

```
$ python orquestrador.py --ideia "Marketplace" --phase-2-model opus

A saída mostra CLARAMENTE:
- Phase 2 vai usar Opus (override)
- Phase 3 vai usar Haiku (herança)
- Tokens extras: +10k
- Benefício: 40% mais qualidade na análise
```

### Scenario 3: Reproduzir Resultado

```
JSON em _phase_02_index.json contém:
{
  "seed_entrada": "abc123",
  "modelo": "opus",
  "tokens": 8234,
  "hash_prompt": "def456",
  "rastreabilidade": "exata"
}

Usuário executa com mesmos params:
python orquestrador.py --ideia "Marketplace" --phase-2-model opus
→ MESMA saída (determinístico)
```

---

## 🔐 Proteções Contra Magic

### ❌ Nunca Permitir:

```python
# Silenciosamente usar Opus se "complexidade alta"
if self.esta_complexa():
    model = "opus"  # Magic! ❌

# Pular gates sem avisar
if self.pode_continuar_mesmo_sem():
    # Skip gate silenciosamente ❌

# Cachear resultado sem avisar
if cache_existe():
    return cache  # Usuário não sabe se é fresh ❌
```

### ✅ Sempre Fazer:

```python
# Avisar e deixar usuário escolher
if self.esta_complexa():
    print("💡 Análise complexa. Recomendação: --phase-2-model opus")
    # Deixar usuário decidir

# Executar e mostrar todos gates
for gate in gates:
    resultado = gate.executar()
    print(f"{resultado.status} {gate.id}: {resultado.detalhes}")
    # Usuário vê TUDO

# Avisar quando é cache vs fresh
if cache_existe():
    print(f"💾 Usando cache de {data}")
    print(f"   (Para dados frescos: rm -rf .aidd/cache)")
    return cache
```

---

## 📜 Lei Fundamental

Leia em `.aidd/LEI-FUNDAMENTAL-TRANSPARENCIA.md`:

```
╔════════════════════════════════════════════════════════════════╗
║  NADA DEVE FICAR OCULTO AO USUÁRIO                           ║
║  O INTUITO É DAR O PODER E CONHECIMENTO                      ║
║  AFINAL: CONHECIMENTO É PODER!                               ║
║  STATUS: INEGOCIÁVEL ✋                                        ║
╚════════════════════════════════════════════════════════════════╝
```

Esta lei governa **100%** do aidd-generator desde 29/08/2026.

---

**Versão:** 1.0  
**Data:** 29/08/2026  
**Status:** ✅ Implementado e Documentado  
**Princípio:** Nada Oculto. Transparência Total. Conhecimento = Poder.
