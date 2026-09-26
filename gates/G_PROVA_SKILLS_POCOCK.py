#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_PROVA_SKILLS_POCOCK (skills-pocock T13 / D13)
=============================================================================
Prova de uso real das skills alteradas no ciclo skills-pocock/ciclo-01.

Modo real (padrão): roda cada skill sem interação (`claude -p --model haiku`)
contra os casos em tests/fixtures/skills_pocock/ e confere o artefato gerado.
Tudo o que o modelo gera fica numa pasta temporária apagada no fim.
  - aidd-diagnose: 3+ hipóteses numeradas em "Hipóteses candidatas" e um
    comando de reprodução (só python) que sai != 0 no projeto com o bug e
    == 0 depois da correção conhecida (prova que é vermelho NESTE bug).
  - aidd-tickets: todo ticket tem "Blocked by"; nenhum ticket só de testes
    ou só de código.
  - aidd-grill: bloco "Consolidated Assumptions" com recomendação por item.
  - aidd-tdd: seção de pontos de teste (seams) antes do primeiro teste.

Modo --artefatos DIR: confere artefatos já salvos (<skill>.md), sem modelo.
É o modo usado pelo teste (gates/test_g_prova_skills_pocock.py).

Gate MANUAL (gasta tokens e depende de rede): fora do pre-commit e do audit;
roda com `pre-commit run --hook-stage manual g-prova-skills-pocock --all-files`
ou `python gates/G_PROVA_SKILLS_POCOCK.py`.

