#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — GATE G_LIVRO_EVIDENCIA
=============================================================================
Audita deterministicamente o livro-texto gerado para um projeto, impedindo que
ele afirme o que nao pode provar.

Um livro-texto e perigoso justamente por parecer confiavel: ele carrega a
autoridade de documento oficial. Se citar um arquivo que nao existe, ou se
apresentar numero fabricado como se fosse medido, ele engana com mais forca do
que um texto qualquer. Este gate existe para tornar isso mecanicamente
impossivel.

Regras auditadas (exit 1 em qualquer violacao):
  R1. Manifesto valido: livro.json existe, e legivel e lista partes reais.
  R2. Rastreabilidade presente: toda parte de conteudo cita suas fontes.
  R3. Evidencia real: todo arquivo citado como fonte existe na pasta do projeto.
  R4. Zero marcador de espaco: nenhum TODO/FIXME/XXX/<preencher> no texto final.
  R5. Procedencia dos artefatos: o que o manifesto diz ter lido esta em disco.
  R6. Ausencia declarada: artefato ausente aparece no apendice de estado honesto.

Uso:
  python gates/G_LIVRO_EVIDENCIA.py --projeto <pasta-do-projeto>
  python gates/G_LIVRO_EVIDENCIA.py --livro <pasta-do-livro>
  python gates/G_LIVRO_EVIDENCIA.py --projeto <pasta> --json

Exit: 0 = aprovado, 1 = reprovado.
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LARGURA = 70
# Marcadores buscados como palavra isolada e em caixa alta: "Todo sistema..." e
# portugues legitimo, "TODO:" e trabalho inacabado. Sem essa distincao o gate
# reprovaria texto correto — e um gate com falso positivo deixa de ser levado a serio.
MARCADORES_PROIBIDOS = (
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bXXX\b"),
    re.compile(r"<preencher>", re.IGNORECASE),
    re.compile(r"\bLOREM IPSUM\b", re.IGNORECASE),
    re.compile(r"\bPLACEHOLDER\b"),
)

# Extensoes que, citadas em codigo inline, devem existir em disco. Nomes com
# outras extensoes (ou sem extensao) sao termos tecnicos, nao referencias.
EXTENSOES_RASTREAVEIS = (".json", ".md", ".py", ".yml", ".yaml", ".toml", ".ini", ".txt")

