# -*- coding: utf-8 -*-
"""
Testes unitarios deterministicos para o detector de drift bidirecional (Fase 4 - Item 6.4).
"""
import os
import sys
import tempfile
import pytest

from pathlib import Path as _Path
ROOT_DIR = str(next((p.parent for p in _Path(__file__).resolve().parents if p.name == "modulos"), _Path(__file__).resolve().parent.parent))  # raiz: pai de modulos/ (VSA) ou de gates/ (árvore sintética)
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

def _achar_candidato_manifesto_extra():
    manifesto = gestor_componentes.carregar_manifesto()
    for nome, _origem, _eh_dir in gestor_componentes._listar_componentes_fonte(manifesto, 'skill', 'compartilhado'):
        resolvidos = gestor_componentes._resolver_manifestos_extra(manifesto, 'skill', 'compartilhado', nome)
        if resolvidos:
            return manifesto, nome, resolvidos[0]
    return None, None, None

def test_gemini_extension_gerada_no_sync():
    manifesto, nome, (caminho_abs, esperado) = _achar_candidato_manifesto_extra()
    if not manifesto:
        pytest.skip('Nenhum componente com manifesto extra (gemini-extension.json) configurado')
    assert os.path.isfile(caminho_abs)
    import json
    with open(caminho_abs, 'r', encoding='utf-8') as f:
        atual = json.load(f)
    assert atual == esperado
    assert atual['name'] == nome

def test_gemini_extension_drift_detectado_e_force_sync():
    manifesto, nome, (caminho_abs, esperado) = _achar_candidato_manifesto_extra()
    if not manifesto:
        pytest.skip('Nenhum componente com manifesto extra (gemini-extension.json) configurado')
    import json
    with open(caminho_abs, 'r', encoding='utf-8') as f:
        conteudo_original = f.read()
    try:
        with open(caminho_abs, 'w', encoding='utf-8') as f:
            json.dump({"name": "adulterado-teste", "version": "0.0.0"}, f)
        relatorio = gestor_componentes.detectar_drift(tipo='skill')
        caminho_rel = os.path.relpath(caminho_abs, ROOT_DIR).replace(os.sep, "/")
        assert caminho_rel in [m.caminho for m in relatorio.modificados]
        res = gestor_componentes.force_sync(tipo='skill')
        assert caminho_abs in res['manifestos_extra_regerados']
        with open(caminho_abs, 'r', encoding='utf-8') as f:
            atual = json.load(f)
        assert atual == esperado
        relatorio_pos = gestor_componentes.detectar_drift(tipo='skill')
        assert caminho_rel not in [m.caminho for m in relatorio_pos.modificados]
    finally:
        with open(caminho_abs, 'w', encoding='utf-8') as f:
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


def test_remover_sobras_diretorio_so_apaga_o_que_saiu_da_fonte(tmp_path):
    origem = tmp_path / 'fonte'
    destino = tmp_path / 'copia'
    (origem / 'scripts').mkdir(parents=True)
    (destino / 'scripts').mkdir(parents=True)
    (origem / 'SKILL.md').write_text('a', encoding='utf-8')
    (origem / 'scripts' / 'novo.py').write_text('b', encoding='utf-8')
    (destino / 'SKILL.md').write_text('a', encoding='utf-8')
    (destino / 'scripts' / 'novo.py').write_text('b', encoding='utf-8')
    (destino / 'scripts' / 'antigo.py').write_text('c', encoding='utf-8')

    previa = gestor_componentes._remover_sobras_diretorio(str(origem), str(destino), dry_run=True)
    assert [os.path.basename(p) for p in previa] == ['antigo.py']
    assert (destino / 'scripts' / 'antigo.py').exists()

    gestor_componentes._remover_sobras_diretorio(str(origem), str(destino), dry_run=False)
    assert not (destino / 'scripts' / 'antigo.py').exists()
    assert (destino / 'scripts' / 'novo.py').exists()
    assert (destino / 'SKILL.md').exists()


def test_sync_remove_arquivo_que_saiu_da_fonte_e_verify_fica_limpo():
    manifesto = gestor_componentes.carregar_manifesto()
    indice = gestor_componentes._indexar_fontes(manifesto, 'skill')
    destino_dir = next((d for d, v in indice.items() if v[4] and os.path.isdir(d)), None)
    if not destino_dir:
        pytest.skip('Nenhuma skill-diretorio sincronizada para teste')
    sobra = os.path.join(destino_dir, '__sobra_removida_da_fonte.py')
    with open(sobra, 'w', encoding='utf-8') as f:
        f.write('# saiu da fonte\n')
    try:
        rel = os.path.relpath(sobra, ROOT_DIR).replace(os.sep, '/')
        assert rel in [o.caminho for o in gestor_componentes.detectar_drift(tipo='skill').orfaos]
        rel_sync = gestor_componentes.sync('skill')
        assert os.path.relpath(sobra, ROOT_DIR) in rel_sync['removidos']
        assert not os.path.exists(sobra)
        assert rel not in [o.caminho for o in gestor_componentes.detectar_drift(tipo='skill').orfaos]
    finally:
        if os.path.exists(sobra):
            os.remove(sobra)

def test_auto_ingest_nao_puxa_skill_de_terceiro_para_a_fonte(monkeypatch):
    """Regressao (PROPOSTA-NOMES-SKILLS, etapa 1): o sync ingeria de volta para
    componentes/ as skills de terceiros instaladas nos harnesses, desfazendo a remocao."""
    import json
    with tempfile.TemporaryDirectory() as raiz:
        os.makedirs(os.path.join(raiz, "modulos", "04-nucleo-compartilhado", "contracts"))
        with open(os.path.join(raiz, "modulos", "04-nucleo-compartilhado", "contracts", "dependencias_externas.json"), "w", encoding="utf-8") as f:
            json.dump({"skills": {"wrangler": {"gitignore": ["*/skills/wrangler/"]}}}, f)
        for nome in ("wrangler", "skill-local-nova"):
            d = os.path.join(raiz, ".claude", "skills", nome)
            os.makedirs(d)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(f"---\nname: {nome}\n---\n")
        monkeypatch.setattr(gestor_componentes, "ROOT_DIR", raiz)
        monkeypatch.setattr(gestor_componentes, "COMPONENTES_DIR", os.path.join(raiz, "componentes"))
        monkeypatch.setattr(gestor_componentes, "carregar_manifesto",
                            lambda: {"harnesses_suportados": {"claude-code": {"prefixo_pasta": ".claude"}}})

        ingeridas = gestor_componentes.auto_ingest_skills()

        fonte = os.listdir(os.path.join(raiz, "componentes", "compartilhado", "skills"))
        assert fonte == ["skill-local-nova"]
        assert len(ingeridas) == 1
