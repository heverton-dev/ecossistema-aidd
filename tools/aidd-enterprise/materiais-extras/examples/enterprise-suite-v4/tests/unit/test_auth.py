from core.security import JWTService


def test_post_login_retorna_token_jwt_valido(app):
    resultado = app.post_login({"email": "admin@logistica.com", "password": "admin"})

    assert resultado["sucesso"] is True
    assert resultado["tipo"] == "Bearer"
    assert resultado["usuario"]["email"] == "admin@logistica.com"

    ok, payload, msg = JWTService.decode(resultado["token"])
    assert ok is True
    assert msg == "OK"
    assert payload["sub"] == "admin@logistica.com"
    assert payload["role"] == "admin"


def test_post_login_usa_email_padrao_quando_omitido(app):
    resultado = app.post_login({})
    assert resultado["usuario"]["email"] == "admin@empresa.com"


def test_get_auth_me_retorna_usuario_autenticado(app):
    resultado = app.get_auth_me({})
    assert resultado["autenticado"] is True
    assert resultado["usuario"]["status"] == "ativo"
