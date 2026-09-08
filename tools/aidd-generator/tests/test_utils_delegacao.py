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


# =============================================================================
# TESTES DE ORIGEM DE MEDIÇÃO (TRANSPARÊNCIA DE TOKENS)
# =============================================================================

def test_modo_delegado_inclui_origem_autodeclarado_mesmo_sem_campo_na_resposta(monkeypatch):
    """ADE externa responde sem campo origem_medicao (como qualquer ADE real hoje):
    código local deve garantir origem_medicao == 'autodeclarado'."""
    import utils_delegacao

    resposta_sem_origem = {
        'id': 'req123',
        'conteudo': 'resposta gerada',
        'tokens_consumidos': 450,
        'modelo_usado': 'claude-sonnet-4-6',
        'timestamp_resposta': '2026-09-05T12:00:00Z',
    }
    monkeypatch.setattr(utils_delegacao.RequisicaoLLMDelegada, 'aguardar_resposta', lambda *a, **kw: resposta_sem_origem)

    resp = utils_delegacao.solicitar_llm_modo_delegado(
        prompt="Analise", contexto="Fase 2", fase="phase_02", timeout=1
    )

    assert resp is not None
    assert resp.get('origem_medicao') == 'autodeclarado'
    assert resp.get('tokens_consumidos') == 450


def test_modo_delegado_sobrescreve_alegacao_de_origem_da_ade(monkeypatch):
    """Se ADE maliciosamente ou por engano alegar 'medido_api', o código local
    sobrescreve para 'autodeclarado' porque modo delegado é não-verificável por definição."""
    import utils_delegacao

    resposta_falsificada = {
        'id': 'req456',
        'conteudo': 'resposta gerada',
        'tokens_consumidos': 500,
        'origem_medicao': 'medido_api',  # tentativa de fingir que mediu
        'modelo_usado': 'gpt-4o',
        'timestamp_resposta': '2026-09-05T12:00:00Z',
    }
    monkeypatch.setattr(utils_delegacao.RequisicaoLLMDelegada, 'aguardar_resposta', lambda *a, **kw: resposta_falsificada)

    resp = utils_delegacao.solicitar_llm_modo_delegado(
        prompt="Analise", contexto="Fase 2", fase="phase_02", timeout=1
    )

    assert resp is not None
    assert resp.get('origem_medicao') == 'autodeclarado'


def test_modo_headless_rotula_medido_api_quando_provider_retorna_usage(monkeypatch):
    """Headless Mode com resposta do litellm contendo usage deve rotular medido_api."""
    import utils_delegacao
    import sys

    class FakeUsage:
        total_tokens = 321

    class FakeMessage:
        content = "conteudo da resposta"

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletionResponse:
        choices = [FakeChoice()]
        usage = FakeUsage()

    fake_litellm = type(sys)('litellm')
    fake_litellm.completion = lambda *a, **kw: FakeCompletionResponse()
    monkeypatch.setitem(sys.modules, 'litellm', fake_litellm)
    monkeypatch.setenv('LLM_MODEL', 'anthropic/claude-3-haiku')

    resp = utils_delegacao.solicitar_llm_modo_headless(
        prompt="prompt", contexto="ctx", fase="phase_02"
    )

    assert resp is not None
    assert resp['tokens_consumidos'] == 321
    assert resp['origem_medicao'] == 'medido_api'


def test_modo_headless_rotula_indisponivel_quando_provider_sem_usage(monkeypatch):
    """Headless Mode quando provider não retorna usage deve rotular indisponivel."""
    import utils_delegacao
    import sys

    class FakeMessage:
        content = "conteudo da resposta"

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletionResponse:
        choices = [FakeChoice()]
        usage = object()  # sem atributo total_tokens

    fake_litellm = type(sys)('litellm')
    fake_litellm.completion = lambda *a, **kw: FakeCompletionResponse()
    monkeypatch.setitem(sys.modules, 'litellm', fake_litellm)
    monkeypatch.setenv('LLM_MODEL', 'anthropic/claude-3-haiku')

    resp = utils_delegacao.solicitar_llm_modo_headless(
        prompt="prompt", contexto="ctx", fase="phase_02"
    )

    assert resp is not None
    assert resp['tokens_consumidos'] is None
    assert resp['origem_medicao'] == 'indisponivel'


# =============================================================================
# TESTES DA TELEMETRIA AUXILIAR LOCAL DE TOKENS (tiktoken, offline)
# =============================================================================

