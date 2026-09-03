# -*- coding: utf-8 -*-
"""
Testes para utils_delegacao.extrair_json_resposta — Correção: fence markdown
embutido dentro do VALOR de um campo JSON ('codigo'/'teste'), não apenas
envolvendo a resposta inteira.

Achado real: ENTREGA-FINAL-rastreador-habitos gerou test_coletar_habitos.py
com "```python" literal na primeira linha (SyntaxError na coleta do pytest),
porque o LLM colou o bloco de código (fences inclusos) como valor literal do
campo "teste" no JSON, e nada removia o fence antes de escrever em disco.
"""

import json

from utils_delegacao import extrair_json_resposta, LLMNaoConfiguradoException


def test_extrai_e_remove_fence_embutido_nos_campos_codigo_e_teste():
    payload = {
        "codigo": "```python\ndef f():\n    pass\n```",
        "teste": "```python\nimport pytest\ndef test_f():\n    pass\n```",
        "caminho_relativo": "x.py",
        "caminho_teste": "test_x.py",
    }
    resultado = extrair_json_resposta(json.dumps(payload))
    assert resultado["codigo"] == "def f():\n    pass"
    assert resultado["teste"] == "import pytest\ndef test_f():\n    pass"
    assert "```" not in resultado["codigo"]
    assert "```" not in resultado["teste"]


def test_nao_afeta_campos_sem_fence():
    payload = {
        "codigo": "def f():\n    pass",
        "teste": "def test_f():\n    pass",
        "caminho_relativo": "x.py",
        "caminho_teste": "test_x.py",
    }
    resultado = extrair_json_resposta(json.dumps(payload))
    assert resultado["codigo"] == "def f():\n    pass"
    assert resultado["teste"] == "def test_f():\n    pass"


def test_remove_fence_mesmo_quando_json_envelopado_em_markdown():
    payload = {
        "codigo": "```python\nx = 1\n```",
        "teste": "```python\nassert x == 1\n```",
        "caminho_relativo": "x.py",
        "caminho_teste": "test_x.py",
    }
    texto = "```json\n" + json.dumps(payload) + "\n```"
    resultado = extrair_json_resposta(texto)
    assert resultado["codigo"] == "x = 1"
    assert resultado["teste"] == "assert x == 1"


# =============================================================================
# TESTES DE TIMEOUT E FALLBACK DO MODO DELEGADO (TAREFA 1)
# =============================================================================

def test_solicitar_llm_modo_delegado_timeout_com_fallback_headless(monkeypatch):
    import utils_delegacao

    # Simula timeout da ADE
    monkeypatch.setattr(utils_delegacao.RequisicaoLLMDelegada, 'aguardar_resposta', lambda *a, **kw: None)

    # Configura LLM_MODEL no ambiente
    monkeypatch.setenv('LLM_MODEL', 'provedor/modelo-teste')

    # Mock do solicitar_llm_modo_headless
    headless_chamado = []
    def fake_headless(prompt, contexto, fase, modelo=None, temperatura=0.7):
        headless_chamado.append((prompt, contexto, fase, modelo))
        return {
            'conteudo': 'resposta do fallback headless',
            'tokens_consumidos': 42,
            'modelo_usado': modelo or 'provedor/modelo-teste',
            'timestamp_resposta': '2026-08-30T00:00:00Z',
        }
    monkeypatch.setattr(utils_delegacao, 'solicitar_llm_modo_headless', fake_headless)

    resp = utils_delegacao.solicitar_llm_modo_delegado(
        prompt="Gerar código", contexto="Phase 8", fase="phase_08", timeout=1
    )

    assert resp is not None
    assert resp['conteudo'] == 'resposta do fallback headless'
    assert len(headless_chamado) == 1
    assert headless_chamado[0][0] == "Gerar código"


def test_solicitar_llm_modo_delegado_timeout_sem_headless_retorna_none(monkeypatch):
    import utils_delegacao

    # Simula timeout da ADE
    monkeypatch.setattr(utils_delegacao.RequisicaoLLMDelegada, 'aguardar_resposta', lambda *a, **kw: None)

    # Remove LLM_MODEL do ambiente
    monkeypatch.delenv('LLM_MODEL', raising=False)

    headless_chamado = []
    monkeypatch.setattr(utils_delegacao, 'solicitar_llm_modo_headless', lambda *a, **kw: headless_chamado.append(1))

    resp = utils_delegacao.solicitar_llm_modo_delegado(
        prompt="Gerar código", contexto="Phase 8", fase="phase_08", timeout=1, modelo=None
    )

    assert resp is None
    assert len(headless_chamado) == 0


