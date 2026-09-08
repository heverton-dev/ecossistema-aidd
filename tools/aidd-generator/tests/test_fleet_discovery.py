#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes: Fleet Discovery (Auto-Descoberta de Frota)
"""

import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts' / 'phases'))

from utils_fleet_discovery import (
    AgenteDetectado,
    FleetStatus,
    detectar_agentes_instalados,
    detectar_via_ambiente,
    rotear_por_especialidade,
    resolver_fleet,
    obter_modelo_para_fleet,
    fleet_status_para_log,
    persistir_fleet_status,
    AGENTES_CONHECIDOS,
    _encontrar_executavel_windows,
)


# =============================================================================
# Testes: Data Classes
# =============================================================================

class TestAgenteDetectado:
    def test_to_dict(self):
        a = AgenteDetectado(
            nome='claude', comando='claude', caminho='/usr/bin/claude',
            especialidades=['codigo'], prioridade=1, descricao='Claude Code',
        )
        d = a.to_dict()
        assert d['nome'] == 'claude'
        assert d['comando'] == 'claude'
        assert d['ativo'] is True


class TestFleetStatus:
    def test_inicializacao(self):
        f = FleetStatus()
        assert f.modo == 'desconhecido'
        assert len(f.agentes_detectados) == 0

    def test_to_dict(self):
        f = FleetStatus(
            agentes_detectados=[
                AgenteDetectado('claude', 'claude', '/bin/claude', ['codigo'], 1, 'Claude')
            ],
            agente_default='claude',
            modo='multi-agente',
        )
        d = f.to_dict()
        assert d['total_detectados'] == 1
        assert d['modo'] == 'multi-agente'


# =============================================================================
# Testes: Auto-Descoberta
# =============================================================================

class TestDetectarAgentes:
    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Linux')
    def test_detectar_com_claude(self, mock_platform, mock_which):
        def which_side_effect(cmd):
            if cmd == 'claude':
                return '/usr/local/bin/claude'
            return None
        mock_which.side_effect = which_side_effect

        agentes = detectar_agentes_instalados()
        assert len(agentes) == 1
        assert agentes[0].nome == 'claude'

    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Linux')
    def test_detectar_multiplos(self, mock_platform, mock_which):
        def which_side_effect(cmd):
            paths = {'claude': '/bin/claude', 'codex': '/bin/codex'}
            return paths.get(cmd)
        mock_which.side_effect = which_side_effect

        agentes = detectar_agentes_instalados()
        assert len(agentes) == 2
        # Ordenados por prioridade
        assert agentes[0].nome == 'claude'
        assert agentes[1].nome == 'codex'

    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Linux')
    def test_detectar_nenhum(self, mock_platform, mock_which):
        mock_which.return_value = None
        agentes = detectar_agentes_instalados()
        assert len(agentes) == 0

    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Linux')
    def test_detectar_kiro_e_cursor(self, mock_platform, mock_which):
        paths = {'claude': '/bin/claude', 'kiro': '/bin/kiro', 'cursor': '/bin/cursor'}
        mock_which.side_effect = lambda cmd: paths.get(cmd)

        agentes = detectar_agentes_instalados()
        nomes = [a.nome for a in agentes]
        assert 'kiro' in nomes
        assert 'cursor' in nomes

    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Linux')
    def test_detectar_hermes(self, mock_platform, mock_which):
        paths = {'claude': '/bin/claude', 'hermes': '/bin/hermes'}
        mock_which.side_effect = lambda cmd: paths.get(cmd)

        agentes = detectar_agentes_instalados()
        nomes = [a.nome for a in agentes]
        assert 'hermes' in nomes

    def test_novos_runtimes_no_registro(self):
        assert 'kiro' in AGENTES_CONHECIDOS
        assert 'cursor' in AGENTES_CONHECIDOS
        assert 'hermes' in AGENTES_CONHECIDOS


class TestExecutavelWindows:
    @patch('utils_fleet_discovery.shutil.which')
    def test_which_encontra_direto(self, mock_which):
        mock_which.return_value = '/usr/bin/ferramenta'
        assert _encontrar_executavel_windows('ferramenta') == '/usr/bin/ferramenta'

    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Linux')
    def test_nao_windows_retorna_none(self, mock_platform, mock_which):
        mock_which.return_value = None
        assert _encontrar_executavel_windows('ferramenta') is None

    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Windows')
    def test_extensao_cmd_fallback(self, mock_platform, mock_which, tmp_path):
        fake = tmp_path / 'kiro.cmd'
        fake.write_text('fake', encoding='utf-8')
        mock_which.return_value = None
        with patch.dict(os.environ, {'PATH': str(tmp_path)}, clear=True):
            assert _encontrar_executavel_windows('kiro') == str(fake)

    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Windows')
    def test_extensao_bat_fallback(self, mock_platform, mock_which, tmp_path):
        fake = tmp_path / 'cursor.bat'
        fake.write_text('fake', encoding='utf-8')
        mock_which.return_value = None
        with patch.dict(os.environ, {'PATH': str(tmp_path)}, clear=True):
            assert _encontrar_executavel_windows('cursor') == str(fake)

    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Windows')
    def test_extensao_ps1_fallback(self, mock_platform, mock_which, tmp_path):
        fake = tmp_path / 'delegador.ps1'
        fake.write_text('fake', encoding='utf-8')
        mock_which.return_value = None
        with patch.dict(os.environ, {'PATH': '/nonexistent'}, clear=True):
            with patch('utils_fleet_discovery.os.path.expandvars', return_value=str(tmp_path)):
                assert _encontrar_executavel_windows('delegador') == str(fake)

    @patch('utils_fleet_discovery.shutil.which')
    @patch('utils_fleet_discovery.platform.system', return_value='Windows')
    def test_sem_correspondencia_retorna_none(self, mock_platform, mock_which, tmp_path):
        mock_which.return_value = None
        with patch.dict(os.environ, {'PATH': str(tmp_path)}, clear=True):
            assert _encontrar_executavel_windows('inexistente') is None


class TestDetectarViaAmbiente:
    def test_claudecode(self):
        with patch.dict(os.environ, {'CLAUDECODE': '1'}):
            detectados = detectar_via_ambiente()
            assert 'claude' in detectados

    def test_aidd_harness_name(self):
        with patch.dict(os.environ, {'AIDD_HARNESS_NAME': 'Antigravity'}):
            detectados = detectar_via_ambiente()
            assert 'antigravity' in detectados

    def test_nenhum(self):
        harness_keys = {'CLAUDECODE', 'MIMOCODE', 'MIMO_SESSION', 'MIMO_WORKSPACE',
                        'OPENCODE', 'OPENCODE_SESSION', 'ANTIGRAVITY_CLI', 'ANTIGRAVITY_AGENT',
                        'AGY_SESSION', 'ORCA_WORKSPACE', 'AIDD_HARNESS_NAME'}
        env_limpo = {k: v for k, v in os.environ.items() if k not in harness_keys}
        with patch.dict(os.environ, env_limpo, clear=True):
            detectados = detectar_via_ambiente()
            assert len(detectados) == 0


# =============================================================================
# Testes: Roteamento
# =============================================================================

class TestRoteamento:
    def _make_agentes(self):
        return [
            AgenteDetectado('claude', 'claude', '/bin/claude',
                          ['arquitetura', 'analise', 'design', 'codigo'], 1, 'Claude'),
            AgenteDetectado('codex', 'codex', '/bin/codex',
                          ['codigo', 'database', 'testes'], 2, 'Codex'),
        ]

    def test_rotear_arquitetura(self):
        agentes = self._make_agentes()
        a = rotear_por_especialidade('arquitetura', agentes)
        assert a.nome == 'claude'

    def test_rotear_database(self):
        agentes = self._make_agentes()
        a = rotear_por_especialidade('database', agentes)
        assert a.nome == 'codex'

    def test_rotear_codigo_prioridade(self):
        agentes = self._make_agentes()
        a = rotear_por_especialidade('codigo', agentes)
        assert a.nome == 'claude'  # Prioridade 1

    def test_rotear_lista_vazia(self):
        a = rotear_por_especialidade('codigo', [])
        assert a is None

    def test_rotear_kiro_unico(self):
        kiro = AgenteDetectado('kiro', 'kiro', '/bin/kiro',
                               ['arquitetura', 'codigo', 'analise', 'testes', 'design'], 2, 'Kiro CLI')
        a = rotear_por_especialidade('arquitetura', [kiro])
        assert a.nome == 'kiro'

    def test_rotear_especialidade_desconhecida(self):
        agentes = self._make_agentes()
        a = rotear_por_especialidade('especialidade_inexistente', agentes)
        assert a is not None  # Fallback para o de maior prioridade
        assert a.nome == 'claude'


# =============================================================================
# Testes: Resolver Fleet
# =============================================================================

class TestResolverFleet:
    @patch('utils_fleet_discovery.detectar_agentes_instalados')
    @patch('utils_fleet_discovery.detectar_via_ambiente')
    def test_multi_agente(self, mock_amb, mock_inst):
        mock_inst.return_value = [
            AgenteDetectado('claude', 'claude', '/bin/claude', ['codigo'], 1, 'Claude'),
            AgenteDetectado('codex', 'codex', '/bin/codex', ['codigo'], 2, 'Codex'),
        ]
        mock_amb.return_value = ['claude']

        fleet = resolver_fleet()
        assert fleet.modo == 'multi-agente'
        assert fleet.agente_default == 'claude'

    @patch('utils_fleet_discovery.detectar_agentes_instalados')
    @patch('utils_fleet_discovery.detectar_via_ambiente')
    def test_agente_unico(self, mock_amb, mock_inst):
        mock_inst.return_value = [
            AgenteDetectado('claude', 'claude', '/bin/claude', ['codigo'], 1, 'Claude'),
        ]
        mock_amb.return_value = []

        fleet = resolver_fleet()
        assert fleet.modo == 'agente-unico'
        assert fleet.agente_default == 'claude'

    @patch('utils_fleet_discovery.detectar_agentes_instalados')
    @patch('utils_fleet_discovery.detectar_via_ambiente')
    def test_nenhum_agente(self, mock_amb, mock_inst):
        mock_inst.return_value = []
        mock_amb.return_value = []

        fleet = resolver_fleet()
        assert fleet.modo == 'nenhum'
        assert fleet.agente_default is None

    @patch('utils_fleet_discovery.detectar_agentes_instalados')
    @patch('utils_fleet_discovery.detectar_via_ambiente')
    def test_override(self, mock_amb, mock_inst):
        mock_inst.return_value = [
            AgenteDetectado('claude', 'claude', '/bin/claude', ['codigo'], 1, 'Claude'),
            AgenteDetectado('codex', 'codex', '/bin/codex', ['codigo'], 2, 'Codex'),
        ]
        mock_amb.return_value = []

        fleet = resolver_fleet(override_harness='codex')
        assert fleet.modo == 'agente-unico'
        assert fleet.override_config == 'codex'

    @patch('utils_fleet_discovery.detectar_agentes_instalados')
    @patch('utils_fleet_discovery.detectar_via_ambiente')
    def test_override_nao_encontrado(self, mock_amb, mock_inst):
        mock_inst.return_value = [
            AgenteDetectado('claude', 'claude', '/bin/claude', ['codigo'], 1, 'Claude'),
        ]
        mock_amb.return_value = []

        fleet = resolver_fleet(override_harness='inexistente')
        assert fleet.modo == 'nenhum'


# =============================================================================
# Testes: Modelo para Fleet
# =============================================================================

class TestObterModelo:
    def test_nenhum_retorna_none(self):
        fleet = FleetStatus(modo='nenhum')
        assert obter_modelo_para_fleet(fleet, 'phase_08') is None

    def test_agente_unico_retorna_default(self):
        fleet = FleetStatus(modo='agente-unico', agente_default='claude')
        assert obter_modelo_para_fleet(fleet, 'phase_08') == 'claude'

    def test_multi_agente_roteia(self):
        fleet = FleetStatus(
            modo='multi-agente',
            agente_default='claude',
            agentes_detectados=[
                AgenteDetectado('claude', 'claude', '/bin/claude',
                              ['arquitetura', 'analise', 'design', 'codigo'], 1, 'Claude'),
                AgenteDetectado('codex', 'codex', '/bin/codex',
                              ['codigo', 'database', 'testes'], 2, 'Codex'),
            ],
        )
        assert obter_modelo_para_fleet(fleet, 'phase_08_schema') == 'codex'
        assert obter_modelo_para_fleet(fleet, 'phase_03') == 'claude'


# =============================================================================
# Testes: Log e Persistência
# =============================================================================

class TestLogPersistencia:
    def test_fleet_status_para_log(self):
        fleet = FleetStatus(
            modo='multi-agente',
            agente_default='claude',
            agentes_detectados=[
                AgenteDetectado('claude', 'claude', '/bin/claude', ['codigo'], 1, 'Claude Code'),
            ],
        )
        log = fleet_status_para_log(fleet)
        assert 'multi-agente' in log
        assert 'Claude Code' in log
        assert 'claude' in log

    def test_persistir_fleet_status(self, tmp_path):
        fleet = FleetStatus(modo='agente-unico', agente_default='claude')
        caminho = persistir_fleet_status(fleet, pasta_cache=tmp_path)
        assert caminho.exists()

        dados = json.loads(caminho.read_text(encoding='utf-8'))
        assert dados['modo'] == 'agente-unico'
