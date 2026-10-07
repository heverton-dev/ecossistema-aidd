# -*- coding: utf-8 -*-
"""
Ticket 4 (fronteiras-ferramentas ciclo-01, D14 / DoD 12): os construtores têm o
nome do fluxo que servem.

    tools/aidd-generator -> modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure     (Fluxo 01)
    tools/aidd-factory   -> modulos/02-triade-motores/fluxo-02-open/core/aidd-open     (Fluxo 02)
    tools/aidd-bridge    -> modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom  (Fluxo 03)

O teste varre os arquivos do repositório (rastreados + novos não ignorados) e
reprova se o nome antigo aparecer no caminho ou no conteúdo fora de dois
lugares permitidos:

1. a tabela de apelidos (componentes/compartilhado/specs/NOMES-ANTIGOS.json),
   única fonte dos nomes antigos que ainda funcionam por 1 ciclo;
2. os documentos históricos, que registram o passado e não são reescritos.

Também confere que os comandos antigos da CLI continuam funcionando como
apelido e avisam "nome antigo".
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
TABELA_APELIDOS = "componentes/compartilhado/specs/NOMES-ANTIGOS.json"
ESTE_TESTE = "tests/test_nomes_padronizados.py"

NOME_ANTIGO = re.compile(r"aidd[-_](generator|factory|bridge)", re.IGNORECASE)

# Repositórios separados no GitHub mantêm o nome antigo (renomear fica fora do
# Ticket 4 e precisa de confirmação própria do usuário).
REPO_EXTERNO = re.compile(r"heverton-dev/aidd-(generator|factory|bridge)", re.IGNORECASE)

# Documentos históricos: registram o que aconteceu com o nome da época.
HISTORICO = (
    re.compile(r"(^|/)secoes/"),                          # sessões registradas
    re.compile(r"^docs/relatorios/"),                     # relatórios gerados
    re.compile(r"^docs/planos/feitos/"),                  # planos fechados
    re.compile(r"^docs/auditoria/historico_auditorias/"),  # auditorias antigas
    re.compile(r"^docs/auditoria/[^/]+/ciclo-\d+/"),       # registros de cada ciclo
    re.compile(r"^docs/(.+/)?\d{2}-\d{2}-\d{4}_[^/]+$"),  # documento datado = foto do dia (livros, melhorias...)
    re.compile(r"^(tools/aidd-enterprise|modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise)/materiais-extras/"),  # material de pesquisa arquivado
    re.compile(r"^(tools/aidd-enterprise|modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise)/materiais-extras/"),  # material de pesquisa arquivado migrado VSA
    re.compile(r"^(?!requirements)[^/]+\.txt$"),          # logs de evidência dos tickets na raiz
    # Fonte única dos dados do relatório datado 11-09-2026 (docs/relatorios/): um teste
    # o executa e regrava o relatório, então reescrevê-lo reescreveria o histórico.
    re.compile(r"^scripts/gerador_relatorio_evolucao_planos\.py$"),
    # Livro gerado e teste de conformidade de livros que testam a menção explícita de apelidos
    re.compile(r"^docs/livros/gerar_livro_auditoria\.py$"),
    re.compile(r"^tests/test_mapas_e_livros_em_dia\.py$"),
)

PERMITIDOS = {TABELA_APELIDOS, ESTE_TESTE}

# Planos fechados guardam o nome da época no próprio ID (ex.: PLAN-0020-...):
# citar esse ID em outro lugar (catálogo, mapas) aponta para o registro histórico.
PLANOS_FECHADOS = RAIZ / "docs" / "planos" / "feitos"

FERRAMENTAS = {
    "aidd-generator": "aidd-pure",
    "aidd-factory": "aidd-open",
    "aidd-bridge": "aidd-freedom",
}
PACOTES = {
    "aidd_generator": "aidd_pure",
    "aidd_factory": "aidd_open",
    "aidd_bridge": "aidd_freedom",
}


def _arquivos_do_repo():
    saida = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=RAIZ, capture_output=True, check=True,
    ).stdout
    caminhos = sorted({c.decode("utf-8") for c in saida.split(b"\0") if c})
    return [c for c in caminhos if (RAIZ / c).is_file()]


def _e_permitido(caminho):
    return caminho in PERMITIDOS or any(p.search(caminho) for p in HISTORICO)


def _ids_congelados():
    if not PLANOS_FECHADOS.is_dir():
        return re.compile(r"(?!)")
    ids = sorted((p.name for p in PLANOS_FECHADOS.iterdir()
                  if p.is_dir() and NOME_ANTIGO.search(p.name)), key=len, reverse=True)
    return re.compile("|".join(map(re.escape, ids)) or r"(?!)")


IDS_CONGELADOS = _ids_congelados()


def _ocorrencias(texto):
    texto = IDS_CONGELADOS.sub("", REPO_EXTERNO.sub("", texto))
    return [m for m in NOME_ANTIGO.finditer(texto)]


@pytest.fixture(scope="module")
def arquivos():
    return [c for c in _arquivos_do_repo() if not _e_permitido(c)]


@pytest.fixture(scope="module")
def tabela():
    caminho = RAIZ / TABELA_APELIDOS
    assert caminho.is_file(), f"falta a tabela de apelidos {TABELA_APELIDOS}"
    return json.loads(caminho.read_text(encoding="utf-8"))


def test_tabela_de_apelidos_mapeia_ferramentas_e_pacotes(tabela):
    assert tabela["ferramentas"] == FERRAMENTAS
    assert tabela["pacotes_python"] == PACOTES
    comandos = tabela["comandos_cli"]
    for antigo in ("generate", "factory", "bridge", *FERRAMENTAS):
        assert antigo in comandos, f"comando antigo sem apelido: {antigo}"


@pytest.mark.parametrize("antigo,novo", sorted(FERRAMENTAS.items()))
def test_pasta_da_ferramenta_tem_o_nome_do_fluxo(antigo, novo):
    sys.path.insert(0, str(RAIZ / "scripts"))
    from pastas_ferramentas import pasta_ferramenta

    assert not (RAIZ / "tools" / antigo).exists(), f"tools/{antigo} ainda existe"
    pasta = pasta_ferramenta(novo, RAIZ)
    assert not (pasta.parent / antigo).exists(), f"{antigo} ainda existe ao lado de {novo}"
    assert (pasta / "README.md").is_file(), f"{pasta} sem README"


def test_pacote_python_do_freedom_renomeado():
    assert (RAIZ / "modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom/aidd_freedom/__init__.py").is_file()
    assert not (RAIZ / "modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom/aidd_bridge").exists()


def test_nenhum_caminho_com_nome_antigo(arquivos):
    sobra = [c for c in arquivos if NOME_ANTIGO.search(c)]
    assert not sobra, f"{len(sobra)} caminho(s) com nome antigo, ex.: {sobra[:15]}"


BASELINE_SEGREDOS = ".secrets.baseline"


def _baseline_sem_historico(texto):
    """O baseline de segredos indexa achados pelo caminho do arquivo: documento histórico
    guarda o nome antigo no caminho, então a chave também (renomeá-la reprovou o G_SEGREDOS
    no gate_final de 01/10). Só sobra para conferir o que aponta para arquivo vivo."""
    resultados = json.loads(texto).get("results", {})
    return "\n".join(c for c in resultados if not _e_permitido(c.replace("\\", "/")))


def test_nenhum_conteudo_com_nome_antigo(arquivos):
    sobra = {}
    for caminho in arquivos:
        dados = (RAIZ / caminho).read_bytes()
        if b"\0" in dados:  # binário
            continue
        texto = dados.decode("utf-8", errors="ignore")
        if caminho == BASELINE_SEGREDOS:
            texto = _baseline_sem_historico(texto)
        n = len(_ocorrencias(texto))
        if n:
            sobra[caminho] = n
    piores = sorted(sobra.items(), key=lambda kv: -kv[1])[:15]
    assert not sobra, (
        f"{len(sobra)} arquivo(s) / {sum(sobra.values())} ocorrência(s) com nome antigo, "
        f"ex.: {piores}"
    )


def test_historico_nao_mascara_codigo_vivo():
    # Os filtros de histórico nunca podem cobrir código ou config das ferramentas.
    for vivo in ("ecossistema.py", "gates/G_X.py", "tests/test_x.py",
                 "modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/scripts/x.py", "componentes/compartilhado/skills/x/SKILL.md",
                 "docs/livros/partes/01-macro.md", "docs/planos/fazendo/x.md"):
        assert not _e_permitido(vivo), vivo
    assert _ocorrencias("ver heverton-dev/aidd-generator") == []
    assert _ocorrencias("plano PLAN-0020-aidd-bridge (feito)") == []
    assert len(_ocorrencias("PLAN-0099-aidd-bridge-novo")) == 1  # só IDs de planos fechados
    assert len(_ocorrencias("tools/aidd-generator e AIDD-Bridge")) == 2
    baseline = json.dumps({"results": {
        "docs\\melhorias\\14-09-2026_melhoria-aidd-factory-plano.json": [],  # histórico: liberado
        "tools\\aidd-factory\\scripts\\x.py": [],                          # vivo: reprova
    }})
    assert len(_ocorrencias(_baseline_sem_historico(baseline))) == 1


@pytest.mark.parametrize("antigo", ["generate", "factory", "bridge",
                                    "aidd-generator", "aidd-factory", "aidd-bridge"])
def test_comando_antigo_vira_apelido_com_aviso(tabela, antigo):
    sys.path.insert(0, str(RAIZ))
    try:
        import ecossistema
    finally:
        sys.path.pop(0)
    novo = tabela["comandos_cli"][antigo]
    comandos = ecossistema.comandos_disponiveis()
    assert novo in comandos, f"apelido {antigo} aponta para comando inexistente {novo}"
    assert antigo in comandos, f"comando antigo {antigo} deixou de funcionar"


def test_auto_ingest_nao_ressuscita_skill_com_nome_antigo(tmp_path, monkeypatch):
    # Cópia velha esquecida numa pasta de harness ignorada pelo git (caso real:
    # .codebuddy/skills/aidd-generator) não pode voltar para a fonte canônica.
    sys.path.insert(0, str(RAIZ / "scripts"))
    try:
        import gestor_componentes as gc
    finally:
        sys.path.pop(0)
    assert gc.nomes_antigos_de_skill() == set(FERRAMENTAS)
    for nome in ("aidd-generator", "skill-nova-de-verdade"):
        pasta = tmp_path / ".claude" / "skills" / nome
        pasta.mkdir(parents=True)
        (pasta / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    (tmp_path / "componentes" / "compartilhado" / "skills").mkdir(parents=True)
    monkeypatch.setattr(gc, "ROOT_DIR", str(tmp_path))
    monkeypatch.setattr(gc, "COMPONENTES_DIR", str(tmp_path / "componentes"))
    ingeridas = gc.auto_ingest_skills(dry_run=True)
    assert [i.split(" ")[0] for i in ingeridas] == ["skill-nova-de-verdade"]


def test_apelido_na_cli_real_avisa_nome_antigo(tabela):
    saida = subprocess.run(
        [sys.executable, "ecossistema.py", "factory", "--help"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    texto = saida.stdout + saida.stderr
    assert saida.returncode == 0, texto[-2000:]
    assert "nome antigo" in texto.lower(), texto[-2000:]
    assert tabela["comandos_cli"]["factory"] in texto, texto[-2000:]
