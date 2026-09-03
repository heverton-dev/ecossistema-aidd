# 🔐 LEI FUNDAMENTAL: TRANSPARÊNCIA TOTAL

## 📜 DECRETO INEGOCIÁVEL

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║  NADA DEVE FICAR OCULTO AO USUÁRIO                           ║
║                                                                ║
║  O INTUITO É DAR O PODER E CONHECIMENTO                      ║
║                                                                ║
║  AFINAL: CONHECIMENTO É PODER!                               ║
║                                                                ║
║  STATUS: INEGOCIÁVEL ✋                                        ║
║  DATA: 29 de Agosto de 2026                                   ║
║  ASSINADO: AIDD Framework                                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
```

---

## ⚖️ O Que Significa

### **Princípio 1: ZERO MAGIA**

❌ **Não permitido:**
```python
# Oculto ao usuário qual modelo está sendo usado
resultado = agent(prompt="...")  # Mystery box!

# Oculto quantos tokens foram consumidos
print("✅ Done!")  # Usuário não sabe o custo

# Oculto decisões tomadas (override de modelo? qual?)
# Sem log explícito do que aconteceu
```

✅ **Permitido:**
```python
# EXPLÍCITO: Qual modelo
print(f"🤖 Usando: {self.model_final}")

# EXPLÍCITO: Quantos tokens
print(f"💾 Consumidos: {tokens_utilizados}k")

# EXPLÍCITO: Por quê essa decisão
print(f"📋 Override? {self.model_override or 'Não, herdando do harness'}")

# EXPLÍCITO: Log rastreável
_registrar_no_json({
    'modelo_utilizado': self.model_final,
    'modelo_origem': 'heranca_harness | override_usuario',
    'tokens': tokens_utilizados,
    'decisao': 'por que foi feita'
})
```

---

### **Princípio 2: TRANSPARÊNCIA EM TEMPO REAL**

Usuário DEVE SABER enquanto código está executando:

```
✅ CORRETO:
   🚀 Phase 3: Subagente "Designer Arquitetural"
      Model: Claude 3.5 Sonnet / GPT-4o (ou herdado do harness)
      Tokens: 8k estimado
      Status: 🔄 Em progresso...
      
   ✅ Resposta recebida
   
   📊 Resultado: 5 camadas AIDD definidas

❌ ERRADO:
   Processing...
   
   Done!
   
   (Usuário não sabe o quê, com qual modelo, quanto custou)
```

---

### **Princípio 3: LOG ESTRUTURADO = RASTREABILIDADE**

Cada phase gera JSON ou registro rastreável com TUDO explícito:

```json
{
  "_phase_02_index.json": {
    "timestamp_inicio": "2026-08-29T16:00:00Z",
    "timestamp_fim": "2026-08-29T16:00:05Z",
    "duracao_segundos": 5.2,
    
    "modelo_utilizado": "claude-haiku-4-5-20251001",
    "modelo_configuracao": {
      "harness_modelo": "claude-haiku-4-5-20251001",
      "override_aplicado": false,
      "razao_nao_override": "Usuário não passou override de modelo"
    },
    
    "tokens": {
      "consumidos": 5234,
      "economizados_cache": 0,
      "estimado_vs_realizado": "5k vs 5.2k ✅"
    },
    
    "gates_executados": [
      {
        "gate_id": "G_SCHEMA_VALIDATION",
        "status": "PASSOU",
        "detalhes_internos": "Campos validados contra JSON Schema Draft 2020-12"
      }
    ],
    
    "avisos_para_usuario": [
      "Análise concluída com sucesso."
    ],
    
    "rastreabilidade": {
      "codigo_executado": "scripts/phases/02_analisador.py",
      "hash_prompt": "abc123def456...",
      "seed_entrada": "ideia_projeto_hash"
    }
  }
}
```

**Usuário PODE:**
- Ver exatamente o quê foi feito
- Verificar decisões tomadas
- Reproduzir resultado (mesma entrada = mesma saída)
- Debugar se algo falhar

---

### **Princípio 4: ESCOLHAS EXPLÍCITAS**

Quando houver opções, TODAS devem estar visíveis:

```
❌ ERRADO (Magic):
   Phase 2 análise concluída ✅

