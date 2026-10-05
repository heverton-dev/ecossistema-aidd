import subprocess
import sys
import pytest

def test_cli_modularizacao_vsa_subcommands():
    from scripts.cli_modularizacao_vsa import main as cli_main

    assert callable(cli_main)
    assert cli_main(["--help"]) == 0
    assert cli_main(["status"]) == 0
    assert cli_main(["inspect"]) == 0
    assert cli_main(["verify"]) == 0
    assert cli_main(["invalid_cmd"]) != 0

def test_ecossistema_modularizacao_vsa_dispatch():
    res = subprocess.run(
        [sys.executable, "ecossistema.py", "modularizacao-vsa", "--help"],
        capture_output=True,
        text=True
    )
    assert res.returncode == 0
    assert "modularizacao-vsa" in res.stdout or "inspect" in res.stdout
