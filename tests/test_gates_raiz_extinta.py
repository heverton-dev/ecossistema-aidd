"""Ticket 8 (ciclo-03 VSA, decisão C): cada gate mora só na fatia dona.

Reprova se sobrar G_*.py na pasta gates/ da raiz, se um gate do ecossistema
existir em mais de uma pasta de gates, se o mapa ainda apontar para um caminho
que não é o final, se o teste do gate não estiver ao lado dele, ou se
allowlist_fronteira.json e manifesto_harnesses.json não estiverem em
modulos/04-nucleo-compartilhado/contracts.
"""

import json
import subprocess
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CONTRATOS = RAIZ / "modulos" / "04-nucleo-compartilhado" / "contracts"
MAPA = CONTRATOS / "MAPA-GATES.json"


def _rastreados() -> list[str]:
    proc = subprocess.run(["git", "ls-files", "-z"], cwd=str(RAIZ), capture_output=True, check=True)
    return [p for p in proc.stdout.decode("utf-8", errors="replace").split("\0") if p]


def _mapa() -> dict:
    return json.loads(MAPA.read_text(encoding="utf-8"))["gates"]


PASTAS_DE_GATES = {
    "gates",
    "modulos/01-governanca-e-qualidade/gates",
    "modulos/02-triade-motores/fluxo-01-pure/gates",
    "modulos/02-triade-motores/fluxo-02-open/gates",
    "modulos/02-triade-motores/fluxo-03-freedom/gates",
    "modulos/03-plataforma-e-entrega/gates",
    "modulos/04-nucleo-compartilhado/gates",
}


def _pasta_de_gates_do_ecossistema(caminho: str) -> bool:
    """Pastas de gates do ecossistema (gates internos das ferramentas não contam)."""
    return caminho.rsplit("/", 1)[0] in PASTAS_DE_GATES


def test_raiz_sem_gates():
    sobras = [p for p in _rastreados() if p.startswith("gates/") and Path(p).name.startswith("G_")]
    assert not sobras, f"G_*.py ainda em gates/ da raiz: {sobras}"
    assert not (RAIZ / "gates").is_dir() or not list((RAIZ / "gates").glob("G_*.py"))


def test_cada_gate_e_cada_teste_de_gate_em_um_lugar_so():
    locais = defaultdict(list)
    for p in _rastreados():
        nome = Path(p).name
        if (nome.startswith("G_") or nome.startswith("test_g_")) and nome.endswith(".py") \
                and _pasta_de_gates_do_ecossistema(p):
            locais[nome].append(p)
    repetidos = {n: ps for n, ps in locais.items() if len(ps) > 1}
    assert not repetidos, f"{len(repetidos)} nome(s) em mais de um lugar: {sorted(repetidos)[:10]}"


def test_mapa_aponta_para_o_caminho_final_e_o_arquivo_existe():
    for nome, info in _mapa().items():
        assert info["caminho"] == info["caminho_final"], f"{nome} ainda em {info['caminho']}"
        assert (RAIZ / info["caminho_final"]).is_file(), f"{nome} ausente em {info['caminho_final']}"


def test_teste_do_gate_mora_ao_lado_do_gate():
    for nome, info in _mapa().items():
        pasta = (RAIZ / info["caminho_final"]).parent
        assert (pasta / f"test_{nome.lower()}.py").is_file(), f"{nome}: teste fora de {pasta}"


def test_contratos_compartilhados_no_nucleo():
    for nome in ("allowlist_fronteira.json", "manifesto_harnesses.json"):
        assert (CONTRATOS / nome).is_file(), f"{nome} fora de {CONTRATOS}"
        assert not (RAIZ / "gates" / nome).exists(), f"{nome} ainda em gates/"
