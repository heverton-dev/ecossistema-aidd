#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SANDBOX NÍVEL 1 — Execução de código gerado com ambiente mínimo e cwd isolado
(Item PLAN-0018: sandbox-nivel-1-subprocess-env-minimo-fase-08)

Garante, para a Fase 8 (08_implementador.py):

1. ENV sanitizado com allowlist estrita de subprocessos de código gerado —
   apenas PATH, PYTHONPATH (src do projeto), PYTHONUTF8 e TMPDIR.
2. cwd isolado em diretório temporário restrito (tempfile.mkdtemp).
3. Auditoria AST: subprocessos de código gerado NUNCA herdam os.environ
   completo (env=os.environ, os.environ.copy(), {**os.environ, ...}).
4. Testabilidade real: código gerado que dumpa variáveis de ambiente não
   enxerga chaves de API do host (coberto por teste de integração real).

Determinismo: 100% Python puro — Zero LLM, Zero Token.
Compatibilidade: Python 3.11+, agnóstico a OS e a harness.
"""

import ast
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

# Allowlist estrita de variáveis de ambiente herdadas por subprocessos de
# código gerado (DoD item 1). Qualquer outra chave do host é descartada.
ENV_EXECUCAO_ALLOWLIST = ('PATH', 'PYTHONPATH', 'PYTHONUTF8', 'TMPDIR')

# Funções de subprocess que disparam processos filhos (usado pela auditoria AST).
_SUBPROCESS_FUNCS = frozenset({
    'run', 'Popen', 'call', 'check_call', 'check_output',
})


# =============================================================================
# ENV MÍNIMO
# =============================================================================

def montar_env_minimo(pythonpath=None, tmpdir=None, path_host=None):
    """Monta dicionário de ambiente restrito com EXATAMENTE as chaves da allowlist.

    Args:
        pythonpath: caminho (str/Path) do src do projeto, ou None para omitir.
        tmpdir: caminho (str/Path) do diretório temporário isolado, ou None.
        path_host: valor de PATH (str) a preservar; default None usa os.environ.

    Returns:
        dict com no máximo as chaves de ENV_EXECUCAO_ALLOWLIST. Nunca espelha
        o os.environ do host ('live') — apenas valores que atendem à allowlist.
    """
    env = {}
    caminho = path_host if path_host is not None else os.environ.get('PATH', '')
    if caminho:
        env['PATH'] = caminho
    if pythonpath is not None:
        env['PYTHONPATH'] = str(pythonpath)
    env['PYTHONUTF8'] = '1'
    if tmpdir is not None:
        env['TMPDIR'] = str(tmpdir)
    return env


# =============================================================================
# SANDBOX (cwd isolado)
# =============================================================================

class SandboxNivel1:
    """Context manager: cria tempdir restrito (cwd) + ambiente mínimo.

    Uso:
        with SandboxNivel1(pythonpath=pasta_projeto / 'src') as sandbox:
            subprocess.run([...], cwd=str(sandbox.cwd), env=sandbox.env)

    O `env` montado contém apenas as chaves de ENV_EXECUCAO_ALLOWLIST, então
    segredos do host (API keys, tokens) não vazam para o código gerado.
    """

    def __init__(self, pythonpath=None, path_host=None):
        self._pythonpath = pythonpath
        self._path_host = path_host
        self.cwd = None
        self.env = None

    def __enter__(self):
        self.cwd = Path(tempfile.mkdtemp(prefix='aidd_sandbox_nivel1_'))
        self.env = montar_env_minimo(
            pythonpath=self._pythonpath, tmpdir=self.cwd, path_host=self._path_host
        )
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.cwd is not None:
            _destruir_sandbox(self.cwd)
            self.cwd = None
        return False

    def rodar(self, args, **kwargs):
        """Roda subprocess com cwd=sandbox e env mínimo (sobrescreve kwargs)."""
        kwargs['cwd'] = str(self.cwd)
        kwargs['env'] = self.env
        return subprocess.run(args, **kwargs)


def _destruir_sandbox(caminho: Path):
    """Remove o tempdir com tolerância a lock temporário (Windows)."""
    for _ in range(3):
        try:
            shutil.rmtree(caminho, ignore_errors=True)
            if not caminho.exists():
                return
        except OSError:
            pass
    # Último recurso: deixar o tempdir órfão (sem impacto funcional).


# =============================================================================
# AUDITORIA AST — subprocessos nunca herdam os.environ completo
# =============================================================================

def _coletar_aliases_subprocess(arvore):
    """Coleta alias de `import subprocess` e nomes de `from subprocess import X`."""
    aliases_subprocess = set()
    funcoes_subprocess = set()
    for node in arvore.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == 'subprocess':
                    aliases_subprocess.add(alias.asname or 'subprocess')
        elif isinstance(node, ast.ImportFrom) and node.module == 'subprocess':
            for alias in node.names:
                if alias.name != '*':
                    funcoes_subprocess.add(alias.asname or alias.name)
    return aliases_subprocess, funcoes_subprocess


def _chamada_e_subprocesso(func, aliases_subprocess, funcoes_subprocess):
    """True se `func` (nó AST de chamada) é uma invocação de subprocesso."""
    if isinstance(func, ast.Name):
        return func.id in funcoes_subprocess
    if isinstance(func, ast.Attribute):
        return (
            func.attr in _SUBPROCESS_FUNCS
            and isinstance(func.value, ast.Name)
            and func.value.id in aliases_subprocess
        )
    return False


def _expressao_referencia_environ(node):
    """True se a expressão do kwarg `env` referencia os.environ de alguma forma."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and sub.attr == 'environ':
            return True
        if isinstance(sub, ast.Name) and sub.id == 'environ':
            return True
    return False


