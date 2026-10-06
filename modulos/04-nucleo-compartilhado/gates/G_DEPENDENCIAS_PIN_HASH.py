# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_DEPENDENCIAS_PIN_HASH
=============================================================================
PLAN-0018 fase 04 (pin-exato-e-hashes-requirements-lockfile — SEC-4):
requirements.txt/requirements-dev.txt usavam `>=` solto, permitindo que
versoes novas (potencialmente corrompidas ou comprometidas na cadeia de
suprimentos) fossem baixadas automaticamente em qualquer build futuro, sem
nenhuma verificacao criptografica do pacote baixado.

Este gate reprova (exit 1) qualquer regressao nas duas camadas da correcao:

  1. Arquivos-fonte (requirements.txt, requirements-dev.txt) so podem conter
     pins EXATOS (`pacote==versao`), linhas de inclusao (`-r arquivo.txt`) ou
     comentarios/linhas em branco. Nunca `>=`, `<=`, `~=`, `!=`, faixa (`,`),
     pacote sem versao, VCS/URL direta (`git+...`, `http://...`) ou instalacao
     editable (`-e`).
  2. Lockfiles derivados (requirements.lock, requirements-dev.lock) precisam
     existir e ter, para CADA pacote resolvido, pelo menos um
     `--hash=sha256:...` — sem isso `pip install --require-hashes` rejeita a
     instalacao inteira (comportamento que queremos, mas auditado aqui de
     forma antecipada e determinista, sem depender de rodar o pip de fato).
  3. O workflow de CI que instala essas dependencias
     (.github/workflows/audit.yml) precisa invocar `pip install
     --require-hashes -r requirements-dev.lock` — nunca instalar direto de um
     .txt sem hash.

Uso:
  python gates/G_DEPENDENCIAS_PIN_HASH.py
      exit 0 = todos os arquivos-fonte com pin exato, lockfiles com hash
               completo e CI usando --require-hashes.
      exit 1 = ao menos 1 violacao (arquivo, linha e motivo sao impressos).
