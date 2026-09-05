# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_DRIFT_NUCLEO_COMPARTILHADO
=============================================================================
Detecta divergência silenciosa entre tools/aidd-master/src/core/ e
tools/aidd-enterprise/src/core/ (R3 do
PLANO-CORRECAO-RISCOS-ECOSSISTEMA-AIDD.md).

Contexto: as duas ferramentas nasceram da mesma linhagem e compartilham
~22 arquivos de núcleo byte-a-byte idênticos (caveman_protocol.py,
subagent_engine.py, database_adapter.py, etc.) — mas são mantidas como
cópias independentes por decisão explícita (nenhum acoplamento de runtime
entre as duas ferramentas, preservando a independência de cada uma).

Esse desenho tem um custo: se alguém corrige um bug em uma cópia e esquece
a outra, nada acusava isso antes deste gate. A correção NÃO é criar uma
dependência de runtime entre as ferramentas (isso quebraria a promessa de
"ferramenta autocontida" do AGENTS.md) — é comparar hashes e falhar quando
um par que deveria estar sincronizado (baseline_nucleo_compartilhado.json)
divergir sem essa mudança ter sido documentada.

Uso:
  python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py
      Roda a checagem. exit 0 = sem drift não documentado. exit 1 = drift
      encontrado ou baseline desatualizado (arquivo novo não catalogado).

  python gates/G_DRIFT_NUCLEO_COMPARTILHADO.py --atualizar-baseline
      Regrava o baseline refletindo o estado atual (todo par idêntico vira
      esperado_identico=true; todo par divergente vira esperado_identico
      =false com motivo placeholder "REVISAR: ..." exigindo edição manual
      antes do commit). Use isso só depois de uma decisão deliberada de
      aceitar uma nova divergência — nunca como forma de "silenciar" o gate.
"""

import hashlib
import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_A = os.path.join(ROOT_DIR, "tools", "aidd-master", "src", "core")
DIR_B = os.path.join(ROOT_DIR, "tools", "aidd-enterprise", "src", "core")
BASELINE_PATH = os.path.join(ROOT_DIR, "gates", "baseline_nucleo_compartilhado.json")


def _hash(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _arquivos_comuns():
    if not os.path.isdir(DIR_A) or not os.path.isdir(DIR_B):
        return []
    nomes_a = {f for f in os.listdir(DIR_A) if f.endswith(".py")}
    nomes_b = {f for f in os.listdir(DIR_B) if f.endswith(".py")}
    return sorted(nomes_a & nomes_b)


def _carregar_baseline():
    if not os.path.exists(BASELINE_PATH):
        return {"arquivos": {}}
    with open(BASELINE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def atualizar_baseline():
    comuns = _arquivos_comuns()
    baseline_antigo = _carregar_baseline()
    entradas = {}
    for nome in comuns:
        identico = _hash(os.path.join(DIR_A, nome)) == _hash(os.path.join(DIR_B, nome))
        anterior = baseline_antigo.get("arquivos", {}).get(nome)
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

    novo_baseline = {
        "descricao": baseline_antigo.get("descricao", "Baseline de sincronismo entre "
            "tools/aidd-master/src/core/ e tools/aidd-enterprise/src/core/."),
        "gerado_em": baseline_antigo.get("gerado_em", "auto"),
        "arquivos": entradas,
    }
    with open(BASELINE_PATH, "w", encoding="utf-8") as f:
        json.dump(novo_baseline, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"[OK] Baseline atualizado com {len(entradas)} arquivo(s) em {BASELINE_PATH}")
    return 0


def checar_drift():
    print("=" * 70)
    print(" [GATE] G_DRIFT_NUCLEO_COMPARTILHADO — aidd-master vs aidd-enterprise")
    print("=" * 70)

    if not os.path.isdir(DIR_A) or not os.path.isdir(DIR_B):
        print("[OK] Uma das ferramentas nao existe neste checkout — nada a comparar.")
        return 0

    baseline = _carregar_baseline().get("arquivos", {})
    comuns = _arquivos_comuns()
    erros = []
    nao_catalogados = []

    # 1. Verifica se algum arquivo com esperado_identico=True desapareceu de DIR_A ou DIR_B
    for nome, entrada in sorted(baseline.items()):
        if entrada.get("esperado_identico") is True:
            caminho_a = os.path.join(DIR_A, nome)
            caminho_b = os.path.join(DIR_B, nome)
            existe_a = os.path.isfile(caminho_a)
            existe_b = os.path.isfile(caminho_b)

            if not existe_a and not existe_b:
                erros.append(
                    f"{nome}: baseline espera IDENTICO, mas o arquivo desapareceu de "
                    f"ambas as ferramentas (DIR_A e DIR_B)."
                )
            elif not existe_a:
                erros.append(
                    f"{nome}: baseline espera IDENTICO, mas o arquivo desapareceu de "
                    f"DIR_A ({DIR_A})."
                )
            elif not existe_b:
                erros.append(
                    f"{nome}: baseline espera IDENTICO, mas o arquivo desapareceu de "
                    f"DIR_B ({DIR_B})."
                )

    # 2. Compara conteúdo de arquivos presentes em ambas
    for nome in comuns:
        caminho_a = os.path.join(DIR_A, nome)
        caminho_b = os.path.join(DIR_B, nome)
        identico_agora = _hash(caminho_a) == _hash(caminho_b)
        entrada = baseline.get(nome)

        if entrada is None:
            nao_catalogados.append((nome, identico_agora))
            continue

        if entrada.get("esperado_identico") is True and not identico_agora:
            erros.append(
                f"{nome}: baseline espera IDENTICO entre as duas ferramentas, "
                f"mas o conteudo diverge agora (drift nao documentado)."
            )
        elif entrada.get("esperado_identico") is False:
            print(f"[INFO] {nome}: divergencia conhecida e documentada — {entrada.get('motivo')}")
        elif entrada.get("esperado_identico") is True and identico_agora:
            print(f"[OK] {nome}: sincronizado com aidd-enterprise.")

    if nao_catalogados:
        for nome, identico_agora in nao_catalogados:
            status = "identico" if identico_agora else "DIVERGENTE"
            erros.append(
                f"{nome}: presente em ambas ferramentas mas ausente do baseline "
                f"(estado atual: {status}). Rode com --atualizar-baseline e documente "
                f"o motivo se a divergencia for intencional."
            )

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
