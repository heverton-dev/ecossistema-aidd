# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — INTAKE DO PLANNER (grill -> spec -> planner)
=============================================================================
A cadeia canônica é /aidd-grill -> /aidd-spec -> /aidd-planner. O planner só abre com:

  .aidd/intake/grill.md   rodada socrática válida (`ecossistema.py grill validar`) que inclui as
                          perguntas visuais: tom, cor, referências e público;
  .aidd/intake/spec.md    especificação válida (`ecossistema.py spec validar`) com um bloco
                          `### Visual Direction` (tom, cor_primaria, referencias, publico).

O modelo que conduz a entrevista e escreve a spec é o harness (nunca uma API key). Quando não há
usuário no chat, o harness registra `--modo autonomo`, e o relatório da etapa deve dizer isso.
O bloco Visual Direction alimenta o DESIGN-SYSTEM.json e as consultas ao Mobbin.
=============================================================================
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PASTA_INTAKE = Path(".aidd") / "intake"
MODOS = ("autonomo", "interativo")

_RE_PERGUNTA = re.compile(r"^(?:###\s*)?(?:Pergunta\s*)?(\d+)[\.\)]\s*(.+)$", re.IGNORECASE)
_TEMAS_VISUAIS = {
    "tom": re.compile(r"\btom\b|\btone\b|\bvoz\b", re.IGNORECASE),
    "cor": re.compile(r"\bcor(?:es)?\b|\bcolor\b|\bpaleta\b", re.IGNORECASE),
    "referências": re.compile(r"refer[eê]ncia|reference|inspira", re.IGNORECASE),
    "público": re.compile(r"p[uú]blico|audience|\busu[aá]rios?\b", re.IGNORECASE),
}
_RE_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_CAMPOS_VISUAIS = ("tom", "cor_primaria", "referencias", "publico")


def _raiz_ecossistema() -> Path:
    for pai in Path(__file__).resolve().parents:
        if (pai / "ecossistema.py").is_file():
            return pai
    return Path(__file__).resolve().parents[4]


def caminhos(pasta: str) -> Dict[str, Path]:
    base = Path(pasta) / PASTA_INTAKE
    return {"grill": base / "grill.md", "spec": base / "spec.md", "registro": base / "intake.json"}


def _rodar_cli(subcomando: str, arquivo: Path) -> "tuple[int, str]":
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(_raiz_ecossistema() / "ecossistema.py"), subcomando, "validar",
         "--arquivo", str(arquivo.resolve())],
        cwd=str(_raiz_ecossistema()), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _temas_visuais_ausentes(texto_grill: str) -> List[str]:
    titulos = [m.group(2) for m in (_RE_PERGUNTA.match(l.strip()) for l in texto_grill.splitlines()) if m]
    return [tema for tema, padrao in _TEMAS_VISUAIS.items() if not any(padrao.search(t) for t in titulos)]


def _extrair_bloco_visual(texto_spec: str) -> Dict[str, str]:
    achou = re.search(r"^#{2,4}\s*Visual Direction\s*$", texto_spec, re.IGNORECASE | re.MULTILINE)
    if not achou:
        return {}
    resto = texto_spec[achou.end():]
    proximo = re.search(r"^#{1,4}\s", resto, re.MULTILINE)
    bloco = resto[: proximo.start()] if proximo else resto
    campos: Dict[str, str] = {}
    for linha in bloco.splitlines():
        m = re.match(r"^\s*[-*]\s*([a-z_]+)\s*:\s*(.+?)\s*$", linha)
        if m:
            campos[m.group(1).lower()] = m.group(2)
    return campos


def ler_direcao_visual(pasta: str) -> Optional[Dict[str, Any]]:
    arquivo = caminhos(pasta)["spec"]
    if not arquivo.is_file():
        return None
    campos = _extrair_bloco_visual(arquivo.read_text(encoding="utf-8"))
    if not all(campos.get(c) for c in _CAMPOS_VISUAIS):
        return None
    return {
        "tom": campos["tom"],
        "cor_primaria": campos["cor_primaria"],
        "referencias": [r.strip() for r in campos["referencias"].split(",") if r.strip()],
        "publico": campos["publico"],
    }


def verificar(pasta: str) -> List[str]:
    """Erros que bloqueiam o planner: intake ausente, grill/spec inválidos ou sem direção visual."""
    arq = caminhos(pasta)
    erros: List[str] = []
    rel_grill = os.path.join(".aidd", "intake", "grill.md")
    rel_spec = os.path.join(".aidd", "intake", "spec.md")

    if not arq["grill"].is_file():
        erros.append(f"Falta a entrevista: rode /aidd-grill (com perguntas visuais: tom, cor, referências, público) "
                     f"e grave a rodada em {rel_grill}.")
    else:
        rc, saida = _rodar_cli("grill", arq["grill"])
        if rc != 0:
            erros.append(f"{rel_grill} reprovou em `grill validar`: {saida.splitlines()[-1] if saida else 'sem saída'}")
        ausentes = _temas_visuais_ausentes(arq["grill"].read_text(encoding="utf-8"))
        if ausentes:
            erros.append(f"{rel_grill} não pergunta o visual; faltam perguntas sobre: {', '.join(ausentes)}.")

    if not arq["spec"].is_file():
        erros.append(f"Falta a especificação: rode /aidd-spec e grave em {rel_spec} "
                     f"(com um bloco '### Visual Direction': tom, cor_primaria, referencias, publico).")
    else:
        rc, saida = _rodar_cli("spec", arq["spec"])
        if rc != 0:
            erros.append(f"{rel_spec} reprovou em `spec validar`: {saida.splitlines()[-1] if saida else 'sem saída'}")
        campos = _extrair_bloco_visual(arq["spec"].read_text(encoding="utf-8"))
        for campo in _CAMPOS_VISUAIS:
            if not campos.get(campo):
                erros.append(f"{rel_spec}: o bloco 'Visual Direction' não tem o item '{campo}'.")
        if campos.get("cor_primaria") and not _RE_HEX.match(campos["cor_primaria"]):
            erros.append(f"{rel_spec}: cor_primaria precisa ser hexadecimal (#RRGGBB), veio '{campos['cor_primaria']}'.")
    return erros


def cmd_intake(args) -> int:
    pasta = os.path.abspath(getattr(args, "pasta", None) or ".")
    modo = getattr(args, "modo", None) or "interativo"
    erros = verificar(pasta)
    if erros:
        print("[ERRO] Intake incompleto; o planner não abre sem grill e spec:", file=sys.stderr)
        for e in erros:
            print("  - " + e, file=sys.stderr)
        return 1
    arq = caminhos(pasta)
    registro = {
        "versao": 1,
        "modo": modo,
        "grill_sha256": hashlib.sha256(arq["grill"].read_bytes()).hexdigest(),
        "spec_sha256": hashlib.sha256(arq["spec"].read_bytes()).hexdigest(),
        "direcao_visual": ler_direcao_visual(pasta),
    }
    arq["registro"].write_text(json.dumps(registro, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"[aidd-planner] Intake válido (modo {modo}); registro em {arq['registro']}.")
    return 0