"""

import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (arquivo-fonte, lockfile derivado) — ambos relativos a raiz do repositorio.
PARES_DEPENDENCIA = [
    ("requirements.txt", "requirements.lock"),
    ("requirements-dev.txt", "requirements-dev.lock"),
]

WORKFLOW_CI = ".github/workflows/audit.yml"

# Especificadores de versao "soltos" — qualquer um deles numa linha de
# dependencia (fora de comentario) e uma violacao do pin exato.
ESPECIFICADORES_PROIBIDOS = (">=", "<=", "~=", "!=", ">", "<")

_RE_INCLUDE = re.compile(r"^-(r|c)\s+\S+")
_RE_EDITAVEL_OU_URL = re.compile(r"^-e\s|^(git|hg|svn|bzr)\+|^https?://")
# pacote[extra1,extra2]==1.2.3 — unico formato aceito para um pin de pacote.
_RE_PIN_EXATO = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9_.\-]*(\[[A-Za-z0-9_,\-]+\])?==[A-Za-z0-9][A-Za-z0-9_.\-]*$"
)


def _linha_util(linha_bruta):
    """Remove comentario final e espacos; None se a linha ficar vazia."""
    sem_comentario = linha_bruta.split("#", 1)[0].rstrip()
    linha = sem_comentario.strip()
    return linha or None


def _auditar_arquivo_fonte(caminho_rel):
    """Retorna lista de erros ('arquivo:linha — motivo') do arquivo-fonte."""
    caminho_abs = os.path.join(ROOT_DIR, caminho_rel)
    if not os.path.isfile(caminho_abs):
        return [f"{caminho_rel} — arquivo nao encontrado"]

    erros = []
    with open(caminho_abs, "r", encoding="utf-8-sig") as f:
        for numero, linha_bruta in enumerate(f, start=1):
            linha = _linha_util(linha_bruta)
            if linha is None:
                continue
            if _RE_INCLUDE.match(linha):
                continue
            if _RE_EDITAVEL_OU_URL.search(linha):
                erros.append(
                    f"{caminho_rel}:{numero} — instalacao editable/VCS/URL nao e um pin "
                    f"reprodutivel/hasheavel: \"{linha}\""
                )
                continue
            if any(op in linha for op in ESPECIFICADORES_PROIBIDOS):
                erros.append(
                    f"{caminho_rel}:{numero} — especificador de versao solto (nao e pin "
                    f"exato '=='): \"{linha}\""
                )
                continue
            if "," in linha:
                erros.append(
                    f"{caminho_rel}:{numero} — faixa de versao (virgula) nao e pin exato: "
                    f"\"{linha}\""
                )
                continue
            if not _RE_PIN_EXATO.match(linha):
                erros.append(
                    f"{caminho_rel}:{numero} — linha nao reconhecida como pin exato "
                    f"'pacote==versao': \"{linha}\""
                )
    return erros


def _auditar_lockfile(caminho_rel):
    """Retorna lista de erros do lockfile: precisa existir e cada pacote
    resolvido precisa ter ao menos um --hash=sha256:... associado."""
    caminho_abs = os.path.join(ROOT_DIR, caminho_rel)
    if not os.path.isfile(caminho_abs):
        return [
            f"{caminho_rel} — lockfile nao encontrado (gere com: uv pip compile "
            f"<arquivo-fonte> --generate-hashes -o {caminho_rel})"
        ]

    with open(caminho_abs, "r", encoding="utf-8-sig") as f:
        linhas = f.readlines()

    erros = []
    pacote_atual = None
    linha_pacote_atual = None
    tem_hash_atual = False

    def _fechar_pacote_atual():
        if pacote_atual is not None and not tem_hash_atual:
            erros.append(
                f"{caminho_rel}:{linha_pacote_atual} — pacote '{pacote_atual}' resolvido "
                f"sem nenhum --hash=sha256:... (pip install --require-hashes vai rejeitar)"
            )

    for numero, linha_bruta in enumerate(linhas, start=1):
        linha = linha_bruta.rstrip("\n")
        if not linha.strip():
            continue
        se_indentada = linha_bruta[0] in (" ", "\t")
        if not se_indentada:
            if linha.lstrip().startswith("#"):
                continue
            # Nova linha de pacote top-level ('pacote==versao \' ou sem continuacao).
            _fechar_pacote_atual()
            pacote_atual = linha.strip().split("=", 1)[0].strip()
            linha_pacote_atual = numero
            tem_hash_atual = False
        else:
            if linha.strip().startswith("--hash="):
                tem_hash_atual = True
    _fechar_pacote_atual()

    return erros


def _auditar_ci_require_hashes():
    """CI (workflow raiz) precisa instalar via pip install --require-hashes
    contra um lockfile (.lock), nunca um .txt sem hash."""
    caminho_abs = os.path.join(ROOT_DIR, WORKFLOW_CI)
    if not os.path.isfile(caminho_abs):
        return [f"{WORKFLOW_CI} — workflow de CI nao encontrado"]

    with open(caminho_abs, "r", encoding="utf-8-sig") as f:
        conteudo = f.read()

    erros = []
    if "--require-hashes" not in conteudo:
        erros.append(
            f"{WORKFLOW_CI} — nenhuma instalacao usa '--require-hashes' "
            f"(instalacao insegura sem verificacao de hash criptografico)"
        )
    if not re.search(r"pip install[^\n]*--require-hashes[^\n]*\.lock", conteudo):
        erros.append(
            f"{WORKFLOW_CI} — nao encontrada a combinacao esperada "
            f"'pip install --require-hashes -r <arquivo>.lock' num unico comando"
        )
    return erros


def auditar():
    print("=" * 70)
    print(" [GATE] G_DEPENDENCIAS_PIN_HASH — Pin exato + hash criptografico")
    print("=" * 70)

    erros_totais = []

    for arquivo_fonte, lockfile in PARES_DEPENDENCIA:
        erros_fonte = _auditar_arquivo_fonte(arquivo_fonte)
        if erros_fonte:
            erros_totais.extend(erros_fonte)
            print(f"[FALHA] {arquivo_fonte} — {len(erros_fonte)} violacao(oes)")
        else:
            print(f"[OK] {arquivo_fonte} — 100% pin exato")

        erros_lock = _auditar_lockfile(lockfile)
        if erros_lock:
            erros_totais.extend(erros_lock)
            print(f"[FALHA] {lockfile} — {len(erros_lock)} violacao(oes)")
        else:
            print(f"[OK] {lockfile} — todo pacote resolvido com hash")

    erros_ci = _auditar_ci_require_hashes()
    if erros_ci:
        erros_totais.extend(erros_ci)
        print(f"[FALHA] {WORKFLOW_CI} — {len(erros_ci)} violacao(oes)")
    else:
        print(f"[OK] {WORKFLOW_CI} — instalacao exige --require-hashes")

    print("\n" + "=" * 70)
    if erros_totais:
        print(f" [FALHA] Quality Gate REPROVADO com {len(erros_totais)} erro(s):")
        for erro in erros_totais:
            print(f"  - {erro}")
        print("=" * 70)
        return 1

    print(" [SUCESSO] Quality Gate G_DEPENDENCIAS_PIN_HASH APROVADO (100% OK)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(auditar())
