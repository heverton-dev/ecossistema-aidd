# -*- coding: utf-8 -*-
"""
Testes unitários para o Result Monad com motor 'returns' (dry-python).
Valida operações monádicas (map, bind, alt, unwrap, value_or) e retrocompatibilidade.
"""

import unittest
from returns.result import Success, Failure, Result as ReturnsResult
from src.core.result import Result


class TestResultReturnsMonad(unittest.TestCase):
    def test_ok_criacao_e_acessores(self):
        res = Result.ok(42, detalhes={"origem": "teste"})
        self.assertTrue(res.sucesso)
        self.assertEqual(res.valor, 42)
        self.assertIsNone(res.erro)
        self.assertEqual(res.codigo, "SUCESSO")
        self.assertEqual(res.detalhes, {"origem": "teste"})
        self.assertEqual(res.unwrap(), 42)
        self.assertEqual(res.value_or(0), 42)
        self.assertIn("42", repr(res))

    def test_fail_criacao_e_acessores(self):
        res = Result.fail("erro de validacao", codigo="INVALID_INPUT", detalhes={"campo": "email"})
        self.assertFalse(res.sucesso)
        self.assertIsNone(res.valor)
        self.assertEqual(res.erro, "erro de validacao")
        self.assertEqual(res.codigo, "INVALID_INPUT")
        self.assertEqual(res.detalhes, {"campo": "email"})
        self.assertEqual(res.value_or(100), 100)
        self.assertIn("INVALID_INPUT", repr(res))

    def test_to_dict_formato(self):
        ok = Result.ok({"id": 1})
        d_ok = ok.to_dict()
        self.assertEqual(d_ok, {"sucesso": True, "codigo": "SUCESSO", "dados": {"id": 1}})

        fail = Result.fail("falhou", codigo="ERR_1")
        d_fail = fail.to_dict()
        self.assertEqual(d_fail, {"sucesso": False, "codigo": "ERR_1", "erro": "falhou"})

    def test_map_monadico_sucesso(self):
        res = Result.ok(10).map(lambda x: x * 3).map(lambda x: f"total: {x}")
        self.assertTrue(res.sucesso)
        self.assertEqual(res.valor, "total: 30")

    def test_map_monadico_ignora_em_falha(self):
        fail = Result.fail("falha original", codigo="ORIG_ERR")
        res = fail.map(lambda x: x * 10)
        self.assertFalse(res.sucesso)
        self.assertEqual(res.erro, "falha original")
        self.assertEqual(res.codigo, "ORIG_ERR")

    def test_bind_flat_map_sucesso(self):
        def parse_int(s: str) -> Result[int]:
            try:
                return Result.ok(int(s))
            except ValueError:
                return Result.fail("nao eh inteiro", codigo="PARSE_ERROR")

        def dobro(n: int) -> Result[int]:
            return Result.ok(n * 2)

        res = Result.ok("25").bind(parse_int).bind(dobro)
        self.assertTrue(res.sucesso)
        self.assertEqual(res.valor, 50)

    def test_bind_interrompe_no_primeiro_erro(self):
        def parse_int(s: str) -> Result[int]:
            try:
                return Result.ok(int(s))
            except ValueError:
                return Result.fail("nao eh inteiro", codigo="PARSE_ERROR")

        def dobro(n: int) -> Result[int]:
            return Result.ok(n * 2)

        res = Result.ok("invalido").bind(parse_int).bind(dobro)
        self.assertFalse(res.sucesso)
        self.assertEqual(res.codigo, "PARSE_ERROR")

    def test_alt_monadico_transforma_erro(self):
        fail = Result.fail("erro 1", codigo="ERR").alt(lambda e: f"prefixo: {e}")
        self.assertFalse(fail.sucesso)
        self.assertEqual(fail.erro, "prefixo: erro 1")

    def test_interoperabilidade_returns_library(self):
        # to_returns
        r_ok = Result.ok("dado")
        ret_ok = r_ok.to_returns()
        self.assertIsInstance(ret_ok, Success)
        self.assertEqual(ret_ok.unwrap(), "dado")

        r_fail = Result.fail("pane")
        ret_fail = r_fail.to_returns()
        self.assertIsInstance(ret_fail, Failure)

        # from_returns
        conv_ok = Result.from_returns(Success(99))
        self.assertTrue(conv_ok.sucesso)
        self.assertEqual(conv_ok.valor, 99)

        conv_fail = Result.from_returns(Failure("msg falha"), codigo="CUSTOM_ERR")
        self.assertFalse(conv_fail.sucesso)
        self.assertEqual(conv_fail.erro, "msg falha")
        self.assertEqual(conv_fail.codigo, "CUSTOM_ERR")


if __name__ == "__main__":
    unittest.main()
