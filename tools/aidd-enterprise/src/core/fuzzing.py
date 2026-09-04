#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Fuzzing Contínuo de APIs (Continuous API Fuzzing)
=============================================================================
Executa testes de fuzzing automáticos contra todas as rotas de API,
verificando robustez contra payloads malformados, null injections, overflow,
e edge cases. Integra com pytest e G_QUALIDADE.
"""

import json
import random
import string
import sys
import uuid
from typing import Dict, List, Any, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class FuzzingStrategy(Enum):
    """Estratégias de geração de payloads de fuzzing."""
    NULL_INJECTION = "null_injection"
    BOUNDARY_VALUES = "boundary_values"
    TYPE_COERCION = "type_coercion"
    OVERFLOW = "overflow"
    SQL_INJECTION = "sql_injection"
    XSS_INJECTION = "xss_injection"
    MALFORMED_JSON = "malformed_json"
    RANDOM_STRING = "random_string"
    UNICODE_ATTACKS = "unicode_attacks"
    DEEP_NESTING = "deep_nesting"


@dataclass
class FuzzTestResult:
    """Resultado de um teste de fuzzing."""
    route: str
    method: str
    strategy: FuzzingStrategy
    payload: Any
    status_code: int
    response: Any
    is_crash: bool
    is_error: bool
    error_message: str = ""


class PayloadGenerator:
    """Gerador de payloads de fuzzing para testes de robustez."""

    @staticmethod
    def null_injection() -> List[Any]:
        """Gera payloads de null injection."""
        return [None, "", 0, False, [], {}]

    @staticmethod
    def boundary_values() -> List[Any]:
        """Gera valores de limite e edge cases."""
        return [
            -2147483648,  # INT_MIN
            2147483647,   # INT_MAX
            -9223372036854775808,  # LONG_MIN
            9223372036854775807,   # LONG_MAX
            float('inf'),
            float('-inf'),
            float('nan'),
            0.0,
            -0.0,
            1e308,
            1e-308,
        ]

    @staticmethod
    def type_coercion() -> List[Dict[str, Any]]:
        """Testa coerção de tipos (strings como números, etc)."""
        return [
            {"value": "12345"},
            {"value": "true"},
            {"value": "false"},
            {"value": "null"},
            {"value": "[1,2,3]"},
            {"value": '{"key":"value"}'},
        ]

    @staticmethod
    def overflow_payloads() -> List[Any]:
        """Gera payloads de overflow."""
        return [
            "A" * 10000,  # String muito longa
            "B" * 1000000,  # String gigante
            [i for i in range(100000)],  # Array gigante
            {"key" + str(i): i for i in range(10000)},  # Objeto com muitas chaves
        ]

    @staticmethod
    def sql_injection_payloads() -> List[str]:
        """Payloads comuns de SQL Injection."""
        return [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "1; DELETE FROM users--",
        ]

    @staticmethod
    def xss_injection_payloads() -> List[str]:
        """Payloads comuns de XSS Injection."""
        return [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(\"xss\")'></iframe>",
        ]

    @staticmethod
    def malformed_json_payloads() -> List[str]:
        """Payloads JSON malformados."""
        return [
            "{invalid}",
            "{'single': 'quotes'}",
            '{"unclosed": "string}',
            '{"missing": "comma" "next": "field"}',
            "{,}",
            '{"duplicate": 1, "duplicate": 2}',
        ]

    @staticmethod
    def random_string_payloads(count: int = 10) -> List[str]:
        """Gera strings aleatórias."""
        return [
            ''.join(random.choices(string.ascii_letters + string.digits, k=50))
            for _ in range(count)
        ]

    @staticmethod
    def unicode_attack_payloads() -> List[str]:
        """Payloads com caracteres Unicode perigosos."""
        return [
            "\x00\x01\x02",  # Null bytes
            "‌‍​‮‭",  # Bidi override characters
            "￿￾",  # Invalid Unicode
            "𝓡𝓞𝓞𝓣",  # Mathematical Alphanumeric Symbols
            "👨‍👩‍👧‍👦",  # Zero-width joiner sequences
        ]

    @staticmethod
    def deep_nesting_payloads(depth: int = 100) -> List[Dict[str, Any]]:
        """Gera estruturas profundamente aninhadas."""
        nested = {"level": 0}
        current = nested
        for i in range(1, depth):
            current["nested"] = {"level": i}
            current = current["nested"]
        return [nested]


class ContinuousAPIFuzzer:
    """Executor de fuzzing contínuo para APIs AIDD."""

    def __init__(self, base_url: str = "http://localhost:3000", max_tests_per_route: int = 50):
        self.base_url = base_url
        self.max_tests_per_route = max_tests_per_route
        self.results: List[FuzzTestResult] = []
        self.payload_generator = PayloadGenerator()

    def generate_fuzz_cases(self, strategy: FuzzingStrategy) -> List[Any]:
        """Gera casos de fuzz para uma estratégia específica."""
        if strategy == FuzzingStrategy.NULL_INJECTION:
            return self.payload_generator.null_injection()
        elif strategy == FuzzingStrategy.BOUNDARY_VALUES:
            return self.payload_generator.boundary_values()
        elif strategy == FuzzingStrategy.TYPE_COERCION:
            return self.payload_generator.type_coercion()
        elif strategy == FuzzingStrategy.OVERFLOW:
            return self.payload_generator.overflow_payloads()
        elif strategy == FuzzingStrategy.SQL_INJECTION:
            return self.payload_generator.sql_injection_payloads()
        elif strategy == FuzzingStrategy.XSS_INJECTION:
            return self.payload_generator.xss_injection_payloads()
        elif strategy == FuzzingStrategy.MALFORMED_JSON:
            return self.payload_generator.malformed_json_payloads()
        elif strategy == FuzzingStrategy.RANDOM_STRING:
            return self.payload_generator.random_string_payloads(10)
        elif strategy == FuzzingStrategy.UNICODE_ATTACKS:
            return self.payload_generator.unicode_attack_payloads()
        elif strategy == FuzzingStrategy.DEEP_NESTING:
            return self.payload_generator.deep_nesting_payloads()
        return []

    def execute_fuzz_request(
        self,
        route: str,
        method: str,
        payload: Any,
        headers: Dict[str, str] = None
    ) -> Tuple[int, Any, bool, str]:
        """Executa uma requisição fuzzed contra a API."""
        import urllib.request
        import urllib.error

        if headers is None:
            headers = {"Content-Type": "application/json"}

        try:
            url = f"{self.base_url}{route}"
            body = json.dumps(payload).encode('utf-8') if method in ["POST", "PUT"] else b""

            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=5) as response:
                    resp_body = response.read().decode('utf-8', errors='replace')
                    try:
                        resp_json = json.loads(resp_body)
                    except:
                        resp_json = resp_body
                    return response.status, resp_json, False, ""
            except urllib.error.HTTPError as e:
                resp_body = e.read().decode('utf-8', errors='replace')
                try:
                    resp_json = json.loads(resp_body)
                except:
                    resp_json = resp_body
                # Status 5xx é considerado crash
                is_crash = e.code >= 500
                return e.code, resp_json, is_crash, str(e)
            except Exception as e:
                return 0, None, True, str(e)

        except Exception as e:
            return 0, None, True, str(e)

    def fuzz_route(
        self,
        route: str,
        method: str = "POST",
        strategies: List[FuzzingStrategy] = None
    ) -> List[FuzzTestResult]:
        """Executa fuzzing em uma rota específica."""
        if strategies is None:
            strategies = list(FuzzingStrategy)

        route_results = []

        for strategy in strategies:
            payloads = self.generate_fuzz_cases(strategy)
            test_count = min(len(payloads), self.max_tests_per_route)

            for payload in payloads[:test_count]:
                status_code, response, is_crash, error_msg = self.execute_fuzz_request(
                    route, method, payload
                )

                is_error = status_code >= 400

                result = FuzzTestResult(
                    route=route,
                    method=method,
                    strategy=strategy,
                    payload=payload,
                    status_code=status_code,
                    response=response,
                    is_crash=is_crash,
                    is_error=is_error,
                    error_message=error_msg
                )

                route_results.append(result)
                self.results.append(result)

        return route_results

    def fuzz_all_routes(self, routes: List[Tuple[str, str]]) -> List[FuzzTestResult]:
        """Executa fuzzing em múltiplas rotas."""
        all_results = []
        for route, method in routes:
            results = self.fuzz_route(route, method)
            all_results.extend(results)
        return all_results

    def generate_report(self) -> Dict[str, Any]:
        """Gera relatório de fuzzing."""
        total_tests = len(self.results)
        crashes = sum(1 for r in self.results if r.is_crash)
        errors = sum(1 for r in self.results if r.is_error and not r.is_crash)
        successes = total_tests - crashes - errors

        crashes_by_route = {}
        errors_by_route = {}
        for result in self.results:
            if result.is_crash:
                crashes_by_route.setdefault(result.route, []).append(result)
            elif result.is_error:
                errors_by_route.setdefault(result.route, []).append(result)

        return {
            "total_tests": total_tests,
            "crashes": crashes,
            "errors": errors,
            "successes": successes,
            "crash_rate": crashes / total_tests if total_tests > 0 else 0,
            "error_rate": errors / total_tests if total_tests > 0 else 0,
            "success_rate": successes / total_tests if total_tests > 0 else 0,
            "crashes_by_route": {k: len(v) for k, v in crashes_by_route.items()},
            "errors_by_route": {k: len(v) for k, v in errors_by_route.items()},
            "critical_findings": [
                {
                    "route": r.route,
                    "method": r.method,
                    "strategy": r.strategy.value,
                    "payload": str(r.payload)[:100],
                    "error": r.error_message
                }
                for r in self.results if r.is_crash
            ]
        }

    def print_report(self):
        """Imprime relatório formatado."""
        report = self.generate_report()

        print("\n" + "=" * 80)
        print("📊 RELATÓRIO DE FUZZING DE API CONTÍNUO (Continuous API Fuzzing)")
        print("=" * 80)
        print(f"\n✓ Testes Executados: {report['total_tests']}")
        print(f"  ├─ ✅ Sucessos: {report['successes']} ({report['success_rate']:.1%})")
        print(f"  ├─ ⚠️  Erros (4xx): {report['errors']} ({report['error_rate']:.1%})")
        print(f"  └─ 💥 Crashes (5xx): {report['crashes']} ({report['crash_rate']:.1%})")

        if report['crashes_by_route']:
            print(f"\n🔴 Rotas com CRASHES ({len(report['crashes_by_route'])}):")
            for route, count in report['crashes_by_route'].items():
                print(f"  └─ {route}: {count} crashes")

        if report['errors_by_route']:
            print(f"\n🟡 Rotas com ERROS ({len(report['errors_by_route'])}):")
            for route, count in report['errors_by_route'].items():
                print(f"  └─ {route}: {count} erros")

        if report['critical_findings']:
            print(f"\n🚨 Findings Críticos ({len(report['critical_findings'])}):")
            for finding in report['critical_findings'][:5]:
                print(f"  └─ {finding['route']} ({finding['strategy']}): {finding['error'][:50]}")

        print("\n" + "=" * 80)

        return report


def extract_routes_from_registry(registry) -> List[Tuple[str, str]]:
    """Extrai rotas do RouteRegistry para fuzzing."""
    routes = []
    try:
        # Acessa as rotas registradas no RouteRegistry
        for method in ["GET", "POST", "PUT", "DELETE"]:
            if method in registry.routes:
                for path in registry.routes[method].keys():
                    routes.append((path, method))
    except Exception as e:
        print(f"[!] Erro ao extrair rotas: {e}")
    return routes


if __name__ == "__main__":
    print("[*] Fuzzing Contínuo de APIs - Teste Standalone")
    print("[*] Este módulo é importado por compose_suite.py e G_QUALIDADE.py")
