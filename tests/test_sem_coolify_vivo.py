# -*- coding: utf-8 -*-
"""Guarda da abolição do Coolify (decisão do usuário, 13/10/2026): o deploy é só `compose-nativo`, em todos os fluxos.

Varre os arquivos versionados (e os novos não ignorados) e reprova qualquer rastro vivo de Coolify:
motor, API, variáveis `COOLIFY_*`, subcomando `ops coolify`, cliente/gerenciador. Linhas que declaram a abolição
("abolido", "sem Coolify", "removido") são aceitas.

Fora da varredura: documentos históricos datados, relatórios da auditoria do fluxo e baselines de segredos (hashes).
"""
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PADRAO = re.compile(r"coolify", re.IGNORECASE)
DECLARA_ABOLICAO = re.compile(r"abolid|abolic|aboli[cç]|abolish|sem coolify|removid|no coolify|not coolify|never coolify|n[aã]o usa coolify",
                              re.IGNORECASE)

HISTORICO = (
    "docs/auditoria/", "docs/melhorias/", "docs/reports/", "docs/relatorios/", "docs/teste-end-to-end/",
    "docs/issues/", "docs/explicacoes/", "docs/testes/", "docs/oficiais/", "docs/secoes/", "docs/features/",
    "docs/livros/", "docs/mapas-visuais/", "secoes/", "AUDITORIA-FLUXO-PURE/", "projetos/", ".mimocode/plans/",
)
# Testes cujo trabalho é provar que o Coolify sumiu.
PROVAM_A_ABOLICAO = (
    "tests/test_sem_coolify_vivo.py",
    "modulos/01-governanca-e-qualidade/core/aidd-planner/tests/test_ambiente.py",
    "modulos/03-plataforma-e-entrega/operacoes-ops/aidd-ops/tests/test_compose_deploy.py",
)
SO_HASHES = (".secrets.baseline",)


def _arquivos():
    saida = subprocess.run(
        ["git", "ls-files", "-co", "--exclude-standard"], cwd=RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    ).stdout.splitlines()
    return [f for f in saida if not f.startswith(HISTORICO)]


def test_nenhum_rastro_vivo_de_coolify():
    achados = []
    for rel in _arquivos():
        if rel in PROVAM_A_ABOLICAO or rel.endswith(SO_HASHES):
            continue
        try:
            texto = (RAIZ / rel).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for numero, linha in enumerate(texto.splitlines(), 1):
            if PADRAO.search(linha) and not DECLARA_ABOLICAO.search(linha):
                achados.append(f"{rel}:{numero}: {linha.strip()[:110]}")
    assert achados == [], f"{len(achados)} rastro(s) vivo(s) de Coolify:\n" + "\n".join(achados[:80])


def test_nao_existem_arquivos_de_coolify():
    nomes = [f for f in _arquivos() if "coolify" in f.lower() and f not in PROVAM_A_ABOLICAO]
    assert nomes == [], f"arquivo(s) de Coolify ainda versionados: {nomes}"
