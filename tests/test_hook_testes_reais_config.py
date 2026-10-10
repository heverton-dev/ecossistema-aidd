# -*- coding: utf-8 -*-
"""
Validação do hook g-testes-reais no .pre-commit-config.yaml (Item 4 pós-c03):
Garante que g-testes-reais não aponta para o caminho extinto ^tools/ e está configurado
com stages: [manual], sendo coberto em commits pelo g-micro-gates-diff.
"""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent


def test_hook_g_testes_reais_nao_tem_filtro_extinto_e_usa_stage_manual():
    config_path = ROOT / ".pre-commit-config.yaml"
    assert config_path.is_file(), "Arquivo .pre-commit-config.yaml não encontrado"

    dados = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    hooks = [h for repo in dados.get("repos", []) for h in repo.get("hooks", [])]
    hook_tr = next((h for h in hooks if h.get("id") == "g-testes-reais"), None)

    assert hook_tr is not None, "Hook g-testes-reais não encontrado no .pre-commit-config.yaml"

    # Não deve ter o filtro de pasta extinta ^tools/
    files_filter = hook_tr.get("files")
    assert files_filter != "^tools/", f"Hook g-testes-reais ainda possui files: {files_filter} (pasta extinta)"

    # Deve possuir stages: [manual]
    stages = hook_tr.get("stages", [])
    assert "manual" in stages, f"Hook g-testes-reais deve ter stage 'manual', encontrado: {stages}"
