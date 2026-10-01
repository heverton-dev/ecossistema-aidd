# -*- coding: utf-8 -*-
"""
=====================================================================
ECOSSISTEMA AIDD — TESTE DO ORQUESTRADOR 4F: CONFLITO DE DERIVADO NO --APROVAR
=====================================================================
Regressão (D14, Ticket 6):
  O Join Barrier (`--aprovar`) mergeava a branch do ciclo e, se o merge
  conflitava, devolvia 1 com a worktree do DESENVOLVEDOR em estado de
  merge pela metade. Dois arquivos do mapa DERIVADOS
  (scripts/regenerar_derivados.py) conflitam em quase todo ciclo —
  assinatura do handoff, hashes do .secrets.baseline, ACHADOS.json,
  livro dos mapas — porque o ciclo os recalcula e a main também os
  recalcula, cada uma por conta própria. O humano era obrigado a
  terminar o merge na mão justamente nos arquivos que ninguém edita.

Regras:
  - Conflito em SOMENTE derivados: o merge é refeito. 'theirs' entra como
    base, `regenerar_derivados` regrava o conteúdo a partir da árvore já
    mesclada e o commit de merge fecha. Nenhuma intervenção humana.
  - Conflito em qualquer outro arquivo: merge abortado, árvore limpa de
    volta (nada pela metade), lista dos conflitos impressa, exit 1.
  - A classificação usa o mapa canônico DERIVADOS (chave exata OU
    arquivo dentro de uma chave de pasta, ex.: docs/livros/mapas-aidd/...).
  - Nada é empacotado no merge além do que o mapa DERIVADOS cobre: lixo
    não versionado da worktree do desenvolvedor nunca entra no histórico.
  - Se a regeneração falhar, o merge também é abortado: derivado não
    regenerado é pior que derivado conflitando.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import orquestrador_4f  # noqa: E402
import regenerar_derivados  # noqa: E402

PIPELINE = "aud-deriva-ciclo-01"
BRANCH_CICLO = f"audit/{PIPELINE}"
REF_APROVAVEL = orquestrador_4f.ref_aprovavel(PIPELINE)

HANDOFF = regenerar_derivados.HANDOFF          # "handoff-melhoria.json" — chave do mapa
LIVRO = "docs/livros/mapas-aidd"                 # chave de pasta do mapa
PAGINA_LIVRO = f"{LIVRO}/pagina.md"              # arquivo DENTRO da chave de pasta
CODIGO = "scripts/modulo.py"                      # código: nunca é derivado

# Conteúdo de "regenerado": distinto dos dois lados do conflito, para provar que o
# que entrou no merge foi o gerador e não o 'theirs' do checkout. indexed pela chave
# do mapa -> {caminho dentro da chave: conteúdo}, porque a chave pode ser uma pasta.
CONTEUDO_REGENERADO = {
    HANDOFF: {"handoff-melhoria.json": '{"artefatos": [], "regenerado": true}\n'},
    LIVRO: {"pagina.md": "# pagina regenerada\n"},
    regenerar_derivados.BASELINE: {".secrets.baseline": '{"results": {}, "regenerado": true}\n'},
}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def _git_tente(repo: Path, *args: str):
    """git sem check: devolve (returncode, stdout) para estados ausentes."""
    res = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    return res.returncode, res.stdout.strip()


def _escrever(repo: Path, relativo: str, texto: str) -> None:
    destino = repo / relativo
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(texto.encode("utf-8"))  # LF: o git não converte com autocrlf=false


CONTEUDO_BASE = {
    CODIGO: "VALOR = 'base'\n",
    HANDOFF: '{"artefatos": [{"caminho": "scripts/modulo.py", "tag": "base"}]}\n',
    PAGINA_LIVRO: "# pagina base\n",
    regenerar_derivados.BASELINE: '{"results": {}, "tag": "base"}\n',
}


def _cenario(tmp_path, toca_main):
    """Repo real: main x branch do ciclo já aprovável, divergindo nos arquivos de toca_main.

    A branch do ciclo altera TODOS os arquivos de CONTEUDO_BASE; a main altera só os
    listados em toca_main, cada um com conteúdo diferente do do ciclo (conflito garantido).
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "core.autocrlf", "false")
    for relativo, texto in CONTEUDO_BASE.items():
        _escrever(repo, relativo, texto)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")

    _git(repo, "checkout", "-q", "-b", BRANCH_CICLO)
    for relativo, texto in CONTEUDO_BASE.items():
        _escrever(repo, relativo, texto.replace("base", "ciclo"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "ciclo")
    _git(repo, "update-ref", REF_APROVAVEL, "HEAD")
    _git(repo, "checkout", "-q", "main")
    for relativo in toca_main:
        _escrever(repo, relativo, CONTEUDO_BASE[relativo].replace("base", "main"))
    if toca_main:
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "main")
    return repo


