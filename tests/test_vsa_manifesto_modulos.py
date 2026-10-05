import pytest
from docs.padroes.contratos.manifesto_modulos import (
    ManifestoModulos,
    validar_manifesto_modulos,
    MACRO_MODULOS_CANONICOS,
    ModuloDef,
)

def test_macro_modulos_canonicos_presentes():
    assert "01-governanca-e-qualidade" in MACRO_MODULOS_CANONICOS
    assert "02-triade-motores" in MACRO_MODULOS_CANONICOS
    assert "03-plataforma-e-entrega" in MACRO_MODULOS_CANONICOS
    assert "04-nucleo-compartilhado" in MACRO_MODULOS_CANONICOS
    assert len(MACRO_MODULOS_CANONICOS) == 4

def test_manifesto_valido():
    dados = {
        "versao": "1.0",
        "macro_modulos": {
            "01-governanca-e-qualidade": {"descricao": "Governança e gates", "submodulos": ["forge"]},
            "02-triade-motores": {"descricao": "Motores de execução", "submodulos": ["pure", "open", "freedom"]},
            "03-plataforma-e-entrega": {"descricao": "Plataforma e ops", "submodulos": ["ops", "enterprise"]},
            "04-nucleo-compartilhado": {"descricao": "Componentes e libs", "submodulos": ["compartilhado"]}
        }
    }
    manifesto = validar_manifesto_modulos(dados)
    assert manifesto.versao == "1.0"
    assert len(manifesto.macro_modulos) == 4

def test_manifesto_invalido_faltando_macro_modulo():
    dados = {
        "versao": "1.0",
        "macro_modulos": {
            "01-governanca-e-qualidade": {"descricao": "Governança e gates", "submodulos": []},
            "02-triade-motores": {"descricao": "Motores de execução", "submodulos": []}
        }
    }
    with pytest.raises(ValueError, match="Macro-módulos canônicos ausentes"):
        validar_manifesto_modulos(dados)

def test_manifesto_invalido_macro_modulo_desconhecido():
    dados = {
        "versao": "1.0",
        "macro_modulos": {
            "01-governanca-e-qualidade": {"descricao": "G", "submodulos": []},
            "02-triade-motores": {"descricao": "T", "submodulos": []},
            "03-plataforma-e-entrega": {"descricao": "P", "submodulos": []},
            "04-nucleo-compartilhado": {"descricao": "N", "submodulos": []},
            "05-extra-invalido": {"descricao": "Inválido", "submodulos": []}
        }
    }
    with pytest.raises(ValueError, match="Macro-módulos não canônicos detectados"):
        validar_manifesto_modulos(dados)
