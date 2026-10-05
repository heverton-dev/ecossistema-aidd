"""Prontidao do forge antes de passar o bastao (Ticket 10, D2, ciclo-01).

Reproduz as 3 falhas do baseline E2E e prova o contrato C1
(``componentes/compartilhado/specs/handoff-forge-to-planner.schema.json``):

- projeto sem commit inicial -> ``forge init`` cria o commit inicial;
- dependencia faltando (``core.logs``) -> prontidao repara com exit 1;
- nenhuma IA -> sem harness ativo a prontidao repara com mensagem clara;
  sem API key + harness ativo (protocolo delegado) o forge esta pronto.

E grava ``<projeto>/.aidd/HANDOFF_FORGE_PLANNER.json`` com evidencia real
(hashes, versoes, espelhos e pastas conferidos), validado contra o schema.

Regra do usuario (sobre o ticket): o ecossistema NUNCA tem LLM ou API key
proprios — o modelo e sempre o do harness em execucao, via protocolo
delegado ``_llm_request``/``_llm_response``. Logo ``capacidade_llm:
"nenhuma"`` nao reprova; o item de prontidao confere que o protocolo
delegado ao harness esta disponivel, nunca uma chamada de API.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

import pytest

from aidd_forge.cli import main

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None, reason="git nao disponivel no PATH"
)

def _achar_raiz_repo() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "ecossistema.py").is_file():
            return parent
    return Path(__file__).resolve().parents[3]


_RAIZ_REPO = _achar_raiz_repo()
_SCHEMA_C1 = (
    _RAIZ_REPO
    / "componentes"
    / "compartilhado"
    / "specs"
    / "handoff-forge-to-planner.schema.json"
)
_CATALOGO = _RAIZ_REPO / "componentes" / "compartilhado" / "CATALOGO.json"

# Variaveis de ambiente que indicam um harness (ADE) ativo na sessao.
# Precisa bater com a lista de `aidd_forge.core.prontidao.detectar_harness`.
HARNESS_ENV_VARS = (
    "CLAUDECODE",
    "MIMOCODE",
    "MIMO_SESSION",
    "MIMO_WORKSPACE",
    "OPENCODE",
    "OPENCODE_SESSION",
    "OPENCODE_CONFIG_DIR",
    "ANTIGRAVITY_CLI",
    "AGY_SESSION",
    "ANTIGRAVITY_AGENT",
    "GEMINI_SESSION",
    "GEMINI_CLI",
    "ORCA_WORKSPACE",
    "ORCA_WORKTREE_ID",
    "ORCA_TERMINAL_HANDLE",
    "AIDD_HARNESS_NAME",
)

# O ecossistema nao usa API key; qualquer resquicio seria mentira de rotulo.
SEM_API_KEY = ("LLM_MODEL", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY")


def _sem_ia(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove todo sinal de harness e de API key do ambiente do teste."""
    for var in HARNESS_ENV_VARS + SEM_API_KEY:
        monkeypatch.delenv(var, raising=False)


