import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_tdd_fallback_runner_check():
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import fallback

    assert fallback.verificar_runner_instalado("python") is True
    assert fallback.verificar_runner_instalado("runner_inexistente_xyz_123") is False

def test_tdd_fallback_circuit_breaker():
    sys.path.insert(0, str(ROOT / ".agents" / "skills" / "aidd-tdd" / "scripts"))
    import fallback

    cb = fallback.CircuitBreakerTdd(max_tentativas=3)
    
    cb.registrar_tentativa()
    cb.registrar_tentativa()
    assert cb.atingiu_limite() is False

    cb.registrar_tentativa()
    assert cb.atingiu_limite() is True

    with pytest.raises(fallback.CircuitBreakerError):
        cb.registrar_tentativa()
