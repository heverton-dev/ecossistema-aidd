# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — ATUALIZADOR DETERMINÍSTICO DE docs/planos/INDEX.md
=============================================================================
Varre docs/planos/ (raiz + subpastas feitos/, fazendo/, a-fazer/), calcula o
status REAL de cada iniciativa (nunca hardcoded), MOVE fisicamente a pasta/
arquivo para a subpasta que corresponde a esse status quando ele mudou desde
a última vez, e reescreve INDEX.md com os caminhos já atualizados.

Duas formas de iniciativa reconhecidas (iguais a antes, agora também
buscadas dentro de feitos/, fazendo/ e a-fazer/, não só na raiz):
  1. Arquivo solto docs/planos/[<subpasta>/]PLANO-<NOME>.md com uma linha
     "> **Status:** <texto livre>" perto do topo.
  2. Pasta docs/planos/[<subpasta>/]<nome>/00-PROCESSO-E-DECISOES.md com uma
     seção "## N. Registro de progresso" contendo uma tabela Markdown cuja
     coluna de status usa os marcadores já convencionados neste monorepo:
     ✅ (concluído), 🔶 (em execução), ⏳ ou 🔒 (aguardando).

Mapeamento status -> subpasta:
  concluido    -> docs/planos/feitos/<nome>
  em_execucao  -> docs/planos/fazendo/<nome>
  aguardando   -> docs/planos/a-fazer/<nome>
  indeterminado -> não move (fica onde está, reportado como aviso)

Uma iniciativa criada direto na raiz de docs/planos/ (ex.: por
`python ecossistema.py plan init <nome>`) é normal e esperada: a primeira
execução deste script depois disso já a move para a subpasta certa.

Uso:
    python scripts/atualizar_index_planos.py            # move + reescreve INDEX.md
    python scripts/atualizar_index_planos.py --dry-run  # só mostra o que faria/geraria
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PLANOS_DIR = RAIZ / "docs" / "planos"
INDEX_PATH = PLANOS_DIR / "INDEX.md"

CONCLUIDO = "concluido"
EM_EXECUCAO = "em_execucao"
AGUARDANDO = "aguardando"
INDETERMINADO = "indeterminado"

TITULOS = {
    CONCLUIDO: "✅ Concluídos",
    EM_EXECUCAO: "🔶 Em execução",
    AGUARDANDO: "⏳ Aguardando execução",
    INDETERMINADO: "⚠️ Status indeterminado (revisar manualmente)",
}

SUBPASTA_DO_STATUS = {
    CONCLUIDO: "feitos",
    EM_EXECUCAO: "fazendo",
    AGUARDANDO: "a-fazer",
}
SUBPASTAS_CONHECIDAS = set(SUBPASTA_DO_STATUS.values())


def status_de_arquivo_unico(caminho: Path) -> str:
    """Lê a linha '> **Status:** ...' de um PLANO-<NOME>.md solto."""
    texto = caminho.read_text(encoding="utf-8")
    m = re.search(r"\*\*Status:\*\*\s*([^\n|]+)", texto)
    if not m:
        return INDETERMINADO
    valor = m.group(1).upper()
    if "CONCLU" in valor:
        return CONCLUIDO
    if "EM ANDAMENTO" in valor or "EM EXECU" in valor or "EXECUTANDO" in valor:
        return EM_EXECUCAO
    return AGUARDANDO


def extrair_linhas_registro_progresso(texto: str) -> list[str]:
    """Retorna as linhas de dados (sem cabeçalho/separador) da tabela sob
    o heading '## N. Registro de progresso' de um 00-PROCESSO-E-DECISOES.md."""
    linhas = texto.splitlines()
    inicio = None
    for i, linha in enumerate(linhas):
        if re.match(r"^#+\s*\d*\.?\s*Registro de progresso", linha.strip(), re.IGNORECASE):
            inicio = i + 1
            break
    if inicio is None:
        return []
    dados = []
    for linha in linhas[inicio:]:
        if linha.strip().startswith("#"):
            break
        if linha.strip().startswith("|") and "---" not in linha:
            dados.append(linha)
    # a primeira linha de dados é o cabeçalho da própria tabela (# | Item | Status | ...) — pular
    return dados[1:] if len(dados) > 1 else []


def status_de_pasta(caminho_00: Path) -> str:
    texto = caminho_00.read_text(encoding="utf-8")
    linhas = extrair_linhas_registro_progresso(texto)
    if not linhas:
        return INDETERMINADO
    marcadores = []
    for linha in linhas:
        if "✅" in linha:
            marcadores.append(CONCLUIDO)
        elif "🔶" in linha:
            marcadores.append(EM_EXECUCAO)
        elif "⏳" in linha or "🔒" in linha:
            marcadores.append(AGUARDANDO)
        else:
            marcadores.append(INDETERMINADO)
    if all(m == CONCLUIDO for m in marcadores):
        return CONCLUIDO
    if any(m == EM_EXECUCAO for m in marcadores) or (
        any(m == CONCLUIDO for m in marcadores) and any(m == AGUARDANDO for m in marcadores)
    ):
        return EM_EXECUCAO
    if all(m == AGUARDANDO for m in marcadores):
        return AGUARDANDO
    return INDETERMINADO


def _sem_prefixo_numerico(nome: str) -> str:
    """Remove um prefixo 'NN-' de prioridade de execucao (ex: '01-nome' -> 'nome'),
    usado só para exibição do título — o prefixo continua no caminho físico."""
    return re.sub(r"^\d+-", "", nome)


