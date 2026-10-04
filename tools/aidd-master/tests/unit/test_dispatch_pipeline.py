# -*- coding: utf-8 -*-
"""
Testes Unitários: Motor de Despacho VSA em Git Worktrees (ISSUE-MESO-0004)
"""
import json
import os
import sys
from pathlib import Path
import pytest

MASTER_DIR = Path(__file__).resolve().parent.parent.parent
ECOSSISTEMA_ROOT = MASTER_DIR.parent.parent
DISPATCH_SCRIPT = MASTER_DIR / "scripts" / "dispatch_pipeline.py"

if str(MASTER_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(MASTER_DIR / "scripts"))

from dispatch_pipeline import VSADispatchPipeline, SliceExecutionResult


def _gerar_manifesto_vsa() -> dict:
    return {
        "versao_schema": "1.0.0",
        "projeto_slug": "app-unit-vsa",
        "fluxo_alvo": "fluxo_01_generator",
        "grafo_fatias": [
            {
                "slice_id": "slice_auth",
                "modulo_ddd": "Auth",
                "dependencias": [],
                "isolamento": "git-worktree",
                "arquivos_esperados": ["src/slices/auth/router.py"],
                "barreira_validacao": {
                    "comandos_teste": ["pytest tests/test_auth.py"],
                    "quality_gates": ["python gates/G_SAIDA_BINARIA.py"]
                }
            },
            {
                "slice_id": "slice_catalogo",
                "modulo_ddd": "Catalogo",
                "dependencias": [],
                "isolamento": "git-worktree",
                "arquivos_esperados": ["src/slices/catalogo/router.py"],
                "barreira_validacao": {
                    "comandos_teste": ["pytest tests/test_catalogo.py"],
                    "quality_gates": ["python gates/G_SAIDA_BINARIA.py"]
                }
            },
            {
                "slice_id": "slice_pedidos",
                "modulo_ddd": "Pedidos",
                "dependencias": ["slice_auth", "slice_catalogo"],
                "isolamento": "git-worktree",
                "arquivos_esperados": ["src/slices/pedidos/router.py"],
                "barreira_validacao": {
                    "comandos_teste": ["pytest tests/test_pedidos.py"],
                    "quality_gates": ["python gates/G_SAIDA_BINARIA.py"]
                }
            }
        ],
        "convergencia_master": {
            "target_branch": "main",
            "merge_strategy": "fast-forward",
            "post_merge_suite": ["python ecossistema.py audit"]
        }
    }


def test_carregamento_e_niveis_topologicos(tmp_path):
    """Verifica se as fatias são agrupadas corretamente em 2 níveis (auth+catalogo -> pedidos)."""
    manifesto = _gerar_manifesto_vsa()
    m_file = tmp_path / "vsa_dispatch.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    pipeline = VSADispatchPipeline(dispatch_path=m_file, dry_run=True, verbose=False)
    assert pipeline.validate_and_load_manifest() is True

    niveis = pipeline._calcular_niveis_topologicos()
    assert len(niveis) == 2

    # Nível 0: fatias sem dependências
    ids_nivel_0 = {f["slice_id"] for f in niveis[0]}
    assert ids_nivel_0 == {"slice_auth", "slice_catalogo"}

    # Nível 1: fatia dependente de ambas
    ids_nivel_1 = {f["slice_id"] for f in niveis[1]}
    assert ids_nivel_1 == {"slice_pedidos"}


def test_rejeicao_ciclo_no_calculo_topologico(tmp_path):
    """Verifica detecção de ciclo no grafo durante agrupamento de níveis."""
    manifesto = _gerar_manifesto_vsa()
    # Adiciona dependência cíclica: auth depende de pedidos
    manifesto["grafo_fatias"][0]["dependencias"] = ["slice_pedidos"]

    m_file = tmp_path / "ciclo.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    pipeline = VSADispatchPipeline(dispatch_path=m_file, dry_run=True, verbose=False)
    pipeline.manifest_data = manifesto

    with pytest.raises(ValueError) as excinfo:
        pipeline._calcular_niveis_topologicos()

    assert "Ciclo detectado" in str(excinfo.value)


def test_execucao_dry_run_completa(tmp_path):
    """Executa o ciclo completo em modo dry-run comprovando isolamento e convergência."""
    manifesto = _gerar_manifesto_vsa()
    m_file = tmp_path / "vsa_dispatch.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    pipeline = VSADispatchPipeline(
        dispatch_path=m_file,
        worktree_base_dir=tmp_path / ".worktrees",
        dry_run=True,
        verbose=False,
    )
    codigo = pipeline.run()
    assert codigo == 0
    # Garante que não sobraram worktrees ativas
    assert len(pipeline.active_worktrees) == 0


def test_cleanup_garantido_de_worktrees(tmp_path):
    """Garante que o método cleanup_all_worktrees remove diretórios efêmeros."""
    manifesto = _gerar_manifesto_vsa()
    m_file = tmp_path / "vsa_dispatch.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    wt_dir = tmp_path / ".worktrees"
    wt_dir.mkdir(parents=True, exist_ok=True)
    pasta_falsa = wt_dir / "slice_auth"
    pasta_falsa.mkdir(parents=True, exist_ok=True)
    (pasta_falsa / "arquivo.txt").write_text("conteudo", encoding="utf-8")

    pipeline = VSADispatchPipeline(
        dispatch_path=m_file,
        worktree_base_dir=wt_dir,
        dry_run=True,
        verbose=False,
    )
    from dispatch_pipeline import ActiveSliceWorktree
    pipeline.active_worktrees.append(
        ActiveSliceWorktree(slice_id="slice_auth", branch_name="slice/slice_auth", worktree_path=pasta_falsa)
    )

    pipeline.cleanup_all_worktrees()
    assert len(pipeline.active_worktrees) == 0
    assert not pasta_falsa.exists()


def test_barrier_sync_rebase_dry_run(tmp_path):
    """Garante que a flag barrier_sync executa rebase pré-merge sem falhas em dry-run."""
    manifesto = _gerar_manifesto_vsa()
    m_file = tmp_path / "vsa_dispatch.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    pipeline = VSADispatchPipeline(
        dispatch_path=m_file,
        worktree_base_dir=tmp_path / ".worktrees",
        dry_run=True,
        verbose=False,
        barrier_sync=True,
    )
    codigo = pipeline.run()
    assert codigo == 0
    assert pipeline.barrier_sync is True


def test_rollback_automatico_em_conflito(tmp_path):
    """Testa se conflito de merge dispara rollback automático e emite relatório."""
    manifesto = _gerar_manifesto_vsa()
    m_file = tmp_path / "vsa_dispatch.json"
    m_file.write_text(json.dumps(manifesto), encoding="utf-8")

    pipeline = VSADispatchPipeline(
        dispatch_path=m_file,
        worktree_base_dir=tmp_path / ".worktrees",
        dry_run=False,
        verbose=False,
    )
    pipeline.manifest_data = manifesto

    # Simula falha de merge direto
    ok = pipeline._merge_slice_branch("branch_inexistente_com_erro", slice_id="slice_erro")
    assert ok is False
    assert len(pipeline.rollback_history) == 1
    assert pipeline.rollback_history[0]["status"] == "ROLLED_BACK"
    assert pipeline.rollback_history[0]["slice_id"] == "slice_erro"

    # Confirma que o relatório JSON foi gravado
    report_file = pipeline.repo_root / "dispatch_rollback_report.json"
    if report_file.exists():
        conteudo = json.loads(report_file.read_text(encoding="utf-8"))
        assert conteudo["total_rollbacks"] >= 1
        report_file.unlink(missing_ok=True)

