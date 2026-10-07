# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_SEGREDOS
=============================================================================
Escaneia arquivos em busca de credenciais hardcoded, delegando a varredura
para o detect-secrets (Yelp) — ferramenta OSS madura com dezenas de
detectores especializados (AWS, GCP, GitHub, Slack, Stripe, JWT, chaves
privadas, alta entropia Shannon/Base64/Hex, etc). Substitui o scanner de
entropia caseiro anterior (achado NIH #1 em
docs/features/08-09-2026_feature-oportunidades-reaproveitamento-nih.md).

Escopo de varredura (mesmo resolvedor do G_TESTES_REAIS, AIDD_GATES_MODO):
  * modo 'rapido' (padrão) — varre APENAS os arquivos staged do commit em
    curso, resolvidos por _escopo_commit.arquivos_staged() e filtrados pelos
    que existem em disco. É o que roda no pre-commit: o commit só pode
    recarregar segredo pelo que ele realmente vai gravar.
  * modo 'completo' (AIDD_GATES_MODO=completo) — varre todos os arquivos
    rastreados pelo git (git ls-files), na raiz do ecossistema, não só um
    subprojeto. É a bateria de auditoria.
  * stage vazio no modo 'rapido' aprova sem varrer nada (não há commit em
    curso para reprovar).
Se o índice git não responder (fora de um work tree, git indisponível), o modo
'rapido' cai para a varredura completa: o escopo nunca encolhe por indeterminismo.

Achados já revisados e catalogados no baseline .secrets.baseline (raiz do
ecossistema) — fixtures de teste, placeholders de demonstração — não
reprovam o gate; um achado novo, fora do baseline, reprova.

O gate só LÊ o baseline (ciclo-03 VSA, Ticket 9): o detect-secrets trabalha
numa cópia temporária, então rodar o gate não regrava .secrets.baseline (antes
o pre-commit reprovava com "files were modified by this hook"). Atualizar o
baseline é um comando explícito e separado:
  1. python scripts/atualizar_baseline_segredos.py
  2. python -m detect_secrets audit .secrets.baseline   (marca real/falso positivo)
  3. Commitar o .secrets.baseline atualizado.

Uso:
  python modulos/04-nucleo-compartilhado/gates/G_SEGREDOS.py
      exit 0 = nenhum segredo novo fora do baseline. exit 1 = achado novo
      não catalogado (ou detect-secrets não instalado).