PADRAO_CITACAO = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./\\-]*)`")


def cabecalho() -> None:
    print("=" * LARGURA)
    print(" [GATE] G_LIVRO_EVIDENCIA — Auditoria de evidencia do livro-texto")
    print("=" * LARGURA)


def encerrar(erros: list[str], avisos: list[str], modo_json: bool, resumo: dict) -> int:
    if modo_json:
        print(json.dumps({"aprovado": not erros, "erros": erros, "avisos": avisos, **resumo},
                         ensure_ascii=False, indent=2))
        return 1 if erros else 0

    for aviso in avisos:
        print(f"  [AVISO] {aviso}")
    print()
    if erros:
        print(" [FALHA] Violacoes encontradas:")
        for erro in erros:
            print(f"   - {erro}")
        print()
        print("=" * LARGURA)
        print(" [REPROVADO] Quality Gate G_LIVRO_EVIDENCIA FALHOU (exit 1)")
        print("=" * LARGURA)
        return 1

    print("=" * LARGURA)
    print(" [SUCESSO] Quality Gate G_LIVRO_EVIDENCIA APROVADO")
    print("=" * LARGURA)
    return 0


def auditar(pasta_livro: Path, pasta_projeto: Path, modo_json: bool) -> int:
    if not modo_json:
        cabecalho()

    erros: list[str] = []
    avisos: list[str] = []

    # --- R1: manifesto -----------------------------------------------------
    manifesto_path = pasta_livro / "livro.json"
    if not manifesto_path.is_file():
        erros.append(f"manifesto ausente: {manifesto_path}")
        return encerrar(erros, avisos, modo_json, {})

    try:
        manifesto = json.loads(manifesto_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        erros.append(f"manifesto ilegivel ({exc.__class__.__name__}): {manifesto_path}")
        return encerrar(erros, avisos, modo_json, {})

    nomes_partes = manifesto.get("partes") or []
    if not nomes_partes:
        erros.append("manifesto nao declara nenhuma parte")

    dir_partes = pasta_livro / manifesto.get("pasta_partes", "partes")
    partes: list[Path] = []
    for nome in nomes_partes:
        caminho = dir_partes / nome
        if caminho.is_file():
            partes.append(caminho)
        else:
            erros.append(f"parte declarada no manifesto e ausente em disco: {nome}")

    if not partes:
        return encerrar(erros, avisos, modo_json, {"partes": 0})

    # --- R5: procedencia dos artefatos -------------------------------------
    lidos = manifesto.get("artefatos_lidos") or []
    for artefato in lidos:
        if not (pasta_projeto / artefato).is_file():
            erros.append(
                f"manifesto afirma ter lido '{artefato}', mas o arquivo nao existe no projeto"
            )

    # --- R2, R3, R4, R6 ----------------------------------------------------
    ausentes_declarados = {a.split(" ")[0] for a in (manifesto.get("artefatos_ausentes") or [])}
    citados_inexistentes: set[str] = set()
    total_citacoes = 0
    partes_sem_rastreabilidade: list[str] = []
    texto_completo: list[str] = []

    for caminho in partes:
        texto = caminho.read_text(encoding="utf-8", errors="replace")
        texto_completo.append(texto)

        # R4: marcador de espaco
        for marcador in MARCADORES_PROIBIDOS:
            achado = marcador.search(texto)
            if achado:
                erros.append(
                    f"{caminho.name}: contem marcador de trabalho inacabado '{achado.group(0)}'"
                )

        # R2: rastreabilidade — o frontmatter e o apendice sao isentos por natureza
        eh_frontmatter = caminho.name.startswith("00")
        eh_apendice = "apendice" in caminho.name.lower() or "apêndice" in texto.lower()[:400]
        if not eh_frontmatter and not eh_apendice and "Rastreabilidade" not in texto:
            partes_sem_rastreabilidade.append(caminho.name)

        # R3: evidencia real
        for citado in PADRAO_CITACAO.findall(texto):
            if not citado.lower().endswith(EXTENSOES_RASTREAVEIS):
                continue
            if citado.startswith(("http", "<")) or "*" in citado:
                continue
            total_citacoes += 1
            # A citacao pode apontar para a pasta do projeto (evidencia) ou para o
            # proprio repositorio do ecossistema (instrucao de uso). So a primeira
            # e obrigatoria; a segunda vira aviso.
            if (pasta_projeto / citado).exists():
                continue
            if (Path(__file__).resolve().parent.parent / citado).exists():
                continue
            # O apendice de estado honesto CITA justamente os artefatos ausentes —
            # essa e a funcao dele. Exigir que existam inverteria a regra: o livro
            # seria punido por ser transparente sobre o que nao pode afirmar.
            if citado in ausentes_declarados:
                continue
            citados_inexistentes.add(citado)

    for nome in partes_sem_rastreabilidade:
        erros.append(f"{nome}: nenhuma secao de rastreabilidade — capitulo sem fonte declarada")

    for citado in sorted(citados_inexistentes):
        erros.append(f"arquivo citado como evidencia nao existe: '{citado}'")

    # R6: toda ausencia registrada no manifesto precisa aparecer no texto final
    ausentes = manifesto.get("artefatos_ausentes") or []
    texto_unico = "\n".join(texto_completo)
    nao_declarados = [a for a in ausentes if a.split(" ")[0] not in texto_unico]
    if nao_declarados:
        erros.append(
            "artefatos ausentes nao declarados no livro: " + ", ".join(nao_declarados[:5])
        )

    if not lidos and not modo_json:
        avisos.append("manifesto nao registra 'artefatos_lidos' — procedencia nao auditavel")

    resumo = {
        "partes": len(partes),
        "citacoes_verificadas": total_citacoes,
        "artefatos_lidos": len(lidos),
        "artefatos_ausentes": len(ausentes),
    }

    if not modo_json:
        print(f"  Partes auditadas:        {resumo['partes']}")
        print(f"  Citacoes verificadas:    {resumo['citacoes_verificadas']}")
        print(f"  Artefatos lidos:         {resumo['artefatos_lidos']}")
        print(f"  Artefatos ausentes:      {resumo['artefatos_ausentes']} (devem estar declarados)")

    return encerrar(erros, avisos, modo_json, resumo)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audita a evidencia de um livro-texto gerado")
    parser.add_argument("--projeto", default=None,
                        help="pasta do projeto (o livro e procurado em <projeto>/livro)")
    parser.add_argument("--livro", default=None, help="pasta do livro, quando fora do projeto")
    parser.add_argument("--json", action="store_true", dest="modo_json",
                        help="saida estruturada em JSON")
    args = parser.parse_args(argv)

    import os
    if not args.projeto and not args.livro:
        args.projeto = os.environ.get("AIDD_LIVRO_PROJETO")
        args.livro = os.environ.get("AIDD_LIVRO_PASTA")

    if not args.projeto and not args.livro:
        parser.error("informe --projeto ou --livro (ou defina AIDD_LIVRO_PROJETO)")

    if args.projeto:
        pasta_projeto = Path(args.projeto).resolve()
        pasta_livro = Path(args.livro).resolve() if args.livro else pasta_projeto / "livro"
    else:
        pasta_livro = Path(args.livro).resolve()
        pasta_projeto = pasta_livro.parent

    if not pasta_livro.is_dir():
        print(f"[ERRO] pasta do livro nao encontrada: {pasta_livro}", file=sys.stderr)
        return 1

    return auditar(pasta_livro, pasta_projeto, args.modo_json)


if __name__ == "__main__":
    sys.exit(main())