def _pastas_de_busca() -> list[Path]:
    """Raiz de docs/planos/ + as 3 subpastas conhecidas (só as que existirem)."""
    pastas = [PLANOS_DIR]
    for nome in sorted(SUBPASTAS_CONHECIDAS):
        candidata = PLANOS_DIR / nome
        if candidata.is_dir():
            pastas.append(candidata)
    return pastas


def descobrir_iniciativas() -> list[dict]:
    """Retorna lista de dicts: nome_exibicao, item (Path real no disco), status."""
    resultado = []
    vistos = set()
    for pasta in _pastas_de_busca():
        for item in sorted(pasta.iterdir()):
            if item.resolve() in vistos:
                continue
            if item.name == "INDEX.md":
                continue
            if item.is_dir() and item.name in SUBPASTAS_CONHECIDAS and pasta == PLANOS_DIR:
                continue  # a própria subpasta-contêiner, não uma iniciativa
            if item.is_file() and item.name.startswith("PLANO-") and item.suffix == ".md":
                status = status_de_arquivo_unico(item)
                titulo = item.stem.replace("PLANO-", "").replace("-", " ").title()
                resultado.append({"titulo": titulo, "item": item, "status": status})
                vistos.add(item.resolve())
            elif item.is_dir():
                arquivo_00 = item / "00-PROCESSO-E-DECISOES.md"
                if arquivo_00.exists():
                    status = status_de_pasta(arquivo_00)
                    titulo = _sem_prefixo_numerico(item.name).replace("-", " ").title()
                    resultado.append({"titulo": titulo, "item": item, "status": status})
                    vistos.add(item.resolve())
    return resultado


def mover_se_necessario(iniciativa: dict, dry_run: bool) -> None:
    """Move fisicamente item para a subpasta correspondente ao status atual,
    se ainda não estiver lá. Indeterminado nunca é movido automaticamente."""
    status = iniciativa["status"]
    if status not in SUBPASTA_DO_STATUS:
        return
    item: Path = iniciativa["item"]
    subpasta_alvo = SUBPASTA_DO_STATUS[status]
    if item.parent.name == subpasta_alvo:
        return  # já está no lugar certo
    destino_dir = PLANOS_DIR / subpasta_alvo
    destino = destino_dir / item.name
    if dry_run:
        print(f"[dry-run] moveria: {item.relative_to(PLANOS_DIR)} -> {subpasta_alvo}/{item.name}")
        return
    destino_dir.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        print(f"[ERRO] destino já existe, não movi: {destino}", file=sys.stderr)
        return
    shutil.move(str(item), str(destino))
    iniciativa["item"] = destino
    print(f"[OK] movido: {subpasta_alvo}/{item.name}")


def montar_markdown(iniciativas: list[dict]) -> str:
    linhas = [
        "# Índice — `docs/planos/`",
        "",
        "> Gerado automaticamente por `python scripts/atualizar_index_planos.py` a partir do status real de cada documento — inclusive a subpasta física (`feitos/`, `fazendo/`, `a-fazer/`), que este script também mantém sincronizada. **Não editar manualmente**: rode o script de novo depois de qualquer mudança de status.",
        "",
    ]
    for chave in (CONCLUIDO, EM_EXECUCAO, AGUARDANDO, INDETERMINADO):
        do_grupo = [ini for ini in iniciativas if ini["status"] == chave]
        if not do_grupo:
            continue
        linhas.append(f"## {TITULOS[chave]}")
        linhas.append("")
        linhas.append("| Iniciativa | Local |")
        linhas.append("|---|---|")
        for ini in do_grupo:
            caminho_rel = ini["item"].relative_to(PLANOS_DIR).as_posix()
            if ini["item"].is_dir():
                caminho_rel += "/"
            linhas.append(f"| {ini['titulo']} | `{caminho_rel}` |")
        linhas.append("")
    linhas.append("---")
    linhas.append("")
    linhas.append(
        "**Convenção:** pastas com `00-PROCESSO-E-DECISOES.md` + `NN-<item>.md` são iniciativas "
        "multi-item (status = agregado da tabela \"Registro de progresso\"); arquivos `PLANO-<NOME>.md` "
        "soltos são planos de item único (status = linha `**Status:**` do próprio arquivo). Uma "
        "iniciativa nova criada direto na raiz de `docs/planos/` (via `plan init`) é normal — a próxima "
        "execução deste script já a move para `feitos/`, `fazendo/` ou `a-fazer/` conforme seu status real."
    )
    linhas.append("")
    return "\n".join(linhas)


def main() -> int:
    # Windows abre stdout/stderr no codepage local (cp1252), que não
    # representa os emojis usados nos marcadores de status — força UTF-8.
    for fluxo in (sys.stdout, sys.stderr):
        if hasattr(fluxo, "reconfigure"):
            fluxo.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Só imprime o resultado, não move nem escreve nada")
    args = parser.parse_args()

    iniciativas = descobrir_iniciativas()
    if not iniciativas:
        print("[ERRO] Nenhuma iniciativa encontrada em docs/planos/ — algo está errado.", file=sys.stderr)
        return 1

    for ini in iniciativas:
        mover_se_necessario(ini, dry_run=args.dry_run)

    conteudo = montar_markdown(iniciativas)

    indeterminados = [i for i in iniciativas if i["status"] == INDETERMINADO]
    if indeterminados:
        print("[AVISO] Status indeterminado (revisar manualmente, não movido automaticamente):", file=sys.stderr)
        for ini in indeterminados:
            print(f"  - {ini['titulo']} ({ini['item'].relative_to(PLANOS_DIR)})", file=sys.stderr)

    if args.dry_run:
        print(conteudo)
        return 0

    INDEX_PATH.write_text(conteudo, encoding="utf-8")
    print(f"[OK] {INDEX_PATH} atualizado com {len(iniciativas)} iniciativa(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
