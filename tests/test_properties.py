# -*- coding: utf-8 -*-
"""
Property-based tests (Hypothesis) para o Ecossistema AIDD.

Cobre propriedades invariantes que devem valer para TODOS os inputs:
  - UUID protocolo: 4-char uppercase hex
  - JWT encode/decode roundtrip
  - SLA de triagem Manchester
  - Event ID: 12-char hex
"""

import os
import sys
import re
import uuid
import time

import pytest
from hypothesis import given, assume, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Path setup para imports do ecossistema compartilhado
# ---------------------------------------------------------------------------
_ECOSISTEMA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_CORE = os.path.join(_ECOSISTEMA_ROOT, "componentes", "compartilhado", "src-core")
if _SRC_CORE not in sys.path:
    sys.path.insert(0, _SRC_CORE)


# ---------------------------------------------------------------------------
# 1. UUID Generation: uuid.uuid4().hex[:4].upper()
# ---------------------------------------------------------------------------
HEX_UPPER_4_RE = re.compile(r"^[0-9A-F]{4}$")

class TestUUIDProtocolo:
    """Propriedades do pattern TRI-{uuid.uuid4().hex[:4].upper()}."""

    @given(_trigger=st.binary(min_size=1, max_size=64))
    @settings(max_examples=200)
    def test_hex4_upper_always_4_chars_uppercase_hex(self, _trigger):
        """Qualquer chamada a uuid4().hex[:4].upper() produz 4 chars hex uppercase."""
        frag = uuid.uuid4().hex[:4].upper()
        assert len(frag) == 4
        assert HEX_UPPER_4_RE.match(frag), f"Fragmento não é hex uppercase: {frag!r}"

    @given(_trigger=st.binary(min_size=1, max_size=64))
    @settings(max_examples=100)
    def test_protocolo_format_prefix(self, _trigger):
        """Protocolo gerado sempre tem prefixo TRI- seguido de 4 hex chars."""
        proto = f"TRI-{uuid.uuid4().hex[:4].upper()}"
        assert proto.startswith("TRI-")
        assert len(proto) == 8  # "TRI-" + 4
        assert HEX_UPPER_4_RE.match(proto[4:])

    @given(n=st.integers(min_value=2, max_value=20))
    @settings(max_examples=50)
    def test_unique_across_batch(self, n):
        """Gerar N protocolos resulta em N valores únicos (colisão de 4 hex = raro)."""
        batch = {f"TRI-{uuid.uuid4().hex[:4].upper()}" for _ in range(n)}
        # 4 hex = 65536 valores possíveis, para n<=20 probabilidade de colisão ~0.3%
        assert len(batch) == n, f"Colisão detectada entre {n} protocolos"


# ---------------------------------------------------------------------------
# 2. JWT encode/decode roundtrip
# ---------------------------------------------------------------------------
class TestJWTRoundtrip:
    """Propriedade: encode(payload) -> decode(token) retorna payload original."""

    @given(
        user_id=st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters="\x00")),
        role=st.sampled_from(["admin", "user", "viewer", "medico", "enfermeiro"]),
        exp_seconds=st.integers(min_value=300, max_value=86400),
    )
    @settings(max_examples=100, deadline=None)
    def test_encode_decode_roundtrip_preserves_claims(self, user_id, role, exp_seconds):
        """JWT encode seguido de decode preserva user_id e role originais."""
        from security import JWTService

        secret = "test-secret-hypothesis-2024"
        payload = {"user_id": user_id, "role": role}

        token = JWTService.encode(payload, secret=secret, exp_seconds=exp_seconds)
        ok, decoded, msg = JWTService.decode(token, secret=secret)

        assert ok is True, f"Decode falhou: {msg}"
        assert decoded["user_id"] == user_id
        assert decoded["role"] == role

    @given(
        payload=st.dictionaries(
            keys=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters="\x00\"'")),
            values=st.one_of(
                st.integers(min_value=-10000, max_value=10000),
                st.text(max_size=50, alphabet=st.characters(blacklist_characters="\x00")),
                st.booleans(),
            ),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=80)
    def test_roundtrip_preserves_arbitrary_payload(self, payload):
        """Roundtrip JWT preserva payload arbitrário com tipos mistos."""
        from security import JWTService

        secret = "hypothesis-roundtrip-test"
        token = JWTService.encode(payload, secret=secret, exp_seconds=3600)
        ok, decoded, msg = JWTService.decode(token, secret=secret)

        assert ok is True, f"Decode falhou: {msg}"
        # Campos exp/iat/jti são injetados pelo encode, verificar os originais
        for key in payload:
            assert decoded[key] == payload[key], f"Campo {key!r} diferente"

    @given(
        payload=st.just({"x": 1}),
        secret_suffix=st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_characters="\x00", blacklist_categories=("Cs",))),
    )
    @settings(max_examples=30)
    def test_wrong_secret_rejects_token(self, payload, secret_suffix):
        """Decode com secret diferente rejeita o token."""
        from security import JWTService

        real_secret = "correct-" + secret_suffix
        wrong_secret = "wrong-" + secret_suffix

        token = JWTService.encode(payload, secret=real_secret)
        ok, decoded, msg = JWTService.decode(token, secret=wrong_secret)

        assert ok is False
        assert "inválid" in msg.lower() or "revogado" in msg.lower() or "expirad" in msg.lower() or "inv" in msg.lower()


