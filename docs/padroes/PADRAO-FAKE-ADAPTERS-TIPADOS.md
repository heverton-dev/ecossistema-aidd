# Padrão de Fake Adapters Tipados de Fronteira Externa (Zero Mocks Preservado)

> **Governança:** Lei Canônica #5 — Zero Stubs / Zero Mocks  
> **Referência Técnica:** `componentes/compartilhado/src-core/external_adapter.py`

---

## 1. Contexto e Motivação

No desenvolvimento ágil e nas práticas tradicionais de desenvolvimento com IA (*vibe coding*), o uso indiscriminado de bibliotecas de simulação dinâmica como `unittest.mock.MagicMock` cria uma falsa sensação de cobertura de testes. 
Mocks dinâmicos frequentemente aceitam qualquer atributo arbitrário ou tipagem inconsistente, permitindo que a suíte passe mesmo quando contratos de APIs externas de pagamento, mensageria ou serviços de IA já foram quebrados.

A **Lei #5 do Ecossistema AIDD** proíbe expressamente stubs vazios e mocks mágicos em ambientes produtivos e suítes de validação rigorosa.

Para resolver a necessidade de testes rápidos, determinísticos e desconectados da internet (ex.: CI/CD e ambientes locais) sem violar a Lei #5, adota-se o **Padrão de Fake Adapters Tipados**.

---

## 2. Pilares Arquiteturais

1. **Contrato Tipado Único (`ExternalServiceAdapter[TRequest, TResponse]`):**
   - Tanto a implementação real que se comunica com a rede externa quanto a implementação em memória implementam estritamente a mesma interface tipada (Generics + Dataclasses/Pydantic).
2. **Invariantes e Validação de Entrada Estrita:**
   - O Fake Adapter não é um stub passivo; ele valida regras de contrato reais (ex.: formato de e-mail, ranges de valores numéricos, tokens válidos). Payloads inválidos retornam erros estruturados ou códigos de erro reais (ex: 400 Bad Request).
3. **Auditoria de Transações em Memória (`ExternalTransactionRecord`):**
   - Cada chamada gera um registro auditável imutável de payload, status de resposta, timestamp UTC e ID de transação determinístico.
4. **Simulação Determinística de Falhas (`force_failure`):**
   - Suporte nativo à injeção controlada de falhas (ex.: timeout 503, indisponibilidade temporária) sem patches dinâmicos em tempo de execução.

---

## 3. Matriz de Paridade

| Característica | Mock Tradicional (`unittest.mock`) | Fake Adapter Tipado AIDD |
| :--- | :---: | :---: |
| **Aderência à Lei #5** | ❌ Não (stubs e objetos dinâmicos) | ✅ Sim (código 100% tipado e funcional) |
| **Verificação de Tipos (mypy/pyright)** | ❌ Falha silenciosa | ✅ 100% verificado |
| **Validação de Invariantes** | ❌ Requer asserts manuais extras | ✅ Integrada no contrato de execução |
| **Rastreabilidade e Auditoria** | ❌ Transitória no mock | ✅ `history` estruturado e exportável |

---

## 4. Exemplo Canônico de Consumo

```python
from src.core.external_adapter import FakeNotificationAdapter, NotificationPayload

def test_fluxo_notificacao_pedido():
    adapter = FakeNotificationAdapter()
    payload = NotificationPayload(
        recipient="cliente@dominio.com",
        subject="Pedido Confirmado",
        body="Seu pedido #1234 foi faturado."
    )
    result = adapter.execute(payload)
    
    assert result.delivered is True
    assert result.status == "DELIVERED"
    assert len(adapter.history) == 1
    assert adapter.history[0].response_code == 200
```
