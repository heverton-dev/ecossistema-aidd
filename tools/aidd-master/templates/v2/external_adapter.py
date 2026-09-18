# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — PADRÃO DE FAKE ADAPTERS TIPADOS DE FRONTEIRA EXTERNA
=============================================================================
Implementação canônica de adaptadores de fronteira para serviços externos
e terceiros (ex: pagamentos, mensageria, IA) em estrita conformidade com a
Lei #5 (Zero Stubs / Zero Mocks).

Em vez de mocks dinâmicos (unittest.mock.MagicMock) que ocultam quebras de contrato
e introduzem fragilidade não tipada, o ecossistema utiliza Adapters Tipados Reais
com implementações Fake em memória orientadas a contrato:
  - 100% tipadas (Generic / Pydantic / TypedDict / Dataclass)
  - Manutenção de estado interno determinístico e auditável
  - Validação estrita de invariantes de negócio e payloads
  - Simulação de erros de rede/timeouts determinísticos sem bibliotecas mágicas
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Generic, List, Optional, TypeVar, Any


TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


@dataclass(frozen=True)
class ExternalTransactionRecord:
    """Registro auditável imutável de transações trafegadas pelo adaptador."""
    transaction_id: str
    service_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = field(default_factory=dict)
    response_code: int = 200
    success: bool = True
    error_message: Optional[str] = None


class ExternalServiceAdapter(ABC, Generic[TRequest, TResponse]):
    """Contrato abstrato universal para integração com fronteiras externas."""

    @abstractmethod
    def execute(self, request: TRequest) -> TResponse:
        """Executa a operação de forma síncrona contra a fronteira."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifica a disponibilidade da fronteira externa."""
        pass


class InMemoryFakeExternalAdapter(ExternalServiceAdapter[TRequest, TResponse]):
    """
    Fake Adapter tipado em memória para testes reais sem chamadas de rede.
    Preserva a Lei #5: é código funcional, tipado, que rejeita payloads inválidos,
    grava auditoria em memória e suporta simulação de falhas determinísticas.
    """

    def __init__(self, service_name: str, force_failure: bool = False):
        self.service_name = service_name
        self.force_failure = force_failure
        self.history: List[ExternalTransactionRecord] = []
        self._next_id: int = 1000

    def record_transaction(
        self,
        payload: Dict[str, Any],
        response_code: int = 200,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> str:
        tx_id = f"{self.service_name.upper()}-TX-{self._next_id}"
        self._next_id += 1
        record = ExternalTransactionRecord(
            transaction_id=tx_id,
            service_name=self.service_name,
            payload=payload,
            response_code=response_code,
            success=success,
            error_message=error_message,
        )
        self.history.append(record)
        return tx_id

    def health_check(self) -> bool:
        return not self.force_failure

    def clear_history(self) -> None:
        self.history.clear()


# =============================================================================
# IMPLEMENTAÇÃO DE REFERÊNCIA: GATEWAY DE NOTIFICAÇÃO (EMAIL / SMS / WEBHOOK)
# =============================================================================

@dataclass
class NotificationPayload:
    recipient: str
    subject: str
    body: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationResult:
    delivered: bool
    message_id: str
    status: str
    error: Optional[str] = None


class FakeNotificationAdapter(InMemoryFakeExternalAdapter[NotificationPayload, NotificationResult]):
    """Fake adapter tipado para serviços de envio de notificações."""

    def __init__(self, force_failure: bool = False):
        super().__init__(service_name="notification-gateway", force_failure=force_failure)

    def execute(self, request: NotificationPayload) -> NotificationResult:
        if not request.recipient or "@" not in request.recipient:
            self.record_transaction(
                payload={"recipient": request.recipient, "subject": request.subject},
                response_code=400,
                success=False,
                error_message="Email do destinatario invalido",
            )
            return NotificationResult(
                delivered=False,
                message_id="",
                status="FAILED",
                error="Email do destinatario invalido",
            )

        if self.force_failure:
            tx_id = self.record_transaction(
                payload={"recipient": request.recipient, "subject": request.subject},
                response_code=503,
                success=False,
                error_message="Servico temporariamente indisponivel",
            )
            return NotificationResult(
                delivered=False,
                message_id=tx_id,
                status="ERROR_503",
                error="Servico temporariamente indisponivel",
            )

        tx_id = self.record_transaction(
            payload={"recipient": request.recipient, "subject": request.subject},
            response_code=200,
            success=True,
        )
        return NotificationResult(
            delivered=True,
            message_id=tx_id,
            status="DELIVERED",
            error=None,
        )
