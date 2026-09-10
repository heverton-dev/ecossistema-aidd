# -*- coding: utf-8 -*-
"""
 =============================================================================
 ECOSSISTEMA AIDD — QUALITY GATE: G_TESTES_REAIS (v2)
 =============================================================================
 Roda pytest de verdade em cada tools/<ferramenta> e falha (exit 1) se
 qualquer suíte tiver failed > 0 ou erro de execução. Métricas (passed/
 failed/skipped/errors) são extraídas do relatório JUnitXML estruturado
 (Item 6 do plano 03-qualidade-testes-e-mutacao) — nada de regex sobre
 stdout. Skipped é regido por orçamento estrito: cada ferramenta só pode
 pular testes autorizados, identificados por test-id, no allowlist
 gates/allowlist_skipped_testes.json (arquivo ausente = orçamento zero).

 Uso:
   python gates/G_TESTES_REAIS.py
       exit 0 = todas as suítes passaram e skipped dentro do orçamento.
       exit 1 = falha, timeout, ou skipped não autorizado em alguma suíte.
"""

import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")
ALLOWLIST_PATH = os.path.join(ROOT_DIR, "gates", "allowlist_skipped_testes.json")

FERRAMENTAS = [
    "aidd-forge",
    "aidd-generator",
    "aidd-master",
    "aidd-enterprise",
    "aidd-ops",
]


def _carregar_allowlist():
    """Retorna {ferramenta: set(test_ids autorizados)}; arquivo ausente = tudo vazio."""
    if not os.path.isfile(ALLOWLIST_PATH):
        return {}
    try:
        with open(ALLOWLIST_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return {k: set(v) for k, v in dados.items()}
    except (OSError, json.JSONDecodeError) as e:
        print(f"  [AVISO] Allowlist de skipped inválida ({e}) — tratando como vazia.")
        return {}


def _rodar_pytest(diretorio, junitxml_path):
    """Executa pytest com relatório JUnitXML e retorna (exit_code, stdout_text)."""
    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no", f"--junitxml={junitxml_path}"],
        cwd=diretorio,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
    )
    return resultado.returncode, resultado.stdout + resultado.stderr


def parsear_junitxml(caminho_xml):
    """Extrai métricas estruturadas do relatório JUnitXML do pytest.

    Retorna dict com totais (tests/errors/failures/skipped) e a lista de
    test-ids pulados ('<arquivo>::<teste>'). Levanta ValueError se o XML
    não for parsesável — falha explícita, nunca silêncio.
    """
    tree = ET.parse(caminho_xml)
    root = tree.getroot()

    if root.tag != "testsuites":
        raise ValueError(f"XML inesperado: raiz '{root.tag}' (esperado 'testsuites')")

    totais = {"tests": 0, "errors": 0, "failures": 0, "skipped": 0}
    skipped_ids = []

    for suite in root.findall("testsuite"):
        for attr in totais:
            totais[attr] += int(suite.get(attr, 0))

        for testcase in suite.iter("testcase"):
            for filho in testcase:
                if filho.tag == "skipped":
                    arquivo = os.path.basename(testcase.get("classname", "")).replace(".", os.sep)
                    nome = testcase.get("name", "desconhecido")
                    classe = testcase.get("classname", "")
                    # classname vem como 'tests.unit.test_arquivo' — converter p/ caminho
                    mod = classe.rsplit(".", 1)[0].replace(".", "/") if "." in classe else ""
                    test_id = f"{mod}/{nome}" if mod else nome
                    skipped_ids.append(test_id)

    return {"totais": totais, "skipped_ids": skipped_ids}


def _skips_nao_autorizados(ferramenta, skipped_ids, allowlist):
    autorizados = allowlist.get(ferramenta, set())
    return [sid for sid in skipped_ids if sid not in autorizados]


