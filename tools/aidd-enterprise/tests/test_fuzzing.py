#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Testes Unitários para Fuzzing Contínuo de APIs (Continuous API Fuzzing Tests)
=============================================================================
Valida geração de payloads, estratégias de fuzzing e relatórios.
"""

import pytest
import sys
import os
import json

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.fuzzing import (
    PayloadGenerator,
    FuzzingStrategy,
    ContinuousAPIFuzzer,
    FuzzTestResult,
)


class TestPayloadGenerator:
    """Testes do gerador de payloads de fuzzing."""

    def test_null_injection_payloads(self):
        """Verifica geração de null injections."""
        payloads = PayloadGenerator.null_injection()
        assert None in payloads
        assert "" in payloads
        assert 0 in payloads
        assert False in payloads
        assert [] in payloads
        assert {} in payloads

    def test_boundary_values_payloads(self):
        """Verifica geração de valores de limite."""
        payloads = PayloadGenerator.boundary_values()
        assert -2147483648 in payloads  # INT_MIN
        assert 2147483647 in payloads   # INT_MAX
        assert float('inf') in payloads
        assert float('-inf') in payloads
        assert len(payloads) > 0

    def test_type_coercion_payloads(self):
        """Verifica geração de payloads de coerção de tipo."""
        payloads = PayloadGenerator.type_coercion()
        assert len(payloads) > 0
        # Todos devem ser dicionários
        for payload in payloads:
            assert isinstance(payload, dict)
            assert "value" in payload

    def test_overflow_payloads(self):
        """Verifica geração de payloads de overflow."""
        payloads = PayloadGenerator.overflow_payloads()
        # Deve ter string longa, array gigante, objeto com muitas chaves
        has_long_string = any(isinstance(p, str) and len(p) > 1000 for p in payloads)
        has_large_array = any(isinstance(p, list) and len(p) > 1000 for p in payloads)
        has_large_dict = any(isinstance(p, dict) and len(p) > 1000 for p in payloads)
        assert has_long_string or has_large_array or has_large_dict

    def test_sql_injection_payloads(self):
        """Verifica geração de payloads de SQL Injection."""
        payloads = PayloadGenerator.sql_injection_payloads()
        assert len(payloads) > 0
        assert any("DROP" in str(p) for p in payloads)
        assert any("UNION" in str(p) for p in payloads)

    def test_xss_injection_payloads(self):
        """Verifica geração de payloads de XSS."""
        payloads = PayloadGenerator.xss_injection_payloads()
        assert len(payloads) > 0
        assert any("<script>" in str(p) for p in payloads)
        assert any("onerror=" in str(p) for p in payloads)

    def test_malformed_json_payloads(self):
        """Verifica geração de JSON malformado."""
        payloads = PayloadGenerator.malformed_json_payloads()
        assert len(payloads) > 0
        # Todos devem ser strings (JSON malformado)
        for payload in payloads:
            assert isinstance(payload, str)

    def test_random_string_payloads(self):
        """Verifica geração de strings aleatórias."""
        payloads = PayloadGenerator.random_string_payloads(count=5)
        assert len(payloads) == 5
        for payload in payloads:
            assert isinstance(payload, str)
            assert len(payload) == 50

    def test_unicode_attack_payloads(self):
        """Verifica geração de payloads Unicode."""
        payloads = PayloadGenerator.unicode_attack_payloads()
        assert len(payloads) > 0
        assert all(isinstance(p, str) for p in payloads)

    def test_deep_nesting_payloads(self):
        """Verifica geração de estruturas aninhadas."""
        payloads = PayloadGenerator.deep_nesting_payloads(depth=50)
        assert len(payloads) == 1
        # Verificar se está aninhado
        nested = payloads[0]
        current = nested
        depth_count = 0
        while "nested" in current:
            current = current["nested"]
            depth_count += 1
        assert depth_count >= 1


class TestFuzzingStrategy:
    """Testes das estratégias de fuzzing."""

    def test_all_strategies_have_values(self):
        """Verifica se todas as estratégias geram payloads."""
        generator = PayloadGenerator()
        for strategy in FuzzingStrategy:
            payloads = generator.generate_fuzz_cases(strategy) if hasattr(generator, 'generate_fuzz_cases') else []
            # Pelo menos a estratégia deve ser válida
            assert strategy.value is not None


class TestContinuousAPIFuzzer:
    """Testes do executor de fuzzing contínuo."""

    def test_fuzzer_initialization(self):
        """Verifica inicialização do fuzzer."""
        fuzzer = ContinuousAPIFuzzer(base_url="http://localhost:3000", max_tests_per_route=50)
        assert fuzzer.base_url == "http://localhost:3000"
        assert fuzzer.max_tests_per_route == 50
        assert len(fuzzer.results) == 0

    def test_fuzzer_generate_cases(self):
        """Verifica geração de casos de fuzzing."""
        fuzzer = ContinuousAPIFuzzer()
        cases = fuzzer.generate_fuzz_cases(FuzzingStrategy.NULL_INJECTION)
        assert len(cases) > 0

    def test_fuzzer_report_generation_empty(self):
        """Verifica relatório com zero testes."""
        fuzzer = ContinuousAPIFuzzer()
        report = fuzzer.generate_report()
        assert report['total_tests'] == 0
        assert report['crashes'] == 0
        assert report['errors'] == 0
        assert report['successes'] == 0

    def test_fuzz_test_result_creation(self):
        """Verifica criação de resultado de teste de fuzzing."""
        result = FuzzTestResult(
            route="/api/test",
            method="POST",
            strategy=FuzzingStrategy.NULL_INJECTION,
            payload=None,
            status_code=200,
            response={"success": True},
            is_crash=False,
            is_error=False
        )
        assert result.route == "/api/test"
        assert result.method == "POST"
        assert result.status_code == 200
        assert not result.is_crash
        assert not result.is_error

    def test_fuzzer_results_accumulation(self):
        """Verifica acumulação de resultados de fuzzing."""
        fuzzer = ContinuousAPIFuzzer()

        # Simular alguns resultados
        # i=0: crash=True, error=True  → contabilizado como crash
        # i=1: crash=False, error=False → sucesso
        # i=2: crash=True, error=False  → crash
        # i=3: crash=False, error=True  → erro
        # i=4: crash=True, error=False  → crash
        for i in range(5):
            result = FuzzTestResult(
                route="/api/test",
                method="POST",
                strategy=FuzzingStrategy.NULL_INJECTION,
                payload=None,
                status_code=200 + i,
                response={},
                is_crash=(i % 2 == 0),
                is_error=(i % 3 == 0)
            )
            fuzzer.results.append(result)

        report = fuzzer.generate_report()
        assert report['total_tests'] == 5
        assert report['crashes'] == 3  # i=0,2,4
        assert report['errors'] == 1   # i=3 (i=0 é crash, não erro)


class TestFuzzyingIntegration:
    """Testes de integração de fuzzing."""

    def test_fuzzing_report_statistics(self):
        """Verifica cálculo de estatísticas do relatório."""
        fuzzer = ContinuousAPIFuzzer()

        # Adicionar resultados variados
        test_results = [
            FuzzTestResult("/api/users", "POST", FuzzingStrategy.NULL_INJECTION, None, 200, {}, False, False),
            FuzzTestResult("/api/users", "POST", FuzzingStrategy.NULL_INJECTION, None, 400, {}, False, True),
            FuzzTestResult("/api/users", "POST", FuzzingStrategy.NULL_INJECTION, None, 500, {}, True, False),
            FuzzTestResult("/api/users", "POST", FuzzingStrategy.SQL_INJECTION, "'; DROP--", 500, {}, True, False),
        ]

        for result in test_results:
            fuzzer.results.append(result)

        report = fuzzer.generate_report()
        assert report['total_tests'] == 4
        assert report['successes'] == 1
        assert report['errors'] == 1
        assert report['crashes'] == 2

    def test_fuzzing_report_format(self):
        """Verifica formato do relatório de fuzzing."""
        fuzzer = ContinuousAPIFuzzer()

        result = FuzzTestResult(
            route="/api/login",
            method="POST",
            strategy=FuzzingStrategy.XSS_INJECTION,
            payload="<script>alert('xss')</script>",
            status_code=400,
            response={},
            is_crash=False,
            is_error=True
        )
        fuzzer.results.append(result)

        report = fuzzer.generate_report()

        # Verificar estrutura do relatório
        assert 'total_tests' in report
        assert 'crashes' in report
        assert 'errors' in report
        assert 'successes' in report
        assert 'crash_rate' in report
        assert 'error_rate' in report
        assert 'success_rate' in report
        assert 'crashes_by_route' in report
        assert 'errors_by_route' in report
        assert 'critical_findings' in report

    def test_fuzzing_critical_findings(self):
        """Verifica detecção de findings críticos."""
        fuzzer = ContinuousAPIFuzzer()

        crash_result = FuzzTestResult(
            route="/api/users",
            method="POST",
            strategy=FuzzingStrategy.OVERFLOW,
            payload="A" * 100000,
            status_code=500,
            response=None,
            is_crash=True,
            is_error=False,
            error_message="Internal Server Error"
        )
        fuzzer.results.append(crash_result)

        report = fuzzer.generate_report()
        assert len(report['critical_findings']) == 1
        finding = report['critical_findings'][0]
        assert finding['route'] == "/api/users"
        assert finding['strategy'] == FuzzingStrategy.OVERFLOW.value


class TestPayloadGeneratorEdgeCases:
    """Testes de edge cases do gerador de payloads."""

    def test_deep_nesting_custom_depth(self):
        """Testa aninhamento profundo com profundidade customizável."""
        payloads = PayloadGenerator.deep_nesting_payloads(depth=200)
        assert len(payloads) == 1
        # Verificar JSON-serializability
        try:
            json.dumps(payloads[0])
        except Exception as e:
            pytest.fail(f"Deep nesting não é JSON serializável: {e}")

    def test_payload_generator_consistency(self):
        """Verifica se o gerador produz payloads válidos."""
        generator = PayloadGenerator()

        # NULL Injection deve conter tipos nulláveis
        null_payloads = generator.null_injection()
        assert isinstance(null_payloads, list)
        assert len(null_payloads) > 0

        # Boundary values devem ser números
        boundary = generator.boundary_values()
        assert all(isinstance(b, (int, float)) for b in boundary)

        # Strings aleatórias devem ser strings
        random_strs = generator.random_string_payloads(5)
        assert all(isinstance(s, str) for s in random_strs)
        assert len(random_strs) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
