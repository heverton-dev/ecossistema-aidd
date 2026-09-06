# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — ATUALIZADOR DETERMINÍSTICO DE docs/planos/INDEX.md
=============================================================================
Varre docs/planos/ e reescreve INDEX.md agrupando cada iniciativa em
Concluídos / Em execução / Aguardando execução, com base no status REAL
lido de cada documento (nunca hardcoded) — nenhuma pasta é movida.

Duas formas de iniciativa reconhecidas:
  1. Arquivo solto docs/planos/PLANO-<NOME>.md com uma linha
     "> **Status:** <texto livre>" perto do topo.
  2. Pasta docs/planos/<nome>/00-PROCESSO-E-DECISOES.md com uma seção
     "## N. Registro de progresso" contendo uma tabela Markdown cuja
     coluna de status usa os marcadores já convencionados neste
     monorepo: ✅ (concluído), 🔶 (em execução), ⏳ ou 🔒 (aguardando).

Uso:
    python scripts/atualizar_index_planos.py            # reescreve INDEX.md
    python scripts/atualizar_index_planos.py --dry-run  # só mostra o que geraria
"""
from __future__ import annotations

import argparse
import re
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


def descobrir_iniciativas() -> list[tuple[str, str, str]]:
    """Retorna lista de (nome_exibicao, caminho_relativo, status)."""
    resultado = []
    for item in sorted(PLANOS_DIR.iterdir()):
        if item.name == "INDEX.md":
            continue
        if item.is_file() and item.name.startswith("PLANO-") and item.suffix == ".md":
            status = status_de_arquivo_unico(item)
            titulo = item.stem.replace("PLANO-", "").replace("-", " ").title()
            resultado.append((titulo, item.name, status))
        elif item.is_dir():
            arquivo_00 = item / "00-PROCESSO-E-DECISOES.md"
            if arquivo_00.exists():
                status = status_de_pasta(arquivo_00)
                titulo = item.name.replace("-", " ").title()
                resultado.append((titulo, f"{item.name}/", status))
    return resultado


def montar_markdown(iniciativas: list[tuple[str, str, str]]) -> str:
    linhas = [
        "# Índice — `docs/planos/`",
        "",
        "> Gerado automaticamente por `python scripts/atualizar_index_planos.py` a partir do status real de cada documento. Nenhum caminho físico muda — os links abaixo apontam para as pastas/arquivos reais. **Não editar manualmente**: rode o script de novo depois de qualquer mudança de status.",
        "",
    ]
    for chave in (CONCLUIDO, EM_EXECUCAO, AGUARDANDO, INDETERMINADO):
        do_grupo = [ini for ini in iniciativas if ini[2] == chave]
        if not do_grupo:
            continue
        linhas.append(f"## {TITULOS[chave]}")
        linhas.append("")
        linhas.append("| Iniciativa | Local |")
        linhas.append("|---|---|")
        for titulo, caminho, _ in do_grupo:
            linhas.append(f"| {titulo} | `{caminho}` |")
        linhas.append("")
    linhas.append("---")
    linhas.append("")
    linhas.append(
        "**Convenção:** pastas com `00-PROCESSO-E-DECISOES.md` + `NN-<item>.md` são iniciativas "
        "multi-item (status = agregado da tabela \"Registro de progresso\"); arquivos `PLANO-<NOME>.md` "
        "soltos são planos de item único (status = linha `**Status:**` do próprio arquivo)."
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
    parser.add_argument("--dry-run", action="store_true", help="Só imprime o resultado, não escreve o arquivo")
    args = parser.parse_args()

    iniciativas = descobrir_iniciativas()
    if not iniciativas:
        print("[ERRO] Nenhuma iniciativa encontrada em docs/planos/ — algo está errado.", file=sys.stderr)
        return 1

    conteudo = montar_markdown(iniciativas)

    indeterminados = [i for i in iniciativas if i[2] == INDETERMINADO]
    if indeterminados:
        print("[AVISO] Status indeterminado (revisar manualmente):", file=sys.stderr)
        for titulo, caminho, _ in indeterminados:
            print(f"  - {titulo} ({caminho})", file=sys.stderr)

    if args.dry_run:
        print(conteudo)
        return 0

    INDEX_PATH.write_text(conteudo, encoding="utf-8")
    print(f"[OK] {INDEX_PATH} atualizado com {len(iniciativas)} iniciativa(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
