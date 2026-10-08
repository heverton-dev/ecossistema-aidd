# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 2 (D13): G_mapa_pecas confere conteúdo, não só existência.

Achado F2 do laudo: 14 arquivos "<html>LIXO" de 330 bytes e um catálogo de listas
vazias passavam como "APROVADO (100% OK)" (mutante M5 sobrevivia). Agora cada mapa
oficial tem de ser byte a byte o que o mapa_visual monta do catálogo, e o catálogo
tem de ter listas cheias com totais iguais ao tamanho de cada lista.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "modulos" / "04-nucleo-compartilhado" / "gates" / "G_mapa_pecas.py"
CATALOGO = ROOT / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json"


def _rodar(*args):
    return subprocess.run([sys.executable, str(GATE), *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def _lixo() -> str:
    texto = "<html>" + "LIXO" * 100
    return texto[:330]


def test_html_lixo_com_nomes_oficiais_reprova(tmp_path):
    sys.path.insert(0, str(ROOT / "scripts"))
    import mapa_visual as mv
    nomes = ["manual-montagem-aidd.html", mv.arquivo_mapa("indice")] + [mv.arquivo_mapa(t) for t, _, _ in mv.MAPAS_PREVISTOS]
    for nome in nomes:
        for pasta in (tmp_path, tmp_path / "nao-tecnicos"):
            pasta.mkdir(exist_ok=True)
            (pasta / nome).write_text(_lixo(), encoding="utf-8")
    assert len(_lixo().encode("utf-8")) == 330
    proc = _rodar("--mapas-dir", str(tmp_path))
    assert proc.returncode == 1, proc.stdout
    assert "difere do que o mapa_visual monta" in proc.stdout


def test_catalogo_de_listas_vazias_reprova(tmp_path):
    vazio = {"versao": 1, "gerado_por": "scripts/catalogo_pecas.py",
             "totais": {"ferramentas": 8, "skills": 37, "leis": 14, "encaixes_quebrados": 0},
             "ferramentas": [], "skills": [], "leis": [], "encaixes": [], "gates": []}
    arq = tmp_path / "catalogo.json"
    arq.write_text(json.dumps(vazio), encoding="utf-8")
    proc = _rodar("--catalogo", str(arq))
    assert proc.returncode == 1, proc.stdout
    for chave in ("ferramentas", "skills", "leis", "encaixes", "gates"):
        assert f"lista '{chave}' vazia" in proc.stdout, chave


def test_total_diferente_do_tamanho_da_lista_reprova(tmp_path):
    dados = json.loads(CATALOGO.read_text(encoding="utf-8"))
    dados["totais"]["skills"] += 1
    arq = tmp_path / "catalogo.json"
    arq.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    proc = _rodar("--catalogo", str(arq))
    assert proc.returncode == 1, proc.stdout
    assert "totais.skills" in proc.stdout


def test_repositorio_real_aprova():
    proc = _rodar()
    assert proc.returncode == 0, proc.stdout + proc.stderr
