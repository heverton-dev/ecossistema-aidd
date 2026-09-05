# -*- coding: utf-8 -*-
"""
Testes do gate G_CLI_HELP_CONSISTENCIA — prova que ele detecta o caso
sintético inconsistente, não acusa os casos sãos, e não reintroduz nenhuma
das 3 classes de falso positivo achadas no diagnóstico do Pacote 1
(subprocess externo, CSS não impresso, docstring/comentário).
"""

import ast
import importlib.util
import os

GATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_CLI_HELP_CONSISTENCIA.py")
_spec = importlib.util.spec_from_file_location("g_cli_help_consistencia", GATE_PATH)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def _auditar_fonte(fonte):
    """Roda a mesma lógica de _auditar_arquivo, mas sobre uma string em memória."""
    arvore = ast.parse(fonte)
    definidas = gate._extrair_flags_definidas(arvore)
    if not definidas:
        return []
    citadas = gate._extrair_flags_citadas(arvore)
    return [flag for flag, _linha, _trecho in citadas if flag not in definidas]


def test_detecta_flag_citada_mas_nao_definida():
    fonte = '''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--mcp-command")

def cmd(args):
    if not args.command:
        print("[ERRO] type 'mcp' exige --command (ex: --command python).")
'''
    inconsistentes = _auditar_fonte(fonte)
    assert "--command" in inconsistentes


def test_flag_definida_nao_gera_erro():
    fonte = '''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--mcp-command")

def cmd(args):
    if not args.mcp_command:
        print("[ERRO] type 'mcp' exige --mcp-command (ex: --mcp-command python).")
'''
    assert _auditar_fonte(fonte) == []


def test_ignora_flag_de_subprocess_externo():
    fonte = '''
import argparse
import subprocess
parser = argparse.ArgumentParser()
parser.add_argument("--dir")

def f():
    subprocess.run(["git", "log", "--oneline", "-1"])
'''
    assert _auditar_fonte(fonte) == []


def test_ignora_variavel_css_nunca_impressa():
    fonte = '''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dir")

def gerar_html():
    html = """
    <style>
      :root { --primary: #2563eb; }
      .btn { color: var(--primary); }
    </style>
    """
    with open("out.html", "w") as f:
        f.write(html)
'''
    assert _auditar_fonte(fonte) == []


def test_ignora_docstring_explicando_conceito_generico():
    fonte = '''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dir")

def strip_flag(args):
    """Remove \'--flag valor\' de uma lista de argumentos, devolvendo (valor, resto)."""
    return args
'''
    assert _auditar_fonte(fonte) == []


def test_detecta_flag_inconsistente_dentro_de_raise():
    fonte = '''
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--saida")

def cmd(args):
    if not args.saida:
        raise ValueError("informe --output para continuar")
'''
    inconsistentes = _auditar_fonte(fonte)
    assert "--output" in inconsistentes


def test_arquivos_reais_do_ecossistema_sem_falso_positivo():
    """Regressão: os 19 pontos de entrada argparse das 4 ferramentas não
    devem acusar nenhuma flag inconsistente no estado atual do repositório
    (allowlist de flags de ferramenta externa já aplicada)."""
    erros_totais = []
    for caminho_rel in gate.ARQUIVOS_AUDITADOS:
        _total, erros = gate._auditar_arquivo(caminho_rel)
        erros_totais.extend(erros or [])
    assert erros_totais == []


def test_gate_completo_aprova_estado_atual():
    assert gate.checar() == 0
