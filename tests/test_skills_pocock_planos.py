# -*- coding: utf-8 -*-
"""
Ticket 10 (skills-pocock ciclo-01, D5): seções de escopo no modelo de plano.

O modelo vem de script (scripts/gerenciador_planos.py, chamado por
`python ecossistema.py plan init`), então o teste roda o gerador de verdade numa
pasta temporária e confere o arquivo gerado, não o texto da skill.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gerenciador_planos import cmd_init, cmd_atualizar_nota  # noqa: E402


def _processo_gerado(tmp_path: Path) -> tuple[Path, str]:
    assert cmd_init("escopo teste", ["Primeiro item"], destino_base=tmp_path) == 0
    pastas = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(pastas) == 1
    return pastas[0], (pastas[0] / "00-PROCESSO-E-DECISOES.md").read_text(encoding="utf-8")


def _secao(texto: str, titulo_regex: str) -> str:
    m = re.search(rf"^###? {titulo_regex}\n(.*?)(?=^##|\Z)", texto, re.MULTILINE | re.DOTALL)
    assert m, f"seção '{titulo_regex}' ausente no plano gerado"
    return m.group(1)


def test_plano_gerado_tem_ainda_nao_especificado(tmp_path):
    _, texto = _processo_gerado(tmp_path)
    _secao(texto, r"Ainda n[aã]o especificado")


def test_plano_gerado_tem_fora_de_escopo_com_regra(tmp_path):
    _, texto = _processo_gerado(tmp_path)
    corpo = _secao(texto, r"Fora de escopo")
    assert re.search(r"nunca volta[^\n]*plano atual", corpo, re.IGNORECASE)


def test_secoes_de_escopo_vem_antes_do_processo(tmp_path):
    _, texto = _processo_gerado(tmp_path)
    i_fora = texto.index("Fora de escopo")
    i_proc = texto.index("## 2. Processo Adotado")
    assert i_fora < i_proc


def test_atualizar_nota_continua_funcionando(tmp_path):
    pasta, _ = _processo_gerado(tmp_path)
    assert cmd_atualizar_nota(str(pasta), None, "6", "pytest tests/x.py exit 0") == 0
    texto = (pasta / "00-PROCESSO-E-DECISOES.md").read_text(encoding="utf-8")
    assert "Fora de escopo" in texto
