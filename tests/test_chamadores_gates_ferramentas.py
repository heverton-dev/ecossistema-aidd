# -*- coding: utf-8 -*-
"""
Validação de chamadores para os 6 gates de ferramentas (Item 3 pós-c03):
- G_FACTORY_ANALYSIS, G_FACTORY_COMPOSE, G_FACTORY_ENV, G_FACTORY_INIT_DB, G_FACTORY_INTEGRATION (aidd-open)
- G_INTEGRACAO_CROSS_SCRIPT (aidd-pure)
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GATES_ALVO = [
    ("G_FACTORY_ANALYSIS", "aidd-open"),
    ("G_FACTORY_COMPOSE", "aidd-open"),
    ("G_FACTORY_ENV", "aidd-open"),
    ("G_FACTORY_INIT_DB", "aidd-open"),
    ("G_FACTORY_INTEGRATION", "aidd-open"),
    ("G_INTEGRACAO_CROSS_SCRIPT", "aidd-pure"),
]


def test_seis_gates_possuem_chamador_ativo_no_codigo():
    """Garante que nenhum dos 6 gates ficou órfão (chamador no código do pipeline)."""
    script_chamadores = Path(r"C:\Users\trcnologia\aidd-logs\b8_scripts\chamadores_gates.py")
    if not script_chamadores.is_file():
        # Fallback inline se o script de log não estiver disponível
        for gate, ferramenta in GATES_ALVO:
            pasta = next(ROOT.glob(f"modulos/**/{ferramenta}"))
            chamadores = []
            for f in pasta.rglob("*.py"):
                if f.name.startswith("G_") or "test_" in f.name:
                    continue
                if gate in f.read_text(encoding="utf-8", errors="replace"):
                    chamadores.append(f.name)
            assert len(chamadores) >= 1, f"Gate {gate} em {ferramenta} sem chamador no código (encontrados: {chamadores})"
        return

    proc = subprocess.run([sys.executable, str(script_chamadores), str(ROOT)],
                          capture_output=True, text=True, check=True)
    linhas = proc.stdout.splitlines()

    for gate, ferramenta in GATES_ALVO:
        linha = next((l for l in linhas if l.startswith(gate)), None)
        assert linha is not None, f"Gate {gate} não encontrado na saída do verificador de chamadores"
        # Deve ter chamadores listados e total >= 1
        assert "total=0" not in linha, f"Gate {gate} ainda está sem chamadores: {linha}"
