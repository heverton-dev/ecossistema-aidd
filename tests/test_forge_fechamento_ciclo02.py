# -*- coding: utf-8 -*-
"""
Fechamento do ciclo-02 do aidd-forge (TICKET-02 / D15 / DoD 8).

Exige:
- handoff-forge.json da raiz em sincronia real com os 7 módulos de
  `.agents/skills/aidd-forge/scripts/` + `gates/G_aidd_forge.py`
  (SHA-256 recomputado, zero claims sem verificação — Lei #8);
- `handoff verify` da CLI retornando exit 0 no repositório;
- os 8 critérios de docs/auditoria/aidd-forge/ciclo-02/DOD.md presentes,
  cada um coberto pelo seu módulo de teste real, com execução exit 0.
"""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
HANDOFF_ARQUIVO = ROOT_DIR / "handoff-forge.json"
CLI_SCRIPT = ROOT_DIR / ".agents" / "skills" / "aidd-forge" / "scripts" / "cli.py"
DOD_ARQUIVO = ROOT_DIR / "docs" / "auditoria" / "aidd-forge" / "ciclo-02" / "DOD.md"

# Os 7 módulos de scripts + o quality gate declarados no handoff canônico.
COMPONENTES_ESPERADOS = [
    ".agents/skills/aidd-forge/scripts/isolamento.py",
    ".agents/skills/aidd-forge/scripts/cli.py",
    ".agents/skills/aidd-forge/scripts/bootstrap.py",
    ".agents/skills/aidd-forge/scripts/orquestracao.py",
    ".agents/skills/aidd-forge/scripts/resiliencia.py",
    ".agents/skills/aidd-forge/scripts/observabilidade.py",
    ".agents/skills/aidd-forge/scripts/rollback.py",
    "gates/G_aidd_forge.py",
]

# Evidência executável de cada critério DoD do ciclo-02.
EVIDENCIAS_DOD = {
    1: ROOT_DIR / "tests" / "test_forge_cli.py",
    2: ROOT_DIR / "tests" / "test_forge_isolamento.py",
    3: ROOT_DIR / "tests" / "test_forge_bootstrap.py",
    4: ROOT_DIR / "tests" / "test_forge_resiliencia.py",
    5: ROOT_DIR / "tests" / "test_forge_observabilidade.py",
    6: ROOT_DIR / "gates" / "test_g_aidd_forge.py",
    7: ROOT_DIR / "tests" / "test_forge_rollback.py",
    8: ROOT_DIR / "tests" / "test_forge_handoff.py",
}


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def test_handoff_raiz_sincronizado_com_os_sete_modulos():
    """handoff-forge.json deve cobrir exatamente os 7 scripts + gate com hash válido."""
    assert HANDOFF_ARQUIVO.is_file(), "handoff-forge.json ausente na raiz do repositório"
    dados = json.loads(HANDOFF_ARQUIVO.read_text(encoding="utf-8"))
    registrados = {
        c["caminho"]: c for c in dados["componentes"] if isinstance(c, dict) and "caminho" in c
    }
    assert set(registrados) == set(COMPONENTES_ESPERADOS), (
        "cobertura divergente no handoff:\n"
        f"  faltando: {sorted(set(COMPONENTES_ESPERADOS) - set(registrados))}\n"
        f"  extra: {sorted(set(registrados) - set(COMPONENTES_ESPERADOS))}"
    )
    divergentes = []
    for relativo in COMPONENTES_ESPERADOS:
        arquivo = ROOT_DIR / relativo
        assert arquivo.is_file(), f"componente inexistente: {relativo}"
        esperado = registrados[relativo].get("sha256")
        atual = _sha256(arquivo)
        if esperado != atual:
            divergentes.append(f"{relativo}: handoff={esperado} atual={atual}")
    assert not divergentes, (
        "hashes SHA-256 divergentes (emita `python ecossistema.py forge handoff emit`):\n"
        + "\n".join(divergentes)
    )


def test_handoff_verify_cli_exit_0_no_repositorio():
    """`forge handoff verify` sem componentes explícitos deve aprovar (exit 0)."""
    res = subprocess.run(
        [sys.executable, str(CLI_SCRIPT), "handoff", "verify"],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert res.returncode == 0, (
        f"handoff verify deve retornar exit 0 (obtido {res.returncode}): "
        f"{res.stdout[-500:]} {res.stderr[-500:]}"
    )


def test_dod_ciclo02_oito_criterios_com_evidencia_executavel():
    """Os 8 critérios do DoD devem existir e cada um ter módulo de teste real."""
    assert DOD_ARQUIVO.is_file(), f"DoD ausente: {DOD_ARQUIVO}"
    texto = DOD_ARQUIVO.read_text(encoding="utf-8", errors="replace")
    criterios = sorted({int(n) for n in re.findall(r"DoD (\d+):", texto)})
    assert criterios == list(range(1, 9)), f"critérios DoD encontrados: {criterios}"
    sem_evidencia = []
    for numero in criterios:
        modulo = EVIDENCIAS_DOD.get(numero)
        if modulo is None or not modulo.is_file():
            sem_evidencia.append(f"DoD {numero}: módulo de evidência ausente")
            continue
        conteudo = modulo.read_text(encoding="utf-8", errors="replace")
        if "def test_" not in conteudo:
            sem_evidencia.append(f"DoD {numero}: {modulo.name} sem testes reais")
    assert not sem_evidencia, "critérios DoD sem evidência executável:\n" + "\n".join(sem_evidencia)


def test_evidencias_dod_executam_com_exit_0():
    """Evidência real: os 8 módulos de teste do DoD rodam e aprovam (exit 0)."""
    modulos = [EVIDENCIAS_DOD[n] for n in sorted(EVIDENCIAS_DOD)]
    res = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *map(str, modulos)],
        capture_output=True,
        text=True,
        cwd=str(ROOT_DIR),
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    assert res.returncode == 0, (
        f"evidências DoD devem aprovar (exit 0), obtido {res.returncode}:\n"
        f"{res.stdout[-1500:]}"
    )
