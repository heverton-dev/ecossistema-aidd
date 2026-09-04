# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — VALIDADORES & VALUE OBJECTS (Objetos de Valor DDD)
=============================================================================
Tipos imutáveis com validação rica embutida para erradicar entidades anêmicas.
"""

import re
from dataclasses import dataclass
from typing import Union


def validar_email(email: str) -> bool:
    padrao = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(padrao, (email or "").strip()))


def validar_cpf(cpf: str) -> bool:
    cpf = re.sub(r'\D', '', cpf or "")
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    for i in range(9, 11):
        val = sum((int(cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        dig = ((val * 10) % 11) % 10
        if int(cpf[i]) != dig:
            return False
    return True


def validar_cnpj(cnpj: str) -> bool:
    cnpj = re.sub(r'\D', '', cnpj or "")
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = sum(int(cnpj[i]) * pesos1[i] for i in range(12)) % 11
    d1 = 0 if d1 < 2 else 11 - d1
    if int(cnpj[12]) != d1:
        return False
    d2 = sum(int(cnpj[i]) * pesos2[i] for i in range(13)) % 11
    d2 = 0 if d2 < 2 else 11 - d2
    return int(cnpj[13]) == d2


@dataclass(frozen=True)
class Email:
    valor: str

    def __post_init__(self):
        v = (self.valor or "").strip().lower()
        if not validar_email(v):
            raise ValueError(f"E-mail inválido: {self.valor}")
        object.__setattr__(self, "valor", v)

    def __str__(self) -> str:
        return self.valor


@dataclass(frozen=True)
class Cpf:
    valor: str

    def __post_init__(self):
        limpo = re.sub(r'\D', '', self.valor or "")
        if not validar_cpf(limpo):
            raise ValueError(f"CPF inválido: {self.valor}")
        object.__setattr__(self, "valor", limpo)

    @property
    def formatado(self) -> str:
        return f"{self.valor[:3]}.{self.valor[3:6]}.{self.valor[6:9]}-{self.valor[9:]}"

    def __str__(self) -> str:
        return self.valor


@dataclass(frozen=True)
class Dinheiro:
    centavos: int

    @classmethod
    def de_reais(cls, valor: Union[float, int]) -> "Dinheiro":
        return cls(centavos=int(round(float(valor) * 100)))

    @property
    def em_reais(self) -> float:
        return self.centavos / 100.0

    @property
    def formatado(self) -> str:
        return f"R$ {self.em_reais:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def __str__(self) -> str:
        return self.formatado
