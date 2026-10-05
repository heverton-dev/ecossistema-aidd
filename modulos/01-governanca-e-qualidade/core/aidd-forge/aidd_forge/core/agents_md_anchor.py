"""Ancoragem idempotente da tabela "Componentes Injetados" no `AGENTS.md` alvo.

Mesmo padrao de `SlashRouter._ensure_intent_router`: procura um marcador de
secao, cria a secao se ausente, e faz upsert de uma linha por chave
(`tipo`, `nome`) quando a secao ja existe — nunca duplica linhas, nunca
acumula secoes repetidas em reinjeicoes.
"""

from __future__ import annotations

from pathlib import Path

MARKER = "## Componentes Injetados"
HEADER_ROW = "| Tipo | Nome | Descricao | Caminho |"
SEP_ROW = "| --- | --- | --- | --- |"


def _format_row(tipo: str, nome: str, descricao: str, caminho: str) -> str:
    return f"| {tipo} | {nome} | {descricao} | {caminho} |"


def render_component_table(original: str, *, tipo: str, nome: str, descricao: str, caminho: str) -> str:
    """Retorna `original` com a linha (`tipo`, `nome`) inserida/atualizada na
    tabela "Componentes Injetados" (secao criada se ausente)."""
    new_row = _format_row(tipo, nome, descricao, caminho)
    row_key = (tipo, nome)

    if MARKER not in original:
        prefix = original.rstrip("\n")
        section = f"{MARKER}\n\n{HEADER_ROW}\n{SEP_ROW}\n{new_row}\n"
        return f"{prefix}\n\n{section}" if prefix else section

    head, _, tail = original.partition(MARKER)
    tail_lines = tail.split("\n")

    idx = 0
    while idx < len(tail_lines) and tail_lines[idx].strip() == "":
        idx += 1
    if idx < len(tail_lines) and tail_lines[idx].strip().startswith("|"):
        idx += 1  # cabecalho
    if idx < len(tail_lines) and tail_lines[idx].strip().startswith("|"):
        idx += 1  # separador

    rows: list[str] = []
    while idx < len(tail_lines) and tail_lines[idx].strip().startswith("|"):
        rows.append(tail_lines[idx].strip())
        idx += 1
    trailing = "\n".join(tail_lines[idx:]).strip("\n")

    row_by_key: dict[tuple[str, str], str] = {}
    order: list[tuple[str, str]] = []
    for row in rows:
        cols = [c.strip() for c in row.strip("|").split("|")]
        key = (cols[0], cols[1])
        row_by_key[key] = row
        order.append(key)

    if row_key not in row_by_key:
        order.append(row_key)
    row_by_key[row_key] = new_row

    section_lines = [MARKER, "", HEADER_ROW, SEP_ROW, *[row_by_key[key] for key in order]]
    section = "\n".join(section_lines) + "\n"
    if trailing:
        section += f"\n{trailing}\n"

    head_stripped = head.rstrip("\n")
    return f"{head_stripped}\n\n{section}" if head_stripped else section


def ensure_component_table(
    target_root: Path, *, tipo: str, nome: str, descricao: str, caminho: str, anchor_name: str = "AGENTS.md"
) -> bool:
    """Le/atualiza `target_root/anchor_name` com a linha (`tipo`, `nome`).

    Retorna `True` se o conteudo do arquivo mudou.
    """
    anchor_path = Path(target_root) / anchor_name
    original = anchor_path.read_text(encoding="utf-8") if anchor_path.exists() else ""

    updated = render_component_table(original, tipo=tipo, nome=nome, descricao=descricao, caminho=caminho)
    if updated == original:
        return False

    anchor_path.parent.mkdir(parents=True, exist_ok=True)
    anchor_path.write_text(updated, encoding="utf-8")
    return True
