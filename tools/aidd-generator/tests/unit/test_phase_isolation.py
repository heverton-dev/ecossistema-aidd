#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes de Isolamento de Micro-Ambientes — SPRINT 03

Valida que:
1. Cada fase tem diretório próprio com AGENTS.md
2. AGENTS.md contém seções obrigatórias (Escopo, Restrições, Gates)
3. O registry de fases do pipeline está completo e correto
4. O carregamento dinâmico isola módulos (apenas 1 em memória)
5. O micro-ambiente é carregado corretamente
6. Diretórios foram renomeados conforme plano (analisador, planejador)
"""

import sys
import importlib.util
from pathlib import Path

import pytest

# Caminho base
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PHASES_DIR = PROJECT_ROOT / 'scripts' / 'phases'
PIPELINE_PATH = PROJECT_ROOT / 'scripts' / 'pipeline_completo.py'

# Adicionar scripts ao path para importar pipeline
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def pipeline_mod():
    """Carrega o módulo pipeline_completo.py para testar funções internas."""
    spec = importlib.util.spec_from_file_location('pipeline_completo', PIPELINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def all_phase_dirs():
    """Retorna todos os diretórios de fases que existem."""
    return [d for d in PHASES_DIR.iterdir() if d.is_dir() and d.name.startswith('phase_')]


# =============================================================================
# TESTES: Estrutura de Diretórios
# =============================================================================

class TestPhaseDirectories:
    """Valida que os micro-ambientes existem com a nomenclatura correta."""

    EXPECTED_DIRS = [
        'phase_01_pesquisa',
        'phase_02_analisador',
        'phase_03_designer',
        'phase_04_planejador',
        'phase_05_criador',
        'phase_06_documentador',
        'phase_07_auto_critica',
        'phase_08_implementador',
    ]

    @pytest.mark.parametrize("dir_name", EXPECTED_DIRS)
    def test_phase_directory_exists(self, dir_name):
        """Cada diretório de fase deve existir."""
        phase_path = PHASES_DIR / dir_name
        assert phase_path.exists(), f'Diretório {dir_name} não encontrado em {PHASES_DIR}'
        assert phase_path.is_dir(), f'{dir_name} existe mas não é um diretório'

    def test_no_old_directory_names(self):
        """Diretórios antigos (phase_02_analise, phase_04_decisor) não devem existir."""
        old_names = ['phase_02_analise', 'phase_04_decisor']
        for old_name in old_names:
            old_path = PHASES_DIR / old_name
            assert not old_path.exists(), f'Diretório antigo {old_name} ainda existe — deveria ter sido renomeado'

    def test_total_phase_dirs(self):
        """Deve haver exatamente 8 diretórios de fase."""
        phase_dirs = [d for d in PHASES_DIR.iterdir()
                      if d.is_dir() and d.name.startswith('phase_')]
        assert len(phase_dirs) == 8, f'Esperado 8 diretórios de fase, encontrado {len(phase_dirs)}'


# =============================================================================
# TESTES: AGENTS.md em cada micro-ambiente
# =============================================================================

class TestAgentsMdContent:
    """Valida que cada AGENTS.md tem as seções obrigatórias."""

    REQUIRED_SECTIONS = ['## Escopo', '## Restrições', '## Saída']

    @pytest.mark.parametrize("dir_name", [
        'phase_01_pesquisa',
        'phase_02_analisador',
        'phase_03_designer',
        'phase_04_planejador',
        'phase_05_criador',
        'phase_06_documentador',
        'phase_07_auto_critica',
        'phase_08_implementador',
    ])
    def test_agents_md_exists(self, dir_name):
        """Cada micro-ambiente deve ter um AGENTS.md."""
        agents_path = PHASES_DIR / dir_name / 'AGENTS.md'
        assert agents_path.exists(), f'AGENTS.md não encontrado em {dir_name}'

    @pytest.mark.parametrize("dir_name", [
        'phase_01_pesquisa',
        'phase_02_analisador',
        'phase_03_designer',
        'phase_04_planejador',
        'phase_05_criador',
        'phase_06_documentador',
        'phase_07_auto_critica',
        'phase_08_implementador',
    ])
    def test_agents_md_has_required_sections(self, dir_name):
        """AGENTS.md deve conter Escopo, Restrições e Saída."""
        agents_path = PHASES_DIR / dir_name / 'AGENTS.md'
        content = agents_path.read_text(encoding='utf-8')
        for section in self.REQUIRED_SECTIONS:
            assert section in content, (
                f'Seção "{section}" não encontrada em {dir_name}/AGENTS.md'
            )

    def test_phase_01_has_filesystem_mcp(self):
        """Phase 01 deve referenciar Filesystem MCP."""
        content = (PHASES_DIR / 'phase_01_pesquisa' / 'AGENTS.md').read_text(encoding='utf-8')
        assert 'Filesystem MCP' in content

    def test_phase_02_has_business_rules(self):
        """Phase 02 deve ter seção de Regras de Negócio."""
        content = (PHASES_DIR / 'phase_02_analisador' / 'AGENTS.md').read_text(encoding='utf-8')
        assert 'Regras de Negócio' in content

    def test_phase_03_has_schema_draft(self):
        """Phase 03 deve referenciar JSON Schema Draft 2020-12."""
        content = (PHASES_DIR / 'phase_03_designer' / 'AGENTS.md').read_text(encoding='utf-8')
        assert 'Draft 2020-12' in content

    def test_phase_04_has_task_division(self):
        """Phase 04 deve ter seção de Divisão de Tarefas."""
        content = (PHASES_DIR / 'phase_04_planejador' / 'AGENTS.md').read_text(encoding='utf-8')
        assert 'Divisão de Tarefas' in content

    def test_phase_05_has_ast_linter(self):
        """Phase 04 deve ter seção de Linter AST."""
        content = (PHASES_DIR / 'phase_05_criador' / 'AGENTS.md').read_text(encoding='utf-8')
        assert 'Linter AST' in content

    def test_phase_08_has_result_monad(self):
        """Phase 08 deve ter seção de Result Monad."""
        content = (PHASES_DIR / 'phase_08_implementador' / 'AGENTS.md').read_text(encoding='utf-8')
        assert 'Result Monad' in content

    def test_phase_08_has_pytest_rules(self):
        """Phase 08 deve ter seção de pytest."""
        content = (PHASES_DIR / 'phase_08_implementador' / 'AGENTS.md').read_text(encoding='utf-8')
        assert '## pytest' in content


# =============================================================================
# TESTES: Registry de Fases do Pipeline
# =============================================================================

class TestPhaseRegistry:
    """Valida o registry centralizado de fases no pipeline."""

    def test_registry_has_all_8_phases(self, pipeline_mod):
        """O registry deve conter exatamente 8 fases."""
        registry = pipeline_mod._FASE_REGISTRY
        assert len(registry) == 8
        for i in range(1, 9):
            assert i in registry, f'Fase {i} não encontrada no registry'

    def test_registry_scripts_exist(self, pipeline_mod):
        """Cada script referenciado no registry deve existir em disco."""
        for num, reg in pipeline_mod._FASE_REGISTRY.items():
            script_path = PHASES_DIR / reg['script']
            assert script_path.exists(), (
                f'Script {reg["script"]} da fase {num} não encontrado'
            )

    def test_registry_micro_env_dirs_exist(self, pipeline_mod):
        """Cada micro-ambiente referenciado no registry deve existir."""
        for num, reg in pipeline_mod._FASE_REGISTRY.items():
            env_path = PHASES_DIR / reg['micro_env']
            assert env_path.exists(), (
                f'Micro-ambiente {reg["micro_env"]} da fase {num} não encontrado'
            )
            assert env_path.is_dir(), (
                f'{reg["micro_env"]} da fase {num} não é um diretório'
            )

    def test_registry_micro_env_has_agents_md(self, pipeline_mod):
        """Cada micro-ambiente do registry deve ter AGENTS.md."""
        for num, reg in pipeline_mod._FASE_REGISTRY.items():
            agents_path = PHASES_DIR / reg['micro_env'] / 'AGENTS.md'
            assert agents_path.exists(), (
                f'AGENTS.md não encontrado em {reg["micro_env"]} (fase {num})'
            )

    def test_registry_aliases_are_unique(self, pipeline_mod):
        """Aliases de módulos devem ser únicos."""
        aliases = [reg['alias'] for reg in pipeline_mod._FASE_REGISTRY.values()]
        assert len(aliases) == len(set(aliases)), 'Aliases duplicados no registry'

    def test_registry_phase_02_points_to_analisador(self, pipeline_mod):
        """Fase 2 deve apontar para phase_02_analisador (não phase_02_analise)."""
        assert pipeline_mod._FASE_REGISTRY[2]['micro_env'] == 'phase_02_analisador'

    def test_registry_phase_04_points_to_planejador(self, pipeline_mod):
        """Fase 4 deve apontar para phase_04_planejador (não phase_04_decisor)."""
        assert pipeline_mod._FASE_REGISTRY[4]['micro_env'] == 'phase_04_planejador'


# =============================================================================
# TESTES: Carregamento Dinâmico (Isolamento)
# =============================================================================

class TestDynamicLoading:
    """Valida que o carregamento dinâmico isola corretamente os módulos."""

    def test_load_single_phase(self, pipeline_mod):
        """Carregar uma fase deve retornar um módulo válido."""
        mod = pipeline_mod._carregar_fase(1)
        assert mod is not None
        assert hasattr(mod, 'PesquisadorFase1')

    def test_cache_has_only_one_phase(self, pipeline_mod):
        """Após carregar uma fase, apenas ela deve estar em cache."""
        pipeline_mod._descarregar_todas_fases()
        pipeline_mod._carregar_fase(1)
        assert len(pipeline_mod._modulo_cache) == 1
        assert 1 in pipeline_mod._modulo_cache

    def test_loading_new_phase_evicts_old(self, pipeline_mod):
        """Carregar uma nova fase deve descartar a anterior."""
        pipeline_mod._descarregar_todas_fases()
        pipeline_mod._carregar_fase(1)
        assert 1 in pipeline_mod._modulo_cache

        pipeline_mod._carregar_fase(3)
        assert 1 not in pipeline_mod._modulo_cache
        assert 3 in pipeline_mod._modulo_cache
        assert len(pipeline_mod._modulo_cache) == 1

    def test_unload_all_phases(self, pipeline_mod):
        """_descarregar_todas_fases deve limpar o cache completamente."""
        pipeline_mod._carregar_fase(5)
        assert len(pipeline_mod._modulo_cache) >= 1

        pipeline_mod._descarregar_todas_fases()
        assert len(pipeline_mod._modulo_cache) == 0

    def test_load_invalid_phase_raises(self, pipeline_mod):
        """Carregar fase inválida deve levantar ValueError."""
        with pytest.raises(ValueError, match='não encontrada'):
            pipeline_mod._carregar_fase(99)

    def test_load_all_phases_sequentially(self, pipeline_mod):
        """Todas as 8 fases devem ser carregáveis sequencialmente."""
        pipeline_mod._descarregar_todas_fases()
        for i in range(1, 9):
            mod = pipeline_mod._carregar_fase(i)
            assert mod is not None, f'Fase {i} retornou None'
            # Verificar isolamento: apenas 1 em cache
            assert len(pipeline_mod._modulo_cache) == 1


# =============================================================================
# TESTES: Carregamento de Micro-Ambiente
# =============================================================================

class TestMicroEnvironmentLoading:
    """Valida o carregamento do contexto AGENTS.md por fase."""

    def test_load_micro_env_returns_content(self, pipeline_mod):
        """Carregar micro-ambiente deve retornar conteúdo do AGENTS.md."""
        content = pipeline_mod._carregar_micro_ambiente(1)
        assert len(content) > 0
        assert 'Phase 01' in content

    def test_load_micro_env_invalid_phase(self, pipeline_mod):
        """Fase inválida deve retornar string vazia."""
        content = pipeline_mod._carregar_micro_ambiente(99)
        assert content == ''

    def test_each_phase_has_unique_context(self, pipeline_mod):
        """Cada fase deve ter contexto AGENTS.md diferente."""
        contexts = {}
        for i in range(1, 9):
            ctx = pipeline_mod._carregar_micro_ambiente(i)
            if ctx:  # Fases 6 e 7 podem ter conteúdo menor
                contexts[i] = ctx

        # Verificar que não há dois contextos idênticos
        values = list(contexts.values())
        assert len(values) == len(set(values)), 'Dois micro-ambientes têm AGENTS.md idênticos'

    def test_micro_env_phase_02_mentions_business_rules(self, pipeline_mod):
        """Micro-ambiente da fase 2 deve mencionar regras de negócio."""
        content = pipeline_mod._carregar_micro_ambiente(2)
        assert 'Negócio' in content or 'Negocio' in content or 'regras' in content.lower()

    def test_micro_env_phase_08_mentions_result_monad(self, pipeline_mod):
        """Micro-ambiente da fase 8 deve mencionar Result Monad."""
        content = pipeline_mod._carregar_micro_ambiente(8)
        assert 'Result' in content


# =============================================================================
# TESTES: Integridade Cross-Phase
# =============================================================================

class TestCrossPhaseIntegrity:
    """Valida consistência entre os diferentes componentes."""

    def test_all_phase_scripts_have_corresponding_dir(self, pipeline_mod):
        """Todo script de fase no registry deve ter um diretório de micro-ambiente."""
        for num, reg in pipeline_mod._FASE_REGISTRY.items():
            env_dir = PHASES_DIR / reg['micro_env']
            assert env_dir.exists(), (
                f'Fase {num}: diretório {reg["micro_env"]} não existe'
            )

    def test_all_phase_dirs_have_corresponding_registry_entry(self, pipeline_mod):
        """Todo diretório phase_XX deve ter entrada no registry."""
        registry_envs = {reg['micro_env'] for reg in pipeline_mod._FASE_REGISTRY.values()}
        for d in PHASES_DIR.iterdir():
            if d.is_dir() and d.name.startswith('phase_'):
                assert d.name in registry_envs, (
                    f'Diretório {d.name} não tem entrada no registry do pipeline'
                )

    def test_agents_md_header_matches_phase_number(self, pipeline_mod):
        """O cabeçalho do AGENTS.md deve corresponder ao número da fase."""
        for num, reg in pipeline_mod._FASE_REGISTRY.items():
            agents_path = PHASES_DIR / reg['micro_env'] / 'AGENTS.md'
            content = agents_path.read_text(encoding='utf-8')
            # O header deve conter o número da fase (ex: "Phase 01", "Phase 08")
            phase_num_str = f'Phase {num:02d}'
            assert phase_num_str in content, (
                f'AGENTS.md de {reg["micro_env"]} não contém header "{phase_num_str}"'
            )
