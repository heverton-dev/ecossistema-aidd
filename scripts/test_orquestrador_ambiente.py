"""ETAPA_08 (Ticket 1): a etapa 2 do /pure só abre o planner com o Ambiente registrado.

O orquestrador roda em subprocesso (sem bytecode) com `_executar_comando` trocado por um gravador:
assim o teste não importa o orquestrador no processo do pytest (o que alteraria o catálogo de peças)
e não dispara o planner de verdade.
"""
import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

SONDA = r"""
import json, sys
sys.path.insert(0, "scripts")
from pathlib import Path
import orquestrador_sincrono as o

pasta, mobbin = sys.argv[1], (sys.argv[2] or None)
orq = o.OrquestradorSincrono("pure", "App Amb", "app-amb", "fintech", pasta, mobbin=mobbin)
chamadas = []
orq._executar_comando = lambda cmd, cwd=None, env_extra=None: (chamadas.append([str(c) for c in cmd]) or 0)
orq._ler_contrato = lambda *a, **k: True
ok = orq.etapa_02_planner()
print("RESULTADO=" + json.dumps({"ok": ok, "chamadas": chamadas}))
"""


def _rodar(pasta, mobbin=""):
    res = subprocess.run(
        [sys.executable, "-B", "-c", SONDA, str(pasta), mobbin],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    linhas = [l for l in res.stdout.splitlines() if l.startswith("RESULTADO=")]
    assert linhas, res.stdout[-800:] + res.stderr[-800:]
    return json.loads(linhas[-1][len("RESULTADO="):]), res.stdout + res.stderr


def _sub(chamada):
    return [c for c in chamada if c in ("ambiente", "init", "export-dispatch")]


def test_sem_ambiente_registrado_a_etapa_2_para_e_lista_os_tres_caminhos(tmp_path):
    resultado, saida = _rodar(tmp_path / "p")
    assert resultado["ok"] is False
    assert resultado["chamadas"] == []
    assert "MCP" in saida and "MOBBIN_API_KEY" in saida and "nenhum" in saida.lower()


def test_com_mobbin_escolhido_registra_o_ambiente_antes_do_init(tmp_path):
    resultado, _ = _rodar(tmp_path / "p", mobbin="3")
    assert resultado["ok"] is True
    ordem = [_sub(c)[0] for c in resultado["chamadas"] if _sub(c)]
    assert ordem[:2] == ["ambiente", "init"]
    chamada_ambiente = next(c for c in resultado["chamadas"] if "ambiente" in c)
    assert "--mobbin" in chamada_ambiente and chamada_ambiente[chamada_ambiente.index("--mobbin") + 1] == "3"


def test_ambiente_ja_registrado_dispensa_a_escolha(tmp_path):
    pasta = tmp_path / "p"
    (pasta / ".aidd").mkdir(parents=True)
    (pasta / ".aidd" / "ambiente.json").write_text('{"mobbin": {"caminho": "nenhum"}}', encoding="utf-8")
    resultado, _ = _rodar(pasta)
    assert resultado["ok"] is True
    assert not any("ambiente" in c for c in resultado["chamadas"])
    assert any("init" in c for c in resultado["chamadas"])
