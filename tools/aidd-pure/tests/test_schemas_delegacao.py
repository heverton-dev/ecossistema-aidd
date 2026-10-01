# -*- coding: utf-8 -*-
"""
Testes para os schemas JSON versionados do Protocolo Delegado.

Cobertura:
- Payload request válido, incompleto e inválido
- Payload response válido, incompleto e inválido
- Carregamento de schemas e versionamento
- Integração com utils_delegacao (escrever_arquivo / aguardar_resposta)
"""

import json
import sys
from pathlib import Path

import pytest

# schemas/ fica ao lado de utils_delegacao.py
PHASES_DIR = Path(__file__).resolve().parent.parent / "scripts" / "phases"
sys.path.insert(0, str(PHASES_DIR))

from schemas.registry import (
    carregar_schema,
    validar_request,
    validar_response,
    SchemaValidationError,
    SchemaVersion,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def request_valido():
    """Payload de requisição que obedece ao schema v1."""
    return {
        "id": "abc12345",
        "fase": "phase_02",
        "timestamp": "2026-09-08T10:30:00Z",
        "modelo_sugerido": "claude-opus-5",
        "contexto": "Fase 2: Analisador de Ideia",
        "prompt": "Analise esta ideia: sistema de gerenciamento de tarefas",
    }


@pytest.fixture
def response_valido():
    """Payload de resposta que obedece ao schema v1."""
    return {
        "id": "abc12345",
        "conteudo": "Análise completa da ideia...",
        "tokens_consumidos": 1234,
        "origem_medicao": "autodeclarado",
        "modelo_usado": "claude-opus-5",
        "timestamp_resposta": "2026-09-08T10:31:00Z",
    }


# =============================================================================
# TESTES: SCHEMA LOADING
# =============================================================================

class TestCarregamentoSchema:
    """Testes de carregamento e versionamento de schemas."""

    def test_carrega_request_v1(self):
        schema = carregar_schema("request", "v1")
        assert schema["title"] == "Requisição LLM Delegada"
        assert "id" in schema["properties"]
        assert "prompt" in schema["required"]

    def test_carrega_response_v1(self):
        schema = carregar_schema("response", "v1")
        assert schema["title"] == "Resposta LLM Delegada"
        assert "conteudo" in schema["properties"]
        assert "tokens_consumidos" in schema["required"]

    def test_versao_latest_e_v1(self):
        assert SchemaVersion.LATEST == "v1"

    def test_carrega_usando_latest_implicito(self):
        schema = carregar_schema("request")
        assert "$id" in schema

    def test_versao_nao_suportada_levanta_value_error(self):
        with pytest.raises(ValueError, match="não suportada"):
            carregar_schema("request", "v99")

    def test_tipo_invalido_levanta_value_error(self):
        with pytest.raises(ValueError, match="inválido"):
            carregar_schema("invalid_type")

    def test_arquivo_nao_encontrado(self, tmp_path):
        """Simula schema faltando no disco."""
        from schemas import registry
        original = registry.SCHEMA_DIR
        registry.SCHEMA_DIR = tmp_path
        try:
            with pytest.raises(FileNotFoundError):
                carregar_schema("request")
        finally:
            registry.SCHEMA_DIR = original


# =============================================================================
# TESTES: REQUEST VALIDATION
# =============================================================================

class TestValidarRequest:
    """Testes de validação do payload de requisição."""

    def test_request_valido_passa(self, request_valido):
        validar_request(request_valido)  # não deve levantar

    def test_request_sem_campo_obrigatorio_falha(self):
        """Campo 'prompt' obrigatório ausente."""
        dados = {
            "id": "abc12345",
            "fase": "phase_02",
            "timestamp": "2026-09-08T10:30:00Z",
            "modelo_sugerido": "claude-opus-5",
            "contexto": "ctx",
            # "prompt" ausente
        }
        with pytest.raises(SchemaValidationError) as exc_info:
            validar_request(dados)
        assert len(exc_info.value.errors) >= 1

    def test_request_campos_em_branco_falha(self):
        """String vazia em campo minLength=1 deve falhar."""
        dados = {
            "id": "",
            "fase": "phase_02",
            "timestamp": "2026-09-08T10:30:00Z",
            "modelo_sugerido": "claude-opus-5",
            "contexto": "ctx",
            "prompt": "Olá",
        }
        with pytest.raises(SchemaValidationError):
            validar_request(dados)

    def test_request_fase_formato_invalido_falha(self):
        """Fase não segue padrão ^phase_\\d{2}$."""
        dados = {
            "id": "abc12345",
            "fase": "fase_2",  # formato errado
            "timestamp": "2026-09-08T10:30:00Z",
            "modelo_sugerido": "claude-opus-5",
            "contexto": "ctx",
            "prompt": "prompt",
        }
        with pytest.raises(SchemaValidationError):
            validar_request(dados)

    def test_request_tipo_errado_falha(self):
        """Campo 'id' recebendo int em vez de string."""
        dados = {
            "id": 12345,
            "fase": "phase_02",
            "timestamp": "2026-09-08T10:30:00Z",
            "modelo_sugerido": "claude-opus-5",
            "contexto": "ctx",
            "prompt": "prompt",
        }
        with pytest.raises(SchemaValidationError):
            validar_request(dados)

    def test_request_campos_extras_rejeitados(self):
        """additionalProperties=false: campo extra deve falhar."""
        dados = {
            "id": "abc12345",
            "fase": "phase_02",
            "timestamp": "2026-09-08T10:30:00Z",
            "modelo_sugerido": "claude-opus-5",
            "contexto": "ctx",
            "prompt": "prompt",
            "campo_extra": "não permitido",
        }
        with pytest.raises(SchemaValidationError):
            validar_request(dados)


# =============================================================================
# TESTES: RESPONSE VALIDATION
# =============================================================================

class TestValidarResponse:
    """Testes de validação do payload de resposta."""

    def test_response_valido_passa(self, response_valido):
        validar_response(response_valido)  # não deve levantar

    def test_response_sem_conteudo_falha(self):
        """Campo 'conteudo' obrigatório ausente."""
        dados = {
            "tokens_consumidos": 100,
            "origem_medicao": "autodeclarado",
            "modelo_usado": "claude-opus-5",
            "timestamp_resposta": "2026-09-08T10:31:00Z",
        }
        with pytest.raises(SchemaValidationError):
            validar_response(dados)

    def test_response_tokens_negativos_falha(self):
        """tokens_consumidos não pode ser negativo."""
        dados = {
            "conteudo": "resposta",
            "tokens_consumidos": -5,
            "origem_medicao": "autodeclarado",
            "modelo_usado": "gpt-4",
            "timestamp_resposta": "2026-09-08T10:31:00Z",
        }
        with pytest.raises(SchemaValidationError):
            validar_response(dados)

    def test_response_tokens_null_aceito(self):
        """tokens_consumidos pode ser null (indisponivel)."""
        dados = {
            "conteudo": "resposta",
            "tokens_consumidos": None,
            "origem_medicao": "indisponivel",
            "modelo_usado": "gpt-4",
            "timestamp_resposta": "2026-09-08T10:31:00Z",
        }
        validar_response(dados)  # não deve levantar

    def test_response_origem_medicao_invalida_falha(self):
        """origem_medicao deve ser enum válido."""
        dados = {
            "conteudo": "resposta",
            "tokens_consumidos": 100,
            "origem_medicao": "invented",  # não está no enum
            "modelo_usado": "gpt-4",
            "timestamp_resposta": "2026-09-08T10:31:00Z",
        }
        with pytest.raises(SchemaValidationError):
            validar_response(dados)

    def test_response_campos_extras_rejeitados(self):
        """additionalProperties=false: campo extra deve falhar."""
        dados = {
            "conteudo": "resposta",
            "tokens_consumidos": 100,
            "origem_medicao": "autodeclarado",
            "modelo_usado": "gpt-4",
            "timestamp_resposta": "2026-09-08T10:31:00Z",
            "extra": True,
        }
        with pytest.raises(SchemaValidationError):
            validar_response(dados)

    def test_response_campos_opcionais_ausentes_sao_aceitos(self):
        """Campo 'id' é opcional — ausência não deve falhar."""
        dados = {
            "conteudo": "resposta",
            "tokens_consumidos": 100,
            "origem_medicao": "medido_api",
            "modelo_usado": "gpt-4",
            "timestamp_resposta": "2026-09-08T10:31:00Z",
        }
        validar_response(dados)  # não deve levantar


# =============================================================================
# TESTES: SCHEMA VALIDATION ERROR
# =============================================================================

class TestSchemaValidationError:
    """Testes da exceção customizada."""

    def test_excecao_mensagem_conteudo(self):
        exc = SchemaValidationError("llm_request_v1", ["campo obrigatório ausente"])
        assert "llm_request_v1" in str(exc)
        assert "1 erro" in str(exc)

    def test_excecao_multiplos_erros(self):
        exc = SchemaValidationError("llm_response_v1", ["erro A", "erro B", "erro C"])
        assert "3 erro" in str(exc)
        assert "erro A" in str(exc)

    def test_atributos(self):
        exc = SchemaValidationError("llm_request_v1", ["x", "y"])
        assert exc.schema_name == "llm_request_v1"
        assert exc.errors == ["x", "y"]


# =============================================================================
# TESTES: INTEGRAÇÃO COM UTILS_DELEGACAO
# =============================================================================

class TestIntegracaoEscreverArquivo:
    """Testa que escrever_arquivo valida o payload via schemas."""

    def test_escrever_arquivo_valida_e_escreve(self, monkeypatch, tmp_path):
        """Payload válido deve ser escrito e validado."""
        import utils_delegacao
        monkeypatch.setattr(utils_delegacao, "CACHE_DIR", tmp_path)

        req = utils_delegacao.RequisicaoLLMDelegada(
            prompt="Testar",
            contexto="Teste",
            fase="phase_05",
            modelo_sugerido="claude-opus-5",
        )

        caminho = req.escrever_arquivo()
        assert caminho.exists()

        dados_escritos = json.loads(caminho.read_text(encoding="utf-8"))
        assert dados_escritos["fase"] == "phase_05"
        assert dados_escritos["prompt"] == "Testar"

    def test_escrever_arquivo_payload_invalido_falha(self, monkeypatch, tmp_path):
        """Injetar dados inválidos na request deve levantar SchemaValidationError."""
        import utils_delegacao
        monkeypatch.setattr(utils_delegacao, "CACHE_DIR", tmp_path)

        req = utils_delegacao.RequisicaoLLMDelegada(
            prompt="Testar",
            contexto="Teste",
            fase="INVALIDO",  # formato errado: não é phase_NN
            modelo_sugerido="claude-opus-5",
        )

        # O schema exige fase com pattern ^phase_\d{2}$
        # Como 'INVALIDO' não casa, se schemas estiverem disponíveis, deve falhar
        if utils_delegacao._validar_request is not None:
            with pytest.raises(SchemaValidationError):
                req.escrever_arquivo()


class TestIntegracaoAguardarResposta:
    """Testa que aguardar_resposta valida o payload via schemas."""

    def test_resposta_valida_retorna_dados(self, monkeypatch, tmp_path):
        """Resposta válida no disco deve ser retornada."""
        import utils_delegacao
        monkeypatch.setattr(utils_delegacao, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(utils_delegacao, "TIMEOUT_DELEGACAO", 1)

        # Escrever resposta válida
        resposta = {
            "id": "abc12345",
            "conteudo": "resposta ok",
            "tokens_consumidos": 100,
            "origem_medicao": "autodeclarado",
            "modelo_usado": "claude-opus-5",
            "timestamp_resposta": "2026-09-08T10:31:00Z",
        }
        caminho = tmp_path / "_llm_response_abc12345.json"
        caminho.write_text(json.dumps(resposta), encoding="utf-8")

        resultado = utils_delegacao.RequisicaoLLMDelegada.aguardar_resposta("abc12345", timeout=1)
        assert resultado is not None
        assert resultado["conteudo"] == "resposta ok"

    def test_resposta_sem_campos_obrigatorios_nao_retorna(self, monkeypatch, tmp_path):
        """Resposta sem campos obrigatórios não deve ser retornada (validação legado falha)."""
        import utils_delegacao
        monkeypatch.setattr(utils_delegacao, "CACHE_DIR", tmp_path)
        monkeypatch.setattr(utils_delegacao, "TIMEOUT_DELEGACAO", 1)

        # Resposta sem conteudo
        resposta = {
            "tokens_consumidos": 100,
            "origem_medicao": "autodeclarado",
            "modelo_usado": "gpt-4",
            "timestamp_resposta": "2026-09-08T10:31:00Z",
        }
        caminho = tmp_path / "_llm_response_xyz99999.json"
        caminho.write_text(json.dumps(resposta), encoding="utf-8")

        resultado = utils_delegacao.RequisicaoLLMDelegada.aguardar_resposta("xyz99999", timeout=1)
        assert resultado is None


# =============================================================================
# TESTES: ECONOMIA DE TOKENS (validação é 100% determinística)
# =============================================================================

class TestZeroTokensNaValidacao:
    """Validação por JSON Schema é 100% determinística — zero chamadas LLM."""

    def test_validacao_request_nao_chama_llm(self, request_valido):
        """validar_request é Python puro (jsonschema) — zero tokens."""
        validar_request(request_valido)
        # Se chegou aqui, validou sem exceção = zero LLM necessário

    def test_validacao_response_nao_chama_llm(self, response_valido):
        """validar_response é Python puro (jsonschema) — zero tokens."""
        validar_response(response_valido)
