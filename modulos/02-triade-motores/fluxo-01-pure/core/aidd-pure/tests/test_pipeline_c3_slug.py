# -*- coding: utf-8 -*-
"""
Achado do /pure real (16/10/2026): o contrato C3 saiu com `projeto_slug` igual ao
nome da pasta (`pure_real2`, com underscore) e foi reprovado pelo schema
(`^[a-z0-9-]+$`). Causas: o slug do Planner mora em `PLANNER.json -> meta.slug`
(o código só olhava a raiz e `metadados_projeto`) e o fallback pelo nome da
pasta não era sanitizado.
"""

import json
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / 'scripts'
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import pipeline_completo  # noqa: E402

PADRAO = re.compile(r'^[a-z0-9-]+$')


def _emitir(pasta: Path) -> dict:
    (pasta / 'src' / 'modules' / 'm').mkdir(parents=True)
    (pasta / 'src' / 'modules' / 'm' / 'a.py').write_text('x = 1\n', encoding='utf-8')
    caminho = pipeline_completo._emitir_contrato_c3(pasta)
    return json.loads(Path(caminho).read_text(encoding='utf-8'))


def test_slug_vem_do_meta_do_planner(tmp_path):
    pasta = tmp_path / 'Pasta_Qualquer'
    pasta.mkdir()
    (pasta / 'PLANNER.json').write_text(json.dumps({'meta': {'slug': 'controle-de-pedidos'}}), encoding='utf-8')
    assert _emitir(pasta)['projeto_slug'] == 'controle-de-pedidos'


def test_fallback_pelo_nome_da_pasta_e_sanitizado(tmp_path):
    pasta = tmp_path / 'Meu_Projeto Novo.v2'
    pasta.mkdir()
    slug = _emitir(pasta)['projeto_slug']
    assert PADRAO.match(slug), slug
    assert slug == 'meu-projeto-novo-v2'


def test_slug_do_planner_fora_do_padrao_tambem_e_sanitizado(tmp_path):
    pasta = tmp_path / 'p'
    pasta.mkdir()
    (pasta / 'PLANNER.json').write_text(json.dumps({'meta': {'slug': 'Controle_De Pedidos'}}), encoding='utf-8')
    assert PADRAO.match(_emitir(pasta)['projeto_slug'])
