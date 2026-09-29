import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_g_nove_camadas_passa_no_template_canonico():
    """Valida que o template canônico atinge 100% de aprovação nas 9 camadas (exit 0)."""
    cmd = [
        sys.executable,
        "gates/G_NOVE_CAMADAS_MERCADO.py",
        "--target",
        "componentes/compartilhado/templates/frontend-tanstack"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 0, f"Deveria passar com exit 0, mas retornou {res.returncode}:\n{res.stdout}"
    assert "O projeto cumpre integralmente as 9 Camadas Arquiteturais de Mercado!" in res.stdout


def test_g_nove_camadas_morde_se_houver_lockin(tmp_path):
    """Lei #13: Prova que o portão morde (exit 1) se houver pacote de lock-in."""
    origem = Path("componentes/compartilhado/templates/frontend-tanstack")
    clone = tmp_path / "app-com-lockin"
    shutil.copytree(origem, clone)

    pkg = clone / "package.json"
    dados = pkg.read_text(encoding="utf-8")
    pkg.write_text(dados.replace('"dependencies": {', '"dependencies": {\n    "@lovable.dev/cloud-auth-js": "1.0",'), encoding="utf-8")

    cmd = [sys.executable, "gates/G_NOVE_CAMADAS_MERCADO.py", "--target", str(clone)]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 1, f"Deveria reprovar com exit 1 por lock-in, retornou {res.returncode}"
    assert "Violação da Lei #6 — detectado pacote proprietário '@lovable.dev'" in res.stdout


def test_g_nove_camadas_morde_se_remover_hmac(tmp_path):
    """Lei #13: Prova que o portão morde (exit 1) se a assinatura HMAC for removida."""
    origem = Path("componentes/compartilhado/templates/frontend-tanstack")
    clone = tmp_path / "app-sem-hmac"
    shutil.copytree(origem, clone)

    seg = clone / "src" / "lib" / "seguranca.ts"
    seg.write_text("// modulo vazio sem hmac\nexport const ok = true;\n", encoding="utf-8")

    cmd = [sys.executable, "gates/G_NOVE_CAMADAS_MERCADO.py", "--target", str(clone)]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    assert res.returncode == 1, f"Deveria reprovar com exit 1 por falta de HMAC, retornou {res.returncode}"
    assert "Assinatura criptográfica HMAC SHA-256 para integridade offline ausente" in res.stdout