✅ CORRETO (Transparência):
   Phase 2 análise concluída ✅
   
   Configuração usada:
   ├─ Modelo: Claude Haiku 4.5 (herdado do harness)
   ├─ Tokens: 5,234
   ├─ Gates: 4/4 passaram
   ├─ Tempo: 5.2 segundos
   │
   └─ Opções disponíveis:
      • python scripts/pipeline_completo.py "ideia" --pasta destino --implementar-codigo
      • Execução por fases individuais via scripts/phases/
      • --verbose (para ver logs detalhados de cada gate)
```

---

### **Princípio 5: EDUCAÇÃO > AUTOMAÇÃO**

Quando há dúvida entre:
- A) Fazer automaticamente (usuário não sabe que aconteceu)
- B) Perguntar ao usuário (usuário escolhe consciente)

**Sempre escolher B.**

```python
# ❌ ERRADO (Magic)
def _resolver_modelo(self):
    if self.esta_analise_complexa():
        return "opus"  # Secretly upgrades to Opus
    return "haiku"

# ✅ CORRETO (Educação)
def _resolver_modelo(self):
    print("""
    🤔 Esta análise é complexa. Sugestões de execução:
    
    - Rápido / Econômico:
      python scripts/pipeline_completo.py "ideia" --pasta ./meu-projeto
    
    - Completo com implementação de código:
      python scripts/pipeline_completo.py "ideia" --pasta ./meu-projeto --implementar-codigo
    
    Qual você prefere?
    """)
```

---

## 🎯 Aplicação Prática: Checklist por Arquivo

### **scripts/phases/01_pesquisador.py**
- [x] Pesquisa referências e padrões de arquitetura para a ideia
- [x] Exibe referências encontradas e domínios consultados
- [x] Log estruturado com entradas, saídas e rastreabilidade
- [x] Avisos sobre completude da base de conhecimento

### **scripts/phases/02_analisador.py**
- [x] Print modelo sendo usado e origem (harness / override / headless)
- [x] Print tokens estimados e consumidos
- [x] Log estruturado com análise de requisitos e complexidade
- [x] Validação de gates mecânicos e exibição do status no stdout

### **scripts/phases/03_designer.py**
- [x] Decomposição de arquitetura em 5 camadas AIDD
- [x] Print de cada subcomponente / camada projetada
- [x] Log estruturado com contratos e especificações
- [x] Rastreabilidade de prompts e decisões de design

### **scripts/phases/04_decisor.py**
- [x] Avaliação de escopo de ferramentas e regras (GLOBAL vs LOCAL)
- [x] Justificativa impressa e transparente para cada escolha
- [x] Log estruturado com mapa de decisões e symlinks
- [x] Feedback claro sobre trade-offs adotados

### **scripts/phases/05_criador.py**
- [x] Criação de estrutura de arquivos, schemas e scaffolding
- [x] Execução de gates de validação (R1..Rn, integridade de schema)
- [x] Inicialização de repositório e baseline estrutural
- [x] Log estruturado registrando cada arquivo e gate validado

### **scripts/phases/06_documentador.py**
- [x] Geração de documentação completa do projeto (AGENTS.md, PLANO, README)
- [x] Execução de gates de consistência de documentação
- [x] Log estruturado com templates e artefatos gerados
- [x] Verificação de integridade de links e referências

### **scripts/phases/07_analisador.py**
- [x] Auditoria cruzada de consistência entre código, schemas e docs
- [x] Validação de aderência às 5 camadas AIDD
- [x] Relatório estruturado de conformidade e gaps
- [x] Exibição explícita de alertas e recomendações de melhoria

### **scripts/phases/08_implementador.py**
- [x] Geração de código-fonte determinístico e testes funcionais
- [x] Execução de gates de compilação, sintaxe e execução de testes
- [x] Rastreabilidade completa de arquivos gerados e modificados
- [x] Relatório final com métricas reais (testes passando, cobertura, status)

---

## 📋 Regras de Implementação

### **Regra T1: Print Before Computing**

Antes de fazer algo, FALE que vai fazer:

```python
# ❌ Errado
resultado = agent(prompt="...")

