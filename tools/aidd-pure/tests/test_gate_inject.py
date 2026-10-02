#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: Gate G_INJECT — validação mecânica do Injetor Universal de Componentes.
"""

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(_SCRIPTS_DIR / 'gates'))

import G_INJECT as gate


class TestGateInject:
    def test_executar_gate_passa_com_estado_real_do_repo(self):
        assert gate.executar_gate(Path('.')) == 0

    def test_checar_schema_passa(self):
        assert gate._checar_schema() is True

    def test_checar_profiles_passa(self):
        assert gate._checar_profiles() is True

    def test_checar_materializacao_e_rollback_passa(self):
        assert gate._checar_materializacao_e_rollback() is True

    def test_main_retorna_exit_code_zero(self):
        assert gate.main() == 0

    def test_checar_schema_falha_se_payload_bom_for_rejeitado(self, monkeypatch):
        import scripts.core.injector.contrato as contrato_mod

        def validar_sempre_invalido(payload):
            return contrato_mod.ResultadoValidacao(valido=False, erros=["forcado para teste"])

        monkeypatch.setattr(gate, "validar_request", validar_sempre_invalido)
        assert gate._checar_schema() is False
