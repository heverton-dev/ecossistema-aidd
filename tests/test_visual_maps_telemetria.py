# -*- coding: utf-8 -*-
"""
aidd-visual-maps ciclo-01, Ticket 12 (D12): telemetria de execução persistida.

Antes, nenhum estágio deixava rastro: não dava para saber quanto o catálogo ou um mapa
levou, quantos arquivos gravou nem com qual catálogo. Agora cada main() (catálogo, mapa,
não técnico, livro), inclusive no --check, acrescenta uma linha JSON em
secoes/medicoes/aidd-visual-maps.jsonl (pasta ignorada pelo git), com destino trocável
por AIDD_MEDICOES_DIR, e llm_tokens 0 explícito (o motor não usa LLM).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _repo_mapas import rodar  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
CATALOGO = ROOT / "docs" / "auditoria" / "mapa-pecas" / "catalogo-pecas.json"
CHAVES = {"estagio", "tipo", "duracao_ms", "arquivos_gravados", "hash_catalogo", "exit_code", "llm_tokens"}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _medicoes(pasta: Path) -> list[dict]:
    arquivo = pasta / "aidd-visual-maps.jsonl"
    if not arquivo.is_file():
        return []
    return [json.loads(linha) for linha in arquivo.read_text(encoding="utf-8").splitlines() if linha.strip()]


def _rodar_medido(pasta: Path, *args: str) -> tuple[int, dict]:
    antes = len(_medicoes(pasta))
    proc = rodar(ROOT, *args, env={"AIDD_MEDICOES_DIR": str(pasta)})
    novas = _medicoes(pasta)[antes:]
    assert len(novas) == 1, f"{args}: esperada 1 linha nova, vieram {len(novas)}\n{proc.stdout}\n{proc.stderr}"
    assert set(novas[0]) == CHAVES
    return proc.returncode, novas[0]


def test_mapa_e_catalogo_gravam_uma_linha_cada(tmp_path):
    medicoes = tmp_path / "medicoes"

    rc, linha = _rodar_medido(medicoes, "scripts/mapa_visual.py", "leis", "--saida", str(tmp_path / "leis.html"))
    assert rc == 0
    assert (linha["estagio"], linha["tipo"], linha["arquivos_gravados"], linha["exit_code"]) == ("mapa", "leis", 1, 0)
    assert linha["llm_tokens"] == 0
    assert isinstance(linha["duracao_ms"], (int, float)) and linha["duracao_ms"] > 0
    assert linha["hash_catalogo"] == _sha(CATALOGO)

    rc, linha = _rodar_medido(medicoes, "scripts/catalogo_pecas.py", "--saida", str(tmp_path / "catalogo.json"))
    assert rc == 0
    assert (linha["estagio"], linha["arquivos_gravados"], linha["exit_code"], linha["llm_tokens"]) == ("catalogo", 1, 0, 0)
    assert linha["hash_catalogo"] == _sha(tmp_path / "catalogo.json")


def test_check_e_falha_tambem_sao_medidos(tmp_path):
    medicoes = tmp_path / "medicoes"

    rc, linha = _rodar_medido(medicoes, "scripts/livro_mapas.py", "--check")
    assert (linha["estagio"], linha["arquivos_gravados"], linha["exit_code"]) == ("livro", 0, rc)

    rc, linha = _rodar_medido(medicoes, "scripts/mapa_visual.py", "leis", "--saida", "AGENTS.md")
    assert rc == 1
    assert (linha["estagio"], linha["arquivos_gravados"], linha["exit_code"]) == ("mapa", 0, 1)


def test_destino_padrao_fica_em_secoes_ignorada_pelo_git(monkeypatch):
    import telemetria_mapas
    monkeypatch.delenv("AIDD_MEDICOES_DIR", raising=False)
    destino = telemetria_mapas.destino()
    assert destino == ROOT / "secoes" / "medicoes" / "aidd-visual-maps.jsonl"
    ignorado = subprocess.run(["git", "check-ignore", "-q", destino.relative_to(ROOT).as_posix()], cwd=ROOT)
    assert ignorado.returncode == 0
