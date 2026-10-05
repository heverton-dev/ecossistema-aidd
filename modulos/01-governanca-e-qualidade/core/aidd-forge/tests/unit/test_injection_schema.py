from aidd_forge.core.injection_schema import validate_request


def _payload(**overrides):
    base = {
        "tipo": "skill",
        "nome": "demo-skill",
        "descricao": "Uma skill de demonstracao",
        "conteudo": "# Demo\n\nConteudo real.\n",
    }
    base.update(overrides)
    return base


def test_valid_payload_passes():
    result = validate_request(_payload())

    assert result.valid is True
    assert result.errors == []


def test_missing_required_field_fails():
    payload = _payload()
    del payload["descricao"]

    result = validate_request(payload)

    assert result.valid is False
    assert any("descricao" in erro for erro in result.errors)


def test_tipo_fora_do_enum_fails():
    result = validate_request(_payload(tipo="agent"))

    assert result.valid is False
    assert any("tipo" in erro for erro in result.errors)


def test_nome_com_maiuscula_fails_pattern():
    result = validate_request(_payload(nome="Demo-Skill"))

    assert result.valid is False
    assert any("nome" in erro for erro in result.errors)


def test_descricao_vazia_fails_min_length():
    result = validate_request(_payload(descricao=""))

    assert result.valid is False
    assert any("descricao" in erro for erro in result.errors)


def test_camada_alvo_fora_do_enum_fails():
    result = validate_request(_payload(camada_alvo=9))

    assert result.valid is False
    assert any("camada_alvo" in erro for erro in result.errors)


def test_campo_desconhecido_fails():
    result = validate_request(_payload(extra="nao deveria existir"))

    assert result.valid is False
    assert any("extra" in erro for erro in result.errors)


def test_payload_nao_dict_fails():
    result = validate_request("nao e um objeto")

    assert result.valid is False
