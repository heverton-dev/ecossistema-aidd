# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 11 (D11): falha estruturada e retry com backoff de I/O.

No Windows, o os.replace de um mapa falha com PermissionError enquanto o navegador ou o
antivírus segura o arquivo. Agora a troca é repetida com espera crescente (0,2 s, 0,4 s)
e só desiste depois da 3ª tentativa; erro de dado (FileNotFoundError, ValueError) não é
transitório e não se repete. Quando desiste, cada script sai com exit 1, uma linha [ERRO]
e uma linha JSON {estagio, tipo, arquivo, tentativas, erro}, sem traceback cru.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _modulos():
    import gravacao_atomica_mapas
    import resiliencia_mapas
    return gravacao_atomica_mapas, resiliencia_mapas


def test_troca_presa_duas_vezes_passa_na_terceira_com_espera_crescente(tmp_path, monkeypatch):
    ga, rm = _modulos()
    esperas, chamadas = [], []
    original = ga.os.replace

    def replace_preso_duas_vezes(origem, destino):
        chamadas.append(destino)
        if len(chamadas) <= 2:
            raise PermissionError(13, "arquivo preso pelo navegador", str(destino))
        return original(origem, destino)

    monkeypatch.setattr(ga.os, "replace", replace_preso_duas_vezes)
    monkeypatch.setattr(rm, "_dormir", esperas.append)
    alvo = tmp_path / "mapa.html"
    alvo.write_text("velho", encoding="utf-8")

    assert ga.gravar_lote({alvo: "novo"}) == [alvo]
    assert alvo.read_text(encoding="utf-8") == "novo"
    assert len(chamadas) == 3
    assert esperas == [0.2, 0.4] and sum(esperas) >= 0.2 + 0.4
    assert sorted(p.name for p in tmp_path.iterdir()) == ["mapa.html"]


@pytest.mark.parametrize("erro", [FileNotFoundError(2, "molde sumiu"), ValueError("molde e gerador desencontrados")])
def test_erro_de_dado_nao_se_repete(erro):
    _, rm = _modulos()
    esperas, chamadas = [], []

    def falha():
        chamadas.append(1)
        raise erro

    with pytest.raises(type(erro)):
        rm.com_retry(falha, dormir=esperas.append)
    assert chamadas == [1] and esperas == []


def test_desistencia_marca_as_tentativas_no_erro():
    _, rm = _modulos()
    esperas = []

    def sempre_presa():
        raise PermissionError(13, "preso")

    with pytest.raises(PermissionError) as info:
        rm.com_retry(sempre_presa, tentativas=3, espera_base=0.2, dormir=esperas.append)
    assert info.value.tentativas == 3
    assert esperas == [0.2, 0.4]


def _linhas_json(saida: str) -> list[dict]:
    linhas = []
    for linha in saida.splitlines():
        try:
            dado = json.loads(linha)
        except ValueError:
            continue
        if isinstance(dado, dict):
            linhas.append(dado)
    return linhas


def _main_catalogo(tmp_path):
    import catalogo_pecas
    return catalogo_pecas.main(["--saida", str(tmp_path / "catalogo.json")])


def _main_mapa(tmp_path):
    import mapa_visual
    return mapa_visual.main(["leis", "--saida", str(tmp_path / "leis.html")])


def _main_nao_tecnico(tmp_path):
    import compilar_mapas_nao_tecnicos
    return compilar_mapas_nao_tecnicos.main()


def _main_livro(tmp_path):
    import livro_mapas
    return livro_mapas.main([])


@pytest.mark.parametrize("estagio, rodar", [("catalogo", _main_catalogo), ("mapa", _main_mapa),
                                            ("nao-tecnico", _main_nao_tecnico), ("livro", _main_livro)])
def test_falha_permanente_sai_com_uma_linha_json(estagio, rodar, tmp_path, monkeypatch, capsys):
    """Troca sempre presa: nada é gravado (rollback), exit 1, [ERRO] e uma linha JSON."""
    ga, rm = _modulos()

    def replace_sempre_preso(origem, destino):
        raise PermissionError(13, "arquivo preso pelo antivírus", str(destino))

    monkeypatch.setattr(ga.os, "replace", replace_sempre_preso)
    monkeypatch.setattr(rm, "_dormir", lambda segundos: None)

    assert rodar(tmp_path) == 1
    saida = capsys.readouterr()
    assert "Traceback" not in saida.out + saida.err
    assert "[ERRO]" in saida.out
    linhas = _linhas_json(saida.out)
    assert len(linhas) == 1, saida.out
    falha = linhas[0]
    assert set(falha) == {"estagio", "tipo", "arquivo", "tentativas", "erro"}
    assert falha["estagio"] == estagio
    assert falha["tentativas"] == 3
    assert falha["arquivo"] and "preso" in falha["erro"]


def test_falha_mapa_vira_json_de_uma_linha():
    _, rm = _modulos()
    falha = rm.FalhaMapa("mapa", "leis", "docs/mapas-visuais/mapa-01-leis.html", PermissionError(13, "preso"), 3)
    texto = falha.para_json()
    assert "\n" not in texto
    assert json.loads(texto) == {"estagio": "mapa", "tipo": "leis", "arquivo": "docs/mapas-visuais/mapa-01-leis.html",
                                 "tentativas": 3, "erro": "[Errno 13] preso"}
