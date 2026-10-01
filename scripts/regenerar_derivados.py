# -*- coding: utf-8 -*-
"""
scripts/regenerar_derivados.py — refaz num comando só os arquivos DERIVADOS do repo.

Arquivo derivado é o que nenhuma pessoa edita: é recalculado a partir de outros
(assinatura do handoff, hashes do .secrets.baseline, ACHADOS.json, livro dos mapas).
Editá-los à mão em cada branch gerava conflito no merge e erro de CRLF (o hash do
AGENTS.md assinado em CRLF no Windows divergia do blob LF do git).

Regras:
  - Um mapa único (DERIVADOS), na ordem de dependência; nada de lógica duplicada:
    cada entrada chama o gerador que já existe.
  - Tudo é gravado com '\\n' (LF) e hash de arquivo é calculado sobre o conteúdo em LF.
  - Idempotente: rodar duas vezes seguidas não gera diff.

Uso:
  python ecossistema.py derivados regenerar [--so CAMINHO ...]
  python ecossistema.py derivados listar
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASELINE = ".secrets.baseline"
HANDOFF = "handoff-melhoria.json"
FILTRO_BASELINE = "detect_secrets.filters.common.is_baseline_file"


def _gravar_lf(caminho: Path, texto: str) -> None:
    caminho.write_bytes(texto.replace("\r\n", "\n").encode("utf-8"))


def sha256_lf(caminho: Path) -> str:
    """Hash do conteúdo como o git guarda (LF), igual numa worktree limpa."""
    return hashlib.sha256(caminho.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _rodar_script(raiz: Path, *args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=raiz, check=True, capture_output=True,
                   text=True, encoding="utf-8", errors="replace")


def regenerar_achados(raiz: Path) -> None:
    _rodar_script(raiz, "scripts/achados_ciclo.py")


def regenerar_livro_mapas(raiz: Path) -> None:
    _rodar_script(raiz, "scripts/livro_mapas.py")


def regenerar_plano_execucao(raiz: Path) -> None:
    _rodar_script(raiz, "ecossistema.py", "status", "--testes", "--write")


def regenerar_handoff(raiz: Path) -> None:
    """Recalcula o sha256 de cada artefato e reassina com o algoritmo do próprio aidd-melhoria."""
    sys.path.insert(0, str(raiz / ".agents" / "skills" / "aidd-improvement" / "scripts"))
    try:
        import handoff as modulo_handoff
    finally:
        sys.path.pop(0)
    caminho = raiz / HANDOFF
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    for artefato in dados.get("artefatos", []):
        artefato["sha256"] = sha256_lf(raiz / artefato["caminho"])
    chave = os.environ.get(modulo_handoff.VAR_CHAVE)
    if dados.get("assinatura", {}).get("algoritmo") == "hmac-sha256" and not chave:
        raise RuntimeError(f"{HANDOFF} usa hmac-sha256: defina {modulo_handoff.VAR_CHAVE} para reassinar.")
    dados.pop("assinatura", None)
    dados["assinatura"] = modulo_handoff._calcular_assinatura(dados, chave)
    _gravar_lf(caminho, json.dumps(dados, indent=2, ensure_ascii=False) + "\n")


def _chave_baseline(caminho_rel: str, usa_backslash: bool) -> str:
    return caminho_rel.replace("/", "\\") if usa_backslash else caminho_rel.replace("\\", "/")


def regenerar_baseline(raiz: Path, arquivos=None) -> None:
    """Revarre SÓ os arquivos derivados (não o repo inteiro) e troca as entradas deles no baseline.

    Mantém as demais entradas e a marcação de auditoria (is_secret) de hashes que continuam iguais.
    """
    from detect_secrets.core.secrets_collection import SecretsCollection
    from detect_secrets.settings import transient_settings

    caminho = raiz / BASELINE
    base = json.loads(caminho.read_text(encoding="utf-8"))
    resultados = base.setdefault("results", {})
    usa_backslash = any("\\" in chave for chave in resultados)
    alvos = arquivos if arquivos is not None else [d for d in DERIVADOS if d != BASELINE]
    config = {"plugins_used": base.get("plugins_used", []),
              "filters_used": [f for f in base.get("filters_used", []) if f.get("path") != FILTRO_BASELINE]}
    cwd = os.getcwd()
    os.chdir(raiz)
    try:
        with transient_settings(config):
            for rel in alvos:
                chave = _chave_baseline(rel, usa_backslash)
                antigos = {s["hashed_secret"]: s for s in resultados.get(chave, [])}
                colecao = SecretsCollection()
                if (raiz / rel).is_file():
                    colecao.scan_file(rel)
                novos = []
                for segredo in sorted(colecao.json().get(rel, []), key=lambda s: (s["line_number"], s["type"])):
                    segredo["filename"] = chave
                    if "is_secret" in antigos.get(segredo["hashed_secret"], {}):
                        segredo["is_secret"] = antigos[segredo["hashed_secret"]]["is_secret"]
                    novos.append(segredo)
                if novos:
                    resultados[chave] = novos
                else:
                    resultados.pop(chave, None)
    finally:
        os.chdir(cwd)
    base["results"] = dict(sorted(resultados.items()))
    _gravar_lf(caminho, json.dumps(base, indent=2, ensure_ascii=False) + "\n")


# Ordem = dependência: livro lê ACHADOS; handoff assina o AGENTS.md; baseline por último
# porque cobre os hashes que os anteriores acabaram de gravar.
DERIVADOS = {
    "docs/auditoria/mapa-pecas/ciclo-01/ACHADOS.json": regenerar_achados,
    "docs/livros/mapas-aidd": regenerar_livro_mapas,
    "PLANO-EXECUCAO-ESTRUTURADO.json": regenerar_plano_execucao,
    HANDOFF: regenerar_handoff,
    BASELINE: regenerar_baseline,
}


def regenerar(raiz: Path = RAIZ, so=None) -> list:
    """Regenera os derivados (todos, ou só os de `so`) e devolve os que foram refeitos."""
    desconhecidos = sorted(set(so or []) - set(DERIVADOS))
    if desconhecidos:
        raise KeyError(f"não é arquivo derivado: {', '.join(desconhecidos)}")
    feitos = []
    for caminho, funcao in DERIVADOS.items():
        if so and caminho not in so:
            continue
        funcao(raiz)
        feitos.append(caminho)
    return feitos


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Regenera os arquivos derivados do ecossistema.")
    sub = parser.add_subparsers(dest="acao", required=True)
    p_reg = sub.add_parser("regenerar", help="refaz os derivados (todos ou só --so)")
    p_reg.add_argument("--so", nargs="+", metavar="CAMINHO", help="só estes derivados")
    sub.add_parser("listar", help="lista os derivados, na ordem em que são refeitos")
    args = parser.parse_args(argv)

    if args.acao == "listar":
        for caminho in DERIVADOS:
            print(caminho)
        return 0
    try:
        feitos = regenerar(RAIZ, args.so)
    except KeyError as erro:
        print(f"[ERRO] {erro.args[0]}. Rode 'derivados listar'.")
        return 1
    except (subprocess.CalledProcessError, RuntimeError, OSError, ValueError) as erro:
        detalhe = getattr(erro, "stdout", "") or ""
        print(f"[ERRO] falha ao regenerar derivado: {erro}\n{detalhe[-800:]}")
        return 1
    for caminho in feitos:
        print(f"[OK] {caminho}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
