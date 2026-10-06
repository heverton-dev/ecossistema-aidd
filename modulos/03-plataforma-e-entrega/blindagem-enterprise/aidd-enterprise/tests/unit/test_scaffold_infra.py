# -*- coding: utf-8 -*-
"""
Testes do scaffolding de infraestrutura declarativa (Onda 4 / v6.0-Enterprise).

Este ambiente de desenvolvimento não possui os binários `terraform`/`helm`
instalados, então os critérios de aceite literais do plano ("terraform
validate" e "helm lint aprovados") não podem ser executados de verdade aqui.
Em vez disso: (1) os arquivos Helm são validados fazendo um "fake render" —
substituindo cada expressão Go-template `{{ ... }}` por um placeholder
escalar e então parseando o resultado com PyYAML, o que valida genuinamente
a estrutura YAML subjacente sem exigir o binário `helm`; (2) o Terraform é
validado estruturalmente (blocos balanceados, blocos obrigatórios presentes).
Se terraform/helm estiverem instalados, os comandos reais devem ser
executados diretamente contra os arquivos gerados — ver docstring de
scaffold_infra().
"""

import os
import re
import sys
import shutil
import subprocess

import pytest
import yaml

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from scaffold_infra import scaffold_infra, _slugify  # noqa: E402


def _fake_render_yaml(content: str):
    """Substitui expressões Go-template {{ ... }} por um placeholder escalar
    SEM aspas próprias (para compor corretamente com linhas que já têm
    aspas externas, ex.: "{{ a }}:{{ b }}") e faz o parse do resultado como
    YAML — simula o efeito estrutural do `helm template` sem exigir o
    binário `helm`."""
    rendered = re.sub(r"\{\{-?\s*.*?\s*-?\}\}", "PLACEHOLDER", content)
    return yaml.safe_load(rendered)


def test_slugify_normalizes_suite_name():
    assert _slugify("Wave4 Infra Check!") == "wave4-infra-check"
    assert _slugify("") == "aidd-suite"


def test_scaffold_infra_generates_all_expected_files(tmp_path):
    scaffold_infra(str(tmp_path), "Minha Suite Enterprise")

    infra_dir = tmp_path / "infra"
    assert (infra_dir / "terraform" / "main.tf").is_file()
    assert (infra_dir / "helm" / "Chart.yaml").is_file()
    assert (infra_dir / "helm" / "values.yaml").is_file()
    assert (infra_dir / "helm" / "templates" / "deployment.yaml").is_file()
    assert (infra_dir / "helm" / "templates" / "service.yaml").is_file()
    assert (infra_dir / "helm" / "templates" / "ingress.yaml").is_file()
    assert (infra_dir / "helm" / "templates" / "hpa.yaml").is_file()


def test_helm_chart_yaml_is_valid_plain_yaml(tmp_path):
    scaffold_infra(str(tmp_path), "Suite Teste")
    data = yaml.safe_load((tmp_path / "infra" / "helm" / "Chart.yaml").read_text(encoding="utf-8"))
    assert data["apiVersion"] == "v2"
    assert data["type"] == "application"


def test_helm_values_yaml_is_valid_plain_yaml(tmp_path):
    scaffold_infra(str(tmp_path), "Suite Teste")
    content = (tmp_path / "infra" / "helm" / "values.yaml").read_text(encoding="utf-8")

    data = yaml.safe_load(content)
    assert data["replicaCount"] == 2
    assert data["service"]["port"] == 3000
    assert data["autoscaling"]["minReplicas"] == 2
    assert data["autoscaling"]["maxReplicas"] == 10


@pytest.mark.parametrize("filename", ["deployment.yaml", "service.yaml", "ingress.yaml", "hpa.yaml"])
def test_helm_templates_are_structurally_valid_yaml_after_fake_render(tmp_path, filename):
    scaffold_infra(str(tmp_path), "Suite Teste")
    content = (tmp_path / "infra" / "helm" / "templates" / filename).read_text(encoding="utf-8")

    # Chaves de template balanceadas (toda {{ tem uma }} correspondente)
    assert content.count("{{") == content.count("}}")

    data = _fake_render_yaml(content)
    assert data is not None
    assert "apiVersion" in data
    assert "kind" in data
    assert "metadata" in data


def test_helm_deployment_references_health_endpoint_for_probes(tmp_path):
    scaffold_infra(str(tmp_path), "Suite Teste")
    content = (tmp_path / "infra" / "helm" / "templates" / "deployment.yaml").read_text(encoding="utf-8")
    assert content.count("path: /health") == 2  # liveness + readiness


def test_terraform_main_tf_has_balanced_braces_and_required_blocks(tmp_path):
    scaffold_infra(str(tmp_path), "Suite Teste")
    content = (tmp_path / "infra" / "terraform" / "main.tf").read_text(encoding="utf-8")

    assert content.count("{") == content.count("}")
    for required in [
        'terraform {', 'provider "aws"', 'resource "aws_db_instance" "postgres"',
        'resource "aws_elasticache_cluster" "redis"', 'output "database_url"', 'output "eventbus_url"'
    ]:
        assert required in content, f"Bloco obrigatorio ausente: {required}"


def test_terraform_main_tf_does_not_hardcode_db_password(tmp_path):
    scaffold_infra(str(tmp_path), "Suite Teste")
    content = (tmp_path / "infra" / "terraform" / "main.tf").read_text(encoding="utf-8")
    assert "sensitive   = true" in content
    assert 'variable "db_password"' in content


# ---------------------------------------------------------------------------
# Validação real opcional com os binários terraform/helm, se instalados
# ---------------------------------------------------------------------------

@pytest.mark.skipif(shutil.which("terraform") is None, reason="binario terraform nao instalado neste ambiente")
def test_terraform_validate_real_binary(tmp_path):
    scaffold_infra(str(tmp_path), "Suite Teste")
    tf_dir = tmp_path / "infra" / "terraform"
    subprocess.run(["terraform", "init", "-backend=false"], cwd=tf_dir, check=True, capture_output=True)
    result = subprocess.run(["terraform", "validate"], cwd=tf_dir, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(shutil.which("helm") is None, reason="binario helm nao instalado neste ambiente")
def test_helm_lint_real_binary(tmp_path):
    scaffold_infra(str(tmp_path), "Suite Teste")
    result = subprocess.run(["helm", "lint", str(tmp_path / "infra" / "helm")], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
