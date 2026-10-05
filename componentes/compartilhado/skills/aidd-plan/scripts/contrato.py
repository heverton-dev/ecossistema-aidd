# -*- coding: utf-8 -*-
"""
Contrato determinístico e validação de regras de ciclo de vida para aidd-plan (D1).
"""

from typing import Tuple, Optional

STATUS_PERMITIDOS = {"DRAFT", "APROVADO", "EM EXECUCAO", "CONCLUIDO"}


def validar_status_item(status: str) -> bool:
    return status.strip().upper() in STATUS_PERMITIDOS


def validar_nota_e_evidencia(nota: Optional[str], evidencia: Optional[str]) -> Tuple[bool, str]:
    if not nota or nota.strip().upper() == "NAO AUDITADO":
        return True, "Nota não auditada ou vazia."

    if not evidencia or not str(evidencia).strip():
        return False, "Nota numérica exige evidencia explicitamente comprovada."

    return True, "Nota e evidência válidas."
