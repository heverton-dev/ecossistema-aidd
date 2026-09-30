# -*- coding: utf-8 -*-
"""
Parser Canônico de Tickets e Validador de Schema para aidd-tickets (Ticket 3 / D4 / DoD 3).
Extrai fatias verticais a partir de markdown estruturado [TICKET-XX] e garante que
todo ticket contenha pelo menos um arquivo de teste e comando de validação.
"""

from __future__ import annotations

import re
from typing import List, Dict, Any, Tuple


RE_TICKET_HEADER = re.compile(r"^\s*###\s+\[(TICKET-\w+)\]\s+(.+)$", re.MULTILINE)
RE_TARGET_FILES = re.compile(r"^\s*-\s+\*\*Target Files:\*\*\s+(.+)$", re.MULTILINE)
RE_VALIDATION_CMD = re.compile(r"^\s*-\s+\*\*Validation Command:\*\*\s+`?([^`\n]+)`?$", re.MULTILINE)
RE_BLOCKED_BY = re.compile(r"^\s*-\s+\*\*Blocked by:\*\*\s+(.+)$", re.MULTILINE)

TEST_PATTERNS = ["test_", "_test", "tests/", ".test.", ".spec."]


def _tem_arquivo_de_teste(arquivos: List[str]) -> bool:
    for arq in arquivos:
        arq_lower = arq.lower()
        if any(padrao in arq_lower for padrao in TEST_PATTERNS):
            return True
    return False


def parsear_tickets_markdown(texto: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    blocos = re.split(r"(?=^\s*###\s+\[TICKET-)", texto, flags=re.MULTILINE)
    tickets = []
    erros = []

    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco or not re.match(r"^###\s+\[TICKET-", bloco):
            continue

        match_header = RE_TICKET_HEADER.search(bloco)
        if not match_header:
            continue

        ticket_id = match_header.group(1).strip()
        titulo = match_header.group(2).strip()

        # Target Files
        match_files = RE_TARGET_FILES.search(bloco)
        if not match_files:
            erros.append(f"[{ticket_id}] Campo 'Target Files' ausente.")
            target_files = []
        else:
            raw_files = match_files.group(1).strip()
            target_files = [f.strip() for f in raw_files.split(",") if f.strip()]

        # Validation Command
        match_val = RE_VALIDATION_CMD.search(bloco)
        if not match_val:
            erros.append(f"[{ticket_id}] Campo 'Validation Command' ausente.")
            validation_cmd = ""
        else:
            validation_cmd = match_val.group(1).strip()

        # Blocked by
        match_blocked = RE_BLOCKED_BY.search(bloco)
        if not match_blocked:
            erros.append(f"[{ticket_id}] Campo 'Blocked by' ausente.")
            blocked_by = []
        else:
            raw_blocked = match_blocked.group(1).strip()
            if raw_blocked.lower() in ["none", "nenhum", "-", ""]:
                blocked_by = []
            else:
                blocked_by = [b.strip() for b in raw_blocked.split(",") if b.strip()]

        # Regra de ouro da Lei #5 / DoD 3: todo ticket deve ter pelo menos um arquivo de teste
        if target_files and not _tem_arquivo_de_teste(target_files):
            erros.append(f"[{ticket_id}] Deve conter pelo menos um arquivo de teste em 'Target Files'.")

        tickets.append({
            "id": ticket_id,
            "titulo": titulo,
            "target_files": target_files,
            "validation_command": validation_cmd,
            "blocked_by": blocked_by
        })

    return tickets, erros
