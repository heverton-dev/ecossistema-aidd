# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def carregar_motor():
    motor_path = ROOT / "componentes" / "compartilhado" / "skills" / "aidd-handoff" / "scripts" / "motor.py"
    spec = importlib.util.spec_from_file_location("aidd_handoff_motor", str(motor_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_motor_valida_secoes_e_rejeita_faltantes():
    motor = carregar_motor()
    incompleto = "# Titulo\n\n## Initial Goal\nX\n"
    res = motor.validar_conteudo(incompleto)
    assert res["valido"] is False
    assert len(res["secoes_faltantes"]) > 0

def test_motor_rejeita_codigo_fonte_colado():
    motor = carregar_motor()
    com_codigo = """# Handoff
## Initial Goal
Fazer algo
## Completed Work
def foo():
    pass
## Quality Gate State
OK
## Next Actions
Continuar
## Discovered Invariants & Gotchas
Nenhum
"""
    res = motor.validar_conteudo(com_codigo)
    assert res["valido"] is False
    assert res["codigo_colado_detectado"] is True

def test_motor_aprova_handoff_limpo():
    motor = carregar_motor()
    limpo = """# Handoff
## Initial Goal
Fazer algo
## Completed Work
- docs/teste.md atualizado
## Quality Gate State
- exit 0
## Next Actions
- continuar etapa 2
## Discovered Invariants & Gotchas
- nenhuma anomalia
"""
    res = motor.validar_conteudo(limpo)
    assert res["valido"] is True
    assert res["codigo_colado_detectado"] is False
    assert len(res["secoes_faltantes"]) == 0
