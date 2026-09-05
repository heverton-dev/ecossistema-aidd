#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: CLI `scripts/aidd_inject.py` — subcomando explícito e linguagem natural.
"""

import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / 'scripts'
sys.path.insert(0, str(_SCRIPTS_DIR))

import aidd_inject
from scripts.core.injector import injetor as _injetor_mod


@pytest.fixture(autouse=True)
def _isolar_cwd(tmp_path, monkeypatch):
    """Protege o repo real: qualquer chamada que caia no cwd default (--root omitido)
    cai neste diretório temporário, nunca no repositório de verdade.

    Isola também a fonte canônica (`componentes/aidd-generator/...`): desde o
    Prompt Corretivo 2, `injetar()` grava um espelho canônico via
    `_default_ecossistema_root()` (achado do Prompt Corretivo 3) — sem este
    monkeypatch, cada teste desta suíte gravaria de verdade na árvore real do
    monorepo, mesmo usando `--root tmp_path`."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(_injetor_mod, "_default_ecossistema_root", lambda: tmp_path / "_ecossistema_fake_root")


class TestCliInjectExplicito:
    def test_inject_skill_com_sucesso(self, tmp_path, capsys):
        exit_code = aidd_inject.main([
            'inject', 'skill', 'skill-de-teste-cli',
            '--descricao', 'Descricao valida para a skill de teste da CLI.',
            '--root', str(tmp_path),
        ])
        assert exit_code == 0
        assert (tmp_path / 'skills' / 'skill-de-teste-cli' / 'SKILL.md').exists()
        assert (tmp_path / '.claude' / 'skills' / 'skill-de-teste-cli' / 'SKILL.md').exists()
        saida = capsys.readouterr().out
        assert 'Componente injetado' in saida

    def test_inject_com_descricao_ausente_falha_no_argparse(self, tmp_path):
        try:
            aidd_inject.main(['inject', 'skill', 'nome-x', '--root', str(tmp_path)])
            assert False, 'deveria ter levantado SystemExit (argparse --descricao obrigatorio)'
        except SystemExit as exc:
            assert exc.code != 0

    def test_inject_tipo_invalido_falha_no_argparse(self, tmp_path):
        try:
            aidd_inject.main(['inject', 'tipo-invalido', 'nome-x', '--descricao', 'x' * 20, '--root', str(tmp_path)])
            assert False, 'deveria ter levantado SystemExit (choices invalido)'
        except SystemExit as exc:
            assert exc.code != 0

    def test_inject_sem_force_recusa_sobrescrever(self, tmp_path):
        argv = [
            'inject', 'config', 'config-de-teste',
            '--descricao', 'Descricao valida para a config de teste da CLI.',
            '--root', str(tmp_path),
        ]
        assert aidd_inject.main(argv) == 0
        assert aidd_inject.main(argv) == 1  # segunda vez sem --forcar deve falhar

    def test_inject_com_forcar_permite_reescrever(self, tmp_path):
        base_argv = [
            'inject', 'config', 'config-forcada',
            '--descricao', 'Descricao valida para a config forcada da CLI.',
            '--root', str(tmp_path),
        ]
        assert aidd_inject.main(base_argv) == 0
        assert aidd_inject.main(base_argv + ['--forcar']) == 0


class TestCliLinguagemNatural:
    def test_frase_natural_detecta_e_injeta(self, tmp_path):
        exit_code = aidd_inject.main([
            'crie', 'uma', 'skill', 'de', 'auditoria', 'de', 'dependencias', 'via', 'cli',
            '--root', str(tmp_path),
        ])
        assert exit_code == 0
        publicados = list((tmp_path / 'skills').rglob('SKILL.md'))
        assert len(publicados) == 1

    def test_frase_sem_intencao_detectavel_falha_com_mensagem(self, capsys, tmp_path):
        exit_code = aidd_inject.main(['oi', '--root', str(tmp_path)])
        assert exit_code == 1
        saida = capsys.readouterr().out
        assert 'não foi possível' in saida.lower() or 'nao foi possivel' in saida.lower()

    def test_flag_root_e_removida_do_texto_natural(self, tmp_path):
        """Regressão: --root não deve ser interpretado como parte da descrição."""
        outro_root = tmp_path / 'destino-real'
        outro_root.mkdir()
        aidd_inject.main([
            'crie', 'um', 'mcp', 'de', 'verificacao', 'de', 'testes',
            '--root', str(outro_root),
        ])
        assert list(outro_root.rglob('server.py'))
        assert not list(tmp_path.glob('mcps'))  # nao vazou para o cwd/tmp_path pai


class TestCliSemArgumentos:
    def test_sem_argumentos_imprime_ajuda_e_retorna_1(self, capsys):
        exit_code = aidd_inject.main([])
        assert exit_code == 1
        assert 'usage' in capsys.readouterr().out.lower()
