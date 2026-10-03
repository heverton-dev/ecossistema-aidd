# -*- coding: utf-8 -*-
"""
Teste de Fronteira da aidd-freedom (Ticket 14, D1 / DoD).

Regras provadas aqui (ESPEC-CONTRATOS-E-GATE.md, Regra 4 + zona de escrita):
1. `bridge scan` NUNCA escreve dentro do export do usuário (o export é um
   repo git de terceiro -- qualquer arquivo novo lá é vazamento confirmado
   pelo E2E em `origem`).
2. O manifesto vai para `PROJETO/.aidd/bridge-manifest.json`.
3. A fatia convertida vai para `PROJETO/src/modules/<dominio>/` e o
   contrato C3 (`HANDOFF_ENGINE_MASTER.json`) é gravado pela própria
   ferramenta, dentro da pasta do projeto, aderente ao schema formal.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import jsonschema
import pytest

ROOT_DIR = Path(__file__).resolve().parents[3]
FREEDOM_DIR = ROOT_DIR / "tools" / "aidd-freedom"
SPECS_DIR = ROOT_DIR / "componentes" / "compartilhado" / "specs"

if str(FREEDOM_DIR) not in sys.path:
    sys.path.insert(0, str(FREEDOM_DIR))

import aidd_freedom.cli as cli_module  # noqa: E402


def _criar_export_git(tmp_path: Path) -> Path:
    """Export low-code mínimo versionado em git (o 'usuário' dono do repo)."""
    export = tmp_path / "export"
    paginas = export / "src" / "pages"
    paginas.mkdir(parents=True)
    (paginas / "Index.tsx").write_text(
        "export default function Index() { return <div>Home</div>; }\n",
        encoding="utf-8",
    )
    app = export / "src" / "App.tsx"
    app.write_text(
        'import { Route, Routes } from "react-router-dom";\n'
        "export default function App() {\n"
        "  return (\n"
        "    <Routes>\n"
        '      <Route path="/" element={<Index />} />\n'
        '      <Route path="/tarefas" element={<Tarefas />} />\n'
        "    </Routes>\n"
        "  );\n"
        "}\n",
        encoding="utf-8",
    )
    (export / "package.json").write_text(
        '{"name": "mock-lovable", "dependencies": {"react": "^18.0.0"}}\n',
        encoding="utf-8",
    )
    mig = export / "supabase" / "migrations"
    mig.mkdir(parents=True)
    (mig / "0001_init.sql").write_text(
        "CREATE TABLE public.tarefas (id uuid PRIMARY KEY);\n",
        encoding="utf-8",
    )

    def _git(*args: str) -> None:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(export),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.returncode == 0, f"git {' '.join(args)} falhou: {proc.stderr}"

    _git("init")
    _git("add", "-A")
    _git(
        "-c", "user.name=fronteira-test", "-c", "user.email=fronteira@test",
        "commit", "-m", "export inicial",
    )
    return export


def _rodar_scan(export: Path, projeto: Path) -> int:
    args = SimpleNamespace(project_dir=str(export), output=str(projeto))
    return cli_module.cmd_scan(args)


def _git_status(export: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(export), "status", "--porcelain"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.strip()


def test_scan_grava_manifesto_no_projeto_e_export_fica_limpo(tmp_path: Path):
    """V10: scan não pode sujar o export do usuário; manifesto fica no projeto."""
    export = _criar_export_git(tmp_path)
    projeto = tmp_path / "projeto"
    projeto.mkdir()

    rc = _rodar_scan(export, projeto)

    assert rc == 0, "bridge scan deve terminar com exit 0"
    assert _git_status(export) == "", (
        "scan escreveu dentro do export do usuário (git status sujo): "
        f"{_git_status(export)}"
    )
    manifesto = projeto / ".aidd" / "bridge-manifest.json"
    assert manifesto.is_file(), "manifesto deve ficar em PROJETO/.aidd/bridge-manifest.json"
    dados = json.loads(manifesto.read_text(encoding="utf-8"))
    assert dados["package_info"]["name"] == "mock-lovable"
    assert not (export / "bridge-manifest.json").exists(), (
        "bridge-manifest.json não pode ser gravado no export"
    )


def test_scan_grava_fatia_convertida_e_c3_na_zona_do_projeto(tmp_path: Path):
    """Zona do construtor: src/modules/<dominio>/** + HANDOFF_ENGINE_MASTER.json."""
    export = _criar_export_git(tmp_path)
    projeto = tmp_path / "projeto"
    projeto.mkdir()

    rc = _rodar_scan(export, projeto)

    assert rc == 0
    dominio = "mock-lovable"  # slug do package name do export
    fatia = projeto / "src" / "modules" / dominio
    assert fatia.is_dir(), f"fatia convertida ausente: src/modules/{dominio}/"
    assert (fatia / "__init__.py").is_file()
    assert (fatia / "schema.sql").is_file(), "schema.sql convertido (DataBridge) ausente"

    c3_path = projeto / "HANDOFF_ENGINE_MASTER.json"
    assert c3_path.is_file(), "C3 (HANDOFF_ENGINE_MASTER.json) deve ser gravado pela ferramenta"

    schema = json.loads(
        (SPECS_DIR / "handoff-engine-to-master.schema.json").read_text(encoding="utf-8")
    )
    c3 = json.loads(c3_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=c3, schema=schema)  # levanta ValidationError

    assert c3["origem_engine"] == "aidd-freedom"
    assert c3["arquivos_fora_da_zona"] == []
    assert c3["slices_geradas"], "C3 precisa listar ao menos uma fatia"
    for slice_info in c3["slices_geradas"]:
        assert slice_info["caminho_src"].startswith("src/modules/")
        assert re.fullmatch(r"[0-9a-f]{64}", slice_info["sha256_arvore"])
        caminho = projeto / slice_info["caminho_src"]
        assert caminho.is_dir(), f"caminho_src do C3 não existe: {slice_info['caminho_src']}"

    # Evidência real de testes (Lei 8): relatório junit existe e bate com o C3
    relatorio = projeto / c3["testes_executados"]["relatorio_pytest"]["caminho"]
    assert relatorio.is_file(), "relatorio_pytest apontado no C3 deve existir"
    assert c3["testes_executados"]["relatorio_pytest"]["exit_code"] == 0
    assert c3["testes_executados"]["falharam"] == 0
    assert c3["testes_executados"]["passaram"] >= 1


def test_scan_nao_escrive_fora_da_zona_do_projeto(tmp_path: Path):
    """Nada fora da zona do construtor (.aidd/, src/modules/, C3)."""
    export = _criar_export_git(tmp_path)
    projeto = tmp_path / "projeto"
    projeto.mkdir()

    assert _rodar_scan(export, projeto) == 0

    permitido = re.compile(
        r"^(\.aidd/(bridge-manifest\.json|cache/.+)|src/modules/[^/]+/.+|"
        r"HANDOFF_ENGINE_MASTER\.json)$"
    )
    for caminho in sorted(projeto.rglob("*")):
        if not caminho.is_file():
            continue
        rel = caminho.relative_to(projeto).as_posix()
        assert permitido.match(rel), f"arquivo fora da zona do construtor: {rel}"
