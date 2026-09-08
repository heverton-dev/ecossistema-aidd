# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_DRIFT_NUCLEO_COMPARTILHADO
=============================================================================
Detecta divergência silenciosa entre pares de diretórios de
tools/aidd-master/ e tools/aidd-enterprise/ que nasceram da mesma linhagem
e compartilham arquivos byte-a-byte idênticos (R3 do
PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md, ampliado pelo item 2 de
docs/planos/fazendo/correcao-arquitetura-limpa/).

Pares cobertos hoje (ver PARES abaixo): src/core, scripts, scripts/gates,
templates/core e templates/v2 — mas são mantidas como cópias independentes
por decisão explícita (nenhum acoplamento de runtime entre as duas
ferramentas, preservando a independência de cada uma).

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

    novo_baseline = {
        "descricao": baseline_antigo.get("descricao", "Baseline de sincronismo entre pares de "
            "diretorios de tools/aidd-master/ e tools/aidd-enterprise/ (ver PARES em "
            "G_DRIFT_NUCLEO_COMPARTILHADO.py)."),
        "gerado_em": baseline_antigo.get("gerado_em", "auto"),
        "arquivos": novos_arquivos,
    }
    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(novo_baseline, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"[OK] Baseline atualizado com {total} arquivo(s) em {len(PARES)} par(es) de diretorios em {BASELINE_PATH}")
    return 0


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
            print(f"[OK] {nome_par}/{nome}: sincronizado com aidd-enterprise.")

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
    print(" [GATE] G_DRIFT_NUCLEO_COMPARTILHADO — aidd-master vs aidd-enterprise")
    print("=" * 70)

    baseline = _carregar_baseline().get("arquivos", {})
    legado = _formato_legado(baseline)

    erros = []
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
