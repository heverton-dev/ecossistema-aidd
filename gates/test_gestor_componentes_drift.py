# -*- coding: utf-8 -*-
"""
Testes unitarios deterministicos para o detector de drift bidirecional (Fase 4 - Item 6.4).
"""
import os
import sys
import tempfile
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT_DIR, 'scripts'))
import gestor_componentes

def test_hash_file_determinismo():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b'Teste de conteudo fixo')
        temp_path = f.name
    try:
        h1 = gestor_componentes._hash_file(temp_path)
        h2 = gestor_componentes._hash_file(temp_path)
        assert h1 == h2
        assert len(h1) == 64
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def test_detectar_drift_modificado_e_force_sync():
    manifesto = gestor_componentes.carregar_manifesto()
    indice = gestor_componentes._indexar_fontes(manifesto)
    candidato = None
    for dest, (tipo, escopo, nome, fonte, eh_dir) in indice.items():
        if not eh_dir and os.path.isfile(dest):
            candidato = (os.path.relpath(dest, ROOT_DIR), dest, tipo, escopo, nome, fonte)
            break
    if not candidato:
        pytest.skip('Nenhum componente arquivo encontrado para teste')
    rel_dest, dest_path, tipo, escopo, nome, fonte_path = candidato
    with open(dest_path, 'r', encoding='utf-8') as f:
        conteudo_original = f.read()
    try:
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_original + '\n# DRIFT_TEST_MODIFICADO\n')
        relatorio = gestor_componentes.detectar_drift(tipo=tipo)
        modificados_caminhos = [m.caminho for m in relatorio.modificados]
        dest_posix = os.path.relpath(dest_path, ROOT_DIR).replace(os.sep, "/")
        assert dest_posix in modificados_caminhos
        res = gestor_componentes.force_sync(tipo=tipo)
        assert len(res['restaurados']) > 0
        with open(dest_path, 'r', encoding='utf-8') as f:
            conteudo_restaurado = f.read()
        assert conteudo_restaurado == conteudo_original
        relatorio_pos = gestor_componentes.detectar_drift(tipo=tipo)
        assert dest_posix not in [m.caminho for m in relatorio_pos.modificados]
    finally:
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(conteudo_original)

def test_detectar_drift_orfao_e_force_sync():
    destino_teste = os.path.join(ROOT_DIR, '.claude', 'commands', '__teste_orfao_drift.md')
    os.makedirs(os.path.dirname(destino_teste), exist_ok=True)
    with open(destino_teste, 'w', encoding='utf-8') as f:
        f.write('# Orfao Temporario\n')
    try:
        relatorio = gestor_componentes.detectar_drift(tipo='command')
        rel_path = os.path.relpath(destino_teste, ROOT_DIR).replace(os.sep, "/")
        orfaos = [o.caminho for o in relatorio.orfaos]
        assert rel_path in orfaos
        res = gestor_componentes.force_sync(tipo='command')
        assert rel_path in res['orfaos_removidos']
        assert not os.path.exists(destino_teste)
        relatorio_pos = gestor_componentes.detectar_drift(tipo='command')
        assert rel_path not in [o.caminho for o in relatorio_pos.orfaos]
    finally:
        if os.path.exists(destino_teste):
            os.remove(destino_teste)
