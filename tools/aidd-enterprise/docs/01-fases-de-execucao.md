# 01. Fases de Execução do AIDD Master Enterprise

> **Framework:** AIDD Master Enterprise  
> **Objetivo:** Estabelecer a esteira determinística de desenvolvimento orientada a IA com garantia matemática de entrega (`exit 0`).

---

## 1. Visão Geral da Esteira AIDD

O ciclo de vida do AIDD Master Enterprise opera em **5 Fases Sequenciais**, combinando a mecânica determinística em Python puro (Zero Token) com a cognição pontual de subagentes efêmeros:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                 ESTEIRA DE EXECUÇÃO AIDD MASTER ENTERPRISE                 │
├─────────────┬─────────────┬──────────────┬───────────────┬────────────────┤
│   FASE 0    │   FASE 1    │    FASE 2    │    FASE 3     │     FASE 4     │
│ Pre-Flight  │ Concepção   │  Composição  │ Validação BDD │  10 Quality    │
│ & Setup     │ Natural     │ Efêmera ORCA │  & Testes TDD │     Gates      │
│ (Zero Token)│ (Cognitivo) │(Context-Purge│ (Determínico) │  (Auto-Healing)│
└─────────────┴─────────────┴──────────────┴───────────────┴────────────────┘
```

---

## 2. Detalhamento das 5 Fases

### Fase 0: Pre-Flight & Fleet Auto-Discovery (Mecânica / Zero Token)
* **Comando:** `python scripts/aidd.py setup`
* **Objetivo:** Inspecionar o ambiente host antes de qualquer linha de código.
* **Ações:**
  1. Verifica versão do Python (>= 3.10) e dependências (`requirements.txt`).
  2. Executa a auto-descoberta de frota (`FleetDiscovery`), mapeando executáveis disponíveis no `$PATH`: Claude Code, Antigravity (`agy`), Codex, Gemini CLI, OpenCode, MimoCode ou Ollama.
  3. Prepara diretórios de persistência SQLite WAL e chaves criptográficas JWT.

### Fase 1: Concepção em Linguagem Natural (Cognição Zero-Friction)
* **Comando:** `/compose <módulos>` ou `python scripts/aidd.py plan "<descrição>"`
* **Objetivo:** Traduzir a intenção de negócio do usuário em especificações de fatias verticais.
* **Ações:**
  1. O **Intent Router** (`src/core/intent_router.py`) analisa o pedido do usuário em PT-BR (ex: *"preciso de uma arquitetura para crm, erp e billing"*).
  2. Extrai os domínios de negócio e gera contratos prévios (`SPEC-<modulo>.md`) com teto estrito de ~1.200 tokens por fatia.

### Fase 2: Composição via Subagentes Efêmeros (Context-Purge Engine)
* **Comando:** `python scripts/aidd.py compose-orca <modulos>`
* **Objetivo:** Construção física paralela das fatias verticais sem contaminação de contexto.
* **Ações:**
  1. O orquestrador mecânico (`src/core/subagent_engine.py`) instancia um subprocesso descartável para cada módulo.
  2. Cada subagente recebe **exclusivamente a especificação da sua fatia** e gera:
     - `models.py`: Entidades de domínio com dataclasses e tipagem estrita.
     - `services.py`: Regras de negócio encapsuladas com Result Monad (`Result.ok`/`Result.fail`).
     - `routes.py`: Endpoints REST documentados para OpenAPI 3.1.
     - `test_<modulo>.py`: Suíte de testes unitários com cobertura de 100% do CRUD.
  3. **Context-Purge:** Concluída a gravação em disco, o subprocesso é encerrado e o contexto de memória da IA é purgado. Zero acúmulo de tokens entre módulos.

### Fase 3: Validação BDD / TDD & Contratos (Mecânica / Zero Token)
* **Comando:** `python -m pytest tests/` ou `python scripts/aidd.py test`
* **Objetivo:** Garantir a execução livre de falhas de 100% dos testes unitários e de integração.
* **Ações:**
  1. Executa a suíte de testes com fixtures isoladas (`tmp_path`) e modo SQLite WAL.
  2. Valida contratos de endpoints e schemas OpenAPI 3.1.
  3. Testa transações ACID com Outbox Worker assíncrono.

### Fase 4: Bateria dos 10 Quality Gates com Auto-Healing
* **Comando:** `python scripts/run_all.py`
* **Objetivo:** Auditoria matemática e bloqueante antes de autorizar a entrega.
* **Ações:**
  1. Executa sequencialmente os 10 Gates de Qualidade.
  2. Se ocorrer falha transitória (formatação, imports fora de ordem, resíduos de cache), o **Auto-Healing** aciona `scripts/autofix.py` e reexecuta o gate.
  3. Só emite certificação de produção se o resultado final for `exit code 0` absoluto em todas as camadas.
