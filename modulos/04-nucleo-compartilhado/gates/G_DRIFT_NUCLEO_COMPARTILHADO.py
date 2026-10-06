# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_DRIFT_NUCLEO_COMPARTILHADO
=============================================================================
Detecta divergência silenciosa entre pares de diretórios que nasceram da
mesma linhagem e compartilham arquivos byte-a-byte idênticos (R3 do
PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md, ampliado pelo item 2 e pelo
item 5 de docs/planos/fazendo/correcao-arquitetura-limpa/).

Dois tipos de par sao cobertos hoje (ver PARES abaixo):
- Cross-tool: src/core, scripts, scripts/gates, templates/core e
  templates/v2 — mesma subpasta relativa comparada entre
  tools/aidd-master/ e tools/aidd-enterprise/.
- Intra-tool (item 5): scripts/gates/ vs templates/gates/ dentro da MESMA
  ferramenta (aidd-enterprise e aidd-master, separadamente) — a versao
  viva que protege este monorepo comparada com a versao entregue a
  projetos novos gerados a partir do template.

- Catalogo (Ticket 18, fronteiras-ferramentas ciclo-01): cada copia listada em
  componentes/compartilhado/CATALOGO.json ("copias" de cada peca) e comparada
  com a versao do catalogo (o sha256 selado da peca), nao so entre master e
  enterprise. Divergencia so passa se documentada em
  baseline["catalogo"]["divergencias_documentadas"][<copia>] com motivo.
  D4 (decisao do usuario, 01/10/2026): tools/aidd-enterprise/materiais-extras/
  examples/** e arquivo historico fora do almoxarifado — nunca e comparado.
  Os pares acima continuam valendo para os arquivos que o catalogo nao cobre
  (ex.: scripts/aidd.py, scripts/add_module.py).

Em ambos os casos as pastas sao mantidas como copias independentes por
decisao explicita (nenhum acoplamento de runtime entre ferramentas nem
entre scripts/ e templates/ de uma mesma ferramenta, preservando a
independencia de cada uma).

Esse desenho tem um custo: se alguém corrige um bug em uma cópia e esquece
a outra, nada acusava isso antes deste gate. A correção NÃO é criar uma
dependência de runtime entre as ferramentas (isso quebraria a promessa de
"ferramenta autocontida" do AGENTS.md) — é comparar hashes e falhar quando
um par que deveria estar sincronizado (baseline_nucleo_compartilhado.json)
divergir sem essa mudança ter sido documentada.

Uso:
  python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py
      Roda a checagem em todos os pares de PARES. exit 0 = sem drift não
      documentado em nenhum par. exit 1 = drift encontrado ou baseline
      desatualizado (arquivo novo não catalogado) em algum par.

  python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py --atualizar-baseline
      Regrava o baseline refletindo o estado atual de todos os pares (todo
      arquivo idêntico vira esperado_identico=true; todo arquivo divergente
      vira esperado_identico=false com motivo placeholder "REVISAR: ..."
      exigindo edição manual do texto do motivo antes do commit — o
      veredito identico/divergente em si nunca é editado a mão, sempre vem
      do hash). Use isso só depois de uma decisão deliberada de aceitar uma
      nova divergência — nunca como forma de "silenciar" o gate.
"""

import hashlib
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE_PATH = os.path.join(ROOT_DIR, "gates", "baseline_nucleo_compartilhado.json")
CATALOGO_PATH = os.path.join(ROOT_DIR, "componentes", "compartilhado", "CATALOGO.json")

# D4: arquivo historico, fora do almoxarifado (CATALOGO.json -> fora_do_almoxarifado).
PREFIXOS_D4 = ("tools/aidd-enterprise/materiais-extras/examples/",)

DESCRICAO_CATALOGO = (
    "Copias de pecas do CATALOGO.json que divergem de proposito da versao do catalogo "
    "(chave = caminho da copia, valor = motivo). Toda outra copia tem de ser byte-identica "
    "a peca. As copias saem do repo no Ticket 19 (remocao com o usuario)."
)


def _tools(*partes):
    return os.path.join(ROOT_DIR, "tools", *partes)


# Pares de diretorios comparados entre aidd-master e aidd-enterprise.
# Cada par tem sua propria chave no baseline (gates/baseline_nucleo_compartilhado.json)
# para nao colidir nomes de arquivo repetidos entre pares diferentes
# (ex.: "openapi.py" existe em src/core, templates/core e templates/v2 com
# conteudos e vereditos diferentes entre si).
PARES = [
    ("src/core", _tools("aidd-master", "src", "core"), _tools("aidd-enterprise", "src", "core")),
    ("scripts", _tools("aidd-master", "scripts"), _tools("aidd-enterprise", "scripts")),
    ("scripts/gates", _tools("aidd-master", "scripts", "gates"), _tools("aidd-enterprise", "scripts", "gates")),
    ("templates/core", _tools("aidd-master", "templates", "core"), _tools("aidd-enterprise", "templates", "core")),
    ("templates/v2", _tools("aidd-master", "templates", "v2"), _tools("aidd-enterprise", "templates", "v2")),
    # Pares intra-ferramenta (item 5): scripts/gates vs templates/gates DENTRO
    # da mesma ferramenta — nao cruza aidd-master com aidd-enterprise, compara
    # a versao viva (scripts/gates) com a versao entregue a projetos novos
    # (templates/gates) de uma unica ferramenta por vez.
    (
        "aidd-enterprise/scripts-gates-vs-templates-gates",
        _tools("aidd-enterprise", "scripts", "gates"),
        _tools("aidd-enterprise", "templates", "gates"),
    ),
    (
        "aidd-master/scripts-gates-vs-templates-gates",
        _tools("aidd-master", "scripts", "gates"),
        _tools("aidd-master", "templates", "gates"),
    ),
]

# Mantidos por compatibilidade: par historico (o unico que existia antes do item 2),
# usado por testes que ainda monkeypatcham DIR_A/DIR_B diretamente.
DIR_A = PARES[0][1]
DIR_B = PARES[0][2]


def _hash(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _arquivos_comuns(dir_a, dir_b):
    if not os.path.isdir(dir_a) or not os.path.isdir(dir_b):
        return []
    nomes_a = {f for f in os.listdir(dir_a) if f.endswith(".py")}
    nomes_b = {f for f in os.listdir(dir_b) if f.endswith(".py")}
    return sorted(nomes_a & nomes_b)


def _carregar_baseline():
    if not os.path.exists(BASELINE_PATH):
        return {"arquivos": {}}
    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _formato_legado(arquivos):
    """Baseline anterior ao item 2 era plano (nome -> entrada), sem chave de par."""
    if not arquivos:
        return False
    algum_valor = next(iter(arquivos.values()))
    return isinstance(algum_valor, dict) and "esperado_identico" in algum_valor


def atualizar_baseline():
    baseline_antigo = _carregar_baseline()
    arquivos_antigo = baseline_antigo.get("arquivos", {})
    legado = _formato_legado(arquivos_antigo)

    novos_arquivos = {}
    total = 0
    for nome_par, dir_a, dir_b in PARES:
        comuns = _arquivos_comuns(dir_a, dir_b)
        if legado and nome_par == "src/core":
            bucket_anterior = arquivos_antigo  # migra baseline plano antigo para o par src/core
        else:
            bucket_anterior = arquivos_antigo.get(nome_par, {})

        entradas = {}
        for nome in comuns:
            identico = _hash(os.path.join(dir_a, nome)) == _hash(os.path.join(dir_b, nome))
            anterior = bucket_anterior.get(nome)
            if identico:
                entradas[nome] = {"esperado_identico": True, "motivo": None}
            elif anterior and anterior.get("esperado_identico") is False and anterior.get("motivo"):
                entradas[nome] = anterior  # preserva motivo já documentado
            else:
                entradas[nome] = {
                    "esperado_identico": False,
                    "motivo": "REVISAR: divergencia nova detectada por --atualizar-baseline. "
                              "Edite este motivo antes de commitar.",
                }
        novos_arquivos[nome_par] = entradas
        total += len(entradas)

    catalogo_antigo = baseline_antigo.get("catalogo", {})
    documentadas_antigas = catalogo_antigo.get("divergencias_documentadas", {})
    novas_documentadas = {}
    for copia, _peca, identico in _estado_catalogo(_carregar_catalogo()):
        if identico is False:
            novas_documentadas[copia] = documentadas_antigas.get(copia) or (
                "REVISAR: divergencia nova detectada por --atualizar-baseline. "
                "Edite este motivo antes de commitar."
            )

    novo_baseline = {
        "descricao": baseline_antigo.get("descricao", "Baseline de sincronismo entre pares de "
            "diretorios de tools/aidd-master/ e tools/aidd-enterprise/ (ver PARES em "
            "G_DRIFT_NUCLEO_COMPARTILHADO.py)."),
        "gerado_em": baseline_antigo.get("gerado_em", "auto"),
        "arquivos": novos_arquivos,
        "catalogo": {
            "descricao": catalogo_antigo.get("descricao", DESCRICAO_CATALOGO),
            "divergencias_documentadas": novas_documentadas,
        },
    }
    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(novo_baseline, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"[OK] Baseline atualizado com {total} arquivo(s) em {len(PARES)} par(es) de diretorios "
          f"e {len(novas_documentadas)} divergencia(s) de copia do catalogo em {BASELINE_PATH}")
    return 0


def _carregar_catalogo():
    if not os.path.isfile(CATALOGO_PATH):
        return None
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _eh_d4(copia):
    return copia.replace(os.sep, "/").startswith(PREFIXOS_D4)


def _sha_catalogo(peca):
    return str(peca.get("sha256", "")).split("sha256-", 1)[-1]


def _caminho_repo(relativo):
    return os.path.join(ROOT_DIR, *str(relativo).split("/"))


def _estado_catalogo(catalogo):
    """Gera (copia, peca, identico) para cada copia do catalogo fora da D4.

    identico = None quando a copia nao existe no disco.
    """
    for peca in (catalogo or {}).get("pecas", []):
        esperado = _sha_catalogo(peca)
        for copia in peca.get("copias", []):
            if _eh_d4(copia):
                continue
            caminho = _caminho_repo(copia)
            if not os.path.isfile(caminho):
                yield copia, peca, None
            else:
                yield copia, peca, _hash(caminho) == esperado


def _checar_catalogo(catalogo, baseline_catalogo):
    """Compara cada copia do CATALOGO.json com a versao do catalogo. Retorna lista de erros (str)."""
    if catalogo is None:
        return [f"catalogo: CATALOGO.json ausente ({CATALOGO_PATH}) — nada contra o que comparar as copias."]

    erros = []
    documentadas = (baseline_catalogo or {}).get("divergencias_documentadas", {})
    pecas = catalogo.get("pecas", [])

    # A propria peca tem de bater com o selo do catalogo; senao a comparacao nao vale.
    for peca in pecas:
        caminho = _caminho_repo(peca.get("caminho", ""))
        if not os.path.isfile(caminho):
            erros.append(f"catalogo/{peca.get('nome')}: peca ausente do disco ({peca.get('caminho')}).")
        elif _hash(caminho) != _sha_catalogo(peca):
            erros.append(
                f"catalogo/{peca.get('nome')}: a peca nao bate com o sha256 do CATALOGO.json "
                f"(peca editada sem atualizar o selo)."
            )
        for copia in peca.get("copias", []):
            if _eh_d4(copia):
                print(f"[INFO] catalogo/{copia}: D4 — arquivo historico (materiais-extras/examples), nao comparado.")

    total = 0
    vistas = set()
    for copia, peca, identico in _estado_catalogo(catalogo):
        total += 1
        vistas.add(copia)
        motivo = documentadas.get(copia)
        if identico is None:
            erros.append(
                f"catalogo/{copia}: copia listada em '{peca.get('nome')}' nao existe no disco "
                f"(atualize 'copias' no CATALOGO.json)."
            )
        elif identico and motivo:
            erros.append(
                f"catalogo/{copia}: baseline documenta divergencia, mas a copia ja e identica "
                f"a '{peca.get('nome')}' (remova a entrada do baseline)."
            )
        elif not identico and not motivo:
            erros.append(
                f"catalogo/{copia}: diverge da peca '{peca.get('nome')}' do catalogo "
                f"(drift nao documentado)."
            )
        elif not identico and str(motivo).startswith("REVISAR"):
            erros.append(f"catalogo/{copia}: motivo da divergencia ainda e o placeholder REVISAR.")
        elif not identico:
            print(f"[INFO] catalogo/{copia}: divergencia documentada — {motivo}")

    for copia in sorted(set(documentadas) - vistas):
        erros.append(f"catalogo/{copia}: baseline documenta copia que nao esta no CATALOGO.json.")

    print(f"[OK] catalogo: {total} copia(s) comparada(s) com a versao do catalogo.")
    return erros


def _checar_par(nome_par, dir_a, dir_b, baseline_par):
    """Checa drift para um unico par de diretorios. Retorna lista de erros (str)."""
    erros = []

    if not os.path.isdir(dir_a) or not os.path.isdir(dir_b):
        print(f"[OK] {nome_par}: uma das ferramentas nao tem esta pasta neste checkout — nada a comparar.")
        return erros

    comuns = _arquivos_comuns(dir_a, dir_b)
    nao_catalogados = []

    # 1. Verifica se algum arquivo com esperado_identico=True desapareceu de dir_a ou dir_b
    for nome, entrada in sorted(baseline_par.items()):
        if entrada.get("esperado_identico") is True:
            caminho_a = os.path.join(dir_a, nome)
            caminho_b = os.path.join(dir_b, nome)
            existe_a = os.path.isfile(caminho_a)
            existe_b = os.path.isfile(caminho_b)

            if not existe_a and not existe_b:
                erros.append(
                    f"{nome_par}/{nome}: baseline espera IDENTICO, mas o arquivo desapareceu de "
                    f"ambas as ferramentas (DIR_A e DIR_B)."
                )
            elif not existe_a:
                erros.append(
                    f"{nome_par}/{nome}: baseline espera IDENTICO, mas o arquivo desapareceu de "
                    f"DIR_A ({dir_a})."
                )
            elif not existe_b:
                erros.append(
                    f"{nome_par}/{nome}: baseline espera IDENTICO, mas o arquivo desapareceu de "
                    f"DIR_B ({dir_b})."
                )

    # 2. Compara conteúdo de arquivos presentes em ambas
    for nome in comuns:
        caminho_a = os.path.join(dir_a, nome)
        caminho_b = os.path.join(dir_b, nome)
        identico_agora = _hash(caminho_a) == _hash(caminho_b)
        entrada = baseline_par.get(nome)

        if entrada is None:
            nao_catalogados.append((nome, identico_agora))
            continue

        if entrada.get("esperado_identico") is True and not identico_agora:
            erros.append(
                f"{nome_par}/{nome}: baseline espera IDENTICO entre as duas ferramentas, "
                f"mas o conteudo diverge agora (drift nao documentado)."
            )
        elif entrada.get("esperado_identico") is False:
            print(f"[INFO] {nome_par}/{nome}: divergencia conhecida e documentada — {entrada.get('motivo')}")
        elif entrada.get("esperado_identico") is True and identico_agora:
            print(f"[OK] {nome_par}/{nome}: sincronizado (par de diretorios idênticos).")

    for nome, identico_agora in nao_catalogados:
        status = "identico" if identico_agora else "DIVERGENTE"
        erros.append(
            f"{nome_par}/{nome}: presente em ambas ferramentas mas ausente do baseline "
            f"(estado atual: {status}). Rode com --atualizar-baseline e documente "
            f"o motivo se a divergencia for intencional."
        )

    return erros


def checar_drift():
    print("=" * 70)
    print(" [GATE] G_DRIFT_NUCLEO_COMPARTILHADO — catalogo, cross-tool e intra-tool")
    print("=" * 70)

    baseline_completo = _carregar_baseline()
    baseline = baseline_completo.get("arquivos", {})
    legado = _formato_legado(baseline)

    erros = _checar_catalogo(_carregar_catalogo(), baseline_completo.get("catalogo", {}))
    for nome_par, dir_a, dir_b in PARES:
        if legado and nome_par == "src/core":
            baseline_par = baseline
        else:
            baseline_par = baseline.get(nome_par, {})
        erros.extend(_checar_par(nome_par, dir_a, dir_b, baseline_par))

    print("\n" + "=" * 70)
    if erros:
        print(f" [FALHA] Quality Gate REPROVADO com {len(erros)} erro(s):")
        for err in erros:
            print(f"  - {err}")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_DRIFT_NUCLEO_COMPARTILHADO APROVADO (100% OK)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    if "--atualizar-baseline" in sys.argv:
        sys.exit(atualizar_baseline())
    sys.exit(checar_drift())
