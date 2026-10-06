# -*- coding: utf-8 -*-
"""
Testes unitários para o padrão de Fake Adapters Tipados de Fronteira Externa.
Garante 100% de conformidade com a Lei #5 (Zero Mocks / Zero Stubs).
"""

import pytest
from src.core.external_adapter import (
    ExternalServiceAdapter,
    InMemoryFakeExternalAdapter,
    NotificationPayload,
    NotificationResult,
    FakeNotificationAdapter,
)


def test_fake_notification_adapter_successful_delivery():
    adapter = FakeNotificationAdapter()
    payload = NotificationPayload(
        recipient="usuario@empresa.com",
        subject="Boas-vindas",
        body="Seu cadastro foi realizado com sucesso.",
    )
    result = adapter.execute(payload)

    assert result.delivered is True
    assert result.status == "DELIVERED"
    assert result.message_id.startswith("NOTIFICATION-GATEWAY-TX-")
    assert len(adapter.history) == 1
    assert adapter.history[0].success is True
    assert adapter.history[0].response_code == 200


def test_fake_notification_adapter_invalid_recipient_validation():
    adapter = FakeNotificationAdapter()
    payload = NotificationPayload(
        recipient="destinatario-invalido",
        subject="Alerta",
        body="Teste de falha",
    )
    result = adapter.execute(payload)

    assert result.delivered is False
    assert result.status == "FAILED"
    assert "invalido" in result.error
    assert len(adapter.history) == 1
    assert adapter.history[0].success is False
    assert adapter.history[0].response_code == 400


def test_fake_notification_adapter_simulated_network_failure():
    adapter = FakeNotificationAdapter(force_failure=True)
    assert adapter.health_check() is False

    payload = NotificationPayload(
        recipient="admin@empresa.com",
        subject="Status",
        body="Checagem de indisponibilidade",
    )
    result = adapter.execute(payload)

    assert result.delivered is False
    assert result.status == "ERROR_503"
    assert "indisponivel" in result.error
    assert len(adapter.history) == 1
    assert adapter.history[0].success is False
    assert adapter.history[0].response_code == 503


def test_fake_adapter_history_clearing():
    adapter = FakeNotificationAdapter()
    payload = NotificationPayload(
        recipient="contato@empresa.com",
        subject="Mensagem",
        body="Ola",
    )
    adapter.execute(payload)
    assert len(adapter.history) == 1

    adapter.clear_history()
    assert len(adapter.history) == 0
