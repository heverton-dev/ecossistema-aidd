import pytest

def test_politica_retry_com_sucesso():
    from scripts.resiliencia_vsa import executar_com_retry

    tentativas = 0

    def operacao_com_falha_transiente():
        nonlocal tentativas
        tentativas += 1
        if tentativas < 3:
            raise IOError("Falha transiente de I/O")
        return "sucesso_recuperado"

    resultado = executar_com_retry(
        operacao_com_falha_transiente,
        max_tentativas=4,
        backoff_inicial=0.01,
        excecoes_permitidas=(IOError,)
    )

    assert resultado == "sucesso_recuperado"
    assert tentativas == 3

def test_politica_retry_esgota_e_falha_graciosamente():
    from scripts.resiliencia_vsa import executar_com_retry

    def operacao_sempre_falha():
        raise IOError("Disco indisponível")

    with pytest.raises(IOError, match="Disco indisponível"):
        executar_com_retry(
            operacao_sempre_falha,
            max_tentativas=2,
            backoff_inicial=0.01,
            excecoes_permitidas=(IOError,)
        )
