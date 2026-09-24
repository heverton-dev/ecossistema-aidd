# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — TESTE DO SCAFFOLD DE AUDITORIA 4F (scripts/scaffold_auditoria.py)
=============================================================================
Regras (auditoria do aidd-diagnose, 2026-09-23/24):
  1. MANIFESTO-4F.json segue RIGOROSAMENTE harness/model/comando_terminal de
     docs/auditoria/CONFIG-EXECUCAO-USUARIO.json (chave 'pipeline_auditoria_4f').
     Nenhum valor padrão inventado: papel ausente ou incompleto reprova.
  2. O manifesto é artefato derivado: é regerado a cada execução, para nunca
     ficar defasado quando o usuário edita o config.
  3. O scaffold NUNCA escreve no CONFIG-EXECUCAO-USUARIO.json (só o humano edita).
  4. Prompts das fases citam o template real (docs/auditoria/...).
  5. Fases 2 e 3 recebem prompts fechados da própria ferramenta.
=============================================================================
"""

import json
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from scaffold_auditoria import criar_scaffold_auditoria  # noqa: E402

TEMPLATE_REAL = "docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md"
PAPEIS = ("inspetor", "arquiteto", "construtor", "retorno")


def _papeis(sufixo: str = "") -> dict:
    return {
        p: {"harness": f"h-{p}{sufixo}", "model": f"m-{p}{sufixo}", "comando_terminal": f"cmd-{p}{sufixo}"}
        for p in PAPEIS
    }


def _config(tmp_path: Path, conteudo: dict) -> Path:
    auditoria = tmp_path / "docs" / "auditoria"
    auditoria.mkdir(parents=True, exist_ok=True)
    caminho = auditoria / "CONFIG-EXECUCAO-USUARIO.json"
    caminho.write_text(json.dumps(conteudo), encoding="utf-8")
    return caminho


def _manifesto(tmp_path: Path, tool: str) -> dict:
    caminho = tmp_path / "docs" / "auditoria" / tool / "MANIFESTO-4F.json"
    return json.loads(caminho.read_text(encoding="utf-8"))


def test_manifesto_segue_config_rigorosamente(tmp_path):
    _config(tmp_path, {"pipeline_auditoria_4f": _papeis()})
    criar_scaffold_auditoria("ferramenta-x", repo_root=tmp_path)
    fases = _manifesto(tmp_path, "ferramenta-x")["fases"]

    for campo, prefixo in (("harness", "h"), ("model", "m"), ("comando_terminal", "cmd")):
        assert [f[campo] for f in fases] == [f"{prefixo}-{p}" for p in PAPEIS]


def test_manifesto_e_regerado_quando_config_muda(tmp_path):
    config = _config(tmp_path, {"pipeline_auditoria_4f": _papeis()})
    criar_scaffold_auditoria("ferramenta-x", repo_root=tmp_path)
    config.write_text(json.dumps({"pipeline_auditoria_4f": _papeis("-v2")}), encoding="utf-8")

    criar_scaffold_auditoria("ferramenta-x", repo_root=tmp_path)
    fases = _manifesto(tmp_path, "ferramenta-x")["fases"]
    assert [f["harness"] for f in fases] == [f"h-{p}-v2" for p in PAPEIS]


@pytest.mark.parametrize("conteudo", [
    {},
    {"pipeline_auditoria_4f": {p: v for p, v in _papeis().items() if p != "retorno"}},
    {"pipeline_auditoria_4f": {**_papeis(), "arquiteto": {"harness": "h", "model": "m"}}},
])
def test_config_ausente_ou_incompleto_reprova_sem_inventar_padrao(tmp_path, conteudo):
    _config(tmp_path, conteudo)
    with pytest.raises(ValueError, match="CONFIG-EXECUCAO-USUARIO.json"):
        criar_scaffold_auditoria("ferramenta-x", repo_root=tmp_path)
    assert not (tmp_path / "docs" / "auditoria" / "ferramenta-x" / "MANIFESTO-4F.json").exists()


def test_scaffold_nunca_escreve_no_config_do_usuario(tmp_path):
    config = _config(tmp_path, {"pipeline_auditoria_4f": _papeis()})
    antes = config.read_bytes()
    criar_scaffold_auditoria("ferramenta-x", repo_root=tmp_path)
    assert config.read_bytes() == antes


def test_prompts_apontam_para_template_existente(tmp_path):
    _config(tmp_path, {"pipeline_auditoria_4f": _papeis()})
    criar_scaffold_auditoria("ferramenta-z", repo_root=tmp_path)
    pasta = tmp_path / "docs" / "auditoria" / "ferramenta-z"

    assert (ROOT_DIR / TEMPLATE_REAL).exists()
    for nome in ("PROMPT-FASE-1-INSPETOR.txt", "PROMPT-FASE-4-RETORNO.txt"):
        texto = (pasta / nome).read_text(encoding="utf-8")
        assert TEMPLATE_REAL in texto, nome
        assert "docs/protocolos/TEMPLATE-AUDITORIA-FERRAMENTA.md" not in texto, nome


def test_fases_2_e_3_recebem_prompt_fechado_da_ferramenta(tmp_path):
    _config(tmp_path, {"pipeline_auditoria_4f": _papeis()})
    criar_scaffold_auditoria("ferramenta-w", repo_root=tmp_path)
    pasta = tmp_path / "docs" / "auditoria" / "ferramenta-w"
    fases = _manifesto(tmp_path, "ferramenta-w")["fases"]

    assert fases[1]["input_prompt"] == "docs/auditoria/ferramenta-w/PROMPT-FASE-2-ARQUITETO.txt"
    assert fases[2]["input_prompt"] == "docs/auditoria/ferramenta-w/PROMPT-FASE-3-CONSTRUTOR.txt"

    f2 = (pasta / "PROMPT-FASE-2-ARQUITETO.txt").read_text(encoding="utf-8")
    assert "docs/auditoria/ferramenta-w/LAUDO-15D-INICIAL.md" in f2
    assert "docs/auditoria/ferramenta-w/PLANO-EVOLUCAO.md" in f2
    assert "**Construtor Prompt (EN):**" in f2

    f3 = (pasta / "PROMPT-FASE-3-CONSTRUTOR.txt").read_text(encoding="utf-8")
    assert "docs/auditoria/ferramenta-w/PLANO-EVOLUCAO.json" in f3
    assert "docs/auditoria/ferramenta-w/prompts_tickets/" in f3

    # Únicos não-ASCII tolerados: rótulos fixos do ticket que o compilador lê por regex.
    rotulos_do_ticket = ("**Implementação Técnica:**", "**Verificação (Green):**")
    f2_sem_rotulos = f2
    for rotulo in rotulos_do_ticket:
        f2_sem_rotulos = f2_sem_rotulos.replace(rotulo, "")
    for texto in (f2_sem_rotulos, f3):
        assert "<ferramenta>" not in texto
        assert texto.isascii(), "prompt de fase deve ser ingles (ASCII)"