"""

import os
import shutil
import subprocess
import sys
import tempfile

_GATES_DIR = os.path.dirname(os.path.abspath(__file__))
if _GATES_DIR not in sys.path:
    sys.path.insert(0, _GATES_DIR)

import _escopo_commit  # noqa: E402  (mesmo diretorio do gate, resolvido acima)

from pathlib import Path as _Path  # noqa: E402
ROOT_DIR = str(next((p.parent for p in _Path(__file__).resolve().parents if p.name == "modulos"), _Path(__file__).resolve().parent.parent))  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)
BASELINE_PATH = os.path.join(ROOT_DIR, ".secrets.baseline")
ARQUIVO_BASELINE = ".secrets.baseline"


def _baseline_usa_barras_invertidas():
    """Detecta se o baseline usa barras invertidas (gerado no Windows) ou barras normais."""
    if not os.path.isfile(BASELINE_PATH):
        return False
    try:
        import json
        with open(BASELINE_PATH, "r", encoding="utf-8") as bf:
            base_data = json.load(bf)
        keys = list(base_data.get("results", {}).keys())
        return bool(keys) and "\\" in keys[0]
    except Exception:
        return False


def _normalizar(caminho, usa_backslash):
    """Normaliza o caminho do git para o mesmo formato de chave do baseline."""
    if usa_backslash:
        return os.path.normpath(caminho)
    return caminho.replace("\\", "/")


def _arquivos_existentes(brutos, usa_backslash):
    """Filtra a lista bruta do git: normaliza, descarta o proprio baseline,
    remove repetidos e mantem somente o que existe em disco."""
    arquivos = []
    vistos = set()
    for bruto in brutos:
        caminho = _normalizar(str(bruto).strip(), usa_backslash)
        if not caminho or caminho == ARQUIVO_BASELINE or caminho in vistos:
            continue
        vistos.add(caminho)
        if os.path.isfile(os.path.join(ROOT_DIR, caminho)):
            arquivos.append(caminho)
    return arquivos


def _indice_git_consultavel():
    """True quando o ROOT_DIR e um work tree git que responde — condicao para o
    escopo rapido poder encolher. Fora disso (git ausente, arvore sem .git,
    indice corrompido) o escopo e indeterminavel e vale a varredura completa."""
    try:
        consulta = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"], cwd=ROOT_DIR,
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return consulta.returncode == 0


def _arquivos_rastreados(usa_backslash):
    """Todos os arquivos rastreados pelo git na raiz do ecossistema."""
    resultado = subprocess.run(
        ["git", "ls-files"], cwd=ROOT_DIR,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if resultado.returncode != 0:
        return []
    return _arquivos_existentes(resultado.stdout.splitlines(), usa_backslash)


def escopo_de_varredura():
    """Retorna (modo, rotulo, arquivos) do escopo a varrer neste commit.

    'rapido' -> apenas o que esta staged; 'completo' -> toda a arvore
    rastreada. O rotulo descreve a origem da lista e vai para o stdout do gate.
    """
    usa_backslash = _baseline_usa_barras_invertidas()
    modo = _escopo_commit.modo()
    if modo == _escopo_commit.MODO_RAPIDO and _indice_git_consultavel():
        arquivos = _arquivos_existentes(
            _escopo_commit.arquivos_staged(raiz=ROOT_DIR), usa_backslash
        )
        rotulo = f"{len(arquivos)} arquivo(s) staged no commit em curso"
    else:
        arquivos = _arquivos_rastreados(usa_backslash)
        rotulo = f"{len(arquivos)} arquivo(s) rastreado(s) pelo git"
    return modo, rotulo, arquivos


def escanear():
    print("=" * 70)
    print(" [GATE] G_SEGREDOS — Varredura de credenciais hardcoded (detect-secrets)")
    print("=" * 70)

    try:
        from detect_secrets import pre_commit_hook
    except ImportError:
        print("[FALHA] Pacote 'detect-secrets' não instalado.")
        print("Instale com: pip install detect-secrets")
        return 1

    modo, rotulo, arquivos = escopo_de_varredura()
    print(f"[INFO] Escopo {modo}: {rotulo}.")

    tem_baseline = os.path.exists(BASELINE_PATH)
    copia_baseline = None
    if tem_baseline:
        print(f"[OK] Baseline carregado de {os.path.relpath(BASELINE_PATH, ROOT_DIR)} (somente leitura)")
        # Cópia temporária: o detect-secrets pode querer regravar números de linha;
        # isso nunca chega ao arquivo versionado.
        fd, copia_baseline = tempfile.mkstemp(prefix="aidd_baseline_", suffix=".json")
        os.close(fd)
        shutil.copyfile(BASELINE_PATH, copia_baseline)
        argv = ["--baseline", copia_baseline]
    else:
        print("[AVISO] Nenhum .secrets.baseline encontrado — tolerância zero "
              "(qualquer achado é tratado como novo).")
        argv = []

    if not arquivos:
        print("[INFO] Escopo vazio — nenhum arquivo a varrer.")
        print(" [SUCESSO] Quality Gate G_SEGREDOS APROVADO (100% OK)!")
        print("=" * 70)
        return 0

    argv += arquivos

    cwd_original = os.getcwd()
    os.chdir(ROOT_DIR)
    try:
        codigo = pre_commit_hook.main(argv)
    finally:
        os.chdir(cwd_original)
        if copia_baseline and os.path.exists(copia_baseline):
            os.remove(copia_baseline)

    print("\n" + "=" * 70)
    if codigo not in (0, 3):
        print(" [FALHA] Quality Gate REPROVADO — achado(s) de credencial fora do baseline.")
        print(
            "\nSe for um falso positivo real, revise e adicione ao baseline com "
            "`python scripts/atualizar_baseline_segredos.py`, audite "
            "com `python -m detect_secrets audit .secrets.baseline` e comite o "
            "baseline atualizado. Se for um segredo de verdade, remova-o do "
            "arquivo e rotacione a credencial imediatamente."
        )
        print("=" * 70)
        return 1

    if codigo == 3:
        print(" [INFO] Números de linha do .secrets.baseline estão desatualizados "
              "(o arquivo NÃO foi alterado). Para atualizar: "
              "`python scripts/atualizar_baseline_segredos.py`.")

    print(" [SUCESSO] Quality Gate G_SEGREDOS APROVADO (100% OK)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(escanear())