Saída: exit 0 = todas as skills aprovadas; exit 1 = alguma reprovada.
=============================================================================
"""
from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Dict, List, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "skills_pocock"
PROJETO_BUG = FIXTURES / "projeto_bug"
SPEC = FIXTURES / "spec.md"
SKILLS_DIR = ROOT / "componentes" / "compartilhado" / "skills"
MODELO = "haiku"
TIMEOUT_MODELO = 600
TIMEOUT_REPRO = 60

sys.path.insert(0, str(ROOT / "scripts"))
from compilador_tickets_plano import extrair_tickets_de_conteudo  # noqa: E402

TITULO = re.compile(r"^#{1,6}\s", re.MULTILINE)
ITEM_NUMERADO = re.compile(r"^\s*\d+[.)]\s+\S", re.MULTILINE)
LINHA_NUMERADA_DE_TABELA = re.compile(r"^\s*\|\s*\**H?\d+\**\s*\|", re.MULTILINE)
MOTIVO_OU_RECOMENDACAO = re.compile(
    r"recomend|recommend|\bbecause\b|\bporque\b|\bpois\b|\braz[aã]o\b|\breason\b", re.IGNORECASE
)
TICKET_CABECALHO = re.compile(r"^#{2,6}\s*\[TICKET-\d+\]", re.MULTILINE)
ARQUIVO_DE_TESTE = re.compile(r"(^|/)tests?/|(^|/)test_[^/]*$|_test\.[a-z]+$|\.(test|spec)\.[a-z]+$")


def _secao(texto: str, titulo: str) -> Optional[str]:
    """Corpo da seção cujo título casa com o padrão, até o próximo título."""
    m = re.search(rf"^#{{1,6}}\s*[^\n]*{titulo}[^\n]*$", texto, re.MULTILINE | re.IGNORECASE)
    if not m:
        return None
    prox = TITULO.search(texto, m.end())
    return texto[m.end():prox.start() if prox else len(texto)]


# ---------------------------------------------------------------- checagens

def checar_diagnose(texto: str) -> List[str]:
    erros: List[str] = []
    lista = _secao(texto, r"Hip[oó]teses\s+candidatas")
    if lista is None:
        erros.append("sem a seção 'Hipóteses candidatas'")
    else:
        # Lista numerada ("1. ...") ou tabela com a 1ª coluna numerada ("| 1 |", "| **H1** |").
        qtd = max(len(ITEM_NUMERADO.findall(lista)), len(LINHA_NUMERADA_DE_TABELA.findall(lista)))
        if qtd < 3:
            erros.append(f"só {qtd} hipótese(s) numerada(s); exige 3 ou mais")

    m = re.search(r"\*\*Comando\*\*:\s*`([^`\n]+)`", texto)
    if not m:
        return erros + ["sem comando de reprodução ('- **Comando**: `...`')"]
    erro_repro = conferir_reproducao(m.group(1).strip())
    return erros + ([erro_repro] if erro_repro else [])


def _rodar_no_projeto(argv: List[str], corrigido: bool) -> int:
    with tempfile.TemporaryDirectory(prefix="prova_pocock_repro_") as tmp:
        projeto = Path(tmp) / "projeto"
        shutil.copytree(PROJETO_BUG, projeto, ignore=shutil.ignore_patterns("correcao"))
        if corrigido:
            shutil.copy2(PROJETO_BUG / "correcao" / "calc.py", projeto / "calc.py")
        try:
            return subprocess.run(
                argv, cwd=str(projeto), capture_output=True, timeout=TIMEOUT_REPRO
            ).returncode
        except (OSError, subprocess.TimeoutExpired):
            return -1


def conferir_reproducao(comando: str) -> Optional[str]:
    """Roda de verdade: tem que dar vermelho com o bug e verde com a correção."""
    try:
        argv = shlex.split(comando)
    except ValueError as exc:
        return f"comando de reprodução ilegível: {exc}"
    if not argv or Path(argv[0]).stem.lower() not in ("python", "python3", "py", "pytest"):
        return f"comando de reprodução '{comando}' recusado: só comandos python rodam no gate"
    argv = [sys.executable, "-m", "pytest", *argv[1:]] if Path(argv[0]).stem.lower() == "pytest" \
        else [sys.executable, *argv[1:]]
    if _rodar_no_projeto(argv, corrigido=False) == 0:
        return f"comando de reprodução '{comando}' não fica vermelho com o bug (exit 0)"
    if _rodar_no_projeto(argv, corrigido=True) != 0:
        return f"comando de reprodução '{comando}' continua vermelho depois da correção: não isola este bug"
    return None


def checar_tickets(texto: str) -> List[str]:
    blocos = [texto[m.start():] for m in TICKET_CABECALHO.finditer(texto)]
    blocos = [b[:TICKET_CABECALHO.search(b, 1).start()] if TICKET_CABECALHO.search(b, 1) else b for b in blocos]
    tickets = extrair_tickets_de_conteudo(texto, "artefato")
    if len(tickets) < 2:
        return [f"só {len(tickets)} ticket(s) no formato [TICKET-XX]; a spec tem 3 comportamentos"]
    erros: List[str] = []
    for bloco, ticket in zip(blocos, tickets):
        if not re.search(r"Blocked\s+by", bloco, re.IGNORECASE):
            erros.append(f"{ticket['id']} sem 'Blocked by'")
        testes = [a for a in ticket["arquivos_alvo"] if ARQUIVO_DE_TESTE.search(a.replace("\\", "/"))]
        if not testes:
            erros.append(f"{ticket['id']} só de código (nenhum arquivo de teste)")
        elif len(testes) == len(ticket["arquivos_alvo"]):
            erros.append(f"{ticket['id']} só de testes (nenhum arquivo de código)")
    return erros


def checar_grill(texto: str) -> List[str]:
    bloco = _secao(texto, r"Consolidated\s+Assumptions")
    if bloco is None:
        return ["sem o bloco 'Consolidated Assumptions'"]
    inicios = [m.start() for m in ITEM_NUMERADO.finditer(bloco)]
    if not inicios:
        return ["'Consolidated Assumptions' sem itens numerados"]
    itens = [bloco[i:j] for i, j in zip(inicios, inicios[1:] + [len(bloco)])]
    sem = [n for n, item in enumerate(itens, 1) if not MOTIVO_OU_RECOMENDACAO.search(item)]
    # Recomendação = resposta com motivo; rótulo "Recommended:" ou "because/porque" contam.
    return [f"item(ns) {sem} sem recomendação (resposta sem motivo)"] if sem else []


def checar_tdd(texto: str) -> List[str]:
    seam = re.search(r"^#{1,6}[^\n]*(seam|pontos?\s+de\s+teste)", texto, re.MULTILINE | re.IGNORECASE)
    teste = re.search(r"def\s+test_|\btest\(|\bit\(|@Test\b|func\s+Test", texto)
    if not seam:
        return ["sem seção de pontos de teste (seams)"]
    if not teste:
        return ["nenhum teste escrito depois dos seams"]
    if teste.start() < seam.start():
        return ["primeiro teste aparece antes da seção de seams"]
    return []


CHECAGENS: Dict[str, Callable[[str], List[str]]] = {
    "aidd-diagnose": checar_diagnose,
    "aidd-tickets": checar_tickets,
    "aidd-grill": checar_grill,
    "aidd-tdd": checar_tdd,
}


# ------------------------------------------------------------ modo real

def _prompt(skill: str) -> str:
    skill_md = (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")
    if skill == "aidd-diagnose":
        caso = (
            "Case: bug report and code below (project folder has only calc.py).\n\n"
            + (PROJETO_BUG / "SINTOMA.md").read_text(encoding="utf-8")
            + "\n```python\n" + (PROJETO_BUG / "calc.py").read_text(encoding="utf-8") + "```\n\n"
            "Deliver the root-cause report markdown. Put the reproduction command in a line "
            "'- **Comando**: `<command>`' that runs from the project folder."
        )
    else:
        caso = "Case: the spec below.\n\n" + SPEC.read_text(encoding="utf-8")
        if skill == "aidd-tdd":
            caso += "\nDeliver the TDD plan and the first failing test for behavior 1."
        elif skill == "aidd-tickets":
            caso += "\nDeliver the ticket list."
        else:
            caso += "\nThis is a non-interactive batch run."
    return (
        f"Follow this skill exactly.\n\n<skill name=\"{skill}\">\n{skill_md}\n</skill>\n\n{caso}\n\n"
        "Non-interactive run: nobody will answer. Where the skill says to ask, show or confirm "
        "with the user, write it in the output and proceed. Output only the final markdown artifact."
    )


def gerar_com_modelo(skill: str, pasta: Path) -> Optional[str]:
    claude = shutil.which("claude")
    if not claude:
        return "CLI 'claude' não encontrada no PATH"
    argv = [claude, "-p", "--model", MODELO, "--no-session-persistence",
            "--disallowedTools", "Bash", "Edit", "Write", "NotebookEdit"]
    res = None
    for tentativa in (1, 2):  # timeout é falha de infraestrutura, não da skill: 1 nova tentativa
        try:
            res = subprocess.run(
                argv, input=_prompt(skill), cwd=str(pasta), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=TIMEOUT_MODELO,
            )
            break
        except subprocess.TimeoutExpired:
            print(f"   (tentativa {tentativa}: modelo passou de {TIMEOUT_MODELO}s)")
        except OSError as exc:
            return f"falha ao rodar o modelo: {exc}"
    if res is None:
        return f"modelo passou de {TIMEOUT_MODELO}s nas 2 tentativas"
    if res.returncode != 0 or not res.stdout.strip():
        return f"modelo saiu com exit {res.returncode}: {(res.stderr or res.stdout)[:300]}"
    (pasta / f"{skill}.md").write_text(res.stdout, encoding="utf-8")
    return None


# ----------------------------------------------------------------- main

def auditar(pasta: Path, skills: List[str], gerar: bool) -> int:
    aprovado = True
    for skill in skills:
        erros: List[str] = []
        if gerar:
            falha = gerar_com_modelo(skill, pasta)
            if falha:
                erros.append(falha)
        artefato = pasta / f"{skill}.md"
        if not erros:
            if artefato.is_file():
                erros = CHECAGENS[skill](artefato.read_text(encoding="utf-8"))
            else:
                erros = [f"artefato ausente: {artefato.name}"]
        if erros:
            aprovado = False
            print(f"[{skill}] REPROVADO")
            for erro in erros:
                print(f"   - {erro}")
        else:
            print(f"[{skill}] APROVADO")
        if gerar and artefato.is_file():
            print(f"   (artefato gerado: {len(artefato.read_text(encoding='utf-8').splitlines())} linhas)")
    print("EXIT 0: todas as skills aprovadas." if aprovado else "EXIT 1: skill(s) reprovada(s).")
    return 0 if aprovado else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="G_PROVA_SKILLS_POCOCK: prova de uso real das skills (manual)")
    parser.add_argument("--artefatos", type=Path, help="confere <skill>.md já salvos nesta pasta (sem modelo)")
    parser.add_argument("--skill", choices=sorted(CHECAGENS), action="append", help="roda só esta(s) skill(s)")
    parser.add_argument("--manter", type=Path, help="copia os artefatos gerados para esta pasta antes de apagar")
    args = parser.parse_args(argv)
    skills = args.skill or list(CHECAGENS)

    if args.artefatos:
        return auditar(args.artefatos, skills, gerar=False)

    with tempfile.TemporaryDirectory(prefix="prova_pocock_") as tmp:
        codigo = auditar(Path(tmp), skills, gerar=True)
        if args.manter:
            args.manter.mkdir(parents=True, exist_ok=True)
            for arq in Path(tmp).glob("*.md"):
                shutil.copy2(arq, args.manter / arq.name)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