def _tokenizador_fake():
    """Fake tokenizador: 1 token por palavra não-vazia (determinístico e stateless)."""
    class _Enc:
        def encode(self, texto):
            return [w for w in texto.split(" ") if w]
    return _Enc()


def test_estimar_tokens_tiktoken_estrutura_dict(monkeypatch):
    """estimar_tokens_tiktoken retorna dict estruturado (entrada/saida/total/tokenizer/metodo)."""
    import utils_delegacao

    tokenizador_fake = type("Enc", (), {"encode": lambda self, t: list(t.split(" "))})()
    monkeypatch.setattr(utils_delegacao, "_obter_tokenizador_tiktoken", lambda: tokenizador_fake)

    est = utils_delegacao.estimar_tokens_tiktoken(
        prompt="primeira segunda", contexto="ctx", conteudo="um dois"
    )

    assert est is not None
    assert set(est.keys()) == {"entrada", "saida", "total", "tokenizer", "metodo"}
    assert est["tokenizer"] == "cl100k_base"
    assert est["metodo"] == "tiktoken"
    # entrada = contexto + prompt; saida = conteudo
    assert est["entrada"] == 3   # "ctx primeira segunda" -> 3 tokens
    assert est["saida"] == 2      # "um dois" -> 2 tokens
    assert est["total"] == est["entrada"] + est["saida"]


def test_estimar_tokens_tiktoken_sem_conteudo_saida_zero(monkeypatch):
    """Conteudo vazio/None resulta em saida 0 (sem crash)."""
    import utils_delegacao

    tokenizador_fake = type("Enc", (), {"encode": lambda self, t: list(t.split(" "))})()
    monkeypatch.setattr(utils_delegacao, "_obter_tokenizador_tiktoken", lambda: tokenizador_fake)

    est = utils_delegacao.estimar_tokens_tiktoken(prompt="a b c", contexto="", conteudo="")

    assert est is not None
    assert est["saida"] == 0
    assert est["total"] == est["entrada"]


def test_estimar_tokens_tiktoken_retorna_none_quando_tokenizador_indisponivel(monkeypatch):
    """Se tiktoken indisponível, telemetria auxiliar vira None (nunca quebra pipeline)."""
    import utils_delegacao

    monkeypatch.setattr(utils_delegacao, "_obter_tokenizador_tiktoken", lambda: None)

    est = utils_delegacao.estimar_tokens_tiktoken(prompt="x", contexto="y", conteudo="z")

    assert est is None


def test_modo_delegado_inclui_tokens_estimativa_local(monkeypatch):
    """Modo delegado adiciona tokens_estimativa_local mantendo origem autodeclarado."""
    import utils_delegacao

    resposta_ade = {
        'id': 'req789',
        'conteudo': 'resposta com tokens',
        'tokens_consumidos': 600,
        'modelo_usado': 'claude-sonnet-4-6',
        'timestamp_resposta': '2026-09-05T12:00:00Z',
    }
    monkeypatch.setattr(utils_delegacao.RequisicaoLLMDelegada, 'aguardar_resposta', lambda *a, **kw: resposta_ade)

    tokenizador_fake = type("Enc", (), {"encode": lambda self, t: list(t.split(" "))})()
    monkeypatch.setattr(utils_delegacao, "_obter_tokenizador_tiktoken", lambda: tokenizador_fake)

    resp = utils_delegacao.solicitar_llm_modo_delegado(
        prompt="Analise", contexto="Fase 2", fase="phase_02", timeout=1
    )

    assert resp is not None
    assert resp['origem_medicao'] == 'autodeclarado'
    assert resp['tokens_consumidos'] == 600
    assert 'tokens_estimativa_local' in resp
    assert resp['tokens_estimativa_local']['total'] == resp['tokens_estimativa_local']['entrada'] + resp['tokens_estimativa_local']['saida']


def test_modo_delegado_manipula_chave_autodeclarado_ignorando_valor_inventado(monkeypatch):
    """Campo tokens_estimativa_local nunca contesta origem_medicao autodeclarado."""
    import utils_delegacao

    resposta_ade = {
        'id': 'req999',
        'conteudo': 'conteudo teste',
        'tokens_consumidos': 10,
        'origem_medicao': 'medido_api',  # tentativa de fingir medição real
        'modelo_usado': 'gpt-4o',
        'timestamp_resposta': '2026-09-05T12:00:00Z',
    }
    monkeypatch.setattr(utils_delegacao.RequisicaoLLMDelegada, 'aguardar_resposta', lambda *a, **kw: resposta_ade)
    monkeypatch.setattr(utils_delegacao, "_obter_tokenizador_tiktoken", lambda: None)

    resp = utils_delegacao.solicitar_llm_modo_delegado(
        prompt="Analise", contexto="Fase 2", fase="phase_02", timeout=1
    )

    assert resp is not None
    assert resp['origem_medicao'] == 'autodeclarado'
    # sem tiktoken, a telemetria auxiliar é explicitamente None (não inventa valor)
    assert resp['tokens_estimativa_local'] is None


