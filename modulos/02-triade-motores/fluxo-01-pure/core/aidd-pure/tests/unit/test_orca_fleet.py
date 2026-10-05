# -*- coding: utf-8 -*-
"""
Testes: ORCA Fleet — Detector + Gerador de Inventario + Fallback em Cascata.

Cobre:
- detector.py: deteccao silenciosa de ferramentas e ORCA ADE
- orca_fleet.py: resolucao de frota, fallback, override, roteamento, geracao de JSON
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

# Path setup para importar scripts/core
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'scripts'))

from core.detector import (
    DetectorResultado,
    FerramentaDetectada,
    detectar_ferramentas,
    detectar_orca_ade,
    executar_deteccao_completa,
    obter_sinais_orca,
    FERRAMENTAS_CONHECIDAS,
    ORCA_AMBIENTE_SINAIS,
)
from core.orca_fleet import (
    OrcaFleetStatus,
    gerar_inventory,
    inicializar_frota,
    resolver_frota,
    resolver_para_fase,
    rotear_por_especialidade,
    FASE_ESPECIALIDADE,
    ROTEAMENTO_ESPECIALIDADE,
)


# =============================================================================
# FIXTURES
# =============================================================================

def _make_ferramenta(nome, comando=None, prioridade=1, especialidades=None):
    """Helper para criar FerramentaDetectada em testes."""
    return FerramentaDetectada(
        nome=nome,
        comando=comando or nome,
        caminho=f'/usr/local/bin/{comando or nome}',
        descricao=f'{nome} (test)',
        especialidades=especialidades or ['codigo'],
        prioridade=prioridade,
    )


@pytest.fixture
def ferramentas_multiplas():
    """Simula host com Claude + Codex instalados."""
    return [
        _make_ferramenta('claude', prioridade=1,
                         especialidades=['arquitetura', 'analise', 'design', 'codigo']),
        _make_ferramenta('codex', prioridade=2,
                         especialidades=['codigo', 'database', 'testes']),
    ]


@pytest.fixture
def ferramenta_unica():
    """Simula host com apenas Antigravity."""
    return [
        _make_ferramenta('agy', comando='agy', prioridade=2,
                         especialidades=['arquitetura', 'codigo', 'design', 'testes']),
    ]


@pytest.fixture
def resultado_multiplas(ferramentas_multiplas):
    return DetectorResultado(
        ferramentas=ferramentas_multiplas,
        orca_presente=False,
        orca_sinais=[],
    )


@pytest.fixture
def resultado_unica(ferramenta_unica):
    return DetectorResultado(
        ferramentas=ferramenta_unica,
        orca_presente=False,
        orca_sinais=[],
    )


@pytest.fixture
def resultado_vazio():
    return DetectorResultado(ferramentas=[], orca_presente=False, orca_sinais=[])


# =============================================================================
# TESTES: detector.py — FerramentasDetectadas
# =============================================================================

class TestFerramentaDetectada:
    def test_to_dict(self):
        f = _make_ferramenta('claude')
        d = f.to_dict()
        assert d['nome'] == 'claude'
        assert d['comando'] == 'claude'
        assert d['caminho'] == '/usr/local/bin/claude'
        assert 'codigo' in d['especialidades']

    def test_valores_default(self):
        f = FerramentaDetectada(
            nome='x', comando='x', caminho='/bin/x', descricao='X',
        )
        assert f.especialidades == []
        assert f.prioridade == 99


class TestDetectorResultado:
    def test_to_dict_vazio(self):
        r = DetectorResultado()
        d = r.to_dict()
        assert d['total_ferramentas'] == 0
        assert d['orca_presente'] is False

    def test_to_dict_com_ferramentas(self):
        r = DetectorResultado(
            ferramentas=[_make_ferramenta('claude')],
            orca_presente=True,
            orca_sinais=['ORCA_WORKSPACE'],
        )
        d = r.to_dict()
        assert d['total_ferramentas'] == 1
        assert d['orca_presente'] is True


# =============================================================================
# TESTES: detector.py — Deteccao de ferramentas
# =============================================================================

class TestDetectarFerramentas:
    @patch('core.detector.shutil.which')
    def test_detecta_claude(self, mock_which):
        def which_side(cmd):
            return '/usr/local/bin/claude' if cmd == 'claude' else None
        mock_which.side_effect = which_side

        resultado = detectar_ferramentas()
        assert len(resultado) == 1
        assert resultado[0].nome == 'claude'

    @patch('core.detector.shutil.which')
    def test_detecta_multiplos_ordenados_por_prioridade(self, mock_which):
        def which_side(cmd):
            paths = {'claude': '/bin/claude', 'codex': '/bin/codex', 'ollama': '/bin/ollama'}
            return paths.get(cmd)
        mock_which.side_effect = which_side

        resultado = detectar_ferramentas()
        assert len(resultado) == 3
        # Ordenados: claude(1), codex(2), ollama(4)
        assert resultado[0].nome == 'claude'
        assert resultado[1].nome == 'codex'
        assert resultado[2].nome == 'ollama'

    @patch('core.detector.shutil.which')
    def test_detecta_nenhum(self, mock_which):
        mock_which.return_value = None
        resultado = detectar_ferramentas()
        assert len(resultado) == 0

    @patch('core.detector.shutil.which')
    def test_detecta_agy_por_alias(self, mock_which):
        """agy pode ser encontrado como 'agy' ou 'antigravity'."""
        def which_side(cmd):
            return '/bin/agy' if cmd == 'agy' else None
        mock_which.side_effect = which_side

        resultado = detectar_ferramentas()
        nomes = [f.nome for f in resultado]
        assert 'agy' in nomes

    @patch('core.detector.shutil.which')
    def test_nao_duplica_agy(self, mock_which):
        """Se 'agy' ja foi encontrado, nao testa 'antigravity'."""
        chamados = []
        def which_side(cmd):
            chamados.append(cmd)
            return '/bin/agy' if cmd == 'agy' else None
        mock_which.side_effect = which_side

        detectar_ferramentas()
        # 'antigravity' nao deve ser testado pois 'agy' ja foi encontrado
        assert 'antigravity' not in chamados


# =============================================================================
# TESTES: detector.py — Deteccao ORCA ADE
# =============================================================================

class TestDetectarOrcaAde:
    def test_orca_presente(self):
        with patch.dict(os.environ, {'ORCA_WORKSPACE': '/some/path'}):
            assert detectar_orca_ade() is True

    def test_orca_ausente(self):
        env_limpo = {k: v for k, v in os.environ.items()
                     if k not in ORCA_AMBIENTE_SINAIS}
        with patch.dict(os.environ, env_limpo, clear=True):
            assert detectar_orca_ade() is False

    def test_multiplos_sinais(self):
        with patch.dict(os.environ, {
            'ORCA_WORKSPACE': '/x',
            'ORCA_WORKTREE_ID': 'wt-1',
        }):
            sinais = obter_sinais_orca()
            assert len(sinais) == 2
            assert 'ORCA_WORKSPACE' in sinais
            assert 'ORCA_WORKTREE_ID' in sinais


class TestDeteccaoCompleta:
    @patch('core.detector.detectar_orca_ade')
    @patch('core.detector.detectar_ferramentas')
    def test_resultado_completo(self, mock_ferr, mock_orca):
        mock_ferr.return_value = [_make_ferramenta('claude')]
        mock_orca.return_value = True

        resultado = executar_deteccao_completa()
        assert len(resultado.ferramentas) == 1
        assert resultado.orca_presente is True


# =============================================================================
# TESTES: orca_fleet.py — Resolucao de frota
# =============================================================================

class TestResolverFrota:
    def test_multi_agente(self, resultado_multiplas):
        fleet = resolver_frota(resultado_multiplas)
        assert fleet.modo == 'multi-agente'
        assert fleet.ferramenta_default == 'claude'
        assert len(fleet.ferramentas) == 2

    def test_agente_unico(self, resultado_unica):
        fleet = resolver_frota(resultado_unica)
        assert fleet.modo == 'agente-unico'
        assert fleet.ferramenta_default == 'agy'
        assert len(fleet.ferramentas) == 1

    def test_nenhum_agente(self, resultado_vazio):
        fleet = resolver_frota(resultado_vazio)
        assert fleet.modo == 'nenhum'
        assert fleet.ferramenta_default is None

    def test_override_filtra_ferramenta(self, resultado_multiplas):
        fleet = resolver_frota(resultado_multiplas, override_harness='codex')
        assert fleet.modo == 'agente-unico'
        assert fleet.override_config == 'codex'
        assert len(fleet.ferramentas) == 1
        assert fleet.ferramentas[0].nome == 'codex'

    def test_override_nao_encontrado(self, resultado_multiplas):
        fleet = resolver_frota(resultado_multiplas, override_harness='inexistente')
        assert fleet.modo == 'nenhum'
        assert fleet.override_config == 'inexistente'

    def test_override_via_env(self, resultado_multiplas):
        with patch.dict(os.environ, {'ORCA_DEFAULT_HARNESS': 'codex'}):
            fleet = resolver_frota(resultado_multiplas)
            assert fleet.modo == 'agente-unico'
            assert fleet.override_config == 'codex'

    def test_override_parametro_tem_precedencia_sobre_env(self, resultado_multiplas):
        """Parametro direto tem precedencia sobre variavel de ambiente."""
        with patch.dict(os.environ, {'ORCA_DEFAULT_HARNESS': 'claude'}):
            fleet = resolver_frota(resultado_multiplas, override_harness='codex')
            assert fleet.override_config == 'codex'
            assert fleet.ferramentas[0].nome == 'codex'


# =============================================================================
# TESTES: orca_fleet.py — Roteamento por especialidade
# =============================================================================

class TestRoteamento:
    def test_rotear_arquitetura_para_claude(self, ferramentas_multiplas):
        f = rotear_por_especialidade('arquitetura', ferramentas_multiplas)
        assert f.nome == 'claude'

    def test_rotear_database_para_codex(self, ferramentas_multiplas):
        f = rotear_por_especialidade('database', ferramentas_multiplas)
        assert f.nome == 'codex'

    def test_rotear_lista_vazia(self):
        f = rotear_por_especialidade('codigo', [])
        assert f is None

    def test_rotear_fallback_para_primeira(self, ferramentas_multiplas):
        """Especialidade desconhecida cai no fallback (primeira ferramenta)."""
        f = rotear_por_especialidade('especialidade_inexistente', ferramentas_multiplas)
        assert f is not None
        assert f.nome == 'claude'


class TestResolverParaFase:
    def test_multi_agente_roteia(self, resultado_multiplas):
        fleet = resolver_frota(resultado_multiplas)
        assert resolver_para_fase('phase_08_schema', fleet) == 'codex'
        assert resolver_para_fase('phase_03', fleet) == 'claude'

    def test_agente_unico_retorna_default(self, resultado_unica):
        fleet = resolver_frota(resultado_unica)
        assert resolver_para_fase('phase_08', fleet) == 'agy'
        assert resolver_para_fase('phase_03', fleet) == 'agy'

    def test_nenhum_retorna_none(self, resultado_vazio):
        fleet = resolver_frota(resultado_vazio)
        assert resolver_para_fase('phase_01', fleet) is None


# =============================================================================
# TESTES: orca_fleet.py — Geracao de inventario JSON
# =============================================================================

class TestGerarInventory:
    def test_gera_json_valido(self, resultado_multiplas, tmp_path):
        fleet = resolver_frota(resultado_multiplas)
        destino = tmp_path / '.orca' / '01_orca_inventory.json'

        caminho = gerar_inventory(fleet, destino=destino)
        assert caminho.exists()

        dados = json.loads(caminho.read_text(encoding='utf-8'))
        assert 'metadata' in dados
        assert 'frota' in dados
        assert 'roteamento' in dados
        assert 'fases' in dados

    def test_json_contem_ferramentas_reais(self, resultado_multiplas, tmp_path):
        fleet = resolver_frota(resultado_multiplas)
        destino = tmp_path / 'inventory.json'

        caminho = gerar_inventory(fleet, destino=destino)
        dados = json.loads(caminho.read_text(encoding='utf-8'))

        assert dados['frota']['total'] == 2
        nomes = [f['nome'] for f in dados['frota']['ferramentas']]
        assert 'claude' in nomes
        assert 'codex' in nomes

    def test_json_contem_fases_mapeadas(self, resultado_multiplas, tmp_path):
        fleet = resolver_frota(resultado_multiplas)
        destino = tmp_path / 'inventory.json'

        caminho = gerar_inventory(fleet, destino=destino)
        dados = json.loads(caminho.read_text(encoding='utf-8'))

        # Fase de database deve ir para codex em modo multi-agente
        assert dados['fases']['phase_08_schema'] == 'codex'
        # Fase de design deve ir para claude
        assert dados['fases']['phase_03'] == 'claude'

    def test_cria_diretorio_pai(self, resultado_multiplas, tmp_path):
        destino = tmp_path / 'deep' / 'nested' / '.orca' / 'inventory.json'
        gerar_inventory(resolver_frota(resultado_multiplas), destino=destino)
        assert destino.exists()

    def test_json_modo_agente_unico(self, resultado_unica, tmp_path):
        fleet = resolver_frota(resultado_unica)
        destino = tmp_path / 'inventory.json'

        caminho = gerar_inventory(fleet, destino=destino)
        dados = json.loads(caminho.read_text(encoding='utf-8'))

        assert dados['frota']['modo'] == 'agente-unico'
        # Todas as fases devem apontar para a mesma ferramenta
        for fase, ferramenta in dados['fases'].items():
            assert ferramenta == 'agy', f"Fase {fase} deveria ser 'agy'"


# =============================================================================
# TESTES: orca_fleet.py — inicializar_frota (interface principal)
# =============================================================================

class TestInicializarFrota:
    @patch('core.orca_fleet.executar_deteccao_completa')
    def test_retorna_fleet_status(self, mock_detec, resultado_multiplas):
        mock_detec.return_value = resultado_multiplas

        fleet = inicializar_frota(gerar_json=False)
        assert fleet.modo == 'multi-agente'

    @patch('core.orca_fleet.executar_deteccao_completa')
    def test_gera_json_por_default(self, mock_detec, resultado_multiplas, tmp_path):
        mock_detec.return_value = resultado_multiplas
        destino = tmp_path / '.orca' / '01_orca_inventory.json'

        inicializar_frota(gerar_json=True, destino_json=destino)
        assert destino.exists()

    @patch('core.orca_fleet.executar_deteccao_completa')
    def test_override_passado_para_resolver(self, mock_detec, resultado_multiplas):
        mock_detec.return_value = resultado_multiplas

        fleet = inicializar_frota(override_harness='codex', gerar_json=False)
        assert fleet.modo == 'agente-unico'
        assert fleet.override_config == 'codex'


# =============================================================================
# TESTES: orca_fleet.py — OrcaFleetStatus
# =============================================================================

class TestOrcaFleetStatus:
    def test_to_dict(self):
        status = OrcaFleetStatus(
            ferramentas=[_make_ferramenta('claude')],
            modo='multi-agente',
            ferramenta_default='claude',
        )
        d = status.to_dict()
        assert d['total'] == 1
        assert d['modo'] == 'multi-agente'
        assert d['ferramenta_default'] == 'claude'

    def test_valores_default(self):
        status = OrcaFleetStatus(ferramentas=[], modo='nenhum')
        assert status.ferramenta_default is None
        assert status.override_config is None
        assert status.orca_presente is False


# =============================================================================
# TESTES: Fallback em cascata — Cenario "apenas 1 agente"
# =============================================================================

class TestFallbackCascata:
    """
    Cenario central do SPRINT 02: se o usuario tem apenas 1 agente
    (ex: Antigravity), TODOS os workers operam nele em worktrees
    separadas sem falhar.
    """

    def test_agente_unico_todas_fases_resolvidas(self, resultado_unica):
        fleet = resolver_frota(resultado_unica)
        assert fleet.modo == 'agente-unico'

        # Nenhuma fase deve retornar None
        for fase in FASE_ESPECIALIDADE:
            resultado = resolver_para_fase(fase, fleet)
            assert resultado is not None, f"Fase {fase} retornou None em modo agente-unico"
            assert resultado == 'agy'

    def test_agente_unico_inventory_todas_fases_iguais(self, resultado_unica, tmp_path):
        fleet = resolver_frota(resultado_unica)
        destino = tmp_path / 'inventory.json'
        gerar_inventory(fleet, destino=destino)

        dados = json.loads(destino.read_text(encoding='utf-8'))
        valores_unicos = set(dados['fases'].values())
        assert len(valores_unicos) == 1, "Em modo agente-unico, todas fases devem usar a mesma ferramenta"
        assert 'agy' in valores_unicos

    def test_multi_agente_distribui_especialidades(self, resultado_multiplas):
        fleet = resolver_frota(resultado_multiplas)
        assert fleet.modo == 'multi-agente'

        fases_codex = [f for f in FASE_ESPECIALIDADE
                       if resolver_para_fase(f, fleet) == 'codex']
        fases_claude = [f for f in FASE_ESPECIALIDADE
                        if resolver_para_fase(f, fleet) == 'claude']

        # Deve haver distribuicao — nao tudo em um so
        assert len(fases_codex) > 0
        assert len(fases_claude) > 0
