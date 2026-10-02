# -*- coding: utf-8 -*-
"""Ticket 18 (D1 / DoD 7): aidd-enterprise só blindagem.

Fronteiras validadas:
1. Os caminhos de código do enterprise (CLI `scripts/aidd.py` e os Use Cases
   em `application/`) não importam `compose_suite`, `provision_project`,
   `scaffold_infra`, `openapi_to_ts`, `scripts/add_module` nem
   `subagent_engine`, e não leem `templates/core` / `templates/v2` nem
   arquivos de infra (Dockerfile, docker-compose, deploy.sh, nginx). As
   cópias antigas ficam no disco até o Ticket 19 (remoção com o usuário).
2. Os comandos de construção (compose, compose-orca, plan, apply, prompt,
   heal, init, add-module, bench, export-frontend, scaffold-infra, deploy)
   são delegados à CLI do dono (aidd-master), com os mesmos argumentos.
3. O injetor é carregado da peça do almoxarifado (`injetor/inject.py`, com
   `injetor/profiles_registry.py` e `injetor/detector_camada.py`), com o selo
   SHA-256 do catálogo conferido antes de executar a peça.
4. `G_DRIFT_NUCLEO_COMPARTILHADO` compara cada cópia do CATALOGO.json com a
   versão do catálogo (sem largar os pares master × enterprise) e aplica a
   D4: `materiais-extras/examples` é arquivo histórico, nunca comparado.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[3]
ENTERPRISE_DIR = ROOT_DIR / "tools" / "aidd-enterprise"
MASTER_CLI = ROOT_DIR / "tools" / "aidd-master" / "scripts" / "aidd.py"
FORGE_DIR = ROOT_DIR / "tools" / "aidd-forge"
GATE_DRIFT = ROOT_DIR / "gates" / "G_DRIFT_NUCLEO_COMPARTILHADO.py"
CATALOGO_PATH = ROOT_DIR / "componentes" / "compartilhado" / "CATALOGO.json"

for _p in (str(ENTERPRISE_DIR), str(ENTERPRISE_DIR / "scripts"), str(FORGE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from aidd_forge.core.almoxarifado import caminho_peca  # noqa: E402

MODULOS_PROIBIDOS = {
    "compose_suite",
    "provision_project",
    "scaffold_infra",
    "openapi_to_ts",
    "subagent_engine",
    "scripts.add_module",
}
TEXTOS_PROIBIDOS = ("templates/core", "templates/v2", "Dockerfile", "docker-compose", "deploy.sh", "nginx")
PASTAS_TEMPLATE_PROIBIDAS = {"core", "v2"}


def _caminhos_de_codigo() -> list[Path]:
    arquivos = [ENTERPRISE_DIR / "scripts" / "aidd.py"]
    arquivos += sorted((ENTERPRISE_DIR / "application").rglob("*.py"))
    # application/commands/inject.py é a cópia antiga do injetor (catálogo: copias
    # de injetor/inject.py); fica no disco até o Ticket 19 e não é mais importada.
    return [a for a in arquivos if a != ENTERPRISE_DIR / "application" / "commands" / "inject.py"]


def _violacoes_estaticas(caminho: Path) -> list[str]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    try:
        rel = caminho.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        rel = caminho.name
    achados = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            nomes = [a.name for a in no.names]
        elif isinstance(no, ast.ImportFrom):
            nomes = [no.module or ""]
        else:
            nomes = []
        for nome in nomes:
            # application.commands.<x> são os Use Cases do próprio enterprise (ex.: o
            # scaffold_infra que delega ao dono), não as cópias de scripts/.
            proprio = nome.startswith("application.")
            if nome in MODULOS_PROIBIDOS or (not proprio and nome.split(".")[-1] in MODULOS_PROIBIDOS):
                achados.append(f"{rel}:{no.lineno} importa {nome}")
            if isinstance(no, ast.ImportFrom) and no.module == "add_module":
                achados.append(f"{rel}:{no.lineno} importa scripts/add_module (cópia do master)")
        if isinstance(no, ast.Constant) and isinstance(no.value, str):
            for texto in TEXTOS_PROIBIDOS:
                if texto in no.value:
                    achados.append(f"{rel}:{no.lineno} cita {texto!r}")
        if isinstance(no, ast.Call) and getattr(no.func, "attr", "") == "join":
            valores = [a.value for a in no.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            for i, valor in enumerate(valores[:-1]):
                if valor == "templates" and valores[i + 1] in PASTAS_TEMPLATE_PROIBIDAS:
                    achados.append(f"{rel}:{no.lineno} lê templates/{valores[i + 1]}")
    return achados


# =============================================================================
# 1. Caminhos de código sem infra, compose_suite e moldes do Quarteto
# =============================================================================

def test_caminhos_de_codigo_do_enterprise_nao_usam_infra_compose_nem_quarteto():
    achados = []
    for arquivo in _caminhos_de_codigo():
        achados.extend(_violacoes_estaticas(arquivo))
    assert achados == [], "Fronteira D1 violada no enterprise:\n" + "\n".join(achados)


def test_analise_estatica_acusa_violacao_plantada(tmp_path):
    """Prova de que a varredura reprova (não é um teste que sempre passa)."""
    plantado = tmp_path / "plantado.py"
    plantado.write_text(
        "import os\nfrom compose_suite import compose_suite\n"
        "x = os.path.join('a', 'templates', 'v2')\nY = 'docker-compose.yml'\n",
        encoding="utf-8",
    )
    achados = _violacoes_estaticas(plantado)
    assert any("compose_suite" in a for a in achados), achados
    assert any("templates/v2" in a for a in achados), achados
    assert any("docker-compose" in a for a in achados), achados


# =============================================================================
# 2. Comandos de construção delegados ao dono (aidd-master)
# =============================================================================

def _ns(**kw):
    return argparse.Namespace(**kw)


CASOS_DELEGACAO = [
    ("compose", "cmd_compose",
     lambda d: _ns(target_dir=d, suite_name="Suite T18", modulos=("crm", "erp"), db="postgres"),
     lambda d: ["compose", d, "Suite T18", "crm", "erp", "--db", "postgres"]),
    ("compose-orca", "cmd_compose_orca",
     lambda d: _ns(dir=d, suite_name="Suite T18", modulos=("crm",)),
     lambda d: ["compose-orca", "--dir", d, "--suite-name", "Suite T18", "crm"]),
    ("apply", "cmd_apply", lambda d: _ns(dir=d), lambda d: ["apply", "--dir", d]),
    ("heal", "cmd_heal", lambda d: _ns(dir=d), lambda d: ["heal", "--dir", d]),
    ("init", "cmd_init", lambda d: _ns(nome="app-t18", dir=d), lambda d: ["init", "app-t18", "--dir", d]),
    ("add-module", "cmd_add_module",
     lambda d: _ns(nome="pedidos", descricao="Pedidos", dir=d),
     lambda d: ["add-module", "pedidos", "--descricao", "Pedidos", "--dir", d]),
    ("bench", "cmd_bench", lambda d: _ns(n=7, dir=d), lambda d: ["bench", "-n", "7", "--dir", d]),
    ("export-frontend", "cmd_export_frontend",
     lambda d: _ns(stack="nextjs", dir=d), lambda d: ["export-frontend", "--stack", "nextjs", "--dir", d]),
    ("scaffold-infra", "cmd_scaffold_infra", lambda d: _ns(dir=d), lambda d: ["scaffold-infra", "--dir", d]),
    ("deploy", "cmd_deploy", lambda d: _ns(alvo="vps"), lambda d: ["deploy", "vps"]),
]


class _PopenFalso:
    """Substitui o subprocess.Popen da delegação: registra o comando e devolve `codigo`."""

    chamadas: list = []
    codigo = 0

    def __init__(self, cmd, **kwargs):
        type(self).chamadas.append({"cmd": [str(c) for c in cmd], "kwargs": kwargs})
        self.stdout = _SaidaFalsa([f"saida do dono: {cmd[2]}\n"])

    def wait(self):
        return type(self).codigo


class _SaidaFalsa(list):
    def close(self):
        pass


def _instalar_popen_falso(monkeypatch, codigo=0):
    delegacao = importlib.import_module("application.commands.delegacao")
    falso = type("PopenFalso", (_PopenFalso,), {"chamadas": [], "codigo": codigo})
    monkeypatch.setattr(delegacao.subprocess, "Popen", falso)
    return falso


@pytest.fixture
def chamadas_delegadas(monkeypatch):
    return _instalar_popen_falso(monkeypatch).chamadas


@pytest.mark.parametrize("comando,funcao,args,esperado", CASOS_DELEGACAO, ids=[c[0] for c in CASOS_DELEGACAO])
def test_comando_de_construcao_e_delegado_ao_master(chamadas_delegadas, tmp_path, capsys, comando, funcao, args, esperado):
    commands = importlib.import_module("application.commands")
    alvo = str(tmp_path / "projeto")
    modulos_antes = set(sys.modules)
    getattr(commands, funcao)(args(alvo))

    assert len(chamadas_delegadas) == 1, chamadas_delegadas
    cmd = chamadas_delegadas[0]["cmd"]
    assert Path(cmd[1]).resolve() == MASTER_CLI.resolve()
    assert cmd[2:] == esperado(alvo)
    novos = set(sys.modules) - modulos_antes
    assert not {m for m in novos if m.split(".")[-1] in MODULOS_PROIBIDOS}, novos
    saida = capsys.readouterr().out
    assert f"[DELEGADO] aidd-enterprise -> aidd-master: {comando}" in saida
    assert f"saida do dono: {comando}" in saida


def test_plan_delegado_preserva_injecao_por_linguagem_natural_local(chamadas_delegadas, tmp_path):
    commands = importlib.import_module("application.commands")
    commands.cmd_plan("crie um crm", base_dir=str(tmp_path), auto_apply=True)
    assert [c["cmd"][2:] for c in chamadas_delegadas] == [["plan", "crie um crm", "--dir", str(tmp_path), "--apply"]]


def test_delegacao_propaga_exit_code_do_dono(monkeypatch, tmp_path):
    _instalar_popen_falso(monkeypatch, codigo=3)
    commands = importlib.import_module("application.commands")
    with pytest.raises(SystemExit) as exc:
        commands.cmd_heal(_ns(dir=str(tmp_path)))
    assert exc.value.code == 3


def test_cli_real_init_delega_e_nao_gera_infra(tmp_path):
    destino = tmp_path / "app-real"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(ENTERPRISE_DIR / "scripts" / "aidd.py"), "init", "app-real", "--dir", str(destino)],
        cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "[DELEGADO] aidd-enterprise -> aidd-master: init" in proc.stdout
    assert (destino / "src").is_dir(), proc.stdout
    for proibido in ("Dockerfile", "docker-compose.yml", "deploy.sh", "nginx"):
        assert not (destino / proibido).exists(), f"enterprise init gerou infra: {proibido}"


# =============================================================================
# 3. Injetor carregado da peça do almoxarifado, com selo SHA-256
# =============================================================================

def test_injetor_vem_da_peca_do_almoxarifado():
    pecas = importlib.import_module("application.pecas_catalogo")
    injetor = pecas.carregar_injetor()

    peca_inject = caminho_peca("injetor/inject.py").resolve()
    assert Path(injetor.cmd_inject.__code__.co_filename).resolve() == peca_inject
    assert Path(injetor.run_inject.__code__.co_filename).resolve() == peca_inject
    for modulo, peca in (("detector_camada", "injetor/detector_camada.py"),
                         ("profiles_registry", "injetor/profiles_registry.py")):
        origem = Path(sys.modules[modulo].__spec__.origin).resolve()
        assert origem == caminho_peca(peca).resolve(), f"{modulo} veio de {origem}"

    commands = importlib.import_module("application.commands")
    assert commands.cmd_inject is injetor.cmd_inject
    assert commands.run_inject is injetor.run_inject
    aidd = importlib.import_module("aidd")
    assert aidd._tentar_injecao_por_linguagem_natural is injetor._tentar_injecao_por_linguagem_natural


def test_injetor_da_peca_ancora_no_enterprise():
    pecas = importlib.import_module("application.pecas_catalogo")
    injetor = pecas.carregar_injetor()
    assert injetor._projeto_padrao() == "aidd-enterprise"
    assert Path(injetor._core_src_path()).resolve() == (ENTERPRISE_DIR / "src" / "core").resolve()


def _raiz_fake_com_peca(tmp_path: Path, conteudo: bytes, sha_catalogo: str) -> Path:
    raiz = tmp_path / "raiz"
    (raiz / "componentes" / "compartilhado" / "injetor").mkdir(parents=True)
    (raiz / "componentes" / "compartilhado" / "injetor" / "inject.py").write_bytes(conteudo)
    (raiz / "componentes" / "compartilhado" / "CATALOGO.json").write_text(json.dumps({"pecas": [{
        "nome": "injetor/inject.py",
        "caminho": "componentes/compartilhado/injetor/inject.py",
        "sha256": f"sha256-{sha_catalogo}",
        "copias": [],
    }]}), encoding="utf-8")
    return raiz


def test_selo_sha256_recusa_peca_adulterada(tmp_path):
    pecas = importlib.import_module("application.pecas_catalogo")
    original = b"VALOR = 1\n"
    raiz = _raiz_fake_com_peca(tmp_path, b"VALOR = 2  # adulterada\n", hashlib.sha256(original).hexdigest())
    with pytest.raises(pecas.ErroSeloPeca) as exc:
        pecas.verificar_selo("injetor/inject.py", raiz=raiz)
    assert "injetor/inject.py" in str(exc.value)


def test_selo_sha256_aceita_peca_integra(tmp_path):
    pecas = importlib.import_module("application.pecas_catalogo")
    conteudo = b"VALOR = 1\n"
    raiz = _raiz_fake_com_peca(tmp_path, conteudo, hashlib.sha256(conteudo).hexdigest())
    caminho = pecas.verificar_selo("injetor/inject.py", raiz=raiz)
    assert caminho.read_bytes() == conteudo


def test_cli_real_inject_rule_pela_peca(tmp_path):
    projeto = tmp_path / "proj"
    projeto.mkdir()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(ENTERPRISE_DIR / "scripts" / "aidd.py"), "inject", "rule", "regra-t18", "--dir", str(projeto)],
        cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=300,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (projeto / "templates" / "rules" / "regra-t18.md").is_file()

    drift = subprocess.run(
        [sys.executable, str(ENTERPRISE_DIR / "scripts" / "aidd.py"), "verificar-drift", "--dir", str(projeto)],
        cwd=str(ROOT_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=300,
    )
    assert drift.returncode == 0, drift.stdout + drift.stderr


# =============================================================================
# 4. G_DRIFT_NUCLEO_COMPARTILHADO contra o catálogo (+ D4)
# =============================================================================

def _rodar_gate(gate: Path, cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run([sys.executable, str(gate)], cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


def _raiz_fake_drift(tmp_path: Path, copias: dict[str, bytes], peca: bytes, documentadas: dict) -> Path:
    raiz = tmp_path / "eco"
    (raiz / "gates").mkdir(parents=True)
    shutil.copy2(GATE_DRIFT, raiz / "gates" / GATE_DRIFT.name)
    caminho = "componentes/compartilhado/src-core/peca_t18.py"
    (raiz / caminho).parent.mkdir(parents=True)
    (raiz / caminho).write_bytes(peca)
    for rel, conteudo in copias.items():
        (raiz / rel).parent.mkdir(parents=True, exist_ok=True)
        (raiz / rel).write_bytes(conteudo)
    catalogo = {
        "fora_do_almoxarifado": {"tools/aidd-enterprise/materiais-extras/examples/**": "D4"},
        "pecas": [{"nome": "src-core/peca_t18.py", "caminho": caminho,
                   "sha256": "sha256-" + hashlib.sha256(peca).hexdigest(), "copias": sorted(copias)}],
    }
    (raiz / "componentes" / "compartilhado" / "CATALOGO.json").write_text(json.dumps(catalogo), encoding="utf-8")
    baseline = {"arquivos": {}, "catalogo": {"divergencias_documentadas": documentadas}}
    (raiz / "gates" / "baseline_nucleo_compartilhado.json").write_text(json.dumps(baseline), encoding="utf-8")
    return raiz


def test_gate_drift_real_compara_copias_com_o_catalogo():
    proc = _rodar_gate(GATE_DRIFT, ROOT_DIR)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    catalogo = json.loads(CATALOGO_PATH.read_text(encoding="utf-8"))
    total = sum(len(p.get("copias", [])) for p in catalogo["pecas"])
    assert f"catalogo: {total} copia(s)" in proc.stdout, proc.stdout[-3000:]
    # Os pares master x enterprise continuam cobertos (fora do catálogo, ex.: scripts/aidd.py).
    assert "scripts/aidd.py" in proc.stdout


def test_gate_drift_reprova_copia_divergente_do_catalogo(tmp_path):
    copia = "tools/aidd-master/src/core/peca_t18.py"
    raiz = _raiz_fake_drift(tmp_path, {copia: b"# editada a mao\n"}, b"# peca\n", {})
    proc = _rodar_gate(raiz / "gates" / GATE_DRIFT.name, raiz)
    assert proc.returncode == 1, proc.stdout
    assert copia in proc.stdout and "drift nao documentado" in proc.stdout


def test_gate_drift_aceita_divergencia_documentada(tmp_path):
    copia = "tools/aidd-master/src/core/peca_t18.py"
    raiz = _raiz_fake_drift(tmp_path, {copia: b"# editada\n"}, b"# peca\n",
                            {copia: "Variante local documentada para o teste."})
    proc = _rodar_gate(raiz / "gates" / GATE_DRIFT.name, raiz)
    assert proc.returncode == 0, proc.stdout


def test_gate_drift_aplica_d4_e_ignora_examples(tmp_path):
    exemplo = "tools/aidd-enterprise/materiais-extras/examples/app-antigo/src/core/peca_t18.py"
    identica = "tools/aidd-enterprise/src/core/peca_t18.py"
    raiz = _raiz_fake_drift(tmp_path, {exemplo: b"# historico\n", identica: b"# peca\n"}, b"# peca\n", {})
    proc = _rodar_gate(raiz / "gates" / GATE_DRIFT.name, raiz)
    assert proc.returncode == 0, proc.stdout
    assert "D4" in proc.stdout and exemplo in proc.stdout


def test_gate_drift_reprova_copia_ausente_do_disco(tmp_path):
    raiz = _raiz_fake_drift(tmp_path, {}, b"# peca\n", {})
    catalogo_path = raiz / "componentes" / "compartilhado" / "CATALOGO.json"
    catalogo = json.loads(catalogo_path.read_text(encoding="utf-8"))
    catalogo["pecas"][0]["copias"] = ["tools/aidd-master/src/core/sumiu.py"]
    catalogo_path.write_text(json.dumps(catalogo), encoding="utf-8")
    proc = _rodar_gate(raiz / "gates" / GATE_DRIFT.name, raiz)
    assert proc.returncode == 1, proc.stdout
    assert "sumiu.py" in proc.stdout
