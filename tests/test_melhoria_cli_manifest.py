# -*- coding: utf-8 -*-
"""
Teste de Componentes, Fractalidade e CLI Fallback (Ticket 2 / D4 / DoD 1).
Exige que `python ecossistema.py melhoria --manifest <json>` processe o manifesto com sucesso via CLI (exit 0).
"""

import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
SLUG_RELATORIO = f"{date.today().strftime('%d-%m-%Y')}_melhoria-refatorar-modulo-logs"


@pytest.fixture
def relatorio_isolado(tmp_path):
    """O CLI grava em docs/melhorias/ real: afasta colisões antes e remove o rastro depois."""
    alvos = [ROOT_DIR / "docs" / "melhorias" / f"{SLUG_RELATORIO}{ext}" for ext in (".json", ".html")]
    reserva = tmp_path / "reserva"
    reserva.mkdir()
    afastados = []
    for alvo in alvos:
        if alvo.exists():
            shutil.move(str(alvo), str(reserva / alvo.name))
            afastados.append(alvo)
    yield alvos
    for alvo in alvos:
        alvo.unlink(missing_ok=True)
    for alvo in afastados:
        shutil.move(str(reserva / alvo.name), str(alvo))


def test_cli_melhoria_com_manifesto_valido(tmp_path, relatorio_isolado):
    """Execução com `--manifest <json>` deve processar com sucesso (exit 0) e gerar os artefatos correspondentes."""
    manifest_file = tmp_path / "manifesto_teste.json"
    manifest_dados = {
        "pedido": "Refatorar modulo de logs para reduzir verbosidade",
        "nome": "refatorar-modulo-logs",
        "nota_atual": "6.5",
        "evidencia": "Logs atuais ocupam 40MB por hora em testes de carga",
        "resumo": "Analise de viabilidade para reducao de verbosidade",
        "achados": [
            "Modulo logging emite DEBUG em producao",
            "Falta agregador de mensagens repetidas"
        ],
        "riscos": [
            "Perda temporaria de visibilidade de depuracao se o filtro for agressivo"
        ],
        "recomendacao": "Sugestao de refatoracao com threshold dinamico de nivel de log",
        "itens_avaliados": [
            "Filtro de nivel::parcial::Existe apenas na configuracao raiz",
            "Agregador LRU::nao-feito::Inexistente no modulo atual"
        ]
    }
    manifest_file.write_text(json.dumps(manifest_dados, ensure_ascii=False, indent=2), encoding="utf-8")

    cmd = [
        sys.executable,
        str(ROOT_DIR / "ecossistema.py"),
        "melhoria",
        "--manifest",
        str(manifest_file),
        "--handoff",
        str(tmp_path / "handoff-melhoria.json"),
    ]

    res = subprocess.run(
        cmd,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert res.returncode == 0, f"Falha na execução: stdout={res.stdout}, stderr={res.stderr}"
    assert "Processamento concluído com sucesso" in res.stdout or "SUCESSO" in res.stdout

    sys.path.insert(0, str(ROOT_DIR / ".agents" / "skills" / "aidd-melhoria" / "scripts"))
    import handoff

    destino_handoff = tmp_path / "handoff-melhoria.json"
    assert all(alvo.is_file() for alvo in relatorio_isolado)
    assert handoff.verificar_handoff(destino_handoff, repo_root=ROOT_DIR) == []
    assert handoff.transicionar_fase(destino_handoff, repo_root=ROOT_DIR)["proxima_fase"] == "plan"