def test_modo_headless_inclui_tokens_estimativa_local(monkeypatch):
    """Headless com usage do provider inclui tokens_estimativa_local e mantém medido_api."""
    import utils_delegacao
    import sys

    class FakeUsage:
        total_tokens = 500

    class FakeMessage:
        content = "conteudo da resposta"

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletionResponse:
        choices = [FakeChoice()]
        usage = FakeUsage()

    fake_litellm = type(sys)('litellm')
    fake_litellm.completion = lambda *a, **kw: FakeCompletionResponse()
    monkeypatch.setitem(sys.modules, 'litellm', fake_litellm)
    monkeypatch.setenv('LLM_MODEL', 'anthropic/claude-3-haiku')

    tokenizador_fake = type("Enc", (), {"encode": lambda self, t: list(t.split(" "))})()
    monkeypatch.setattr(utils_delegacao, "_obter_tokenizador_tiktoken", lambda: tokenizador_fake)

    resp = utils_delegacao.solicitar_llm_modo_headless(
        prompt="prompt", contexto="ctx", fase="phase_02"
    )

    assert resp is not None
    assert resp['origem_medicao'] == 'medido_api'
    assert resp['tokens_consumidos'] == 500
    assert 'tokens_estimativa_local' in resp
    assert resp['tokens_estimativa_local']['metodo'] == 'tiktoken'




# =============================================================================
# TESTES DO PARSING ESTRUTURADO COM INSTRUCTOR (Fase2-Gen2, NIH #23)
# =============================================================================

import pydantic


class ModeloCodegen(pydantic.BaseModel):
    """Modelo Pydantic alvo do parsing estruturado (codegen)."""
    codigo: str
    teste: str
    caminho_relativo: str
    caminho_teste: str


def test_instructor_instalado_e_importavel():
    """Critério da fase: instructor instalado e disponível no ambiente de teste."""
    import instructor
    assert instructor is not None


def test_extrair_json_com_response_model_valida_pydantic():
    """Passar response_model usa validação Pydantic (com retry) via instructor."""
    from utils_delegacao import extrair_json_resposta

    payload = {
        "codigo": "def f():\n    pass",
        "teste": "def test_f():\n    pass",
        "caminho_relativo": "x.py",
        "caminho_teste": "test_x.py",
    }
    import json as _json
    resultado = extrair_json_resposta(_json.dumps(payload), response_model=ModeloCodegen)

    assert isinstance(resultado, ModeloCodegen)
    assert resultado.codigo == "def f():\n    pass"
    assert resultado.teste == "def test_f():\n    pass"
    assert resultado.caminho_relativo == "x.py"


def test_extrair_json_sem_response_model_retorna_dict_mantendo_compatibilidade():
    """Sem response_model, o comportamento legado (dict) é preservado."""
    from utils_delegacao import extrair_json_resposta

    payload = {"codigo": "def f():\n    pass", "teste": "def test_f():\n    pass"}
    import json as _json
    resultado = extrair_json_resposta(_json.dumps(payload))

    assert isinstance(resultado, dict)
    assert resultado["codigo"] == "def f():\n    pass"


def test_extrair_json_com_response_model_aceita_field_extra_ignorando():
    """Pydantic por padrão ignora campos extras; parsing estruturado não quebra."""
    from utils_delegacao import extrair_json_resposta

    payload = {
        "codigo": "def f():\n    pass",
        "teste": "def test_f():\n    pass",
        "caminho_relativo": "x.py",
        "caminho_teste": "test_x.py",
        "campo_extra_inesperado": 123,
    }
    import json as _json
    resultado = extrair_json_resposta(_json.dumps(payload), response_model=ModeloCodegen)

    assert isinstance(resultado, ModeloCodegen)


