import pytest

from aidd_forge.core.camada_detector import CamadaConflitanteError, TIPO_PARA_CAMADA, detectar_camada


@pytest.mark.parametrize(
    "tipo,esperado",
    [
        ("rule", 1),
        ("spec", 2),
        ("mcp", 4),
        ("skill", 5),
        ("roteiro", 5),
    ],
)
def test_detectar_camada_sem_conflito(tipo, esperado):
    assert detectar_camada(tipo) == esperado
    assert TIPO_PARA_CAMADA[tipo] == esperado


def test_detectar_camada_com_camada_alvo_coerente():
    assert detectar_camada("skill", camada_alvo=5) == 5


def test_detectar_camada_com_camada_alvo_conflitante_levanta_erro():
    with pytest.raises(CamadaConflitanteError):
        detectar_camada("rule", camada_alvo=5)


def test_tipo_sem_camada_mapeada_levanta_erro():
    with pytest.raises(ValueError):
        detectar_camada("desconhecido")