def executar():
    print("=" * 70)
    print(" [GATE] G_TESTES_REAIS v2 — Execução real de pytest por ferramenta")
    print("         (métricas via JUnitXML + orçamento de skipped)")
    print("=" * 70)
    print()

    allowlist = _carregar_allowlist()
    if not allowlist:
        print("  [INFO] Orçamento de skipped: ZERO (allowlist ausente ou vazia).")
    else:
        total_autorizados = sum(len(v) for v in allowlist.values())
        print(f"  [INFO] Orçamento de skipped: {total_autorizados} test-id(s) autorizados.")
    print()

    resultados = []
    falhou = False

    for ferramenta in FERRAMENTAS:
        dir_ferramenta = os.path.join(TOOLS_DIR, ferramenta)
        if not os.path.isdir(dir_ferramenta):
            print(f"  [{ferramenta}] DIRETÓRIO AUSENTE — ignorado")
            resultados.append((ferramenta, "AUSENTE", 0, 0, 0, []))
            continue

        print(f"  [{ferramenta}] Rodando pytest...", end=" ", flush=True)

        fd_tmp, junitxml_path = tempfile.mkstemp(suffix=".xml", prefix="junit_gtestes_")
        os.close(fd_tmp)
        try:
            try:
                exit_code, output = _rodar_pytest(dir_ferramenta, junitxml_path)
            except subprocess.TimeoutExpired:
                print("TIMEOUT (900s)")
                resultados.append((ferramenta, "TIMEOUT", 0, 0, 0, []))
                falhou = True
                continue
            except Exception as e:
                print(f"ERRO: {e}")
                resultados.append((ferramenta, "ERRO", 0, 0, 0, []))
                falhou = True
                continue

            if not os.path.isfile(junitxml_path) or os.path.getsize(junitxml_path) == 0:
                print("ERRO: JUnitXML não gerado pelo pytest")
                resultados.append((ferramenta, "ERRO", 0, 0, 0, []))
                falhou = True
                continue

            try:
                metricas = parsear_junitxml(junitxml_path)
            except (ValueError, ET.ParseError) as e:
                print(f"ERRO: JUnitXML inválido ({e})")
                resultados.append((ferramenta, "ERRO", 0, 0, 0, []))
                falhou = True
                continue

            totais = metricas["totais"]
            passed = totais["tests"] - totais["failures"] - totais["errors"] - totais["skipped"]
            failed = totais["failures"] + totais["errors"]
            skipped = totais["skipped"]

            nao_autorizados = _skips_nao_autorizados(ferramenta, metricas["skipped_ids"], allowlist)

            status = "OK"
            if failed > 0:
                print(f"FALHOU ({passed} passed, {failed} failed, {skipped} skipped)")
                status = "FALHA"
                falhou = True
            elif nao_autorizados:
                print(f"ORÇAMENTO ESTOURADO ({passed} passed, {skipped} skipped, "
                      f"{len(nao_autorizados)} não autorizado(s))")
                status = "SKIP_NAO_AUTORIZADO"
                falhou = True
            elif passed == 0 and skipped == 0:
                print("SEM TESTES (0 resultados)")
            else:
                msg = f"OK ({passed} passed, {failed} failed, {skipped} skipped)"
                if skipped:
                    msg += " [dentro do orçamento]"
                print(msg)

            resultados.append((ferramenta, status, passed, failed, skipped, nao_autorizados))
        finally:
            try:
                os.remove(junitxml_path)
            except OSError:
                pass

    # Resumo
    print()
    print("-" * 70)
    print(" RESUMO G_TESTES_REAIS v2")
    print("-" * 70)

    total_passed = sum(p for _, _, p, _, _, _ in resultados)
    total_failed = sum(f for _, _, _, f, _, _ in resultados)
    total_skipped = sum(s for _, _, _, _, s, _ in resultados)

    for ferramenta, status, passed, failed, skipped, nao_autorizados in resultados:
        if status == "AUSENTE":
            icon = "SKIP"
        elif status in ("TIMEOUT", "ERRO", "FALHA", "SKIP_NAO_AUTORIZADO"):
            icon = "FALHA"
        else:
            icon = " OK "
        linha = f"  [{icon}] {ferramenta:<24} {passed:>4} passed, {failed:>2} failed, {skipped:>2} skipped"
        print(linha)
        for sid in nao_autorizados:
            print(f"           -> skipped sem autorização: {sid}")

    print("-" * 70)
    print(f"  TOTAL: {total_passed} passed, {total_failed} failed, {total_skipped} skipped")
    print()

    if falhou:
        print(" [FALHA] Quality Gate G_TESTES_REAIS REPROVADO — falhas reais ou skipped fora do orçamento!")
        print("  Ação necessária: corrija os testes ou documente o skip em")
        print(f"  gates/allowlist_skipped_testes.json com justificativa.")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_TESTES_REAIS v2 APROVADO — todas as suítes passaram!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(executar())
