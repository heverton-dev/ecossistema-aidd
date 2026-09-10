# -*- coding: utf-8 -*-
"""Use Case: verificar-drift — checagem SHA-256 de componentes registrados em CAPABILITIES.json."""

import os
import sys

from application.commands.inject import _core_src_path
from application.commands.setup import ensure_environment


def cmd_verificar_drift(args):
    """Roda a checagem de drift (SHA-256) dos componentes registrados em CAPABILITIES.json."""
    ensure_environment()
    core_src = _core_src_path()
    if core_src not in sys.path:
        sys.path.insert(0, core_src)
    from sincronizador_harness import verificar_sincronizacao

    target_dir = os.path.abspath(getattr(args, "dir", "."))
    print("=" * 80)
    print(f"🔍 [AIDD VERIFICAR-DRIFT] Verificando drift em {target_dir}")
    print("=" * 80)

    res = verificar_sincronizacao(target_dir)
    if res.sucesso:
        print(f"\n✅ [SUCESSO] Nenhum drift detectado ({res.valor.get('verificados', 0)} arquivo(s) verificado(s)).")
        sys.exit(0)
    else:
        print(f"\n[ERRO] {res.codigo}: {res.erro}")
        for problema in res.detalhes.get("problemas", []):
            print(f"   - {problema}")
        sys.exit(1)