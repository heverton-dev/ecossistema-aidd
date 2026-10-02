# -*- coding: utf-8 -*-
"""
Almoxarifado único com catálogo (fronteiras-ferramentas ciclo-01, Ticket 8, D15).

Regras:
  - As famílias de cópias saem da foto do inventário (INVENTARIO-ANTES.json, Ticket 3), não do
    catálogo: gate de projeto, molde do Quarteto, molde de infra, injetor, sincronizador de
    harness e núcleo src-core. Toda cópia de cada família tem de estar no catálogo (como peça
    ou como cópia de uma peça).
  - Cada peça mora em componentes/compartilhado/{gates,src-core,moldes/quarteto,moldes/infra,
    injetor,specs}/ e traz dono_do_conteudo, versao, sha256 (do arquivo de hoje, como digest
    'sha256-<hex>') e consumidores.
  - Uma peça = a versão principal + as variantes dela. Variante só existe com motivo:
      implementacao_independente  mesmo nome, outra ferramenta, outra API (DIAGNOSTICO Etapa 2, item 7);
      versao_divergente           mesma linhagem: as capacidades foram juntadas na principal e o texto
                                  original fica guardado até a remoção com o usuário (Ticket 19);
      renderizado                 saída já renderizada do molde, servida pela própria ferramenta.
  - Zero perda: cada função, classe, teste e linha (fora .md) de cada cópia existe na peça; função e
    classe de cópia da mesma linhagem existem na principal; e `inventario_capacidades.py comparar`
    dá zero órfão entre todas as cópias e o almoxarifado.
  - materiais-extras/examples fica fora (D4: vira arquivo histórico fora do repo, não peça).
  - As cópias antigas continuam no lugar nesta fase.
"""

import hashlib
import json
import py_compile
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))
import inventario_capacidades as inv  # noqa: E402

ALMOXARIFADO = "componentes/compartilhado"
CATALOGO = ROOT_DIR / ALMOXARIFADO / "CATALOGO.json"
FOTO = ROOT_DIR / "docs/auditoria/fronteiras-ferramentas/ciclo-01/INVENTARIO-ANTES.json"
APELIDOS = ROOT_DIR / inv.TABELA_APELIDOS
SCRIPT = ROOT_DIR / "scripts" / "inventario_capacidades.py"

PASTAS = ("gates", "src-core", "moldes/quarteto", "moldes/infra", "injetor", "specs")
FERRAMENTAS = ("aidd-forge", "aidd-planner", "aidd-pure", "aidd-open", "aidd-freedom",
               "aidd-master", "aidd-enterprise", "aidd-ops")
CONSUMIDORES_VALIDOS = FERRAMENTAS + ("ecossistema-raiz",)
EXEMPLOS = "/materiais-extras/examples/"
CAMPOS = ("nome", "caminho", "categoria", "familia", "papel", "dono_do_conteudo", "versao",
          "sha256", "consumidores", "copias")
TIPOS_VARIANTE = ("implementacao_independente", "versao_divergente", "renderizado")

RE_GATE = re.compile(r"/(templates/gates|scripts/gates|sandbox-forge-teste/gates)/G_[A-Za-z0-9_]+\.py$")
QUARTETO = {"mcp_server.py", "mcp_studio.html", "webhooks.py", "webhook_studio.html",
            "openapi.py", "swagger.html", "docs.html", "openapi.json.j2"}
RE_QUARTETO = re.compile(r"^tools/aidd-[a-z]+/(templates/(core|v2|vsa|docs)|src/static)/[^/]+$")
INFRA = {"Dockerfile", "docker-compose.yml", "deploy.sh", "nginx.conf", "generate_ssl.py"}
RE_INFRA = re.compile(r"^tools/aidd-[a-z]+/templates/(core|v2|vsa)/")
RE_INJETOR = re.compile(
    r"^tools/aidd-pure/scripts/(core/injector/[^/]+|aidd_inject\.py)$"
    r"|^tools/aidd-forge/aidd_forge/(core/(injector|injector_profiles|universal_injector"
    r"|injection_schema|materializador)\.py|schemas/injection_request\.schema\.json)$"
    r"|^tools/aidd-(master|enterprise)/application/commands/inject\.py$"
    r"|^tools/aidd-(master|enterprise)/src/core/(detector_camada\.py|profiles_registry\.py"
    r"|schema_injector_request\.json)$"
    r"|^tools/aidd-enterprise/scripts/injector/")


def _ferramentas_renomeadas():
    return json.loads(APELIDOS.read_text(encoding="utf-8"))["ferramentas"]


def _caminho_atual(rel):
    """Caminho da foto (nomes antigos) traduzido para o nome de hoje da ferramenta."""
    partes = rel.split("/")
    if len(partes) > 1 and partes[0] == "tools":
        partes[1] = _ferramentas_renomeadas().get(partes[1], partes[1])
    return "/".join(partes)


