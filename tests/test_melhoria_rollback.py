# -*- coding: utf-8 -*-
"""
Teste de Critério de Rejeição, Limpeza e Rollback (Ticket 7 / D14).
Valida:
1. Rejeição e limpeza imediata em caso de erro no meio da análise (ex. parser crash).
2. Se arquivos intermediários (.tmp, .partial, rascunhos) forem gerados antes da falha,
   o mecanismo DEVE expurgá-los completamente (zero rastro residual).
3. Reversão completa (rollback) de quaisquer alterações em arquivos existentes ou variáveis de ambiente.
4. Sucesso na execução preserva o artefato final e limpa intermediários transitórios.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_SCRIPTS = ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"
if str(SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SKILL_SCRIPTS))

import rollback
from rollback import (
    GerenciadorRollback,
    ParserCrashSimuladoError,
    executar_com_rollback,
    limpar_artefatos_residuais,
)


def test_parser_crash_no_meio_da_analise_exclui_arquivos_intermediarios(tmp_path):
    """
    TDD Red->Green:
    Injeta um erro no meio da análise (parser crash).
    Garante que arquivos parciais/intermediários criados antes do crash
    sejam sumariamente deletados do disco pelo GerenciadorRollback.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    docs_melhorias = repo / "docs" / "melhorias"
    docs_melhorias.mkdir(parents=True)

    arquivo_parcial = docs_melhorias / "analise_parcial.tmp"
    arquivo_draft = docs_melhorias / "rascunho_analise.partial"

    with pytest.raises(ParserCrashSimuladoError):
        with GerenciadorRollback(repo_root=repo) as rb:
            # Etapa 1: Início da análise escreve arquivos intermediários
            arquivo_parcial.write_text("conteudo parcial preliminar", encoding="utf-8")
            arquivo_draft.write_text("rascunho em progresso", encoding="utf-8")
            rb.registrar_temporario(arquivo_parcial)
            rb.registrar_temporario(arquivo_draft)

            assert arquivo_parcial.exists()
            assert arquivo_draft.exists()

            # Etapa 2: Injeção de erro no meio da análise (parser crash)
            raise ParserCrashSimuladoError("Crash crítico no parser JSON durante a análise sintática")

    # Verificação pós-crash: zero rastro residual de arquivos intermediários
    assert not arquivo_parcial.exists(), "Arquivo intermediário .tmp ainda permaneceu em disco após crash!"
    assert not arquivo_draft.exists(), "Arquivo parcial .partial ainda permaneceu em disco após crash!"


def test_rollback_reverte_alteracoes_em_arquivos_existentes_apos_falha(tmp_path):
    """
    Garante que se um arquivo existente no repositório for alterado durante a análise
    e ocorrer uma falha / crash subsequente, o arquivo seja revertido ao conteúdo original (rollback).
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    docs = repo / "docs"
    docs.mkdir()

    arquivo_existente = docs / "indice_melhorias.json"
    conteudo_original = '{"melhorias": ["melhoria-1"]}'
    arquivo_existente.write_text(conteudo_original, encoding="utf-8")

    with pytest.raises(RuntimeError):
        with GerenciadorRollback(repo_root=repo) as rb:
            # Faz snapshot antes de modificar
            rb.salvar_snapshot(arquivo_existente)

            # Modifica arquivo existente
            arquivo_existente.write_text('{"melhorias": ["melhoria-1", "corrompida"]}', encoding="utf-8")
            assert "corrompida" in arquivo_existente.read_text(encoding="utf-8")

            # Falha fatal
            raise RuntimeError("Falha não recuperável no pipeline analítico")

    # O arquivo deve ter sido revertido ao conteúdo original idêntico
    assert arquivo_existente.exists()
    assert arquivo_existente.read_text(encoding="utf-8") == conteudo_original


def test_rollback_reverte_variaveis_de_ambiente(tmp_path):
    """
    Garante que alterações em variáveis de ambiente efetuadas durante a execução
    sejam revertidas ao estado prévio caso ocorra falha.
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    chave_teste = "AIDD_TEST_ENV_VAR"
    os.environ[chave_teste] = "VALOR_INICIAL"

    try:
        with pytest.raises(ValueError):
            with GerenciadorRollback(repo_root=repo) as rb:
                rb.definir_env(chave_teste, "VALOR_TRANSITORIO")
                assert os.environ[chave_teste] == "VALOR_TRANSITORIO"
                raise ValueError("Erro que dispara rollback de ambiente")

        assert os.environ[chave_teste] == "VALOR_INICIAL"
    finally:
        os.environ.pop(chave_teste, None)


def test_limpeza_automatica_de_padroes_intermediarios_sem_registro_explicito(tmp_path):
    """
    Garante que arquivos intermediários criados no diretório de trabalho com extensões
    típicas de temporários (.tmp, .partial, .draft, .part) sejam detectados e expurgados
    mesmo se o desenvolvedor esquecer de registrá-los explicitamente.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    docs_melhorias = repo / "docs" / "melhorias"
    docs_melhorias.mkdir(parents=True)

    f1 = docs_melhorias / "temp1.tmp"
    f2 = docs_melhorias / "item.partial"
    f3 = docs_melhorias / "rascunho.draft"

    with pytest.raises(Exception):
        with GerenciadorRollback(repo_root=repo, varredura_automatica=True) as rb:
            f1.write_text("temp", encoding="utf-8")
            f2.write_text("partial", encoding="utf-8")
            f3.write_text("draft", encoding="utf-8")
            raise Exception("Falha simulada com varredura automática")

    assert not f1.exists()
    assert not f2.exists()
    assert not f3.exists()


def test_execucao_bem_sucedida_consolida_artefatos_e_descarta_apenas_temporarios(tmp_path):
    """
    Em execução com sucesso (sem exceção e rb.commit()), artefatos finais são preservados
    enquanto arquivos intermediários transitórios registrados são descartados.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    docs_melhorias = repo / "docs" / "melhorias"
    docs_melhorias.mkdir(parents=True)

    temp_buff = docs_melhorias / "buffer.tmp"
    final_json = docs_melhorias / "relatorio_final.json"

    with GerenciadorRollback(repo_root=repo) as rb:
        temp_buff.write_text("dados temporarios do calculo", encoding="utf-8")
        rb.registrar_temporario(temp_buff)

        final_json.write_text('{"relatorio": {"pedido": "otimizacao", "status": "ok"}}', encoding="utf-8")
        rb.registrar_artefato_final(final_json)

        rb.commit()

    # O temporário deve sumir, o final deve ficar
    assert not temp_buff.exists()
    assert final_json.exists()
    assert "otimizacao" in final_json.read_text(encoding="utf-8")


def test_executar_com_rollback_helper_retorna_codigo_saida_e_limpa_em_erro(tmp_path):
    """
    Testa helper de nível superior executar_com_rollback que encapsula funções retornando
    código de saída não-zero e limpando arquivos intermediários.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    arquivo_parcial = repo / "intermediario.tmp"

    def funcao_falha(rb: GerenciadorRollback) -> int:
        arquivo_parcial.write_text("intermediario que deve sumir", encoding="utf-8")
        rb.registrar_temporario(arquivo_parcial)
        # Retorna código de erro não-zero
        return 1

    codigo = executar_com_rollback(funcao_falha, repo_root=repo)
    assert codigo == 1
    assert not arquivo_parcial.exists()
