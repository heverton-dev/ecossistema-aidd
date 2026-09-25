#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_aidd_diagnose (D13 / DoD 6)
=============================================================================
Quality Gate Determinístico e Rótulo Honesto para a ferramenta aidd-diagnose.
Valida estritamente os critérios científicos de relatório de causa-raiz:
  1. Comando de reprodução determinística executado N vezes com o mesmo resultado.
  2. Formulação estrita de apenas UMA hipótese ativa por vez.
  3. Teste de regressão permanente que comprovadamente falhou antes da correção
     e passou após a intervenção.
  4. Honestidade de rótulo: veta suposições falsas, conclusões prematuras ou
     afirmações de cura sem evidência empírica comprovada.

Critérios de Aceite:
  - Exit 0: Relatório satisfaz 100% dos requisitos de causa-raiz e integridade.
  - Exit 1: Violação de reprodução, múltiplas hipóteses simultâneas, ausência
            de teste de regressão com comprovação falha/sucesso ou rótulo desonesto.
=============================================================================
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent


PADROES_ILUSORIOS_PROIBIDOS = [
    re.compile(r"\bdiagn[oó]stico\s+dispens[aá]vel\b", re.IGNORECASE),
    re.compile(r"\bcorre[cç][aã]o\s+sem\s+teste\b", re.IGNORECASE),
    re.compile(r"\bachismo\b", re.IGNORECASE),
    re.compile(r"\bshotgun\s+debugging\b", re.IGNORECASE),
    re.compile(r"\bsem\s+reprodu[cç][aã]o\b", re.IGNORECASE),
]


def extrair_metadados_markdown(texto: str) -> Dict[str, Any]:
    """Extrai informações estruturadas de um relatório de causa-raiz em Markdown."""
    dados: Dict[str, Any] = {
        "comando_reproducao": None,
        "execucoes_reproducao": 0,
        "resultado_deterministico": False,
        "hipoteses_ativas": [],
        "hipoteses_descartadas": [],
        "teste_regressao": None,
    }

    # Procura seção JSON embutida se existir
    idx_json = texto.rfind("METADADOS_JSON:")
    if idx_json != -1:
        ini = texto.find("{", idx_json)
        fim = texto.rfind("}", ini)
        if ini != -1 and fim != -1:
            try:
                sub_json = json.loads(texto[ini : fim + 1])
                if isinstance(sub_json, dict):
                    if sub_json.get("comando_reproducao"):
                        dados["comando_reproducao"] = sub_json["comando_reproducao"]
                        dados["execucoes_reproducao"] = sub_json.get("execucoes", 1)
                        dados["resultado_deterministico"] = True
                    if "hipoteses" in sub_json:
                        dados["hipoteses_ativas"] = sub_json["hipoteses"]
                    if "teste_regressao" in sub_json:
                        dados["teste_regressao"] = sub_json["teste_regressao"]
            except Exception:
                pass

    # Extração via Regex e parser de seções Markdown
    # 1. Comando de Reprodução
    match_cmd = re.search(
        r"-\s+\*\*Comando\*\*:\s*`?([^`\r\n]+)`?", texto, re.IGNORECASE
    )
    if not match_cmd:
        match_cmd = re.search(
            r"COMANDO\s+(?:DE\s+)?REPRODUCAO:\s*\r?\n\s*`?([^\r\n`]+)`?",
            texto,
            re.IGNORECASE,
        )
    if match_cmd:
        cmd_val = match_cmd.group(1).strip()
        if cmd_val and cmd_val.upper() != "N/A" and cmd_val.upper() != "NONE":
            dados["comando_reproducao"] = cmd_val

    # Contagem de execuções de reprodução
    match_execs = re.search(
        r"(\d+)\s+execu[cç][oõ]es(?:\s+com\s+o\s+mesmo\s+resultado|\s+consistentes|\s+consecutivas|\s+determin[ií]sticas)?",
        texto,
        re.IGNORECASE,
    )
    if not match_execs:
        match_execs = re.search(r"ran\s+(\d+)\s+times\s+with\s+same\s+result", texto, re.IGNORECASE)

    if match_execs:
        dados["execucoes_reproducao"] = int(match_execs.group(1))

    match_det = re.search(
        r"(?:Resultado\s+Determin[ií]stico|deterministico):\s*(Sim|True|100%|[1-9]\d*%)",
        texto,
        re.IGNORECASE,
    )
    if match_det or dados["execucoes_reproducao"] >= 1:
        dados["resultado_deterministico"] = True

    # 2. Hipóteses Ativas
    sec_hip = re.search(
        r"\*\*Hip[oó]teses\s+Ativas\*\*:(.*?)(?=\*\*Hip[oó]teses\s+Descartadas\*\*|###|##|\Z)",
        texto,
        re.DOTALL | re.IGNORECASE,
    )
    if not sec_hip:
        sec_hip = re.search(
            r"HIPOTESES\s+ATIVAS:(.*?)(?=HIPOTESES\s+DESCARTADAS|METADADOS_JSON|###|##|\Z)",
            texto,
            re.DOTALL | re.IGNORECASE,
        )

    if sec_hip:
        linhas_hip = [
            line.strip()[2:].strip()
            for line in sec_hip.group(1).splitlines()
            if line.strip().startswith("- ") or line.strip().startswith("* ")
        ]
        linhas_validas = [
            h for h in linhas_hip if h and not h.startswith("(") and h.lower() != "nenhuma"
        ]
        if linhas_validas:
            dados["hipoteses_ativas"] = linhas_validas

    # 3. Teste de Regressão
    match_reg_file = re.search(
        r"-\s+\*\*Teste\s+de\s+Regress[aã]o\*\*:\s*`?([^`\r\n]+)`?",
        texto,
        re.IGNORECASE,
    )
    if match_reg_file:
        reg_val = match_reg_file.group(1).strip()
        falhou_antes = bool(
            re.search(r"-\s+\*\*Resultado\s+Antes\s+do\s+Fix\*\*:\s*FALHA", texto, re.IGNORECASE)
            or re.search(r"failed\s+before\s+fix", texto, re.IGNORECASE)
        )
        passou_depois = bool(
            re.search(r"-\s+\*\*Resultado\s+Ap[oó]s\s+o\s+Fix\*\*:\s*PASSOU", texto, re.IGNORECASE)
            or re.search(r"passed\s+after\s+fix", texto, re.IGNORECASE)
        )
        dados["teste_regressao"] = {
            "arquivo": reg_val,
            "falhou_antes": falhou_antes,
            "passou_depois": passou_depois,
        }

    return dados


