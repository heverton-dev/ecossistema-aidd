#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retry de I/O e falha estruturada dos mapas visuais (aidd-visual-maps, D11).

com_retry(funcao) repete só erro transitório de arquivo (PermissionError/OSError: no
Windows, o navegador ou o antivírus segura o mapa por alguns instantes), esperando
espera_base * 2**n entre as tentativas (0,2 s, 0,4 s...). FileNotFoundError e ValueError
são erro de dado, não de momento: sobem na primeira vez. Quando desiste, o erro sobe com
o atributo `tentativas`.

FalhaMapa(estagio, tipo, arquivo, erro, tentativas) é o relato de uma falha numa linha
JSON; relatar_falha() é o que os main() do catálogo, dos mapas, do não técnico e do livro
fazem com um erro: linha [ERRO] legível + linha JSON, e exit 1 (nunca traceback cru).
"""
import json
import time
from pathlib import Path

NAO_TRANSITORIOS = (FileNotFoundError, ValueError)


def _dormir(segundos: float) -> None:
    time.sleep(segundos)


def com_retry(funcao, tentativas: int = 3, espera_base: float = 0.2, erros=(PermissionError, OSError), dormir=None):
    """Chama funcao() até dar certo ou esgotar as tentativas; devolve o resultado dela."""
    dormir = dormir or _dormir
    for n in range(tentativas):
        try:
            return funcao()
        except NAO_TRANSITORIOS:
            raise
        except erros as erro:
            if n == tentativas - 1:
                erro.tentativas = tentativas
                raise
            dormir(espera_base * 2 ** n)
    raise ValueError("com_retry precisa de pelo menos uma tentativa")


def ler_texto(caminho: Path) -> str:
    """Leitura UTF-8 de catálogo ou molde, com retry de I/O."""
    return com_retry(lambda: Path(caminho).read_text(encoding="utf-8"))


class FalhaMapa(Exception):
    """Falha de um estágio dos mapas (catalogo, mapa, nao-tecnico, livro) pronta para virar JSON."""

    def __init__(self, estagio: str, tipo: str, arquivo, erro: BaseException, tentativas: int = 1):
        super().__init__(f"{arquivo}: {erro}")
        self.estagio, self.tipo, self.arquivo = estagio, tipo, str(arquivo)
        self.erro, self.tentativas = erro, tentativas

    def para_json(self) -> str:
        return json.dumps({"estagio": self.estagio, "tipo": self.tipo, "arquivo": self.arquivo,
                           "tentativas": self.tentativas, "erro": str(self.erro)}, ensure_ascii=False)


def relatar_falha(erro: BaseException, estagio: str, tipo: str, arquivo_padrao) -> int:
    """Imprime a linha [ERRO] e a linha JSON da falha; devolve o exit code 1."""
    if isinstance(erro, FalhaMapa):
        falha = erro
    else:
        arquivo = getattr(erro, "arquivo", None) or getattr(erro, "filename", None) or arquivo_padrao
        falha = FalhaMapa(estagio, tipo, arquivo, erro, getattr(erro, "tentativas", 1))
    print(f"[ERRO] {falha}")
    print(falha.para_json())
    return 1