def test_validar_pydantic_com_retry_sucesso_na_primeira():
    """Validação Pydantic com retry: sucesso direto (sem retry)."""
    from utils_delegacao import _validar_pydantic_com_retry
    import json as _json

    dados = {"codigo": "x", "teste": "y", "caminho_relativo": "a.py", "caminho_teste": "t_a.py"}
    resultado = _validar_pydantic_com_retry(_json.dumps(dados), ModeloCodegen, max_retries=3)

    assert isinstance(resultado, ModeloCodegen)


def test_validar_pydantic_com_retry_aceita_dict_direto():
    """_validar_pydantic_com_retry aceita dict já desserializado."""
    from utils_delegacao import _validar_pydantic_com_retry

    dados = {"codigo": "x", "teste": "y", "caminho_relativo": "a.py", "caminho_teste": "t_a.py"}
    resultado = _validar_pydantic_com_retry(dados, ModeloCodegen, max_retries=3)

    assert isinstance(resultado, ModeloCodegen)


def test_validar_pydantic_com_retry_levanta_validation_error_apos_tentativas():
    """Dados que nunca validam levantam erro Pydantic após esgotar as tentativas."""
    from utils_delegacao import _validar_pydantic_com_retry
    import pytest as _pytest
    from pydantic import ValidationError

    # Faltam campos obrigatórios — sempre inválido
    dados_invalidos = {"codigo": "x"}

    with _pytest.raises(ValidationError):
        _validar_pydantic_com_retry(dados_invalidos, ModeloCodegen, max_retries=2)


# =============================================================================
# TESTES DO ITEM 6.3: POLLING ADAPTATIVO EVENT-DRIVEN E TIMEOUTS POR FASE
# =============================================================================

def test_obter_timeout_por_fase_defaults():
    """Fases conhecidas retornam seus timeouts específicos; fase desconhecida usa padrão."""
    from utils_delegacao import obter_timeout_por_fase, TIMEOUT_PADRAO_DELEGACAO

    assert obter_timeout_por_fase("phase_01") == 30
    assert obter_timeout_por_fase("phase_02") == 45
    assert obter_timeout_por_fase("phase_04") == 60
    assert obter_timeout_por_fase("phase_08") == 180
    assert obter_timeout_por_fase("08_implementador") == 180
    assert obter_timeout_por_fase("fase_inexistente") == TIMEOUT_PADRAO_DELEGACAO
    assert obter_timeout_por_fase(None) == TIMEOUT_PADRAO_DELEGACAO


def test_obter_timeout_por_fase_overrides(monkeypatch):
    """Timeout explícito tem precedência sobre env vars e defaults de fase."""
    from utils_delegacao import obter_timeout_por_fase

    # 1. Override por parâmetro custom
    assert obter_timeout_por_fase("phase_08", timeout_custom=15) == 15

    # 2. Override por env global
    monkeypatch.setenv("AIDD_TIMEOUT_DELEGACAO", "99")
    assert obter_timeout_por_fase("phase_08") == 99

    # 3. Override por env específico da fase (tem prioridade quando global ausente)
    monkeypatch.delenv("AIDD_TIMEOUT_DELEGACAO", raising=False)
    monkeypatch.setenv("AIDD_TIMEOUT_PHASE_08", "250")
    assert obter_timeout_por_fase("phase_08") == 250


def test_aguardar_resposta_retorno_imediato_quando_arquivo_existe(tmp_path, monkeypatch):
    """Se o arquivo já existe no CACHE_DIR, retorna em 0ms sem atraso."""
    import utils_delegacao
    monkeypatch.setattr(utils_delegacao, "CACHE_DIR", tmp_path)

    resposta_valida = {
        "id": "req123",
        "conteudo": "codigo gerado",
        "tokens_consumidos": 50,
        "origem_medicao": "autodeclarado",
        "modelo_usado": "claude-3-5-sonnet",
        "timestamp_resposta": "2026-09-08T12:00:00Z"
    }
    caminho = tmp_path / "_llm_response_req123.json"
    caminho.write_text(json.dumps(resposta_valida), encoding="utf-8")

    import time
    t0 = time.time()
    res = utils_delegacao.RequisicaoLLMDelegada.aguardar_resposta("req123", timeout=5)
    duracao = time.time() - t0

    assert res is not None
    assert res["conteudo"] == "codigo gerado"
    assert duracao < 0.2  # Instantâneo