def _manifesto(tmp_path) -> Path:
    """Manifesto FORA do repo: o assert de 'git status limpo' não pode blisterar untracked."""
    m = tmp_path / "manifesto.json"
    m.write_text(json.dumps({"pipeline_id": PIPELINE, "target_tool": "agilidade-gates",
                             "ciclo": "ciclo-01", "gate_final": "exit 0", "fases": []}),
                 encoding="utf-8")
    return m


def _aprovar(repo: Path, monkeypatch, manifesto: Path) -> int:
    monkeypatch.chdir(repo)
    monkeypatch.setattr(sys, "argv", ["orquestrador_4f.py", "--manifest", str(manifesto), "--aprovar"])
    try:
        orquestrador_4f.main()
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def _regenerador(chamadas, erro=None):
    """Dublê do gerador: registra as chaves pedidas e grava conteúdo inequívoco."""
    def falso(repo_root, chaves):
        chamadas.append(list(chaves))
        if erro:
            raise erro
        for chave in chaves:
            raiz = Path(repo_root) / chave
            # Chave de pasta: o gerador escreve DENTRO dela; chave de arquivo: nela mesma.
            base = raiz if raiz.is_dir() else raiz.parent
            prefixo = base.relative_to(Path(repo_root)).as_posix()
            for interno, texto in CONTEUDO_REGENERADO[chave].items():
                _escrever(Path(repo_root), f"{prefixo}/{interno}", texto)
    return falso


def _status_limpo(repo: Path) -> bool:
    return _git(repo, "status", "--porcelain") == ""


def _em_merge(repo: Path) -> bool:
    return _git_tente(repo, "rev-parse", "--verify", "--quiet", "MERGE_HEAD")[0] == 0


def _pais_do_topo(repo: Path) -> list:
    return _git(repo, "log", "-1", "--format=%P").split()


# ======================================================================
# 1. Conflito só em derivado: o merge FINA, sozinho.
# ======================================================================

def test_conflito_somente_em_derivado_fina_o_merge(tmp_path, monkeypatch, capsys):
    repo = _cenario(tmp_path, [HANDOFF])
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "_regenerar_derivados", _regenerador(chamadas))
    main_antes = _git(repo, "rev-parse", "main")

    assert _aprovar(repo, monkeypatch, _manifesto(tmp_path)) == 0

    # O gerador canônico foi chamado com a chave exata do conflito.
    assert chamadas == [[HANDOFF]]
    # O que entrou no merge é o conteúdo REGENERADO, não o 'theirs' do checkout.
    assert (repo / HANDOFF).read_text(encoding="utf-8") == CONTEUDO_REGENERADO[HANDOFF]["handoff-melhoria.json"]
    # Merge de fato concluído: commit de merge com 2 pais, MERGE_HEAD limpo, status limpo.
    assert _pais_do_topo(repo) and len(_pais_do_topo(repo)) == 2
    assert main_antes in _pais_do_topo(repo)
    assert not _em_merge(repo)
    assert _status_limpo(repo)
    # Join Barrier concluído: branch do ciclo e ref aprovável removidas.
    assert BRANCH_CICLO not in _git(repo, "branch", "--list")
    assert _git_tente(repo, "rev-parse", "--verify", "--quiet", REF_APROVAVEL)[0] != 0
    saida = capsys.readouterr().out
    assert HANDOFF in saida


