# 04. Matriz de Qualidade: Os 10 Gates Rígidos com Auto-Healing

> **Framework:** AIDD Master Enterprise  
> **Filosofia:** Governança inegociável por barreiras matemáticas binárias (`exit 0` = Aprovado / `exit 1` = Bloqueado).

---

## 1. Visão Consolidada dos 10 Quality Gates

O AIDD Master Enterprise possui a suíte mais completa de gates da indústria, auditando desde a Árvore Sintática (AST) até a latência de execução e vulnerabilidades em tempo real:

| Gate | Script Responsável | Escopo de Auditoria | Critério de Reprovação (`exit 1`) |
| :--- | :--- | :--- | :--- |
| **G1: Estrutura** | `scripts/gates/G_ESTRUTURA.py` | Layout modular, pastas e manifestos. | Arquivos obrigatórios ausentes em fatias. |
| **G2: Arquitetura** | `scripts/gates/G_ARQUITETURA.py` | Bounded Contexts via AST em `src/modules/`. | Qualquer import direto entre módulos vizinhos. |
| **G3: Qualidade** | `scripts/gates/G_QUALIDADE.py` | Análise estática, anti-stubs e mutações. | Funções com stubs (`pass`), mocks vazios. |
| **G4: Performance** | `scripts/gates/G_PERFORMANCE.py` | SLAs de Latência, Memória RSS e N+1. | p99 > 200ms, RSS > 512MB ou N+1 queries. |
| **G5: Testes** | `scripts/gates/G_TESTES.py` | Execução completa com `pytest`. | Qualquer teste com falha ou erro de assert. |
| **G6: Contratos** | `scripts/gates/G_CONTRACTS.py` | Schemas OpenAPI 3.1 e servidores MCP. | Schemas malformados ou rotas sem contrato. |
| **G7: Segredos** | `scripts/gates/G_SEGREDOS.py` | Varredura de alta entropia de Shannon. | Chaves de API, senhas ou tokens no código. |
| **G8: Segurança** | `scripts/gates/G_SEGURANCA.py` | OWASP Top 10, JWT e CVEs com `pip-audit`. | SQL Injection, falha JWT ou CVE HIGH/CRITICAL. |
| **G9: Caos** | `scripts/gates/G_CHAOS.py` | Resiliência estocástica e Circuit Breaker. | Falha em cascata sem fallback seguro. |
| **G10: Portabilidade**| `scripts/gates/G_HARNESS_COMPAT.py`| Compatibilidade Multi-Harness e paths. | Caminhos absolutos hardcoded no código. |

---

## 2. Mecanismo de Orquestração com Auto-Healing

O script `scripts/run_all.py` atua como o maestro de todos os gates. Ele possui capacidade nativa de auto-correção:

```
                      INÍCIO: RUN_ALL.PY
                              │
                              ▼
                      EXECUTA O GATE (G_X)
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
      PASSOU (Exit 0)                   FALHOU (Exit 1)
             │                                 │
             ▼                                 ▼
       PRÓXIMO GATE                   DISPARA AUTO-HEALING
                                      (scripts/autofix.py)
                                      • Limpa __pycache__ / .pyc
                                      • Executa formatação black
                                      • Reordena imports com isort
                                               │
                                               ▼
                                      RE-TENTA O GATE (G_X)
                                               │
                                ┌──────────────┴──────────────┐
                                ▼                             ▼
                         PASSOU (Exit 0)               FALHOU (Exit 1)
                                │                             │
                                ▼                             ▼
                          CONTINUA ESTEIRA             BLOQUEIA RELEASE
```

---

## 3. Detalhamento dos Gates Mais Críticos

### G_ARQUITETURA (Linter AST de Bounded Context)
* O gate não faz busca ingênua por texto: ele lê o bytecode gerado pelo módulo nativo `ast` do Python.
* Percorre os nós `ast.Import` e `ast.ImportFrom`.
* Se o arquivo estiver dentro de `src/modules/crm/` e contiver `from modules.erp.services import ...`, o gate aborta a execução instantaneamente.

### G_PERFORMANCE (SLAs e OpenTelemetry)
* Monitora o uso de memória RSS em tempo real na plataforma (Linux, macOS e Windows via Win32 API).
* Valida a instrumentação de spans OpenTelemetry (`@trace_span`).
* Bloqueia anti-patterns de queries de banco dentro de loops em fatias de negócio (detecção estática de N+1).

### G_SEGURANCA (Auditoria Militar e CVEs)
* Varredura ativa de dependências com `pip-audit --format=json -r requirements.txt`.
* Bloqueia a esteira caso qualquer pacote de terceiros possua vulnerabilidade conhecida classificada como **HIGH** ou **CRITICAL**.
* Testa criptografia de tokens JWT, garantindo que adulterações na assinatura digital sejam estritamente rejeitadas.
