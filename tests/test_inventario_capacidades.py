import json
import os
from pathlib import Path
from subprocess import CalledProcessError, run


def _run(cmd, cwd=None, check=True):
    result = run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise CalledProcessError(
            result.returncode, cmd, output=result.stdout, stderr=result.stderr
        )
    return result


def test_foto_and_comparar_detects_orphan(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "mod_a.py").write_text("def foo():\n    return 1\n\n")
    copy = repo / "mod_a_copy.py"
    copy.write_text("def foo():\n    return 1\n\n\ndef extra():\n    pass\n")

    cycle = repo / "docs" / "auditoria" / "fronteiras-ferramentas" / "ciclo-01"
    cycle.mkdir(parents=True, exist_ok=True)

    script = Path(__file__).resolve().parents[1] / "scripts" / "inventario_capacidades.py"

    _run("git init && git add . && git config user.name test && git config user.email test@test.com && git commit -m init", cwd=repo)

    result = _run(f"python {script} foto --repo {repo} --cycle docs/auditoria/fronteiras-ferramentas/ciclo-01", cwd=repo, check=False)
    assert result.returncode == 0

    antes = cycle / "INVENTARIO-ANTES.json"
    assert antes.exists()

    copy.unlink()
    try:
        _run("git rm mod_a_copy.py", cwd=repo, check=True)
    except Exception:
        pass

    comp = _run(f"python {script} comparar --repo {repo} --cycle docs/auditoria/fronteiras-ferramentas/ciclo-01", cwd=repo, check=False)
    assert comp.returncode == 1
