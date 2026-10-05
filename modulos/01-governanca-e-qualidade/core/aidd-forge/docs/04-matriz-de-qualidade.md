# Matriz de Qualidade e Governança Mecânica: AIDD Forge

> **Versão:** 1.0.0  
> **Objetivo:** Estabelecer os critérios determinísticos de aceitação, cobertura e conformidade que garantem a Nota 10.0+ contínua no AIDD Forge.

---

## 1. Os 7 Quality Gates Mecânicos

Todo código ou projeto governado pelo AIDD Forge deve passar sem exceção pelos 7 Gates mecânicos:

| Gate | Script Responsável | Escopo de Verificação | Bloqueio |
| :---: | :--- | :--- | :---: |
| **G1** | `G_BLOQUEAR_SEGREDOS.py` | Detecta chaves AWS, chaves de API, senhas hardcoded e tokens em arquivos commitados. | Binário (`exit 1`) |
| **G2** | `G_ESTRUTURA_AST.py` | Analisa a sintaxe de todos os arquivos `.py` via `ast.parse`. | Binário (`exit 1`) |
| **G3** | `G_HARNESS_COMPAT.py` | Garante que symlinks entre `.agent`, `.claude` e `.cursor` permaneçam íntegros. | Binário (`exit 1`) |
| **G4** | `G_CONTRACTS.py` | Valida compatibilidade e integridade de schemas JSON Draft 2020-12. | Binário (`exit 1`) |
| **G5** | `G_TESTES_REAIS.py` | Executa a suíte `pytest` exigindo 100% de aprovação (Zero Fail). | Binário (`exit 1`) |
| **G6** | `G_CYBERSECURITY_OWASP.py`| Varre código estaticamente barrando `eval()`, `shell=True`, SQL injections e entradas inseguras. | Binário (`exit 1`) |
| **G7** | `G_PERFORMANCE.py` | Valida se o tempo de resposta e latência de endpoints respeitam o orçamento configurado. | Binário (`exit 1`) |

---

## 2. Métricas de Cobertura e SLAs Homologados

| Dimensão | Métrica Exigida | Atingido no AIDD Forge | Status |
| :--- | :--- | :---: | :---: |
| **Suíte Geral de Testes** | 100% de aprovação no Pytest | **126 passed, 1 skipped, 0 falhas** | 🏆 Homologado |
| **Tempo de Execução dos Testes**| < 30 segundos para a suíte completa | **~18 a 20 segundos** | 🏆 Homologado |
| **Tempo de Bootstrap (`init`)** | < 2 segundos para provisionamento total | **~0.4 a 0.8 segundos** | 🏆 Homologado |
| **Orçamento de Regras de Contexto** | Máximo 1.500 tokens por arquivo de regra | **Todos < 1.000 tokens** | 🏆 Homologado |
| **Regras de Fase Granular** | ~380 tokens por micro-fase | **~350 a 390 tokens** | 🏆 Homologado |
| **Tolerância a Falhas de Frota** | 0 quebras em hosts com 1 único agente | **100% resiliente** | 🏆 Homologado |

---

## 3. Política de "Zero Stubs" em Produção

É terminantemente proibido:
- Funções com corpo contendo apenas `pass` ou comentários indicando "TODO".
- Retornos vazios simulados que não executam validação real.
- Mocks estáticos de fachada entregues como código de produção.

Qualquer violação é interceptada pelos testes unitários de integração e pelos Quality Gates antes de ser integrada à branch principal.