def _harness_ativo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simula harness ativo (protocolo delegado) SEM nenhuma API key."""
    for var in SEM_API_KEY:
        monkeypatch.delenv(var, raising=False)
    for var in HARNESS_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("AIDD_HARNESS_NAME", "mimo")


def _git(target: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=target, capture_output=True, text=True, encoding="utf-8"
    )


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _alvo(tmp_path: Path) -> Path:
    target = tmp_path / "projeto"
    target.mkdir(parents=True, exist_ok=True)
    return target


# --- 1. commit inicial + handoff com evidencia ---------------------------------


def test_forge_init_faz_commit_inicial_e_grava_handoff_com_evidencia(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _harness_ativo(monkeypatch)
    target = _alvo(tmp_path)

    assert not (target / ".git").exists(), "pre-condicao: projeto sem git"

    exit_code = main(["init", str(target)])

    assert exit_code == 0, "forge init com harness ativo deve fechar com exit 0"

    # commit inicial existe de verdade
    head = _git(target, "rev-parse", "HEAD")
    assert head.returncode == 0, "git rev-parse HEAD deve responder"
    hash_commit = head.stdout.strip()
    assert re.fullmatch(r"[0-9a-f]{7,40}", hash_commit), f"hash invalido: {hash_commit!r}"

    # handoff C1 gravado e valido contra o schema
    handoff_path = target / ".aidd" / "HANDOFF_FORGE_PLANNER.json"
    assert handoff_path.is_file(), "C1 deve ser gravado em .aidd/HANDOFF_FORGE_PLANNER.json"

    jsonschema = pytest.importorskip("jsonschema")
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    schema = json.loads(_SCHEMA_C1.read_text(encoding="utf-8"))
    jsonschema.validate(instance=dados, schema=schema)

    # evidencia real, campo a campo
    assert dados["git"]["inicializado"] is True
    assert dados["git"]["commit_inicial"] == hash_commit

    assert len(dados["dependencias"]) >= 1
    for dep in dados["dependencias"]:
        assert dep["pacote"] and dep["versao"]

    assert len(dados["leis_e_guardas"]) >= 1
    for item in dados["leis_e_guardas"]:
        assert re.fullmatch(r"[0-9a-f]{64}", item["sha256"])
        assert (target / "gates" / item["gate"]).is_file()

    assert len(dados["harnesses"]) >= 1
    for espelho in dados["harnesses"]:
        assert (target / espelho).is_dir(), f"espelho ausente: {espelho}"

    catalogo_sha = hashlib.sha256(_CATALOGO.read_bytes()).hexdigest()
    assert dados["almoxarifado"]["catalogo_sha256"] == catalogo_sha
    assert len(dados["almoxarifado"]["pecas_disponiveis"]) >= 1

    assert dados["capacidade_llm"] in (
        "delegado_com_resposta",
        "headless_com_chave",
        "nenhuma",
    )
    # sem respondedor no teste: sem chave e sem resposta real -> "nenhuma"
    assert dados["capacidade_llm"] == "nenhuma"

    assert len(dados["estrutura_projeto"]["pastas_criadas"]) >= 1
    for pasta in dados["estrutura_projeto"]["pastas_criadas"]:
        assert (target / pasta).is_dir(), f"pasta do handoff ausente: {pasta}"


# --- 2. dependencia faltando reprovava (baseline: No module named 'core.logs') ---


def test_dependencia_faltando_reprova_prontidao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _harness_ativo(monkeypatch)
    target = _alvo(tmp_path)
    (target / "requirements.txt").write_text("core-logs==9.9.9\n", encoding="utf-8")

    exit_code = main(["init", str(target)])
    output = capsys.readouterr().out

    assert exit_code == 1, "dependencia nao importavel deve reprovar a prontidao"
    assert "core-logs" in output, "a falha deve nomear a dependencia que faltou"
    assert not (target / ".aidd" / "HANDOFF_FORGE_PLANNER.json").exists(), (
        "sem prontidao nao ha passagem de bastao"
    )


# --- 3. nenhuma IA sem harness reprovava com mensagem clara --------------------


def test_sem_harness_sem_api_key_reprova_com_mensagem_clara(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _sem_ia(monkeypatch)
    target = _alvo(tmp_path)

    exit_code = main(["init", str(target)])
    output = capsys.readouterr().out

    assert exit_code == 1, "sem harness ativo a prontidao deve reprovar"
    assert "nenhuma IA disponivel" in output, (
        f"mensagem clara obrigatoria, veja saida:\n{output}"
    )
    assert not (target / ".aidd" / "HANDOFF_FORGE_PLANNER.json").exists()


# --- 4. sem API key + harness ativo = pronto (regra do usuario) -----------------


def test_sem_api_key_com_harness_ativo_esta_pronto(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _harness_ativo(monkeypatch)
    assert all(var not in os.environ for var in SEM_API_KEY)
    target = _alvo(tmp_path)

    exit_code = main(["init", str(target)])
    output = capsys.readouterr().out

    assert exit_code == 0, f"sem API key + harness ativo deve estar pronto:\n{output}"
    handoff_path = target / ".aidd" / "HANDOFF_FORGE_PLANNER.json"
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert dados["capacidade_llm"] == "nenhuma", (
        "sem resposta real de LLM o valor honesto e 'nenhuma', e isso NAO reprova"
    )


# --- 5. round trip delegado real vira capacidade_llm ---------------------------


def test_round_trip_delegado_responde_e_vira_capacidade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _harness_ativo(monkeypatch)
    monkeypatch.setenv("AIDD_FORGE_PROBE_TIMEOUT_S", "15")
    target = _alvo(tmp_path)
    cache_dir = target / ".aidd" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    parar = threading.Event()

    def respondedor() -> None:
        """Responde ao probe como um harness faria via protocolo delegado."""
        respondidas: set[str] = set()
        while not parar.is_set():
            for req in cache_dir.glob("_llm_request_*.json"):
                req_id = req.stem.replace("_llm_request_", "")
                if req_id in respondidas:
                    continue
                try:
                    dados_req = json.loads(req.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                resposta = {
                    "conteudo": "pong",
                    "tokens_consumidos": 0,
                    "modelo_usado": "harness-teste",
                    "fase": dados_req.get("fase", ""),
                }
                alvo = cache_dir / f"_llm_response_{req_id}.json"
                alvo.write_text(
                    json.dumps(resposta, ensure_ascii=False), encoding="utf-8"
                )
                respondidas.add(req_id)
            time.sleep(0.1)

    fio = threading.Thread(target=respondedor, daemon=True)
    fio.start()
    try:
        exit_code = main(["init", str(target)])
    finally:
        parar.set()
        fio.join(timeout=5)

    assert exit_code == 0
    handoff_path = target / ".aidd" / "HANDOFF_FORGE_PLANNER.json"
    dados = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert dados["capacidade_llm"] == "delegado_com_resposta", (
        "pedido -> resposta no protocolo delegado deve virar "
        "capacidade_llm='delegado_com_resposta'"
    )
    respostas = list(cache_dir.glob("_llm_response_*.json"))
    assert respostas, "a resposta do harness deve ficar como evidencia no cache"


# --- 6. gate fora da versao do catalogo reprova -------------------------------


def test_gate_divergente_do_catalogo_reprova_prontidao(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _harness_ativo(monkeypatch)
    target = _alvo(tmp_path)

    assert main(["init", str(target)]) == 0
    capsys.readouterr()

    gate = target / "gates" / "G_CONTRACTS.py"
    gate.write_text(gate.read_text(encoding="utf-8") + "\n# adulterado\n", encoding="utf-8")

    # segunda passada sem --force nao reinstala gates: a divergencia fica
    exit_code = main(["init", str(target)])
    output = capsys.readouterr().out

    assert exit_code == 1, "gate divergente do catologo deve reprovar a prontidao"
    assert "G_CONTRACTS.py" in output
    assert "catalogo" in output.lower()
    assert not (target / ".aidd" / "HANDOFF_FORGE_PLANNER.json").exists(), (
        "handoff de uma rodada anterior deve ser removido quando a prontidao reprova"
    )
