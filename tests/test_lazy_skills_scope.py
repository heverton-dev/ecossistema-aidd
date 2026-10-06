#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Testes unitários determinísticos para o GestorSkillsVSA e Poda de Contexto (Ticket 7)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.lazy_skills_scope import GestorSkillsVSA, obter_resumo_skills_fatia


class TestLazySkillsScope(unittest.TestCase):
    """Bateria de testes de resolução preguiçosa e poda de contexto."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.raiz = Path(self.temp_dir.name)

        # Criar estrutura simulada de fatias e skills
        self.mod_dir = self.raiz / "modulos" / "01-governanca-e-qualidade" / "skills" / "aidd-exemplo-local"
        self.mod_dir.mkdir(parents=True, exist_ok=True)
        self.skill_file = self.mod_dir / "SKILL.md"

        corpo_longo = "\n".join([f"Linha de detalhe tecnico extensivo {i}" for i in range(200)])
        conteudo = f"""---
name: aidd-exemplo-local
description: "Use when executing local slice governance audits."
---

# aidd-exemplo-local

Instrucoes basicas de governanca da fatia.

## Detalhes Extensivos
{corpo_longo}

## Negative Guardrails
- NEVER omit deterministic quality checks.

## Failure Modes
- Process failure falls back to manual inspection.

## Stopping Checklist
- [ ] Exit code 0 verified.
"""
        self.skill_file.write_text(conteudo, encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_mapeamento_preguicoso_fatias(self):
        """Valida que o gestor localiza skills de módulos agrupados por fatia."""
        gestor = GestorSkillsVSA(self.raiz)
        indice = gestor.mapear_fatias_locais()
        self.assertIn("01-governanca-e-qualidade", indice)
        self.assertEqual(len(indice["01-governanca-e-qualidade"]), 1)

    def test_extracao_metadados_sem_carregar_corpo_todo(self):
        """Valida extração determinística do frontmatter e use_when."""
        gestor = GestorSkillsVSA(self.raiz)
        meta = gestor.resolver_meta_preguicoso(self.skill_file)

        self.assertEqual(meta.nome, "aidd-exemplo-local")
        self.assertEqual(meta.fatia, "01-governanca-e-qualidade")
        self.assertTrue(meta.requer_carregamento_profundo)
        self.assertIn("local slice governance audits", meta.use_when)

    def test_poda_contexto_preserva_guardrails(self):
        """Garante que a poda reduz linhas sem perder guardrails mandatórios."""
        gestor = GestorSkillsVSA(self.raiz)
        podado = gestor.podar_contexto_skill(self.skill_file, max_linhas=150)

        self.assertIn("CONTEXT-PRUNING ACTIVE", podado)
        self.assertIn("## Negative Guardrails", podado)
        self.assertIn("## Failure Modes", podado)
        self.assertIn("## Stopping Checklist", podado)
        self.assertNotIn("Linha de detalhe tecnico extensivo 150", podado)
        self.assertLess(len(podado.splitlines()), 100)

    def test_resumo_skills_fatia(self):
        """Valida emissão do resumo compacto em dicionário para subagentes."""
        resumo = obter_resumo_skills_fatia("01-governanca-e-qualidade", self.raiz)
        self.assertEqual(len(resumo), 1)
        self.assertEqual(resumo[0]["skill"], "aidd-exemplo-local")
        self.assertIn("local slice governance audits", resumo[0]["use_when"])


if __name__ == "__main__":
    unittest.main()