def conferir_teste_regressao(arquivo: Any, base_relatorio: Optional[Path]) -> Optional[str]:
    """
    Não confia no 'passou_depois' declarado: o arquivo tem que existir e o pytest
    tem que passar agora. 'falhou_antes' continua declarado (não dá para voltar no tempo).
    """
    if not arquivo or not str(arquivo).strip():
        return "Teste de regressão sem arquivo: impossível conferir que ele passa (D13)."
    alvo = Path(str(arquivo).strip())
    candidatos = [alvo] if alvo.is_absolute() else [
        c / alvo for c in (base_relatorio, ROOT_DIR) if c is not None
    ]
    existente = next((c for c in candidatos if c.is_file()), None)
    if existente is None:
        return f"Teste de regressão '{arquivo}' não existe em disco: relatório não comprovado (D13)."
    res = subprocess.run(
        [sys.executable, "-m", "pytest", str(existente), "-q", "-p", "no:cacheprovider"],
        cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=600,
    )
    if res.returncode != 0:
        return (
            f"Teste de regressão '{arquivo}' falha agora (pytest exit {res.returncode}): "
            "'passou_depois' declarado não confere com a execução real (D13)."
        )
    return None


def validar_conteudo_diagnose(
    dados: Dict[str, Any], texto_bruto: str = "", base_relatorio: Optional[Path] = None
) -> Tuple[bool, List[str]]:
    """
    Valida as regras de integridade do diagnóstico e causa-raiz:
      1. Comando de reprodução executado N vezes com mesmo resultado (N >= 1 e determinístico).
      2. Exatamente UMA hipótese ativa por vez.
      3. Teste de regressão comprovado com falha antes e sucesso depois; o arquivo
         precisa existir e passar de verdade quando o gate roda.
    """
    erros: List[str] = []

    # 0. Checagem de termos ilusórios proibidos no texto bruto
    if texto_bruto:
        for padrao in PADROES_ILUSORIOS_PROIBIDOS:
            match = padrao.search(texto_bruto)
            if match:
                termo = match.group(0)
                erros.append(
                    f"Rótulo Desonesto detectado: termo proibido '{termo}' presente. "
                    "Violação da honestidade de causa-raiz (D13)."
                )

    # 1. Validação do Comando de Reprodução
    cmd_repro = dados.get("comando_reproducao")
    execucoes = dados.get("execucoes_reproducao", 0)
    det = dados.get("resultado_deterministico", False)

    if not cmd_repro or not str(cmd_repro).strip() or cmd_repro == "N/A":
        erros.append(
            "Ausência de comando de reprodução determinística (missing repro). "
            "A causa-raiz exige isolamento e comprovação determinística de falha (D13)."
        )
    elif execucoes < 1 or not det:
        erros.append(
            f"Comando de reprodução não comprovou determinismo (execuções={execucoes}, determinístico={det}). "
            "Exige-se execução consistente com o mesmo resultado."
        )

    # 2. Validação de Hipótese Ativa Única (one active hypothesis at a time)
    hipoteses_ativas = dados.get("hipoteses_ativas", [])
    if isinstance(hipoteses_ativas, list):
        qtd_hipoteses = len(hipoteses_ativas)
        if qtd_hipoteses > 1:
            erros.append(
                f"Mais de uma hipótese ativa simultânea detectada ({qtd_hipoteses} ativas: {hipoteses_ativas}). "
                "Regra inviolável do AIDD-Diagnose: exatamente UMA hipótese ativa por vez (one active hypothesis at a time)."
            )
        elif qtd_hipoteses == 0:
            erros.append(
                "Nenhuma hipótese formulada para a causa-raiz investigada."
            )
    else:
        erros.append("Campo de hipóteses ativas em formato inválido (deve ser lista).")

    # 3. Validação do Teste de Regressão Permanente
    reg_test = dados.get("teste_regressao")
    if not reg_test or not isinstance(reg_test, dict):
        erros.append(
            "Ausência de especificação do teste de regressão permanente (missing regression test). "
            "A etapa 5 exige um teste automatizado definitivo que preserve a correção."
        )
    else:
        falhou_antes = reg_test.get("falhou_antes") is True
        passou_depois = reg_test.get("passou_depois") is True
        if not falhou_antes or not passou_depois:
            erros.append(
                f"Teste de regressão não comprovou ciclo Red-Green completo "
                f"(falhou_antes={falhou_antes}, passou_depois={passou_depois}). "
                "Exige-se prova de que o teste falhava antes da correção e passou após o fix cirúrgico."
            )
        else:
            erro_execucao = conferir_teste_regressao(reg_test.get("arquivo"), base_relatorio)
            if erro_execucao:
                erros.append(erro_execucao)

    if erros:
        return False, erros
    return True, ["APROVADO: Relatório de causa-raiz em total conformidade determinística. EXIT 0"]


