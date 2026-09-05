#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: Injetor Universal de Componentes — contrato, profiles e detector.
"""

from scripts.core.injector.contrato import (
    InjectorRequest,
    ResultadoValidacao,
    TIPOS_VALIDOS,
    validar_request,
)
from scripts.core.injector.detector_camada import detectar_tipo
from scripts.core.injector.profiles_registry import (
    PROFILES,
    ProjetoNaoSuportadoError,
    TipoNaoSuportadoError,
    resolver_rota,
    tipos_suportados,
)


# =============================================================================
# Contrato / Schema
# =============================================================================

class TestValidarRequest:
    def test_payload_valido_e_aceito(self):
        resultado = validar_request({
            "tipo": "skill",
            "nome": "minha-skill-teste",
            "descricao": "Descricao suficientemente longa para passar na validacao.",
        })
        assert resultado.valido is True
        assert resultado.erros == []
        assert isinstance(resultado.request, InjectorRequest)
        assert resultado.request.tipo == "skill"
        assert resultado.request.alvo_projeto == "aidd-generator"

    def test_payload_vazio_e_rejeitado_com_erros_estruturados(self):
        resultado = validar_request({})
        assert resultado.valido is False
        assert len(resultado.erros) >= 3  # tipo, nome, descricao ausentes

    def test_tipo_invalido_e_rejeitado(self):
        resultado = validar_request({
            "tipo": "nao-existe",
            "nome": "nome-valido",
            "descricao": "descricao valida com tamanho suficiente",
        })
        assert resultado.valido is False
        assert any("tipo" in e for e in resultado.erros)

    def test_nome_com_maiusculas_e_rejeitado(self):
        resultado = validar_request({
            "tipo": "skill",
            "nome": "Nome-Invalido",
            "descricao": "descricao valida com tamanho suficiente",
        })
        assert resultado.valido is False

    def test_nome_curto_demais_e_rejeitado(self):
        resultado = validar_request({
            "tipo": "skill",
            "nome": "ab",
            "descricao": "descricao valida com tamanho suficiente",
        })
        assert resultado.valido is False

    def test_descricao_curta_demais_e_rejeitada(self):
        resultado = validar_request({
            "tipo": "skill",
            "nome": "nome-valido",
            "descricao": "curta",
        })
        assert resultado.valido is False

    def test_campo_extra_nao_permitido_e_rejeitado(self):
        resultado = validar_request({
            "tipo": "skill",
            "nome": "nome-valido",
            "descricao": "descricao valida com tamanho suficiente",
            "campo_desconhecido": "x",
        })
        assert resultado.valido is False

    def test_alvo_projeto_invalido_e_rejeitado(self):
        resultado = validar_request({
            "tipo": "skill",
            "nome": "nome-valido",
            "descricao": "descricao valida com tamanho suficiente",
            "alvo_projeto": "projeto-fantasma",
        })
        assert resultado.valido is False

    def test_payload_nao_dict_e_rejeitado(self):
        resultado = validar_request("nao sou um dict")
        assert isinstance(resultado, ResultadoValidacao)
        assert resultado.valido is False


# =============================================================================
# Profiles Registry
# =============================================================================

class TestProfilesRegistry:
    def test_todos_os_tipos_validos_resolvem_para_aidd_generator(self):
        for tipo in TIPOS_VALIDOS:
            rota = resolver_rota("aidd-generator", tipo, "componente-x")
            assert rota.dest
            assert "componente-x" in rota.dest

    def test_skill_tem_mirror_no_claude(self):
        rota = resolver_rota("aidd-generator", "skill", "minha-skill")
        assert rota.dest == "skills/minha-skill/SKILL.md"
        assert ".claude/skills/minha-skill/SKILL.md" in rota.mirrors

    def test_mcp_tem_anchor_harness_compat(self):
        rota = resolver_rota("aidd-generator", "mcp", "meu-mcp")
        assert "HARNESS-COMPAT.json" in rota.anchors

    def test_spec_tem_anchor_plano_execucao(self):
        rota = resolver_rota("aidd-generator", "spec", "minha-spec")
        assert "PLANO-EXECUCAO-ESTRUTURADO.json" in rota.anchors

    def test_projeto_nao_suportado_levanta_erro(self):
        try:
            resolver_rota("aidd-forge", "skill", "x")
            assert False, "deveria ter levantado ProjetoNaoSuportadoError"
        except ProjetoNaoSuportadoError:
            pass

    def test_tipo_nao_suportado_levanta_erro(self):
        try:
            resolver_rota("aidd-generator", "tipo-inexistente", "x")
            assert False, "deveria ter levantado TipoNaoSuportadoError"
        except TipoNaoSuportadoError:
            pass

    def test_tipos_suportados_lista_os_5_tipos(self):
        tipos = tipos_suportados("aidd-generator")
        assert set(tipos) == set(TIPOS_VALIDOS)

    def test_tipos_suportados_none_para_projeto_desconhecido(self):
        assert tipos_suportados("projeto-fantasma") is None

    def test_profile_aidd_generator_existe(self):
        assert "aidd-generator" in PROFILES


# =============================================================================
# Detector de Camada (heuristica + explicito)
# =============================================================================

class TestDetectorCamada:
    def test_tipo_hint_explicito_e_usado_diretamente(self):
        resultado = detectar_tipo("qualquer coisa", tipo_hint="config")
        assert resultado.tipo == "config"
        assert resultado.confianca == 1.0
        assert resultado.origem == "explicito"

    def test_detecta_mcp_por_palavra_chave(self):
        resultado = detectar_tipo("crie um servidor mcp para verificar CVEs")
        assert resultado.tipo == "mcp"
        assert resultado.confianca >= 0.55

    def test_detecta_skill_por_palavra_chave(self):
        resultado = detectar_tipo("preciso de uma skill de auditoria de dependencias")
        assert resultado.tipo == "skill"

    def test_detecta_rule_por_palavra_chave(self):
        resultado = detectar_tipo("adicione uma regra de nao commitar segredos")
        assert resultado.tipo == "rule"

    def test_detecta_spec_por_palavra_chave(self):
        resultado = detectar_tipo("crie uma especificacao tecnica do modulo de pagamentos")
        assert resultado.tipo == "spec"

    def test_detecta_config_por_palavra_chave(self):
        resultado = detectar_tipo("adicione uma configuracao de timeout do pipeline")
        assert resultado.tipo == "config"

    def test_descricao_ambigua_usa_fallback_llm_injetado(self):
        chamadas = []

        def chamar_llm_fake(prompt):
            chamadas.append(prompt)
            return "spec"

        resultado = detectar_tipo(
            "coisa generica sem palavras-chave claras",
            chamar_llm=chamar_llm_fake,
        )
        assert resultado.origem == "llm"
        assert resultado.tipo == "spec"
        assert len(chamadas) == 1

    def test_descricao_sem_nenhuma_palavra_chave_sem_llm_devolve_tipo_none(self):
        resultado = detectar_tipo(
            "coisa generica sem palavras-chave claras",
            chamar_llm=lambda prompt: None,
        )
        assert resultado.tipo is None
        assert resultado.confianca == 0.0
        assert resultado.origem == "heuristica"


# =============================================================================
# Destino Canonico e Raiz do Monorepo
# =============================================================================

class TestCanonicalDestination:
    def test_canonical_root_resolves_to_monorepo_root(self):
        from pathlib import Path
        import scripts.core.injector.injetor as injetor_mod
        injetor_file = Path(injetor_mod.__file__).resolve()
        ecossistema_root = injetor_file.parents[5]
        assert (ecossistema_root / "gates" / "manifesto_harnesses.json").exists(), (
            f"Raiz calculada invalida: {ecossistema_root} (gates/manifesto_harnesses.json nao existe)"
        )
        assert (ecossistema_root / "ecossistema.py").exists()

        dest_canonico = ecossistema_root / injetor_mod.CANONICAL_TEMPLATES["skill"].format(nome="demo")
        assert dest_canonico == ecossistema_root / "componentes" / "aidd-generator" / "skills" / "demo" / "SKILL.md"
        assert "tools/componentes" not in dest_canonico.as_posix()