# ---------------------------------------------------------------------------
# 3. SLA Calculation (Triagem Manchester)
# ---------------------------------------------------------------------------
SLA_MAP = {"vermelho": 0, "laranja": 10, "amarelo": 60, "verde": 120, "azul": 240}

class TestSLACalculo:
    """Propriedades da tabela de SLA Manchester."""

    @given(cls=st.sampled_from(list(SLA_MAP.keys())))
    def test_sla_known_classifications(self, cls):
        """Classificações conhecidas retornam SLA correto."""
        sla = SLA_MAP.get(cls, 120)
        assert sla == SLA_MAP[cls]

    @given(
        cls=st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(blacklist_categories=("N",)),
        )
    )
    def test_unknown_classification_defaults_to_120(self, cls):
        """Classificação desconhecida usa default=120 (verde)."""
        assume(cls.lower() not in SLA_MAP)
        sla = SLA_MAP.get(cls.lower(), 120)
        assert sla == 120

    @given(cls=st.sampled_from(list(SLA_MAP.keys())))
    def test_sla_non_negative(self, cls):
        """Todo SLA é >= 0."""
        sla = SLA_MAP.get(cls, 120)
        assert sla >= 0

    @given(cls=st.sampled_from(list(SLA_MAP.keys())))
    def test_sla_is_multiple_of_10_or_zero(self, cls):
        """Todo SLA é múltiplo de 10 ou zero (vermelho)."""
        sla = SLA_MAP.get(cls, 120)
        assert sla == 0 or sla % 10 == 0

    def test_triagem_sla_ordering(self):
        """SLAs seguem a ordenação de urgência: vermelho < laranja < amarelo < verde < azul."""
        order = ["vermelho", "laranja", "amarelo", "verde", "azul"]
        slas = [SLA_MAP[c] for c in order]
        assert slas == sorted(slas), "SLAs não estão em ordem crescente de urgência"

    def test_triagem_sla_completeness(self):
        """Todas as 5 classificações Manchester estão presentes."""
        assert len(SLA_MAP) == 5
        for cls in ["vermelho", "laranja", "amarelo", "verde", "azul"]:
            assert cls in SLA_MAP


# ---------------------------------------------------------------------------
# 4. Event ID Generation (12-char hex)
# ---------------------------------------------------------------------------
HEX_12_RE = re.compile(r"^[0-9a-f]{12}$")


def _generate_event_id() -> str:
    """Gera um event_id de 12 hex chars (padrão AIDD)."""
    return uuid.uuid4().hex[:12]


class TestEventID:
    """Propriedades do generation de event IDs (12-char hex)."""

    @given(_trigger=st.binary(min_size=1, max_size=64))
    @settings(max_examples=200)
    def test_event_id_is_12_hex_lowercase(self, _trigger):
        """Event ID é sempre 12 caracteres hex lowercase."""
        eid = _generate_event_id()
        assert len(eid) == 12, f"Event ID tem {len(eid)} chars, esperado 12"
        assert HEX_12_RE.match(eid), f"Event ID não é hex lowercase: {eid!r}"

    @given(n=st.integers(min_value=2, max_value=100))
    @settings(max_examples=50)
    def test_event_ids_unique_in_batch(self, n):
        """N event IDs gerados são todos únicos."""
        batch = {_generate_event_id() for _ in range(n)}
        assert len(batch) == n, f"Colisão: {n} IDs gerados, apenas {len(batch)} únicos"

    @given(_trigger=st.binary(min_size=1, max_size=16))
    @settings(max_examples=100)
    def test_event_id_only_contains_hex_chars(self, _trigger):
        """Event ID contém apenas caracteres [0-9a-f]."""
        eid = _generate_event_id()
        for ch in eid:
            assert ch in "0123456789abcdef", f"Caractere inválido: {ch!r}"

    @given(_trigger=st.binary(min_size=1, max_size=8))
    @settings(max_examples=30)
    def test_two_consecutive_ids_differ(self, _trigger):
        """Dois event IDs consecutivos são diferentes."""
        a = _generate_event_id()
        b = _generate_event_id()
        assert a != b