def _src_core_espelhos():
    manifesto = json.loads((ROOT_DIR / ALMOXARIFADO / "src-core/MANIFEST.json").read_text(encoding="utf-8"))
    return {f"{destino}/{arquivo}" for destino in manifesto["destinos"] for arquivo in manifesto["arquivos"]}


def _categoria(rel, espelhos):
    if EXEMPLOS in rel:
        return None
    nome = PurePosixPath(rel).name
    if RE_GATE.search(rel):
        return "gate de projeto"
    if nome in QUARTETO and RE_QUARTETO.match(rel):
        return "molde do Quarteto"
    if nome in INFRA and RE_INFRA.match(rel):
        return "molde de infra"
    if RE_INJETOR.search(rel):
        return "injetor"
    if nome == "sincronizador_harness.py":
        return "sincronizador de harness"
    if rel in espelhos or rel.startswith(f"{ALMOXARIFADO}/src-core/"):
        return "núcleo src-core"
    return None


def familias_do_inventario():
    """{(categoria, nome do arquivo): [caminhos de hoje]} a partir da foto do Ticket 3."""
    foto = json.loads(FOTO.read_text(encoding="utf-8"))
    espelhos = _src_core_espelhos()
    familias = {}
    for rel_foto in foto:
        rel = _caminho_atual(rel_foto)
        categoria = _categoria(rel, espelhos)
        if categoria:
            familias.setdefault((categoria, PurePosixPath(rel).name), []).append(rel)
    # Gate de projeto: só o que tem cópia em 2+ lugares ou é instalado de templates/gates.
    return {chave: sorted(copias) for chave, copias in familias.items()
            if chave[0] != "gate de projeto" or len(copias) > 1
            or any("/templates/gates/" in c for c in copias)}


