"""Tests for plan_parser.py — parse real fixture folders."""

import pytest
from pathlib import Path

# Ensure the scripts package is importable
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from plan_parser import parse_plan, Plan, Front, extrair_prompt_executor


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent


def _plano(nome_curto: str) -> Path:
    """Acha a pasta do plano pelo nome curto, em qualquer subpasta de status.

    Resolve por glob de proposito: o nome fisico carrega o prefixo
    PLAN-<NNNN>_<dd-mm-aaaa>-, e o plano muda de subpasta conforme o status
    real. Fixar o caminho literal quebraria o teste a cada renomeacao ou
    mudanca de status — foi o que aconteceu em 11-09-2026.
    """
    partes = nome_curto.split("-")
    # Tenta o nome inteiro e vai encurtando: o nome fisico guarda so as 3
    # primeiras palavras significativas, entao "skill-gerador-planos-auditoria"
    # precisa casar com "...-skill-gerador-planos".
    while partes:
        alvo = "-".join(partes)
        for sub in ("feitos", "fazendo", "a-fazer", ""):
            base = REPO_ROOT / "docs" / "planos" / sub if sub else REPO_ROOT / "docs" / "planos"
            achados = sorted(p for p in base.glob(f"*{alvo}") if p.is_dir())
            if achados:
                return achados[0]
        partes.pop()
    raise FileNotFoundError(f"Plano '{nome_curto}' nao encontrado em docs/planos/")

FIXTURES = {
    "evolucao-notas-auditoria": _plano("evolucao-notas-auditoria"),
    "refinamento-notas-auditoria": _plano("refinamento-notas-auditoria"),
    "testes-completos-ecossistema": _plano("testes-completos-ecossistema"),
    "skill-gerador-planos-auditoria": _plano("skill-gerador-planos-auditoria"),
}

# Manually verified front counts (NN-*.md files, excluding 00-PROCESSO-E-DECISOES.md)
EXPECTED_COUNTS = {
    "evolucao-notas-auditoria": 7,   # 01..07
    "refinamento-notas-auditoria": 6, # 01..06
    "testes-completos-ecossistema": 6, # 01..05
    "skill-gerador-planos-auditoria": 1, # 01
}


class TestParseRealFixtures:
    """Parse each of the 4 real fixture folders."""

    @pytest.mark.parametrize(
        "folder_name",
        list(FIXTURES.keys()),
        ids=list(FIXTURES.keys()),
    )
    def test_parse_without_error(self, folder_name: str) -> None:
        folder = FIXTURES[folder_name]
        plan = parse_plan(folder)

        assert isinstance(plan, Plan)
        assert plan.front_count == EXPECTED_COUNTS[folder_name]

    def test_evolution_fronts_have_correct_names(self) -> None:
        plan = parse_plan(FIXTURES["evolucao-notas-auditoria"])
        names = [f.name for f in plan.fronts]
        assert names == [
            "transparencia-gates",
            "testabilidade-determinismo",
            "modularizacao-injector",
            "cobertura-comandos-restantes",
            "economia-tokens-agentico",
            "universalidade",
            "agnosticismo-distribuicao-componentes",
        ]

    def test_master_content_is_populated(self) -> None:
        plan = parse_plan(FIXTURES["testes-completos-ecossistema"])
        assert len(plan.master_content) > 100
        assert "PROCESSO" in plan.master_content.upper()

    def test_fronts_are_sorted_by_index(self) -> None:
        plan = parse_plan(FIXTURES["refinamento-notas-auditoria"])
        indices = [f.index for f in plan.fronts]
        assert indices == sorted(indices)

    def test_invalid_folder_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_plan("/nonexistent/path/xyz")

    def test_folder_without_master_raises(self, tmp_path: Path) -> None:
        (tmp_path / "01-algo.md").write_text("content")
        with pytest.raises(FileNotFoundError, match="Master file"):
            parse_plan(tmp_path)

    def test_folder_without_fronts_raises(self, tmp_path: Path) -> None:
        (tmp_path / "00-PROCESSO-E-DECISOES.md").write_text("master")
        with pytest.raises(ValueError, match=r"No NN-\*\.md"):
            parse_plan(tmp_path)

    def test_parse_dot_relative(self, tmp_path: Path) -> None:
        """Parser accepts '.' or relative paths."""
        (tmp_path / "00-PROCESSO-E-DECISOES.md").write_text("master content")
        (tmp_path / "01-frente-a.md").write_text("front a content")
        (tmp_path / "02-frente-b.md").write_text("front b content")

        plan = parse_plan(tmp_path)
        assert plan.front_count == 2
        assert plan.fronts[0].name == "frente-a"
        assert plan.fronts[1].name == "frente-b"


class TestParseFrontContent:
    """Verify that front content is actually read from files."""

    def test_front_content_matches_file(self) -> None:
        plan = parse_plan(FIXTURES["skill-gerador-planos-auditoria"])
        assert plan.front_count == 1
        front = plan.fronts[0]
        assert front.name == "criar-skill-planos"
        # Content should be read from disk
        disk_content = front.file_path.read_text(encoding="utf-8")
        assert front.content == disk_content


class TestExtrairPromptExecutor:
    """extrair_prompt_executor deve sempre incluir o texto de instrucao em
    ingles real (nao so a cerca de codigo) - regressao de um bug real onde
    o grupo errado da regex era capturado e o corpo do prompt sumia."""

    ITEM_COM_CERCA_TRIPLA = """## Escopo
> **Escopo:** Texto de escopo.

## Definicao de Pronto

1. Criterio um.
2. Criterio dois.

## Criterio de saida

- Saida um.

## Prompt de Execucao (PT-BR)

```
Prompt em portugues.
```

## Prompt de Execucao — English version

```
You are going to implement this. Follow the Definition of Done above.
```
"""

    ITEM_COM_CERCA_SIMPLES = ITEM_COM_CERCA_TRIPLA.replace("```", "`")

    def test_extrai_corpo_real_do_prompt_ingles_cerca_tripla(self) -> None:
        resultado = extrair_prompt_executor(self.ITEM_COM_CERCA_TRIPLA)
        assert "You are going to implement this." in resultado
        assert "Follow the Definition of Done above." in resultado
        assert "Criterio um." in resultado

    def test_extrai_corpo_real_do_prompt_ingles_cerca_simples(self) -> None:
        resultado = extrair_prompt_executor(self.ITEM_COM_CERCA_SIMPLES)
        assert "You are going to implement this." in resultado

    def test_fallback_para_conteudo_integral_quando_formato_nao_reconhecido(self) -> None:
        texto = "# Item sem estrutura nenhuma\nsó um paragrafo qualquer.\n"
        assert extrair_prompt_executor(texto) == texto

    def test_nunca_inclui_apenas_a_cerca_de_codigo_vazia(self) -> None:
        """Trava especifica do bug: group(1) era a cerca ('```' ou '`'),
        nao o conteudo - garante que isso nunca mais escapa em silencio."""
        resultado = extrair_prompt_executor(self.ITEM_COM_CERCA_TRIPLA)
        assert resultado.strip() not in ("```", "`", "")
