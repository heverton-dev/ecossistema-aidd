# -*- coding: utf-8 -*-
"""Use Case: verificar-drift — checagem SHA-256 de componentes registrados em CAPABILITIES.json."""

import os
import sys

from application_enterprise.pecas_catalogo import CORE_DIR
from application_enterprise.commands.setup import ensure_environment


import hashlib
import json
from pathlib import Path


def _emitir_contrato_c5(target_dir: str):
    """Emite formalmente o contrato C5 (handoff-enterprise-to-ops.schema.json)."""
    p_target = Path(target_dir)
    registry_file = p_target / "COMPONENT-REGISTRY.json"
    if not registry_file.exists():
        conteudo_reg = {"versao": "1.0.0", "componentes": []}
        registry_file.write_text(json.dumps(conteudo_reg, indent=2), encoding="utf-8")
    
    sha_reg = hashlib.sha256(registry_file.read_bytes()).hexdigest()
    selo = hashlib.sha256(f"enterprise-selo:{p_target.name}:{sha_reg}".encode("utf-8")).hexdigest()
    
    c5_dados = {
        "versao_schema": "1.0.0",
        "diretorio_projeto": str(p_target.resolve()),
        "registry": {
            "caminho": "COMPONENT-REGISTRY.json",
            "sha256": sha_reg,
        },
        "selo_sha256": selo,
        "drift": {
            "verificado": True,
            "exit_code": 0,
        },
        "perfil_app": {
            "tipo_runtime": "monolito_modular_docker",
            "portas_expostas": [8000],
            "banco": "sqlite",
        },
    }
    
    c5_path = p_target / "HANDOFF_ENTERPRISE_OPS.json"
    c5_path.write_text(json.dumps(c5_dados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [+] Contrato formal C5 emitido com sucesso: {c5_path}")


def cmd_verificar_drift(args):
    """Roda a checagem de drift (SHA-256) dos componentes registrados em CAPABILITIES.json."""
    ensure_environment()
    core_src = str(CORE_DIR)
    if core_src not in sys.path:
        sys.path.insert(0, core_src)
    from sincronizador_harness import verificar_sincronizacao

    target_dir = os.path.abspath(getattr(args, "dir", "."))
    print("=" * 80)
    print(f"🔍 [AIDD VERIFICAR-DRIFT] Verificando drift em {target_dir}")
    print("=" * 80)

    res = verificar_sincronizacao(target_dir)
    if res.sucesso:
        _emitir_contrato_c5(target_dir)
        print(f"\n✅ [SUCESSO] Nenhum drift detectado ({res.valor.get('verificados', 0)} arquivo(s) verificado(s)).")
        sys.exit(0)
    else:
        print(f"\n[ERRO] {res.codigo}: {res.erro}")
        for problema in res.detalhes.get("problemas", []):
            print(f"   - {problema}")
        sys.exit(1)