def _sha256(caminho):
    """Digest 'sha256-<hex>': hex puro entre aspas o detect-secrets acusa como credencial (Ticket 3)."""
    return "sha256-" + hashlib.sha256(caminho.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def catalogo():
    assert CATALOGO.is_file(), f"catálogo ausente: {CATALOGO.relative_to(ROOT_DIR).as_posix()}"
    dados = json.loads(CATALOGO.read_text(encoding="utf-8"))
    assert dados.get("pecas"), "CATALOGO.json sem 'pecas'"
    return dados


@pytest.fixture(scope="module")
def pecas(catalogo):
    return catalogo["pecas"]


def test_foto_do_inventario_tem_as_seis_categorias():
    categorias = {cat for cat, _ in familias_do_inventario()}
    assert categorias == {"gate de projeto", "molde do Quarteto", "molde de infra", "injetor",
                          "sincronizador de harness", "núcleo src-core"}


def test_cada_peca_tem_os_campos_e_o_sha256_de_hoje(pecas):
    nomes = [p.get("nome") for p in pecas]
    assert len(nomes) == len(set(nomes)), "nome de peça repetido no catálogo"
    for peca in pecas:
        faltando = [c for c in CAMPOS if c not in peca]
        assert not faltando, f"{peca.get('nome')}: faltam {faltando}"
        assert peca["caminho"].startswith(f"{ALMOXARIFADO}/"), peca["nome"]
        assert peca["nome"] == peca["caminho"][len(ALMOXARIFADO) + 1:], peca["nome"]
        assert any(peca["nome"].startswith(f"{pasta}/") for pasta in PASTAS), \
            f"{peca['nome']}: fora de {PASTAS}"
        arquivo = ROOT_DIR / peca["caminho"]
        assert arquivo.is_file(), f"peça sem arquivo: {peca['caminho']}"
        assert peca["sha256"] == _sha256(arquivo), f"sha256 desatualizado: {peca['nome']}"
        assert peca["dono_do_conteudo"] in FERRAMENTAS, peca["nome"]
        assert re.fullmatch(r"\d+\.\d+\.\d+", peca["versao"]), peca["nome"]
        assert peca["consumidores"] and set(peca["consumidores"]) <= set(CONSUMIDORES_VALIDOS), peca["nome"]
        assert peca["papel"] in ("principal", "variante"), peca["nome"]
        if peca["papel"] == "variante":
            principal = next((p for p in pecas if p["nome"] == peca.get("variante_de")), None)
            assert principal and principal["papel"] == "principal", f"{peca['nome']}: variante_de inválido"
            assert peca.get("tipo_variante") in TIPOS_VARIANTE, peca["nome"]
            assert peca.get("motivo"), f"{peca['nome']}: variante sem motivo"
            assert "/variantes/" in peca["nome"], f"{peca['nome']}: variante fora de variantes/"


def test_consumidores_incluem_toda_ferramenta_que_guarda_copia(pecas):
    for peca in pecas:
        donos_das_copias = {c.split("/")[1] for c in peca["copias"] if c.startswith("tools/")}
        faltando = donos_das_copias - set(peca["consumidores"])
        assert not faltando, f"{peca['nome']}: consumidores sem {sorted(faltando)}"


def test_toda_familia_do_inventario_esta_no_catalogo(pecas):
    cobertos = {}
    for peca in pecas:
        for rel in [peca["caminho"], *peca["copias"]]:
            assert rel not in cobertos, f"{rel} em duas peças: {cobertos.get(rel)} e {peca['nome']}"
            cobertos[rel] = peca["nome"]
    faltando = []
    for (categoria, familia), copias in sorted(familias_do_inventario().items()):
        for rel in copias:
            assert (ROOT_DIR / rel).is_file(), f"cópia antiga sumiu (tem de ficar no lugar): {rel}"
            if rel not in cobertos:
                faltando.append(f"{categoria} / {familia}: {rel}")
    assert not faltando, f"{len(faltando)} cópia(s) fora do catálogo:\n" + "\n".join(faltando[:40])


def test_catalogo_tem_peca_de_cada_pasta_e_o_sincronizador(pecas):
    for pasta in PASTAS:
        assert any(p["nome"].startswith(f"{pasta}/") for p in pecas), f"nenhuma peça em {pasta}/"
    assert any(p["familia"] == "sincronizador_harness.py" for p in pecas)


def test_pecas_python_e_json_sao_validas(pecas, tmp_path):
    for peca in pecas:
        arquivo = ROOT_DIR / peca["caminho"]
        if arquivo.suffix == ".py":
            py_compile.compile(str(arquivo), cfile=str(tmp_path / "x.pyc"), doraise=True)
        elif arquivo.suffix == ".json":
            json.loads(arquivo.read_text(encoding="utf-8"))


def _conteudo(rel, trocas, trocas_sem_caixa):
    texto = (ROOT_DIR / rel).read_text(encoding="utf-8")
    nomes = set()
    if rel.endswith(".py"):
        funcoes, classes, testes = inv._capacidades(texto)
        nomes = {("funcoes", n) for n in funcoes} | {("classes", n) for n in classes} \
            | {("testes", n) for n in testes}
    linhas = set()
    if not rel.endswith(inv.SEM_COMPARAR_LINHAS):
        linhas = {inv._traduzir(l.lower(), trocas_sem_caixa) for l in inv._linhas_unicas(texto)}
    return {(t, inv._traduzir(n, trocas)) for t, n in nomes}, linhas


def _grupos(pecas):
    """{nome da principal: [principal, *variantes]}."""
    grupos = {p["nome"]: [p] for p in pecas if p["papel"] == "principal"}
    for p in pecas:
        if p["papel"] == "variante":
            grupos[p["variante_de"]].append(p)
    return grupos


def test_cada_peca_guarda_todo_o_conteudo_unico_das_suas_copias(pecas):
    trocas = inv.carregar_apelidos(APELIDOS)
    trocas_sem_caixa = {a.lower(): n.lower() for a, n in trocas.items()}
    orfas = []
    for nome, grupo in _grupos(pecas).items():
        nomes_principal, _ = _conteudo(grupo[0]["caminho"], trocas, trocas_sem_caixa)
        nomes_grupo, linhas_grupo = set(), set()
        for item in grupo:
            n, l = _conteudo(item["caminho"], trocas, trocas_sem_caixa)
            nomes_grupo |= n
            linhas_grupo |= l
        for item in grupo:
            mesma_linhagem = item.get("tipo_variante") != "implementacao_independente"
            for copia in item["copias"]:
                nomes, linhas = _conteudo(copia, trocas, trocas_sem_caixa)
                referencia = nomes_principal if mesma_linhagem else nomes_grupo
                orfas += [f"{nome} <- {copia}: {t} {n}" for t, n in sorted(nomes - referencia)]
                orfas += [f"{nome} <- {copia}: linha {l[:100]!r}" for l in sorted(linhas - linhas_grupo)]
    assert not orfas, f"{len(orfas)} órfão(s):\n" + "\n".join(orfas[:60])


def _repo(destino, arquivos):
    destino.mkdir()
    for rel in arquivos:
        alvo = destino / rel
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT_DIR / rel, alvo)
    for args in (["init", "-q"], ["add", "-A"]):
        subprocess.run(["git", *args], cwd=destino, check=True, capture_output=True)
    return destino


def test_comparar_da_zero_orfao_entre_todas_as_copias_e_o_almoxarifado(pecas, tmp_path):
    copias = sorted({c for p in pecas for c in p["copias"]})
    repo_copias = _repo(tmp_path / "copias", copias)
    repo_almox = _repo(tmp_path / "almoxarifado", [p["caminho"] for p in pecas])
    foto = subprocess.run([sys.executable, str(SCRIPT), "foto", "--repo", str(repo_copias),
                           "--cycle", "foto"], capture_output=True, text=True, encoding="utf-8")
    assert foto.returncode == 0, foto.stdout + foto.stderr
    comparar = subprocess.run([sys.executable, str(SCRIPT), "comparar",
                               str(repo_copias / "foto" / inv.NOME_FOTO), "--repo", str(repo_almox),
                               "--apelidos", str(APELIDOS)],
                              capture_output=True, text=True, encoding="utf-8")
    assert comparar.returncode == 0, comparar.stdout + comparar.stderr
    assert "zero órfão" in comparar.stdout