def test_conflito_em_arquivo_dentro_de_derivado_de_pasta_fina_o_merge(tmp_path, monkeypatch):
    # A chave do mapa é a PASTA; o git reporta o ARQUIVO. O gerador recebe a pasta,
    # porque regenerar(so=...) só aceita chaves exatas.
    repo = _cenario(tmp_path, [PAGINA_LIVRO])
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "_regenerar_derivados", _regenerador(chamadas))

    assert _aprovar(repo, monkeypatch, _manifesto(tmp_path)) == 0
    assert chamadas == [[LIVRO]]
    assert (repo / PAGINA_LIVRO).read_text(encoding="utf-8") == CONTEUDO_REGENERADO[LIVRO]["pagina.md"]
    assert len(_pais_do_topo(repo)) == 2
    assert _status_limpo(repo)


def test_conflito_em_varios_derivados_regenera_todos_de_uma_vez(tmp_path, monkeypatch):
    repo = _cenario(tmp_path, [HANDOFF, PAGINA_LIVRO])
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "_regenerar_derivados", _regenerador(chamadas))

    assert _aprovar(repo, monkeypatch, _manifesto(tmp_path)) == 0
    assert chamadas == [[LIVRO, HANDOFF]]  # ordem do mapa, não a alfabética do git
    assert _status_limpo(repo)


def test_conflito_no_secrets_baseline_fina_o_merge(tmp_path, monkeypatch):
    # .secrets.baseline é o derivado que mais conflita: os hashes são recalculados
    # pelo ciclo e pela main, cada um por conta própria.
    repo = _cenario(tmp_path, [regenerar_derivados.BASELINE])
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "_regenerar_derivados", _regenerador(chamadas))

    assert _aprovar(repo, monkeypatch, _manifesto(tmp_path)) == 0
    assert chamadas == [[regenerar_derivados.BASELINE]]
    assert (repo / regenerar_derivados.BASELINE).read_text(encoding="utf-8") == CONTEUDO_REGENERADO[regenerar_derivados.BASELINE][".secrets.baseline"]
    assert len(_pais_do_topo(repo)) == 2
    assert _status_limpo(repo)


# ======================================================================
# 2. Conflito em código: ABORTA, árvore limpa, exit 1.
# ======================================================================

def test_conflito_em_codigo_aborta_o_merge_com_arvore_limpa(tmp_path, monkeypatch, capsys):
    repo = _cenario(tmp_path, [CODIGO])
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "_regenerar_derivados", _regenerador(chamadas))
    main_antes = _git(repo, "rev-parse", "main")

    assert _aprovar(repo, monkeypatch, _manifesto(tmp_path)) == 1

    # Nada pela metade: sem merge em andamento, sem resíduo na árvore, main intacta.
    assert not _em_merge(repo)
    assert _status_limpo(repo)
    assert _git(repo, "rev-parse", "main") == main_antes
    assert _git(repo, "rev-parse", "HEAD") == main_antes
    # Nada foi regenerado: conflito de código não é para o gerador resolver.
    assert chamadas == []
    # O ciclo continua aprovável: a ref e a branch sobrevivem para o humano resolver.
    assert BRANCH_CICLO in _git(repo, "branch", "--list")
    assert _git_tente(repo, "rev-parse", "--verify", "--quiet", REF_APROVAVEL)[0] == 0
    saida = capsys.readouterr().out
    assert CODIGO in saida
    assert "abort" in saida.lower()