def auditar_subprocess_env_ast(codigo):
    """Audita código-fonte (str) via AST por subprocessos herdando os.environ.

    Returns:
        List[Dict] de violações [{'linha', 'coluna', 'detalhe'}] — vazio = limpo.
        Código com SyntaxError é ignorado (retorna vazio): o pytest real é quem
        reporta erro de sintaxe, não este auditor (mesma política do contrato).
    """
    try:
        arvore = ast.parse(codigo)
    except (SyntaxError, ValueError):
        return []

    aliases_subprocess, funcoes_subprocess = _coletar_aliases_subprocess(arvore)
    violacoes = []
    vistos = set()

    for node in ast.walk(arvore):
        if not isinstance(node, ast.Call):
            continue
        if not _chamada_e_subprocesso(node.func, aliases_subprocess, funcoes_subprocess):
            continue
        for kw in node.keywords:
            if kw.arg != 'env' or kw.value is None:
                continue
            if not _expressao_referencia_environ(kw.value):
                continue
            chave = (node.lineno, node.col_offset)
            if chave in vistos:
                continue
            vistos.add(chave)
            violacoes.append({
                'linha': node.lineno,
                'coluna': node.col_offset,
                'detalhe': (
                    f"subprocesso na linha {node.lineno} passa env derivado de "
                    f"os.environ — herança de ambiente completo do host proibida "
                    f"(SANDBOX NÍVEL 1)"
                ),
            })
    return violacoes


def formatar_violacoes_auditoria(violacoes, prefixo=''):
    """Formata violações da auditoria AST para mensagem de correção (fix-loop)."""
    if not violacoes:
        return ''
    linhas = []
    for v in violacoes:
        local = f"{v.get('arquivo', prefixo or 'código gerado')}:{v['linha']}"
        linhas.append(f"{local}: {v['detalhe']}")
    return (
        "CONTRATO SANDBOX QUEBRADO: subprocessos de código gerado nunca podem "
        "herdar os.environ completo do host. "
        + ' '.join(linhas)
        + " Troque env=os.environ por um dicionário explícito contendo apenas "
          "as variáveis necessárias (sem os.environ do host)."
    )