def validar_arquivo_diagnose(caminho: Union[str, Path]) -> Tuple[bool, List[str]]:
    """Lê e audita arquivo de diagnóstico/relatório de causa raiz."""
    p = Path(caminho).resolve()
    if not p.is_file():
        return False, [f"Arquivo de relatório de diagnose não encontrado: {p}"]

    try:
        texto = p.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return False, [f"Falha ao ler arquivo {p}: {exc}"]

    if p.suffix.lower() == ".json":
        try:
            dados = json.loads(texto)
            if not isinstance(dados, dict):
                return False, [f"Arquivo JSON {p} não contém um objeto raiz."]
            return validar_conteudo_diagnose(dados, texto_bruto=texto, base_relatorio=p.parent)
        except json.JSONDecodeError as exc:
            return False, [f"JSON inválido em {p}: {exc}"]
    else:
        dados = extrair_metadados_markdown(texto)
        return validar_conteudo_diagnose(dados, texto_bruto=texto, base_relatorio=p.parent)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="G_aidd_diagnose: Quality Gate Determinístico de Causa-Raiz e Rótulo Honesto (D13)"
    )
    parser.add_argument(
        "--relatorio",
        "-r",
        dest="relatorio",
        default=None,
        help="Caminho do arquivo de relatório de causa raiz (.md ou .json)",
    )
    parser.add_argument(
        "arquivos",
        nargs="*",
        default=[],
        help="Arquivos adicionais de relatório para validação",
    )

    args = parser.parse_args(argv)

    alvos: List[Path] = []
    if args.relatorio:
        alvos.append(Path(args.relatorio))
    for arq in args.arquivos:
        alvos.append(Path(arq))

    if not alvos:
        docs_dir = Path("docs") / "diagnosticos"
        if docs_dir.is_dir():
            alvos.extend(sorted(docs_dir.glob("**/RELATORIO-CAUSA-RAIZ.md")))
            alvos.extend(sorted(docs_dir.glob("**/relatorio_causa_raiz.json")))

    if not alvos:
        print("[AVISO] Nenhum relatório de diagnose especificado ou encontrado para auditoria.")
        return 0

    aprovado_geral = True
    for alvo in alvos:
        aprovado, msgs = validar_arquivo_diagnose(alvo)
        for msg in msgs:
            print(f"[{alvo.name}] {msg}")
        if not aprovado:
            aprovado_geral = False

    if aprovado_geral:
        print("[SUCESSO] Quality Gate G_aidd_diagnose APROVADO. EXIT 0")
        return 0
    else:
        print("[ERRO] Quality Gate G_aidd_diagnose REPROVADO. EXIT 1")
        return 1


if __name__ == "__main__":
    sys.exit(main())