def test_conflito_misto_aborta_sem_regenerar_nada(tmp_path, monkeypatch, capsys):
    repo = _cenario(tmp_path, [HANDOFF, CODIGO])
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "_regenerar_derivados", _regenerador(chamadas))

    assert _aprovar(repo, monkeypatch, _manifesto(tmp_path)) == 1
    assert chamadas == []
    assert not _em_merge(repo)
    assert _status_limpo(repo)
    saida = capsys.readouterr().out
    assert CODIGO in saida and HANDOFF in saida


# ======================================================================
# 3. Falha do gerador também aborta (derivado pela metade é pior que conflito).
# ======================================================================

def test_falha_ao_regenerar_derivado_aborta_o_merge(tmp_path, monkeypatch, capsys):
    repo = _cenario(tmp_path, [HANDOFF])
    chamadas = []
    monkeypatch.setattr(orquestrador_4f, "_regenerar_derivados",
                        _regenerador(chamadas, erro=RuntimeError("hmac sem chave")))
    main_antes = _git(repo, "rev-parse", "main")

    assert _aprovar(repo, monkeypatch, _manifesto(tmp_path)) == 1
    assert chamadas == [[HANDOFF]]
    assert not _em_merge(repo)
    assert _status_limpo(repo)
    assert _git(repo, "rev-parse", "HEAD") == main_antes
    assert "hmac sem chave" in capsys.readouterr().out


# ======================================================================
# 4. Nada além dos derivados entra no merge.
# ======================================================================

def test_merge_de_derivado_nao_empacota_lixo_nao_versionado(tmp_path, monkeypatch):
    # Arquivo não rastreado no meio do conflito é lixo do desenvolvedor: o merge
    # fecha sem varrê-lo (o commit de fase usa 'git add -A', o Join Barrier não).
    repo = _cenario(tmp_path, [HANDOFF])
    (repo / "lixo.txt").write_text("nao versionado\n", encoding="utf-8")
    monkeypatch.setattr(orquestrador_4f, "_regenerar_derivados", _regenerador([]))

    assert _aprovar(repo, monkeypatch, _manifesto(tmp_path)) == 0
    assert _git(repo, "status", "--porcelain") == "?? lixo.txt"


# ======================================================================
# 5. Classificação pura: o mapa DERIVADOS decide, sem git.
# ======================================================================

@pytest.mark.parametrize("conflito,chave_esperada", [
    (HANDOFF, HANDOFF),
    ("docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json", "docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json"),
    (PAGINA_LIVRO, LIVRO),
    ("docs/livros/mapas-aidd/sub/longe.md", LIVRO),
    ("PLANO-EXECUCAO-ESTRUTURADO.json", "PLANO-EXECUCAO-ESTRUTURADO.json"),
    ("handoff-melhoria.json.bak", None),                      # prefixo de nome, não o arquivo
    ("docs/auditoria/mapa-pecas/ciclo-02/ACHADOS.json", None),  # só o ciclo-01 está no mapa
    ("docs/livros/mapas-aidd-extra/pagina.md", None),          # pasta irmã com prefixo em comum
    ("docs/livros/mapas-aidd2.md", None),
    (CODIGO, None),
    ("MEMORY.md", None),
])
def test_classificacao_de_conflito_usa_o_mapa_canonico(conflito, chave_esperada):
    assert orquestrador_4f._chave_derivado(conflito, list(regenerar_derivados.DERIVADOS)) == chave_esperada


def test_classificacao_separa_derivados_de_fora_na_ordem_do_mapa():
    chaves, fora = orquestrador_4f._classificar_conflitos(
        [HANDOFF, PAGINA_LIVRO, CODIGO, HANDOFF], list(regenerar_derivados.DERIVADOS))
    assert chaves == [LIVRO, HANDOFF]  # ordem canônica do mapa (dependência), sem repetir
    assert fora == [CODIGO]