def test_aguardar_resposta_backoff_adaptativo_progressivo(tmp_path, monkeypatch):
    """Testa que o polling adaptativo inicia em 100ms e cresce com backoff sem busy wait."""
    import utils_delegacao
    monkeypatch.setattr(utils_delegacao, "CACHE_DIR", tmp_path)
    # Desativa watchdog no teste para inspecionar intervalos do sleep
    monkeypatch.setattr(utils_delegacao, "_WATCHDOG_DISPONIVEL", False)

    sleeps_registrados = []
    def fake_sleep(duracao):
        sleeps_registrados.append(duracao)

    monkeypatch.setattr(utils_delegacao.time, "sleep", fake_sleep)

    # Simula arquivo aparecendo na 3ª verificação
    tentativas = {"count": 0}
    caminho = tmp_path / "_llm_response_req_backoff.json"

    original_exists = utils_delegacao.Path.exists
    def fake_exists(self):
        if self.name == "_llm_response_req_backoff.json":
            tentativas["count"] += 1
            if tentativas["count"] >= 3:
                if not original_exists(caminho):
                    caminho.write_text(json.dumps({
                        "conteudo": "ok",
                        "tokens_consumidos": 10
                    }), encoding="utf-8")
                return True
            return False
        return original_exists(self)

    monkeypatch.setattr(utils_delegacao.Path, "exists", fake_exists)

    res = utils_delegacao.RequisicaoLLMDelegada.aguardar_resposta(
        "req_backoff",
        timeout=5,
        intervalo_inicial=0.1,
        fator_backoff=2.0
    )

    assert res is not None
    assert res["conteudo"] == "ok"
    assert len(sleeps_registrados) == 2
    # 1º sleep: 0.1s (100ms), 2º sleep: 0.2s (200ms)
    assert abs(sleeps_registrados[0] - 0.1) < 0.01
    assert abs(sleeps_registrados[1] - 0.2) < 0.01


def test_aguardar_resposta_event_driven_com_criacao_assincrona(tmp_path, monkeypatch):
    """Testa que criação assíncrona do arquivo acorda a espera rapidamente."""
    import utils_delegacao
    import threading
    import time

    monkeypatch.setattr(utils_delegacao, "CACHE_DIR", tmp_path)

    id_req = "async_req_1"
    caminho = tmp_path / f"_llm_response_{id_req}.json"

    def escritor_tardio():
        time.sleep(0.05)  # Escreve em 50ms
        caminho.write_text(json.dumps({
            "conteudo": "resposta assincrona recebida",
            "tokens_consumidos": 15
        }), encoding="utf-8")

    t = threading.Thread(target=escritor_tardio)
    t.start()

    t0 = time.time()
    res = utils_delegacao.RequisicaoLLMDelegada.aguardar_resposta(id_req, timeout=3)
    duracao = time.time() - t0
    t.join()

    assert res is not None
    assert res["conteudo"] == "resposta assincrona recebida"
    assert duracao < 1.0  # Muito antes do timeout de 3s


def test_solicitar_llm_modo_delegado_timeout_fallback_limpo_com_excecao(monkeypatch):
    """Timeout com fallback headless que levanta LLMNaoConfiguradoException trata limpo sem crash."""
    import utils_delegacao
    from utils_delegacao import LLMNaoConfiguradoException

    monkeypatch.setattr(utils_delegacao.RequisicaoLLMDelegada, 'aguardar_resposta', lambda *a, **kw: None)
    monkeypatch.setenv('LLM_MODEL', 'modelo-invalido')

    def falha_headless(*a, **kw):
        raise LLMNaoConfiguradoException("Credenciais ausentes", "detalhes tecnicos")

    monkeypatch.setattr(utils_delegacao, 'solicitar_llm_modo_headless', falha_headless)

    res = utils_delegacao.solicitar_llm_modo_delegado(
        prompt="Gerar teste", contexto="Phase 08", fase="phase_08", timeout=1
    )

    # Não deve crashar; retorna None limpamente
    assert res is None


def test_solicitar_llm_modo_delegado_timeout_fallback_limpo_com_erro_generico(monkeypatch):
    """Timeout com fallback headless que levanta erro genérico não quebra a execução."""
    import utils_delegacao

    monkeypatch.setattr(utils_delegacao.RequisicaoLLMDelegada, 'aguardar_resposta', lambda *a, **kw: None)
    monkeypatch.setenv('LLM_MODEL', 'modelo-invalido')

    def erro_generico(*a, **kw):
        raise RuntimeError("Conexão recusada pela API")

    monkeypatch.setattr(utils_delegacao, 'solicitar_llm_modo_headless', erro_generico)

    res = utils_delegacao.solicitar_llm_modo_delegado(
        prompt="Gerar teste", contexto="Phase 08", fase="phase_08", timeout=1
    )

    assert res is None