def test_solicitar_llm_modo_delegado_sucesso_nao_chama_headless(monkeypatch):
    import utils_delegacao

    # Simula ADE respondendo a tempo
    resposta_ade = {
        'id': '123',
        'conteudo': 'resposta delegada oficial',
        'tokens_consumidos': 100,
        'modelo_usado': 'claude-opus-5',
        'timestamp_resposta': '2026-08-30T00:00:00Z',
    }
    monkeypatch.setattr(utils_delegacao.RequisicaoLLMDelegada, 'aguardar_resposta', lambda *a, **kw: resposta_ade)
    monkeypatch.setenv('LLM_MODEL', 'provedor/modelo-teste')

    headless_chamado = []
    monkeypatch.setattr(utils_delegacao, 'solicitar_llm_modo_headless', lambda *a, **kw: headless_chamado.append(1))

    resp = utils_delegacao.solicitar_llm_modo_delegado(
        prompt="Gerar código", contexto="Phase 8", fase="phase_08", timeout=1
    )

    assert resp is not None
    assert resp['conteudo'] == 'resposta delegada oficial'
    assert len(headless_chamado) == 0


# =============================================================================
# TESTES DE EXCEÇÃO CUSTOMIZADA LLMNaoConfiguradoException
# =============================================================================

def _criar_erro(nome: str, msg: str):
    """Cria uma exceção com o nome de classe exato (type().__name__ == nome)."""
    cls = type(nome, (Exception,), {})
    return cls(msg)


