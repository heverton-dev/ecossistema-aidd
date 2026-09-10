# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops MVP — Item 10: Teste de Integração Helm
=============================================================================
Executa helm lint e helm template sobre o chart gerado pelo aidd-ops
(tools/aidd-ops/charts/aidd-ops/) e valida que os resources calculados
pelo sizing REAL (Fase 3 — scripts/phases/03_sizing.py) são injetados sem
erro nos manifests Kubernetes renderizados.

Design:
  - Subprocess REAL do binário helm (nada de mock/stub — validação binária).
  - Fonte de verdade dos resources: data/requisitos_recursos.json consumido
    por dimensionar() — o mesmo dado que o pipeline usa para somar o VPS.
  - Skip honesto (não pass silencioso) se o binário helm não existir.
=============================================================================
"""

from __future__ import annotations

import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHART_DIR = os.path.join(TOOL_ROOT, "charts", "aidd-ops")
DATA_DIR = os.path.join(TOOL_ROOT, "data")
REQUISITOS_PATH = os.path.join(DATA_DIR, "requisitos_recursos.json")


def _encontrar_helm() -> str | None:
    """Resolve o binário helm: env HELM_BIN > PATH > caminhos comuns."""
    env = os.environ.get("HELM_BIN")
    if env and os.path.isfile(env):
        return env
    no_path = shutil.which("helm") or shutil.which("helm.exe")
    if no_path:
        return no_path
    try:
        home = Path.home()
    except Exception:
        home = Path()
    bases = [
        home / ".local" / "bin",
        Path("/usr/local/bin"),
        Path("/opt/homebrew/bin"),
        Path("C:/Program Files/Helm"),
        Path("C:/ProgramData/chocolatey/bin"),
    ]
    for base in bases:
        for nome in ("helm", "helm.exe"):
            cand = base / nome
            if cand.is_file():
                return str(cand)
    return None


HELM_BIN = _encontrar_helm()


def _carregar_requisitos() -> dict:
    with open(REQUISITOS_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _carregar_sizing() -> dict:
    """Carrega a Fase 3 real (mesmo módulo do pipeline) e dimensiona uma
    stack real. Usa o catálogo de requisitos para evitar depender de um
    nicho específico; o contrato é: para cada ferramenta cadastrada, os
    resources do chart devem refletir os requisitos reais."""
    sys.path.insert(0, os.path.join(TOOL_ROOT, "scripts", "phases"))
    sizing = importlib.import_module("03_sizing")
    requisitos = _carregar_requisitos()
    ferramentas = [{"nome": nome} for nome in requisitos["ferramentas"]]
    resultado = sizing.dimensionar(ferramentas)
    assert resultado.sucesso is True
    return resultado.valor


def _slug_ferramenta(nome: str) -> str:
    return nome.lower().replace(" ", "_").replace(".", "")


def _memory_k8s(ram_gb: float, fator: float = 1.0) -> str:
    """ram_gb (Gi) -> memória k8s em Mi, com fator de escala."""
    return f"{int(round(ram_gb * 1024 * fator))}Mi"


def _cpu_k8s(vcpu: float, fator: float = 1.0) -> str:
    """vcpu -> cpu k8s em cores (string), com fator de escala."""
    return f"{vcpu * fator:g}"


def _construir_values_do_sizing(sizing_valor: dict) -> dict:
    """Mapeia o sizing real numa estrutura de values.yaml do chart.

    Cada ferramenta cadastrada em requisitos_recursos.json vira um serviço
    em services.apps.<slug>, com requests/limits derivados dos MESMOS
    números (vcpu/ram_gb/disco_gb) que a Fase 3 soma para o VPS.
    O postgres (banco centralizado) recebe o disco do sizing total.
    """
    requisitos = _carregar_requisitos()["ferramentas"]
    apps: dict = {}
    for nome, req in requisitos.items():
        vcpu = float(req["vcpu"])
        ram = float(req["ram_gb"])
        apps[_slug_ferramenta(nome)] = {
            "enabled": True,
            "image": {"repository": f"example/{_slug_ferramenta(nome)}", "tag": "latest"},
            "replicas": 1,
            "ports": {"http": 3000 + len(apps)},
            "resources": {
                "requests": {"cpu": _cpu_k8s(vcpu), "memory": _memory_k8s(ram)},
                "limits": {"cpu": _cpu_k8s(vcpu, 2), "memory": _memory_k8s(ram, 2)},
            },
        }
    disco = int(sizing_valor["vps"]["disco_gb"])
    return {
        "global": {"namespace": "aidd-ops-test"},
        "services": {
            "postgres": {
                "resources": {
                    "requests": {"cpu": "0.5", "memory": "512Mi"},
                    "limits": {"cpu": "2", "memory": "2Gi"},
                },
                "persistence": {"enabled": True, "size": f"{disco}Gi"},
            },
            "apps": apps,
        },
    }


def _rodar_helm(helm_abs: str, args: list, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        [helm_abs] + args,
        capture_output=True,
        text=True,
        cwd=TOOL_ROOT,
        timeout=timeout,
    )


def _renderizar_manifests(helm_abs: str, values_path: str | None = None) -> list[dict]:
    """Roda helm template e devolve os documentos YAML renderizados."""
    cmd = ["template", "test-release", CHART_DIR]
    if values_path:
        cmd += ["-f", values_path]
    proc = _rodar_helm(helm_abs, cmd)
    assert proc.returncode == 0, (
        f"helm template falhou (exit {proc.returncode}).\n"
        f"STDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    )
    documentos = [d for d in yaml.safe_load_all(proc.stdout) if d]
    assert documentos, "helm template nao produziu nenhum documento."
    return documentos


@pytest.fixture(scope="module")
def helm_bin():
    if HELM_BIN is None:
        pytest.skip(
            "Binario helm nao encontrado. Instale via https://helm.sh/docs/intro/install/ "
            "ou aponte a variavel HELM_BIN para o executavel."
        )
    return HELM_BIN


# ── 1. helm lint sobre o chart gerado ──

def test_helm_lint_chart_aprovado(helm_bin):
    """helm lint deve terminar com exit 0 (apenas INFO/WARNINGS permitidos)."""
    proc = _rodar_helm(helm_bin, ["lint", CHART_DIR])
    assert proc.returncode == 0, (
        f"helm lint reprovou (exit {proc.returncode}).\n"
        f"STDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    )
    assert "0 chart(s) failed" in proc.stdout


# ── 2. helm template com values padrão (infra) ──

def test_helm_template_valores_padrao(helm_bin):
    """Com os values padrao, os objetos de infra (postgres/traefik) devem
    renderizar como objetos Kubernetes validos."""
    documentos = _renderizar_manifests(helm_bin)

    kinds = {(d.get("kind"), d.get("metadata", {}).get("name")) for d in documentos}
    assert ("Namespace", "aidd-ops") in kinds
    assert ("Deployment", "postgres") in kinds
    assert ("Deployment", "traefik") in kinds
    assert ("Service", "postgres") in kinds
    assert ("Service", "traefik") in kinds
    assert ("PersistentVolumeClaim", "postgres-pvc") in kinds
    assert ("PersistentVolumeClaim", "traefik-pvc") in kinds

    # Resources padrao dos deployments devem existir (nao vazios)
    for doc in documentos:
        if doc.get("kind") == "Deployment":
            c = doc["spec"]["template"]["spec"]["containers"][0]
            assert "resources" in c, f"Deployment {doc['metadata']['name']} sem resources"


# ── 3. Resources do SIZING REAL injetados sem erro ──

def test_sizing_resources_injetados_sem_erro(helm_bin, tmp_path):
    """Sizing real (dimensionar) -> values.yaml -> helm template: a renderizacao
    deve passar (exit 0) e cada Deployment deve conter EXATAMENTE os resources
    calculados para a ferramenta."""
    sizing_valor = _carregar_sizing()
    values = _construir_values_do_sizing(sizing_valor)

    values_path = os.path.join(str(tmp_path), "values_sizing.yaml")
    with open(values_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(values, f)

    documentos = _renderizar_manifests(helm_bin, values_path)

    # Banco central: storage do PVC deve refletir o disco total calculado
    disco_esperado = f'{int(sizing_valor["vps"]["disco_gb"])}Gi'
    pvcs = [d for d in documentos if d.get("kind") == "PersistentVolumeClaim"]
    postgres_pvc = next(d for d in pvcs if d["metadata"]["name"] == "postgres-pvc")
    assert postgres_pvc["spec"]["resources"]["requests"]["storage"] == disco_esperado

    # Cada ferramenta cadastrada vira um Deployment com os resources exatos
    deployments = {d["metadata"]["name"]: d for d in documentos if d.get("kind") == "Deployment"}
    requisitos = _carregar_requisitos()["ferramentas"]
    for nome, req in requisitos.items():
        slug = _slug_ferramenta(nome)
        assert slug in deployments, f"Deployment {slug} ausente no render"
        container = deployments[slug]["spec"]["template"]["spec"]["containers"][0]
        resources = container["resources"]
        vcpu = float(req["vcpu"])
        ram = float(req["ram_gb"])
        assert resources["requests"]["cpu"] == _cpu_k8s(vcpu)
        assert resources["requests"]["memory"] == _memory_k8s(ram)
        assert resources["limits"]["cpu"] == _cpu_k8s(vcpu, 2)
        assert resources["limits"]["memory"] == _memory_k8s(ram, 2)


# ── 4. Contrato: valores renderizados == values injetados ──

def test_contrato_values_renderizados(helm_bin, tmp_path):
    """O que entra no values.yaml deve sair byte-a-byte equivalente no YAML do
    template — sem transformacao que mude valores de CPU/memoria."""
    values = {
        "global": {"namespace": "aidd-ops-test"},
        "services": {
            "postgres": {
                "resources": {
                    "requests": {"cpu": "1", "memory": "1Gi"},
                    "limits": {"cpu": "2", "memory": "2Gi"},
                }
            },
            "apps": {
                "app_fixture": {
                    "enabled": True,
                    "image": {"repository": "example/app_fixture", "tag": "latest"},
                    "ports": {"http": 3000},
                    "resources": {
                        "requests": {"cpu": "0.5", "memory": "512Mi"},
                        "limits": {"cpu": "1", "memory": "1Gi"},
                    },
                }
            },
        },
    }
    values_path = os.path.join(str(tmp_path), "values_contrato.yaml")
    with open(values_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(values, f)

    documentos = _renderizar_manifests(helm_bin, values_path)

    deployments = {d["metadata"]["name"]: d for d in documentos if d.get("kind") == "Deployment"}
    for nome_servico, esperado in [
        ("postgres", values["services"]["postgres"]["resources"]),
        ("app_fixture", values["services"]["apps"]["app_fixture"]["resources"]),
    ]:
        container = deployments[nome_servico]["spec"]["template"]["spec"]["containers"][0]
        assert container["resources"] == esperado