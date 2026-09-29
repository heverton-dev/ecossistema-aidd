import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_g_template_tanstack_offline_passa_no_template_real():
    """Valida que o template canônico em componentes/compartilhado passa com exit 0."""
    cmd = [
        sys.executable,
        "gates/G_TEMPLATE_TANSTACK_OFFLINE.py",
        "componentes/compartilhado/templates/frontend-tanstack"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0, f"Deveria passar com exit 0, mas retornou {res.returncode}: {res.stdout}\n{res.stderr}"
    assert "EXIT 0" in res.stdout


def test_g_template_tanstack_offline_morde_se_houver_lockin(tmp_path):
    """Lei #13: Prova que o portão morde (exit 1) se houver dependência com lock-in."""
    origem = Path("componentes/compartilhado/templates/frontend-tanstack")
    destino = tmp_path / "template-corrompido"
    shutil.copytree(origem, destino)

    pkg = destino / "package.json"
    conteudo = pkg.read_text(encoding="utf-8")
    pkg.write_text(conteudo.replace('"@tanstack/react-router":', '"@lovable.dev/cloud-auth-js": "1.0",\n    "@tanstack/react-router":'), encoding="utf-8")

    cmd = [sys.executable, "gates/G_TEMPLATE_TANSTACK_OFFLINE.py", str(destino)]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 1, f"Deveria falhar com exit 1 por lock-in, mas retornou {res.returncode}"
    assert "Violação da Lei #6: detectada dependência com '@lovable.dev'" in res.stdout


def test_g_template_tanstack_offline_morde_se_faltar_quarteto(tmp_path):
    """Lei #13: Prova que o portão morde (exit 1) se o AdminShell não integrar o Quarteto."""
    origem = Path("componentes/compartilhado/templates/frontend-tanstack")
    destino = tmp_path / "template-sem-quarteto"
    shutil.copytree(origem, destino)

    shell = destino / "src" / "components" / "AdminShell.tsx"
    conteudo = shell.read_text(encoding="utf-8")
    shell.write_text(conteudo.replace('to="/webhook"', 'to="/outro"'), encoding="utf-8")

    cmd = [sys.executable, "gates/G_TEMPLATE_TANSTACK_OFFLINE.py", str(destino)]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 1, f"Deveria falhar com exit 1 por falta de rota do Quarteto, mas retornou {res.returncode}"
    assert "AdminShell não possui link de navegação para '/webhook'" in res.stdout
