import subprocess
import sys

def test_ecossistema_quadro_help():
    res = subprocess.run(
        [sys.executable, "ecossistema.py", "quadro", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    assert res.returncode == 0
    assert "Quadro Kanban de Pipelines AIDD" in res.stdout

def test_ecossistema_kanban_apelido_help():
    res = subprocess.run(
        [sys.executable, "ecossistema.py", "kanban", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )
    assert res.returncode == 0
    assert "Quadro Kanban de Pipelines AIDD" in res.stdout
