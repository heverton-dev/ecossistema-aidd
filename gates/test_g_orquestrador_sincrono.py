# -*- coding: utf-8 -*-
import pytest
from gates.G_ORQUESTRADOR_SINCRONO import auditar

def test_gate_orquestrador_sincrono_passa():
    assert auditar() == 0
