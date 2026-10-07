"""Ticket 12 (ciclo-03 VSA, D3 / DoD 4): o almoxarifado só entrega peça para pasta de projeto.

Prova de 06/10: `_destino_teste_almoxarifado` foi versionado dentro de modulos/ porque
um teste pediu a peça com destino no código das ferramentas. A guarda de
`obter_peca` recusa, com erro claro e sem criar nada, destino:
  - dentro de modulos/ (código das fatias);
  - dentro de componentes/ (o próprio almoxarifado);
  - na raiz do ecossistema (a pasta raiz ou um arquivo direto nela).
Projeto de verdade fora do ecossistema continua recebendo a peça, mesmo com pasta
chamada `modulos` ou `componentes`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from aidd_forge.core.almoxarifado import obter_peca

PECA = "moldes/infra/Dockerfile"


def _achar_raiz_repo() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "ecossistema.py").is_file():
            return parent
    raise RuntimeError("raiz do ecossistema não encontrada")


RAIZ = _achar_raiz_repo()

PROIBIDOS = {
    "modulos": (RAIZ / "modulos" / "_destino_teste_t12", "modulos"),
    "componentes": (RAIZ / "componentes" / "compartilhado" / "_destino_teste_t12", "componentes"),
    "raiz_pasta": (RAIZ, "raiz do ecossistema"),
    "raiz_arquivo": (RAIZ / "Dockerfile_destino_teste_t12", "raiz do ecossistema"),
}


@pytest.mark.parametrize("caso", sorted(PROIBIDOS))
def test_obter_peca_recusa_destino_proibido_sem_criar_nada(caso: str) -> None:
    destino, motivo = PROIBIDOS[caso]
    existia = destino.exists()
    with pytest.raises(ValueError, match=motivo):
        obter_peca(PECA, destino=destino, raiz=RAIZ)
    assert destino.exists() == existia, f"{caso}: a guarda deixou {destino} criado"
    assert not (RAIZ / "Dockerfile").exists(), "peça copiada para a raiz do ecossistema"


@pytest.mark.parametrize("pasta", ["modulos", "componentes"])
def test_projeto_fora_do_ecossistema_com_pasta_homonima_recebe_a_peca(tmp_path: Path, pasta: str) -> None:
    projeto = tmp_path / pasta / "meu_app"
    projeto.mkdir(parents=True)
    entregue = obter_peca(PECA, destino=projeto, raiz=RAIZ)
    assert entregue == projeto / "Dockerfile" and entregue.is_file()