# ✅ Correto
print(f"🤖 Enviando para Agent com modelo: {self.model}")
resultado = agent(prompt="...")
```

### **Regra T2: Log After Computing**

Depois de fazer, REGISTRE o que foi feito:

```python
# ❌ Errado
resultado = agent(prompt="...")
print("✅ Done!")

# ✅ Correto
resultado = agent(prompt="...")
tokens_usados = getattr(resultado, 'usage', {}).get('output_tokens', 0)
print(f"✅ Concluído | Tokens: {tokens_usados}")
self._registrar_json({
    'tokens_usados': tokens_usados,
    'modelo': self.model,
    'sucesso': True
})
```

### **Regra T3: Avisos Educativos**

Se há alternativas, eduque:

```python
print(f"""
📊 Fase concluída com sucesso!
   Modelo: {self.model}
   Tokens: {tokens_usados}
   
   💡 Opções para próxima etapa:
      • Executar pipeline completo: python scripts/pipeline_completo.py "sua ideia" --pasta destino --implementar-codigo
      • Executar testes: python -m pytest tests/ -v
""")
```

### **Regra T4: Zero Assunções**

Nunca assuma que o usuário sabe. Sempre explique:

```python
# ❌ Errado
print("Model override applied")

# ✅ Correto
print(f"""
⚙️ Configuração de Execução:
   Harness detectado: {harness_nome}
   Modo: Protocolo Delegado (Zero API Key)
   Destino: {pasta_destino}
""")
```

---

## 🔍 Auditoria: Como Verificar Conformidade

```bash
# 1. Executar pipeline completo do aidd-generator
python scripts/pipeline_completo.py "Ideia do Projeto" --pasta ./saida-projeto --implementar-codigo

# 2. Verificar se o output contém tudo:
# - Qual modelo / harness está sendo usado?
# - Quantos tokens foram consumidos?
# - Quais gates executaram e passaram?
# - Há avisos e recomendações claras?

# 3. Verificar relatórios e JSONs gerados no destino
# - PLANO-EXECUCAO-ESTRUTURADO.json
# - HARNESS-COMPAT.json
# - Relatórios de auditoria e gates

# 4. Se tudo acima MOSTRA explicitamente:
# ✅ Lei de Transparência foi cumprida
```

---

## ✋ Recusa Explícita

Se alguém propuser adicionar "magic" (feature oculta ao usuário):

```
❌ "Vamos alterar modelos ou parâmetros silenciosamente sem avisar"
   → RECUSADO — violaria a Lei de Transparência

❌ "Vamos pular gates silenciosamente se parecer que vai passar"
   → RECUSADO — o usuário precisa saber exatamente o que foi validado

❌ "Vamos mascarar falhas ou inventar métricas simuladas"
   → RECUSADO — integridade de dados e métricas reais são inegociáveis
```

**Contrapropostas corretas:**

✅ "Vamos AVISAR sobre recomendações de configuração e deixar o usuário decidir"

✅ "Vamos EXECUTAR todos os gates mecânicos e MOSTRAR o resultado no stdout e em JSON"

✅ "Vamos REGISTRAR métricas reais de consumo, tempo e taxa de sucesso"

---

## 📜 Assinatura

Por esta lei, **TODOS** os scripts, templates e ferramentas do **aidd-generator** se comprometem com:

1. **Nada Oculto** — Zero magic, tudo explícito
2. **Transparência Total** — Usuário sabe tudo em tempo real
3. **Log Estruturado** — Tudo registrado em JSON e relatórios para auditoria
4. **Educação** — Quando há opções, explicar e deixar o usuário escolher
5. **Rastreabilidade** — Reproduzibilidade 100% (mesma entrada = mesma saída)

---

**Lei Inegociável desde:** 29/08/2026  
**Revisão:** Permanente — esta lei é a base ética e técnica do projeto  
**Aplicabilidade:** 100% dos arquivos do projeto aidd-generator  
**Assinado:** AIDD Framework
