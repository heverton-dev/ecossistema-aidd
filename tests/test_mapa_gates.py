"""Ticket 7 (ciclo-03 VSA, decisão C): mapa de donos dos gates.

Cada gate G_*.py do ecossistema aparece uma vez em
modulos/04-nucleo-compartilhado/contracts/MAPA-GATES.json com um dono e um
caminho final. O runner do 'audit', o .pre-commit-config.yaml e os gates que
varrem "todos os gates" (G_SAIDA_BINARIA, G_PORTAO_PROVA_QUE_MORDE) leem os
caminhos do mapa.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MAPA = RAIZ / "modulos" / "04-nucleo-compartilhado" / "contracts" / "MAPA-GATES.json"
PRECOMMIT = RAIZ / ".pre-commit-config.yaml"
FATIAS = {
    "01-governanca-e-qualidade",
    "02-triade-motores/fluxo-01-pure",
    "02-triade-motores/fluxo-02-open",
    "02-triade-motores/fluxo-03-freedom",
    "03-plataforma-e-entrega",
    "04-nucleo-compartilhado",
}
NUCLEO = "04-nucleo-compartilhado"

sys.path.insert(0, str(RAIZ))
try:
    from scripts import mapa_gates  # noqa: E402
except ImportError:  # vermelho do TDD: cada teste reprova (exit 1), não erro de coleta
    mapa_gates = None


@pytest.fixture(autouse=True)
def _leitor_existe():
    assert mapa_gates is not None, "scripts/mapa_gates.py ausente"


def _gates_no_disco() -> set[str]:
    nomes = {p.stem for p in (RAIZ / "gates").glob("G_*.py")}
    for fatia in FATIAS:
        nomes |= {p.stem for p in (RAIZ / "modulos" / fatia / "gates").glob("G_*.py")}
    return nomes


def _gates_no_precommit() -> set[str]:
    return set(re.findall(r"entry:\s*python\s+\S*?(G_\w+)\.py", PRECOMMIT.read_text(encoding="utf-8")))


def _mapa() -> dict:
    return json.loads(MAPA.read_text(encoding="utf-8"))["gates"]


def test_mapa_existe_e_cobre_todo_gate_do_disco_e_da_bateria():
    gates = _mapa()
    faltando = (_gates_no_disco() | _gates_no_precommit()) - set(gates)
    assert not faltando, f"gates fora do mapa: {sorted(faltando)}"
    sobrando = set(gates) - _gates_no_disco()
    assert not sobrando, f"mapa cita gate inexistente: {sorted(sobrando)}"


def test_cada_gate_tem_um_dono_e_um_caminho_final_na_pasta_do_dono():
    finais = []
    for nome, info in _mapa().items():
        assert info["dono"] in FATIAS, f"{nome}: dono inválido {info['dono']!r}"
        esperado = f"modulos/{info['dono']}/gates/{nome}.py"
        assert info["caminho_final"] == esperado, f"{nome}: caminho_final fora da pasta do dono"
        if info["transversal"]:
            assert info["dono"] == NUCLEO, f"{nome}: transversal mora em {NUCLEO}"
        assert (RAIZ / info["caminho"]).is_file(), f"{nome}: caminho vigente não existe: {info['caminho']}"
        finais.append(info["caminho_final"])
    assert len(finais) == len(set(finais))


def test_donos_fixados_pelo_plano():
    gates = _mapa()
    for nome in ("G_SEGREDOS", "G_SAIDA_BINARIA", "G_HARNESS_COMPAT", "G_ECOSSISTEMA_INTEGRIDADE"):
        assert gates[nome]["dono"] == NUCLEO and gates[nome]["transversal"], nome
    assert gates["G_aidd_forge"]["dono"] == "01-governanca-e-qualidade"
    assert gates["G_MIGRATION_ROT"]["dono"] == "02-triade-motores/fluxo-03-freedom"
    assert gates["G_INFRA_COMPOSE"]["dono"] == "03-plataforma-e-entrega"


def test_leitor_resolve_caminho_pelo_mapa(tmp_path):
    destino = tmp_path / "modulos" / NUCLEO / "contracts"
    destino.mkdir(parents=True)
    (destino / "MAPA-GATES.json").write_text(json.dumps({"gates": {"G_X": {
        "dono": NUCLEO, "transversal": True, "caminho": "outro/lugar/G_X.py",
        "caminho_final": f"modulos/{NUCLEO}/gates/G_X.py"}}}), encoding="utf-8")
    assert mapa_gates.caminho("G_X", raiz=tmp_path) == tmp_path / "outro" / "lugar" / "G_X.py"
    with pytest.raises(KeyError):
        mapa_gates.caminho("G_INEXISTENTE", raiz=tmp_path)


def test_precommit_usa_os_caminhos_do_mapa():
    gates = _mapa()
    entradas = re.findall(r"entry:\s*python\s+(\S*G_\w+\.py)", PRECOMMIT.read_text(encoding="utf-8"))
    assert entradas
    for caminho in entradas:
        nome = Path(caminho).stem
        assert caminho == gates[nome]["caminho"], f"{nome}: pre-commit aponta {caminho}"
    assert mapa_gates.verificar_precommit(RAIZ) == []


def test_sincronizar_precommit_reescreve_entry_divergente(tmp_path):
    cfg = tmp_path / ".pre-commit-config.yaml"
    cfg.write_text("      - id: g-saida-binaria\n        entry: python gates/G_SAIDA_BINARIA.py --x\n",
                   encoding="utf-8")
    mapa = {"G_SAIDA_BINARIA": {"caminho": f"modulos/{NUCLEO}/gates/G_SAIDA_BINARIA.py"}}
    assert mapa_gates.verificar_precommit(tmp_path, mapa=mapa)
    mapa_gates.sincronizar_precommit(tmp_path, mapa=mapa)
    assert f"entry: python modulos/{NUCLEO}/gates/G_SAIDA_BINARIA.py --x" in cfg.read_text(encoding="utf-8")
    assert mapa_gates.verificar_precommit(tmp_path, mapa=mapa) == []


def test_runner_do_audit_resolve_gates_pelo_mapa(monkeypatch):
    import ecossistema

    chamados = []
    monkeypatch.setattr(mapa_gates, "caminho", lambda nome, raiz=None: Path("lugar_do_mapa") / f"{nome}.py")
    monkeypatch.setattr(ecossistema, "run_command", lambda cmd, **kw: chamados.append(cmd[1]) or 0)
    assert ecossistema._audit_gates_legado([]) == 0
    assert chamados and all(Path(c).parent == Path("lugar_do_mapa") for c in chamados)


def test_g_saida_binaria_le_a_lista_do_mapa(tmp_path):
    """Gate fora de gates/ mas listado no mapa precisa ser auditado (e reprovar)."""
    ruim = tmp_path / "modulos" / NUCLEO / "gates" / "G_RUIM.py"
    ruim.parent.mkdir(parents=True)
    ruim.write_text("import sys\nif __name__ == '__main__':\n    sys.exit(3)\n", encoding="utf-8")
    contratos = tmp_path / "modulos" / NUCLEO / "contracts"
    contratos.mkdir(parents=True)
    (contratos / "MAPA-GATES.json").write_text(json.dumps({"gates": {"G_RUIM": {
        "dono": NUCLEO, "transversal": True, "caminho": f"modulos/{NUCLEO}/gates/G_RUIM.py",
        "caminho_final": f"modulos/{NUCLEO}/gates/G_RUIM.py"}}}), encoding="utf-8")
    gate = RAIZ / mapa_gates.caminho("G_SAIDA_BINARIA")
    proc = subprocess.run([sys.executable, str(gate), "--raiz", str(tmp_path)],
                          capture_output=True, text=True, cwd=str(RAIZ))
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "G_RUIM.py" in proc.stdout


def test_g_portao_prova_que_morde_lista_gates_pelo_mapa(tmp_path):
    contratos = tmp_path / "modulos" / NUCLEO / "contracts"
    contratos.mkdir(parents=True)
    (contratos / "MAPA-GATES.json").write_text(json.dumps({"gates": {"G_SEM_TESTE": {
        "dono": NUCLEO, "transversal": True, "caminho": f"modulos/{NUCLEO}/gates/G_SEM_TESTE.py",
        "caminho_final": f"modulos/{NUCLEO}/gates/G_SEM_TESTE.py"}}}), encoding="utf-8")
    gate_dir = tmp_path / "modulos" / NUCLEO / "gates"
    gate_dir.mkdir(parents=True)
    (gate_dir / "G_SEM_TESTE.py").write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    gate = RAIZ / mapa_gates.caminho("G_PORTAO_PROVA_QUE_MORDE")
    proc = subprocess.run([sys.executable, str(gate), "--raiz", str(tmp_path)],
                          capture_output=True, text=True, cwd=str(RAIZ),
                          env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "G_SEM_TESTE.py" in proc.stdout
