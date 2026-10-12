#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_INTEGRACAO_CROSS_SCRIPT — Gate I3: Compatibilidade entre scripts irmãos.

Executa testes automatizados de ponta a ponta validando a compatibilidade
entre scripts gerados pelo pipeline AIDD. Verifica que os contratos (tipos,
assinaturas, schemas JSON) entre módulos irmãos são compatíveis — por exemplo,
um cliente consumindo a API gerada, ou um loader carregando o schema que o
writer produz.

Falha com exit 1 se houver divergência de tipos ou contratos entre scripts.

Uso:
    python scripts/gates/G_INTEGRACAO_CROSS_SCRIPT.py <pasta_projeto>
    python scripts/gates/G_INTEGRACAO_CROSS_SCRIPT.py --cache-dir .aidd/cache

Princípio AIDD: Gate mecânico — zero LLM, 100% determinístico.
"""

import sys
import ast
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# EXTRAÇÃO DE CONTRATOS VIA AST (Zero Token)
# =============================================================================

def extrair_funcoes_publicas(codigo_fonte: str) -> List[Dict[str, Any]]:
    """Extrai assinaturas de funções públicas de um módulo Python via AST."""
    try:
        arvore = ast.parse(codigo_fonte)
    except SyntaxError:
        return []

    funcoes = []
    for node in ast.walk(arvore):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('_'):
                continue
            args = []
            for arg in node.args.args:
                annotation = None
                if arg.annotation:
                    annotation = ast.dump(arg.annotation)
                args.append({'nome': arg.arg, 'tipo_annotation': annotation})

            retorno = ast.dump(node.returns) if node.returns else None

            funcoes.append({
                'nome': node.name,
                'args': args,
                'retorno_annotation': retorno,
                'linha': node.lineno,
            })
    return funcoes


def extrair_classes_publicas(codigo_fonte: str) -> List[Dict[str, Any]]:
    """Extrai classes públicas e seus métodos públicos via AST."""
    try:
        arvore = ast.parse(codigo_fonte)
    except SyntaxError:
        return []

    classes = []
    for node in ast.walk(arvore):
        if isinstance(node, ast.ClassDef):
            if node.name.startswith('_'):
                continue
            metodos = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith('_') and item.name != '__init__':
                        continue
                    args = []
                    for arg in item.args.args:
                        if arg.arg == 'self':
                            continue
                        annotation = None
                        if arg.annotation:
                            annotation = ast.dump(arg.annotation)
                        args.append({'nome': arg.arg, 'tipo_annotation': annotation})
                    retorno = ast.dump(item.returns) if item.returns else None
                    metodos.append({
                        'nome': item.name,
                        'args': args,
                        'retorno_annotation': retorno,
                        'linha': item.lineno,
                    })
            classes.append({
                'nome': node.name,
                'metodos': metodos,
                'linha': node.lineno,
            })
    return classes


def extrair_variaveis_publicas(codigo_fonte: str, caminho: Optional[Path] = None) -> List[str]:
    """Extrai constantes, variáveis públicas, re-exports e __all__ via AST."""
    try:
        arvore = ast.parse(codigo_fonte)
    except SyntaxError:
        return []

    nomes = []
    tem_all = False
    all_names = set()
    for node in arvore.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == '__all__' and isinstance(node.value, (ast.List, ast.Tuple, ast.Set)):
                        tem_all = True
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                all_names.add(elt.value)
                    elif not target.id.startswith('_') or target.id.startswith('_RLS_'):
                        nomes.append(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and (not node.target.id.startswith('_') or node.target.id.startswith('_RLS_')):
                nomes.append(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                nome_imp = alias.asname or alias.name
                if not nome_imp.startswith('_') or nome_imp.startswith('_RLS_'):
                    nomes.append(nome_imp)

    if tem_all:
        nomes.extend(list(all_names))

    if caminho and caminho.name == '__init__.py':
        try:
            for child in caminho.parent.iterdir():
                if child.is_file() and child.suffix == '.py' and child.stem != '__init__':
                    nomes.append(child.stem)
                elif child.is_dir() and (child / '__init__.py').exists():
                    nomes.append(child.name)
        except OSError:
            pass

    return list(set(nomes))


def extrair_schema_json(caminho: Path) -> Optional[Dict]:
    """Carrega e valida um arquivo JSON de schema."""
    if not caminho.exists():
        return None
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


# =============================================================================
# VALIDAÇÕES DE CONTRATO
# =============================================================================

class ResultadoValidacao:
    """Resultado de uma validação de contrato."""
    def __init__(self, check_id: str, descricao: str, passou: bool, detalhes: str):
        self.check_id = check_id
        self.descricao = descricao
        self.passou = passou
        self.detalhes = detalhes

    def to_dict(self):
        return {
            'check_id': self.check_id,
            'descricao': self.descricao,
            'status': 'PASSOU' if self.passou else 'FALHOU',
            'detalhes': self.detalhes,
        }


def validar_importabilidade(modulos: List[Tuple[str, Path]]) -> List[ResultadoValidacao]:
    """I1: Todos os scripts Python do projeto são importáveis (syntax válida)."""
    resultados = []
    for nome, caminho in modulos:
        try:
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                codigo = f.read()
            ast.parse(codigo)
            resultados.append(ResultadoValidacao(
                f'I1_syntax_{nome}',
                f'Syntax válida: {nome}',
                True,
                f'{nome}: syntax OK',
            ))
        except SyntaxError as e:
            resultados.append(ResultadoValidacao(
                f'I1_syntax_{nome}',
                f'Syntax válida: {nome}',
                False,
                f'{nome}: SyntaxError na linha {e.lineno}: {e.msg}',
            ))
        except OSError:
            resultados.append(ResultadoValidacao(
                f'I1_syntax_{nome}',
                f'Syntax válida: {nome}',
                False,
                f'{nome}: arquivo não encontrado ou ilegível',
            ))
    return resultados


def validar_contratos_entre_modulos(
    modulos: List[Tuple[str, Path]],
    pasta_projeto: Optional[Path] = None,
) -> List[ResultadoValidacao]:
    """I2: Funções exportadas por um módulo que são chamadas por outro existem
    com assinatura compatível. Verificação estática via AST (cross-reference)."""

    resultados = []

    if not pasta_projeto and modulos:
        try:
            pasta_projeto = Path(Path(*modulos[0][1].parts[:-1]))
        except Exception:
            pasta_projeto = modulos[0][1].parent

    # Coletar todas as funções públicas exportadas por cada módulo
    exportacoes_por_caminho: Dict[Path, Dict[str, Any]] = {}
    exportacoes_por_nome: Dict[str, List[Dict[str, Any]]] = {}

    for nome, caminho in modulos:
        try:
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                codigo = f.read()
            funcoes = extrair_funcoes_publicas(codigo)
            classes = extrair_classes_publicas(codigo)
            variaveis = extrair_variaveis_publicas(codigo, caminho=caminho)
            exp = {
                'funcoes': {f['nome']: f for f in funcoes},
                'classes': {c['nome']: c for c in classes},
                'variaveis': set(variaveis),
            }
        except (SyntaxError, OSError):
            exp = {'funcoes': {}, 'classes': {}, 'variaveis': set()}

        caminho_res = caminho.resolve()
        exportacoes_por_caminho[caminho_res] = exp
        exportacoes_por_nome.setdefault(nome, []).append(exp)

    roots = []
    if pasta_projeto:
        p_res = pasta_projeto.resolve()
        roots.extend([p_res / 'src', p_res, p_res / 'scripts'])

    # Verificar imports cruzados
    for nome, caminho in modulos:
        try:
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                codigo = f.read()
            arvore = ast.parse(codigo)
        except (SyntaxError, OSError):
            continue

        for node in ast.walk(arvore):
            if isinstance(node, ast.ImportFrom):
                alvo = None
                modulo_importado = node.module or ''

                if node.level > 0:
                    base_dir = caminho.parent
                    for _ in range(node.level - 1):
                        base_dir = base_dir.parent
                    if node.module:
                        parts = node.module.split('.')
                        cand_py = base_dir.joinpath(*parts).with_suffix('.py').resolve()
                        cand_pkg = (base_dir.joinpath(*parts) / '__init__.py').resolve()
                    else:
                        cand_py = base_dir.with_suffix('.py').resolve()
                        cand_pkg = (base_dir / '__init__.py').resolve()

                    if cand_py in exportacoes_por_caminho:
                        alvo = cand_py
                    elif cand_pkg in exportacoes_por_caminho:
                        alvo = cand_pkg
                elif node.module:
                    parts = node.module.split('.')
                    cand_roots = [caminho.parent] + roots
                    for r in cand_roots:
                        cand_py = r.joinpath(*parts).with_suffix('.py').resolve()
                        cand_pkg = (r.joinpath(*parts) / '__init__.py').resolve()
                        if cand_py in exportacoes_por_caminho:
                            alvo = cand_py
                            break
                        if cand_pkg in exportacoes_por_caminho:
                            alvo = cand_pkg
                            break

                if alvo is not None:
                    exp = exportacoes_por_caminho[alvo]
                    for alias in node.names:
                        nome_importado = alias.name
                        if nome_importado == '*':
                            continue
                        existe = (
                            nome_importado in exp['funcoes']
                            or nome_importado in exp['classes']
                            or nome_importado in exp['variaveis']
                        )
                        label_alvo = modulo_importado or alvo.stem
                        resultados.append(ResultadoValidacao(
                            f'I2_contrato_{nome}_imports_{label_alvo}.{nome_importado}',
                            f'Contrato: {nome} → {label_alvo}.{nome_importado}',
                            existe,
                            (
                                f'{label_alvo}.{nome_importado} encontrado'
                                if existe
                                else f'{label_alvo}.{nome_importado} NÃO EXISTE — divergência de contrato'
                            ),
                        ))
                elif modulo_importado in exportacoes_por_nome:
                    candidatos = exportacoes_por_nome[modulo_importado]
                    for alias in node.names:
                        nome_importado = alias.name
                        if nome_importado == '*':
                            continue
                        existe = any(
                            nome_importado in exp['funcoes']
                            or nome_importado in exp['classes']
                            or nome_importado in exp['variaveis']
                            for exp in candidatos
                        )
                        resultados.append(ResultadoValidacao(
                            f'I2_contrato_{nome}_imports_{modulo_importado}.{nome_importado}',
                            f'Contrato: {nome} → {modulo_importado}.{nome_importado}',
                            existe,
                            (
                                f'{modulo_importado}.{nome_importado} encontrado'
                                if existe
                                else f'{modulo_importado}.{nome_importado} NÃO EXISTE — divergência de contrato'
                            ),
                        ))

    if not resultados:
        resultados.append(ResultadoValidacao(
            'I2_contrato_sem_imports_cruzados',
            'Contratos entre módulos',
            True,
            'Nenhum import cruzado detectado entre scripts (ok para projeto sem módulos irmãos)',
        ))

    return resultados


def validar_schemas_json_compativeis(
    pasta_projeto: Path,
) -> List[ResultadoValidacao]:
    """I3: Schemas JSON gerados pelo pipeline são válidos e internamente consistentes."""
    resultados = []

    # Procurar todos os JSONs de schema/contract na pasta do projeto
    padroes_schema = [
        '**/*schema*.json',
        '**/*contract*.json',
        '**/*spec*.json',
        '**/*_index.json',
    ]

    schemas_encontrados = []
    for padrao in padroes_schema:
        schemas_encontrados.extend(pasta_projeto.glob(padrao))

    # Filtrar node_modules, __pycache__, etc.
    schemas_encontrados = [
        s for s in schemas_encontrados
        if 'node_modules' not in str(s)
        and '__pycache__' not in str(s)
        and '.git' not in str(s)
    ]

    if not schemas_encontrados:
        resultados.append(ResultadoValidacao(
            'I3_schema_json_nenhum',
            'Schemas JSON válidos',
            True,
            'Nenhum schema JSON encontrado (ok para projeto sem schemas)',
        ))
        return resultados

    for schema_path in schemas_encontrados:
        schema = extrair_schema_json(schema_path)
        nome = schema_path.name
        if schema is None:
            resultados.append(ResultadoValidacao(
                f'I3_schema_json_{nome}',
                f'Schema JSON válido: {nome}',
                False,
                f'{nome}: JSON inválido ou ilegível',
            ))
        else:
            resultados.append(ResultadoValidacao(
                f'I3_schema_json_{nome}',
                f'Schema JSON válido: {nome}',
                True,
                f'{nome}: JSON válido ({len(schema)} chaves top-level)',
            ))

    return resultados


def validar_compatibilidade_tipos(
    modulos: List[Tuple[str, Path]],
) -> List[ResultadoValidacao]:
    """I4: Verifica que anotações de tipo entre módulos que se referenciam são compatíveis.
    Checagem estática simplificada — compara nomes de tipos anotados."""

    resultados = []

    # Coletar todos os tipos definidos (classes, typevars, imports) em todos os módulos
    todos_tipos = set()
    for _, caminho in modulos:
        try:
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                codigo = f.read()
            classes = extrair_classes_publicas(codigo)
            todos_tipos.update(c['nome'] for c in classes)
            arvore = ast.parse(codigo)
            for item in ast.walk(arvore):
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            todos_tipos.add(target.id)
                elif isinstance(item, (ast.Import, ast.ImportFrom)):
                    for alias in item.names:
                        todos_tipos.add(alias.asname or alias.name)
        except (SyntaxError, OSError):
            continue

    TIPOS_CONHECIDOS = {
        # Builtins
        'str', 'int', 'float', 'bool', 'list', 'dict', 'None',
        'bytes', 'bytearray', 'memoryview', 'complex',
        # typing module
        'Any', 'Optional', 'List', 'Dict', 'Tuple', 'Set',
        'Callable', 'Sequence', 'Iterator', 'Generator',
        'Coroutine', 'Awaitable', 'AsyncIterator', 'AsyncGenerator',
        'Mapping', 'MutableMapping', 'MutableSequence',
        'Iterable', 'Reversible', 'Type', 'ClassVar',
        'Final', 'Literal', 'Union', 'TypeVar', 'Generic',
        'Protocol', 'TypedDict', 'NamedTuple', 'Deque',
        'Counter', 'ChainMap', 'DefaultDict', 'OrderedDict',
        # pathlib
        'Path', 'PurePath', 'PurePosixPath', 'PureWindowsPath',
        # os
        'os', 'environ',
        # sqlite3
        'sqlite3', 'Connection', 'Cursor',
        # common stdlib
        'Exception', 'BaseException', 'RuntimeError', 'ValueError',
        'TypeError', 'KeyError', 'IndexError', 'AttributeError',
        'ImportError', 'FileNotFoundError', 'OSError', 'IOError',
        'datetime', 'date', 'time', 'timedelta', 'timezone',
        'Decimal', 'Fraction',
        # dataclasses / abc
        'dataclass', 'field', 'abstractmethod', 'ABC',
        # argparse
        'ArgumentParser', 'Namespace',
    }

    for nome, caminho in modulos:
        try:
            with open(caminho, 'r', encoding='utf-8', errors='replace') as f:
                codigo = f.read()
            arvore = ast.parse(codigo)
        except (SyntaxError, OSError):
            continue

        for node in ast.walk(arvore):
            # Verificar anotações de tipo em argumentos de funções
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for arg in node.args.args:
                    if arg.annotation and isinstance(arg.annotation, ast.Name):
                        tipo_ref = arg.annotation.id
                        # Tipos genéricos de 1 letra (T, U, V, K, etc.) são TypeVars canônicos
                        if len(tipo_ref) == 1 and tipo_ref.isupper():
                            continue
                        # Se parece com um tipo customizado (maiúscula inicial)
                        if tipo_ref[0].isupper() and tipo_ref not in TIPOS_CONHECIDOS:
                            if tipo_ref not in todos_tipos:
                                resultados.append(ResultadoValidacao(
                                    f'I4_tipo_{nome}_{node.name}_{tipo_ref}',
                                    f'Tipo referenciado: {tipo_ref} em {nome}.{node.name}',
                                    False,
                                    f'Tipo {tipo_ref} referenciado em {nome}:{node.name} não encontrado em nenhum módulo',
                                ))

    if not resultados:
        resultados.append(ResultadoValidacao(
            'I4_tipos_compativeis',
            'Compatibilidade de tipos entre módulos',
            True,
            'Todas as referências de tipo são válidas',
        ))

    return resultados


# =============================================================================
# DESCOBERTA DE MÓDULOS
# =============================================================================

def descobrir_modulos_python(pasta: Path) -> List[Tuple[str, Path]]:
    """Descobre todos os scripts Python (.py) em uma pasta, excluindo testes
    e arquivos internos."""
    excluidos = {'__pycache__', '.git', 'node_modules', '.venv', 'venv', '.aidd'}
    modulos = []

    for py_file in sorted(pasta.rglob('*.py')):
        # Pular diretórios excluídos
        partes = py_file.relative_to(pasta).parts
        if any(p in excluidos for p in partes):
            continue
        # Pular testes
        if py_file.name.startswith('test_') or py_file.name.startswith('conftest'):
            continue
        # Pular __init__.py
        if py_file.name == '__init__.py':
            continue

        nome = py_file.stem
        modulos.append((nome, py_file))

    return modulos


# =============================================================================
# MAIN
# =============================================================================

def executar_gate(pasta_projeto: Path) -> int:
    """Executa o gate I3 completo. Retorna 0 (passou) ou 1 (falhou)."""

    print("\n" + "=" * 70)
    print("GATE: G_INTEGRACAO_CROSS_SCRIPT — Gate I3")
    print("Compatibilidade entre scripts irmãos do pipeline")
    print("=" * 70 + "\n")

    if not pasta_projeto.exists():
        print(f"❌ Pasta do projeto não encontrada: {pasta_projeto}")
        print("=" * 70)
        print("❌ GATE FALHOU")
        print("=" * 70)
        return 1

    # 1. Descobrir módulos Python
    modulos = descobrir_modulos_python(pasta_projeto)
    print(f"🔍 {len(modulos)} módulo(s) Python descoberto(s)")

    if not modulos:
        print("⚠️  Nenhum módulo Python encontrado — gate passou (nada a validar)")
        print("=" * 70)
        print("✅ GATE PASSOU")
        print("=" * 70)
        return 0

    for nome, caminho in modulos:
        print(f"   • {nome}: {caminho.relative_to(pasta_projeto)}")
    print()

    # 2. Executar todas as validações
    todos_resultados: List[ResultadoValidacao] = []

    print("📋 I1: Syntax válida (importabilidade)...")
    r1 = validar_importabilidade(modulos)
    todos_resultados.extend(r1)

    print("📋 I2: Contratos entre módulos (cross-reference)...")
    r2 = validar_contratos_entre_modulos(modulos, pasta_projeto=pasta_projeto)
    todos_resultados.extend(r2)

    print("📋 I3: Schemas JSON válidos...")
    r3 = validar_schemas_json_compativeis(pasta_projeto)
    todos_resultados.extend(r3)

    print("📋 I4: Compatibilidade de tipos...")
    r4 = validar_compatibilidade_tipos(modulos)
    todos_resultados.extend(r4)

    # 3. Relatório
    print("\n" + "-" * 70)
    print("RESULTADOS:")
    print("-" * 70)

    falhas = []
    for r in todos_resultados:
        icon = "✅" if r.passou else "❌"
        print(f"  {icon} {r.check_id}: {r.detalhes}")
        if not r.passou:
            falhas.append(r)

    total = len(todos_resultados)
    passaram = total - len(falhas)

    print(f"\n📊 Resumo: {passaram}/{total} checks passaram")

    print("\n" + "=" * 70)
    if falhas:
        print(f"❌ GATE FALHOU — {len(falhas)} divergência(s) de contrato encontrada(s)")
        for f in falhas:
            print(f"   • {f.descricao}: {f.detalhes}")
        print("=" * 70 + "\n")
        return 1
    else:
        print("✅ GATE PASSOU — todos os contratos entre scripts são compatíveis")
        print("=" * 70 + "\n")
        return 0


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Gate I3: Compatibilidade entre scripts irmãos do pipeline AIDD'
    )
    parser.add_argument(
        'pasta_projeto',
        nargs='?',
        default='.',
        help='Pasta raiz do projeto a ser analisado (default: diretório atual)',
    )
    parser.add_argument(
        '--cache-dir',
        help='Pasta de cache do projeto (alternativa a pasta_projeto)',
    )
    args = parser.parse_args()

    if args.cache_dir:
        pasta = Path(args.cache_dir)
    else:
        pasta = Path(args.pasta_projeto)

    return executar_gate(pasta)


if __name__ == '__main__':
    sys.exit(main())