class TestLLMNaoConfiguradoException:
    """Testes para a exceção customizada e a tradução de erros do litellm."""

    def test_excecao_tem_atributos_mensagem_usuario_e_detalhes_tecnicos(self):
        exc = LLMNaoConfiguradoException(
            mensagem_usuario="Mensagem amigável",
            detalhes_tecnicos="BadRequestError: detalhe técnico completo"
        )
        assert exc.mensagem_usuario == "Mensagem amigável"
        assert exc.detalhes_tecnicos == "BadRequestError: detalhe técnico completo"

    def test_str_retorna_mensagem_usuario(self):
        exc = LLMNaoConfiguradoException(
            mensagem_usuario="Mensagem amigável",
            detalhes_tecnicos="erro original"
        )
        assert str(exc) == "Mensagem amigável"

    def test_excecao_e_subclasse_de_exception(self):
        exc = LLMNaoConfiguradoException(
            mensagem_usuario="msg", detalhes_tecnicos="det"
        )
        assert isinstance(exc, Exception)

    def test_traduz_bad_request_error(self):
        """BadRequestError do litellm vira LLMNaoConfiguradoException amigável."""
        import utils_delegacao
        import pytest

        erro = _criar_erro('BadRequestError', "Provider List repeated 4x invalid model")

        with pytest.raises(LLMNaoConfiguradoException) as exc_info:
            utils_delegacao._traduzir_erro_litellm(erro, 'modelo/inexistente')

        assert "configurado" in exc_info.value.mensagem_usuario.lower()
        assert "modelo/inexistente" in exc_info.value.mensagem_usuario
        assert "BadRequestError" in exc_info.value.detalhes_tecnicos

    def test_traduz_authentication_error(self):
        """AuthenticationError do litellm vira LLMNaoConfiguradoException amigável."""
        import utils_delegacao
        import pytest

        erro = _criar_erro('AuthenticationError', "Invalid API key provided")

        with pytest.raises(LLMNaoConfiguradoException) as exc_info:
            utils_delegacao._traduzir_erro_litellm(erro, 'gpt-4')

        assert "chave" in exc_info.value.mensagem_usuario.lower()
        assert ".env" in exc_info.value.mensagem_usuario
        assert "AuthenticationError" in exc_info.value.detalhes_tecnicos
        assert "Invalid API key" in exc_info.value.detalhes_tecnicos

    def test_traduz_connection_error(self):
        """ConnectionError vira LLMNaoConfiguradoException amigável."""
        import utils_delegacao
        import pytest

        erro = _criar_erro('ConnectionError', "Failed to establish connection")

        with pytest.raises(LLMNaoConfiguradoException) as exc_info:
            utils_delegacao._traduzir_erro_litellm(erro, 'gpt-4')

        assert "conectar" in exc_info.value.mensagem_usuario.lower() or \
               "conexão" in exc_info.value.mensagem_usuario.lower()
        assert "ConnectionError" in exc_info.value.detalhes_tecnicos

    def test_traduz_api_connection_error(self):
        """APIConnectionError vira LLMNaoConfiguradoException amigável."""
        import utils_delegacao
        import pytest

        erro = _criar_erro('APIConnectionError', "Connection refused")

        with pytest.raises(LLMNaoConfiguradoException) as exc_info:
            utils_delegacao._traduzir_erro_litellm(erro, 'claude-3')

        assert "conectar" in exc_info.value.mensagem_usuario.lower() or \
               "conexão" in exc_info.value.mensagem_usuario.lower()

    def test_traduz_timeout_error(self):
        """Timeout vira LLMNaoConfiguradoException amigável."""
        import utils_delegacao
        import pytest

        erro = _criar_erro('Timeout', "Request timed out")

        with pytest.raises(LLMNaoConfiguradoException) as exc_info:
            utils_delegacao._traduzir_erro_litellm(erro, 'gpt-4')

        assert "conectar" in exc_info.value.mensagem_usuario.lower() or \
               "conexão" in exc_info.value.mensagem_usuario.lower()

    def test_erro_desconhecido_nao_levanta_excecao(self):
        """Erros não mapeados não levantam LLMNaoConfiguradoException (retorna None)."""
        import utils_delegacao

        erro_generico = ValueError("algo inesperado")
        resultado = utils_delegacao._traduzir_erro_litellm(erro_generico, 'gpt-4')
        assert resultado is None

    def test_headless_levanta_excecao_quando_bad_request(self, monkeypatch):
        """Integração: solicitar_llm_modo_headless levanta LLMNaoConfiguradoException em BadRequestError."""
        import utils_delegacao
        import sys
        import pytest

        bad_request_cls = type('BadRequestError', (Exception,), {})
        fake_module = type(sys)('litellm')
        fake_module.completion = lambda *a, **kw: (_ for _ in ()).throw(
            bad_request_cls("Provider not found: bad-provider/model")
        )
        monkeypatch.setitem(sys.modules, 'litellm', fake_module)
        monkeypatch.setenv('LLM_MODEL', 'bad-provider/model')

        with pytest.raises(LLMNaoConfiguradoException) as exc_info:
            utils_delegacao.solicitar_llm_modo_headless(
                prompt="teste", contexto="ctx", fase="phase_test"
            )

        assert "bad-provider/model" in exc_info.value.mensagem_usuario
        assert "BadRequestError" in exc_info.value.detalhes_tecnicos

    def test_headless_levanta_excecao_quando_auth_error(self, monkeypatch):
        """Integração: solicitar_llm_modo_headless levanta LLMNaoConfiguradoException em AuthenticationError."""
        import utils_delegacao
        import sys
        import pytest

        auth_cls = type('AuthenticationError', (Exception,), {})
        fake_module = type(sys)('litellm')
        fake_module.completion = lambda *a, **kw: (_ for _ in ()).throw(
            auth_cls("bad key")
        )
        monkeypatch.setitem(sys.modules, 'litellm', fake_module)
        monkeypatch.setenv('LLM_MODEL', 'openai/gpt-4')

        with pytest.raises(LLMNaoConfiguradoException) as exc_info:
            utils_delegacao.solicitar_llm_modo_headless(
                prompt="teste", contexto="ctx", fase="phase_test"
            )

        assert "chave" in exc_info.value.mensagem_usuario.lower()

    def test_mensagem_usuario_nao_contem_stack_trace(self):
        """A mensagem_usuario não deve conter termos técnicos de stack trace."""
        import utils_delegacao
        import pytest

        erro = _criar_erro('BadRequestError', "Traceback (most recent call last): ...")

        with pytest.raises(LLMNaoConfiguradoException) as exc_info:
            utils_delegacao._traduzir_erro_litellm(erro, 'modelo-x')

        # mensagem_usuario deve ser limpa, sem traceback
        assert "Traceback" not in exc_info.value.mensagem_usuario
        # detalhes_tecnicos DEVE conter o erro original
        assert "Traceback" in exc_info.value.detalhes_tecnicos

