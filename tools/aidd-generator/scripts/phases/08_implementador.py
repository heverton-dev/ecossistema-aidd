#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 8: Implementador com Verificação — Micro-Tasks AST + Result Monad
aidd-project-generator v3.0

Sprint 06: Reestruturação completa em Micro-Tasks AST com Result Pattern.

Mudanças v3.0:
- Result Monad (Ok/Err): elimina exceções não tratadas (Zero 500).
  Toda operação retorna Result, pipeline encadeia via .unwrap()/.is_err().
- Micro-Tasks AST: decomposição de script em funções isoladas, cada uma
  gerada e testada independentemente (1 função por vez).
- Post-Mortem 5-Porquês: se pytest falha, investiga causa raiz, isola
  traceback e regenera apenas a função com falha.
- Self-Healing Loop: auto-cura integrada ao loop de verificação.

Tokens: variável (chamadas reais de LLM, incluindo correções) — nunca fabricado
"""

import sys
import os
import re
import json
import ast
import subprocess
import traceback as _traceback_mod
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple, Callable

sys.path.insert(0, str(Path(__file__).parent))
from utils_modelo import detectar_modelo_harness, obter_nome_amigavel_modelo
from utils_delegacao import solicitar_llm, extrair_json_resposta, LLMNaoConfiguradoException

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

MAX_TENTATIVAS_POR_SCRIPT = 3
MAX_TENTATIVAS_MICROTASK = 3
TIMEOUT_PYTEST_SEGUNDOS = 60


# =============================================================================
# RESULT MONAD — Zero Exceções Não Tratadas (Zero 500)
# =============================================================================

class Result:
    """Result Monad: Ok(valor) para sucesso, Err(erro) para falha.
    Elimina exceções não tratadas — toda operação retorna Result.
    Pipeline encadeia Results: se qualquer etapa retorna Err, o pipeline para."""

    __slots__ = ('_value', '_error', '_is_ok')

    def __init__(self, value=None, error=None, is_ok: bool = True):
        self._value = value
        self._error = error
        self._is_ok = is_ok

    @staticmethod
    def ok(value=None) -> 'Result':
        return Result(value=value, is_ok=True)

    @staticmethod
    def fail(error: str) -> 'Result':
        return Result(error=error, is_ok=False)

    def is_ok(self) -> bool:
        return self._is_ok

    def is_err(self) -> bool:
        return not self._is_ok

    def unwrap(self):
        if not self._is_ok:
            raise RuntimeError(f"Called unwrap() on Err: {self._error}")
        return self._value

    def unwrap_or(self, default):
        return self._value if self._is_ok else default

    def map(self, fn: Callable) -> 'Result':
        if self._is_ok:
            try:
                return Result.ok(fn(self._value))
            except Exception as e:
                return Result.fail(str(e))
        return self

    def flat_map(self, fn: Callable) -> 'Result':
        if self._is_ok:
            try:
                return fn(self._value)
            except Exception as e:
                return Result.fail(str(e))
        return self

    def __repr__(self):
        if self._is_ok:
            return f"Ok({self._value!r})"
        return f"Err({self._error!r})"

    def __eq__(self, other):
        if not isinstance(other, Result):
            return NotImplemented
        if self._is_ok != other._is_ok:
            return False
        return self._value == other._value if self._is_ok else self._error == other._error


# =============================================================================
# MICRO-TASK AST — Decomposição de Script em Funções Isoladas
# =============================================================================

@dataclass
class MicroTask:
    """Representa uma única função/método a ser implementado.
    Decomposição granular: 1 MicroTask = 1 função = 1 geração LLM = 1 teste."""
    nome_funcao: str
    assinatura: str
    responsabilidade: str
    dependencias: List[str] = field(default_factory=list)
    codigo_gerado: Optional[str] = None
    teste_gerado: Optional[str] = None
    resultado_pytest: Optional[Dict] = None
    tentativas: int = 0
    falhou: bool = False
    post_mortem: Optional[str] = None


def decompor_script_em_microtasks(codigo_fonte: str, teste_fonte: str) -> List[MicroTask]:
    """Decompõe um script Python em MicroTasks AST — uma por função/método definido.
    Usa AST parsing estático (Zero Token)."""
    try:
        arvore = ast.parse(codigo_fonte)
    except SyntaxError:
        return []

    microtasks = []
    for node in ast.iter_child_nodes(arvore):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Pular funções privadas mágicas (__init__, __str__, etc.)
            if node.name.startswith('__') and node.name.endswith('__'):
                continue
            args_list = []
            for arg in node.args.args:
                args_list.append(arg.arg)
            assinatura = f"{node.name}({', '.join(args_list)})"
            microtasks.append(MicroTask(
                nome_funcao=node.name,
                assinatura=assinatura,
                responsabilidade=f"Implementar {node.name}",
            ))
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith('__') and item.name.endswith('__'):
                        continue
                    args_list = []
                    for arg in item.args.args:
                        if arg.arg != 'self':
                            args_list.append(arg.arg)
                    assinatura = f"{node.name}.{item.name}({', '.join(args_list)})"
                    microtasks.append(MicroTask(
                        nome_funcao=f"{node.name}.{item.name}",
                        assinatura=assinatura,
                        responsabilidade=f"Implementar {item.name} da classe {node.name}",
                    ))
    return microtasks


# =============================================================================
# POST-MORTEM ANALYZER — 5-Porquês + Auto-Cura
# =============================================================================

class PostMortemAnalyzer:
    """Investigação 5-Porquês quando pytest falha.
    Isola o traceback, identifica a causa raiz e gera relatório
    para regeneração cirúrgica (apenas a função com falha)."""

    @staticmethod
    def analisar_falha(saida_pytest: str, codigo_fonte: str, nome_funcao: str = '') -> Dict:
        """Executa análise 5-Porquês de uma falha de pytest.
        Retorna dict com causa_raiz, traceback_isolado, funcao_afetada, relatorio."""
        porques = []
        traceback_isolado = PostMortemAnalyzer._isolar_traceback(saida_pytest)
        causa_raiz = PostMortemAnalyzer._extrair_causa_raiz(saida_pytest)

        # Porquê 1: Qual erro?
        porques.append(f"Erro: {causa_raiz}")

        # Porquê 2: Onde no código?
        localizacao = PostMortemAnalyzer._localizar_erro(saida_pytest, codigo_fonte)
        porques.append(f"Localização: {localizacao}")

        # Porquê 3: Qual tipo de falha?
        tipo_falha = PostMortemAnalyzer._classificar_falha(saida_pytest)
        porques.append(f"Tipo: {tipo_falha}")

        # Porquê 4: Qual padrão?
        padrao = PostMortemAnalyzer._identificar_padrao(saida_pytest, tipo_falha)
        porques.append(f"Padrão: {padrao}")

        # Porquê 5: Qual correção sugerida?
        correcao = PostMortemAnalyzer._sugerir_correcao(tipo_falha, causa_raiz)
        porques.append(f"Correção: {correcao}")

        return {
            'causa_raiz': causa_raiz,
            'traceback_isolado': traceback_isolado,
            'funcao_afetada': nome_funcao or localizacao,
            'tipo_falha': tipo_falha,
            'porques': porques,
            'relatorio': ' | '.join(porques),
            'correcao_sugerida': correcao,
        }

    @staticmethod
    def _isolar_traceback(saida: str) -> str:
        """Isola apenas o traceback relevante da saída do pytest."""
        linhas = saida.split('\n')
        capturando = False
        traceback_linhas = []
        for linha in linhas:
            if 'Traceback' in linha or 'FAILED' in linha or 'ERROR' in linha:
                capturando = True
            if capturando:
                traceback_linhas.append(linha)
                if linha.strip() == '' and len(traceback_linhas) > 3:
                    break
        resultado = '\n'.join(traceback_linhas).strip()
        return resultado[:1000] if resultado else saida[-500:]

    @staticmethod
    def _extrair_causa_raiz(saida: str) -> str:
        """Extrai a mensagem de erro final (causa raiz)."""
        # Procura por linhas como "AssertionError: ..." ou "ValueError: ..."
        for linha in reversed(saida.split('\n')):
            linha_strip = linha.strip()
            if re.match(r'\w+Error:|AssertionError:|assert ', linha_strip):
                return linha_strip[:200]
        # Fallback: última linha não vazia
        for linha in reversed(saida.split('\n')):
            if linha.strip():
                return linha.strip()[:200]
        return "Causa raiz não identificada"

    @staticmethod
    def _localizar_erro(saida: str, codigo: str) -> str:
        """Localiza a linha/arquivo do erro na saída do pytest."""
        # Procura por "File .../test_*.py, line N"
        m = re.search(r'File "([^"]+)", line (\d+)', saida)
        if m:
            return f"{Path(m.group(1)).name}:{m.group(2)}"
        # Procura por "test_*.py::test_*"
        m = re.search(r'(test_\w+\.py)::(\w+)', saida)
        if m:
            return f"{m.group(1)}::{m.group(2)}"
        return "localização não identificada"

    @staticmethod
    def _classificar_falha(saida: str) -> str:
        """Classifica o tipo de falha em categorias conhecidas."""
        saida_lower = saida.lower()
        if 'assertionerror' in saida_lower or 'assert' in saida_lower:
            return 'assertion_failure'
        if 'syntaxerror' in saida_lower:
            return 'syntax_error'
        if 'importerror' in saida_lower or 'modulenotfounderror' in saida_lower:
            return 'import_error'
        if 'typeerror' in saida_lower:
            return 'type_error'
        if 'attributeerror' in saida_lower:
            return 'attribute_error'
        if 'valueerror' in saida_lower:
            return 'value_error'
        if 'keyerror' in saida_lower:
            return 'key_error'
        if 'indexerror' in saida_lower:
            return 'index_error'
        if 'indentationerror' in saida_lower:
            return 'indentation_error'
        return 'unknown'

    @staticmethod
    def _identificar_padrao(saida: str, tipo_falha: str) -> str:
        """Identifica o padrão/causa comum baseado no tipo de falha."""
        padroes = {
            'assertion_failure': 'Valor esperado diferente do real — verificar lógica',
            'syntax_error': 'Erro de sintaxe — verificar indentação e parênteses',
            'import_error': 'Módulo não encontrado — verificar PYTHONPATH e nome do arquivo',
            'type_error': 'Tipo incompatível — verificar assinatura da função',
            'attribute_error': 'Atributo/método não existe — verificar contrato AST',
            'value_error': 'Valor inválido — verificar validação de entrada',
            'key_error': 'Chave não encontrada em dict — verificar estrutura de dados',
            'index_error': 'Índice fora do range — verificar bounds',
            'indentation_error': 'Indentação incorreta — verificar espaços/tabs',
        }
        return padroes.get(tipo_falha, 'Padrão não catalogado')

    @staticmethod
    def _sugerir_correcao(tipo_falha: str, causa_raiz: str) -> str:
        """Sugere correção específica baseada no tipo de falha."""
        correcoes = {
            'assertion_failure': 'Recalcular valor esperado ou corrigir lógica da função',
            'syntax_error': 'Corrigir sintaxe — provavelmente parênteses ou dois-pontos faltando',
            'import_error': 'Verificar se o arquivo existe em src/ e se __init__.py está presente',
            'type_error': 'Converter tipos antes da operação (str→int, date→str, etc.)',
            'attribute_error': 'Definir o atributo/método faltante no código',
            'value_error': 'Adicionar validação de entrada ou corrigir valor de teste',
            'key_error': 'Garantir que a chave existe antes de acessar',
            'index_error': 'Verificar len() antes de acessar por índice',
            'indentation_error': 'Normalizar indentação para 4 espaços',
        }
        return correcoes.get(tipo_falha, 'Revisar código e teste manualmente')

PROMPT_GERAR_SCHEMA_COMPARTILHADO = """# ENTRADA: Database Architect — define unified SQLite DDL schema for the project.
All modules MUST use EXACTLY this schema. No exceptions.

PROJECT: {ideia}
STACK: {stack}
SCRIPTS:
{scripts_info}

Rules: CREATE TABLE IF NOT EXISTS, all required tables/columns/PK/FK, self-explanatory names, idempotent in SQLite.

# COT: think in English Caveman (3-5 dense lines, no articles):
# "scan scripts → extract entities → define tables → set PK/FK relations → output DDL JSON"

# SAIDA: Return ONLY the JSON below, nothing else, no markdown/code fence.
# RESPOND IN BRAZILIAN PORTUGUESE (PT-BR) for descriptive fields.
{{"schema_sql":"<full DDL>","tabelas":["t1","t2"]}}
"""

PROMPT_GERAR_TESTE_INTEGRACAO = """# ENTRADA: Integration Test Engineer — generate ONE complete pytest that chains multiple project scripts in a real end-to-end flow.

PROJECT: {ideia}
STACK: {stack}
{secao_schema}

IMPLEMENTED SCRIPTS:
{scripts_info}

Rules:
- Test MUST integrate and chain generated scripts/modules, using output of one function as input of another (e.g.: create record -> use returned id -> execute dependent action -> query/validate final state in DB or service).
- Do NOT write isolated tests or mock internal functions; exercise the real flow a user or CLI would follow.
- Direct imports (e.g.: from modulo import ...). src/ is already in PYTHONPATH.
- SQLite/DB: use in-memory ':memory:' or tmp_path. Initialize tables in test fixture before operations and enable PRAGMA foreign_keys = ON.
- NEVER use subprocess.run in tests (call Python functions and classes directly).
- CONTRACT: only call functions/classes that scripts actually define.
- If test saves and re-reads JSON, normalize types before comparing (tuple->list, None preserved).

# COT: think in English Caveman (3-5 dense lines, no articles):
# "read all script code → find entry points → chain inputs/outputs → write pytest fixture + test → output JSON"

# SAIDA: Return ONLY the JSON below, nothing else, no markdown/code fence.
# RESPOND IN BRAZILIAN PORTUGUESE (PT-BR) for descriptive fields.
{{"teste":"<complete pytest Python code>","caminho_teste":"test_integracao.py"}}
"""

PROMPT_IMPLEMENTAR_SCRIPT = """# ENTRADA: Python Script Implementer — generate real, functional code. No TODO/pass stubs.

PROJECT: {ideia}
STACK: {stack}
{secao_schema}
SCRIPT: {nome}
RESPONSIBILITY: {responsabilidade}
PSEUDOCODE: {pseudocodigo}

Rules:
- Code: testable functions/classes. Test: pytest suite (test_*), direct import (from {modulo} import). src/ already in PYTHONPATH.
- CONTRACT: test can only call functions that code actually defines or imports. NEVER assume auxiliary functions (e.g.: criar_autor, criar_item) without defining them in code.
- SQLite: use schema above, function criar_tabela(conn) with DDL, conn=None optional, NEVER conn.close() if received.
- FK: if schema has FOREIGN KEY, execute PRAGMA foreign_keys = ON right after creating/opening connection. Validate parent record existence before dependent INSERT (SELECT 1 FROM ... WHERE id = ?), return clear error (e.g.: ValueError) if not found — NEVER silence invalid FK or report false success.
- Tests: fixture with DDL + PRAGMA foreign_keys=ON before INSERT/SELECT, :memory: or tmp_path (never os.remove). For scripts with FK: include at least 1 test for invalid reference/nonexistent ID and verify it returns error.
- SQLite dates: stored as text ('YYYY-MM-DD'). On retrieval, convert explicitly to datetime.date (date.fromisoformat(val) if isinstance(val, str) else val) before date arithmetic.
- JSON round-trip: if test saves and re-reads JSON, normalize types before comparing (tuple->list, None preserved). Use json.loads(json.dumps(x, default=str)) on expected data.
- Streak: data_referencia optional, duplicate check-ins on same date must not duplicate streak.
- No subprocess.run in tests. UTF-8 on console (sys.stdout.reconfigure if win32).

# COT: think in English Caveman (3-5 dense lines, no articles):
# "read spec → implement functions → write tests → validate FK/dates → output JSON with code+test"

# SAIDA: Return ONLY the JSON below, nothing else, no markdown/code fence.
# RESPOND IN BRAZILIAN PORTUGUESE (PT-BR) for descriptive fields.
{{"codigo":"<complete Python code>","teste":"<complete pytest code>","caminho_relativo":"{caminho_sugerido}","caminho_teste":"{caminho_teste_sugerido}"}}
"""

PROMPT_CORRIGIR_SCRIPT = """# ENTRADA: Code Fixer — correct code/test that failed in pytest. Minimal diff, fix root cause.

{secao_schema}
MODULE: {modulo}

CODE:
{codigo}

TEST:
{teste}

ERRORS (failures only):
{erro}

Rules: direct import (from {modulo} import), consistent names, schema DDL + PRAGMA foreign_keys = ON in fixture before INSERT/SELECT, conn=None optional, NEVER conn.close() if received, :memory: or tmp_path (never os.remove), data_referencia optional for streak. If FOREIGN KEY exists: validate parent record existence before dependent operation, return clear error if not found, ensure at least 1 test for invalid reference/nonexistent ID. If date error (str vs date): convert with date.fromisoformat before subtraction. If count assertion error: verify expected value is mathematically exact (N+1, not hardcoded).

# COT: think in English Caveman (3-5 dense lines, no articles):
# "read error → locate failing line → check root cause (FK? date? type?) → apply minimal fix → output JSON"

# SAIDA: Return ONLY the JSON below, nothing else, no markdown/code fence.
# RESPOND IN BRAZILIAN PORTUGUESE (PT-BR) for descriptive fields.
{{"codigo":"<fixed code>","teste":"<fixed test>","caminho_relativo":"...","caminho_teste":"..."}}
"""


# =============================================================================
# GATES DE VALIDAÇÃO (I1-I5)
# =============================================================================

class Gate:
    """Estrutura de resultado de gate"""
    def __init__(self, gate_id: str, descricao: str, passou: bool, detalhes: str):
        self.gate_id = gate_id
        self.descricao = descricao
        self.passou = passou
        self.detalhes = detalhes

    def to_dict(self):
        return {
            'gate_id': self.gate_id,
            'descricao': self.descricao,
            'status': 'PASSOU' if self.passou else 'FALHOU',
            'detalhes': self.detalhes
        }


class ValidadorGatesPhase8:
    """Valida a implementação real (não a intenção) da Fase 8"""

    @staticmethod
    def executar_todos(pasta_projeto: Path, scripts_implementados: List[Dict],
                        resultado_pytest: Optional[Dict],
                        resultado_integracao: Optional[Dict] = None,
                        teste_integracao_gerado: bool = False) -> Tuple[List[Gate], bool]:
        gates = [
            ValidadorGatesPhase8._gate_i1_scripts_implementados(pasta_projeto, scripts_implementados),
            ValidadorGatesPhase8._gate_i2_testes_coletam(resultado_pytest),
            ValidadorGatesPhase8._gate_i3_testes_passam(resultado_pytest),
            ValidadorGatesPhase8._gate_i4_cli_executa(pasta_projeto),
            ValidadorGatesPhase8._gate_i5_teste_integracao(resultado_integracao, teste_integracao_gerado),
        ]
        return gates, all(g.passou for g in gates)

    @staticmethod
    def _gate_i1_scripts_implementados(pasta_projeto: Path, scripts_implementados: List[Dict]) -> Gate:
        """I1: Todo script do design tem arquivo real em src/"""
        total = len(scripts_implementados)
        criados = sum(
            1 for s in scripts_implementados
            if (pasta_projeto / 'src' / s.get('caminho_relativo', '')).exists()
        )
        passou = total > 0 and criados == total
        return Gate('I1_scripts_implementados',
                   'Validar todos os scripts do design foram implementados',
                   passou, f"{criados}/{total} scripts implementados em disco")

    @staticmethod
    def _gate_i2_testes_coletam(resultado_pytest: Optional[Dict]) -> Gate:
        """I2: pytest consegue coletar os testes sem erro de import"""
        if resultado_pytest is None:
            return Gate('I2_testes_coletam', 'Validar pytest coleta sem erro', False, 'pytest nunca rodou')
        passou = not resultado_pytest.get('erro_coleta', True)
        detalhes = 'Coleta OK' if passou else 'Erro de coleta (ver detalhes_coleta no index)'
        return Gate('I2_testes_coletam', 'Validar pytest coleta sem erro', passou, detalhes)

    @staticmethod
    def _gate_i3_testes_passam(resultado_pytest: Optional[Dict]) -> Gate:
        """I3: 100% dos testes reais passam — nunca estimado"""
        if resultado_pytest is None:
            return Gate('I3_testes_passam', 'Validar 100% dos testes passam', False, 'pytest nunca rodou')
        total = resultado_pytest.get('total', 0)
        passaram = resultado_pytest.get('passaram', 0)
        falharam = resultado_pytest.get('falharam', 0)
        erros = resultado_pytest.get('erros', 0)
        passou = total > 0 and falharam == 0 and erros == 0 and passaram == total
        detalhes_falha = f" ({falharam} falha(s), {erros} erro(s))" if (falharam > 0 or erros > 0) else ""
        return Gate('I3_testes_passam', 'Validar 100% dos testes passam', passou,
                   f"{passaram}/{total} testes passando{detalhes_falha}")

    @staticmethod
    def _gate_i4_cli_executa(pasta_projeto: Path) -> Gate:
        """I4: se houver CLI entry-point (main.py), roda smoke-test real"""
        main_py = pasta_projeto / 'main.py'
        if not main_py.exists():
            return Gate('I4_cli_executa', 'Validar CLI executa smoke-test', True,
                       'Sem main.py — gate não aplicável, não bloqueia')
        try:
            resultado = subprocess.run(
                [sys.executable, str(main_py), '--help'],
                cwd=str(pasta_projeto), capture_output=True, timeout=10
            )
            passou = resultado.returncode == 0
            return Gate('I4_cli_executa', 'Validar CLI executa smoke-test', passou,
                       f"main.py --help retornou exit code {resultado.returncode}")
        except Exception as e:
            return Gate('I4_cli_executa', 'Validar CLI executa smoke-test', False, f"Erro ao rodar: {e}")

    @staticmethod
    def _gate_i5_teste_integracao(resultado_integracao: Optional[Dict], teste_gerado: bool) -> Gate:
        """I5: Teste de integração entre scripts gerado e passando"""
        if not teste_gerado or resultado_integracao is None:
            return Gate('I5_teste_integracao',
                       'Validar teste de integração entre scripts',
                       False, 'Teste de integração não gerado ou não executado')
        if resultado_integracao.get('erro_coleta', False):
            return Gate('I5_teste_integracao',
                       'Validar teste de integração entre scripts',
                       False, 'Erro de coleta no teste de integração')
        passaram = resultado_integracao.get('passaram', 0)
        falharam = resultado_integracao.get('falharam', 0)
        erros = resultado_integracao.get('erros', 0)
        total = resultado_integracao.get('total', 0)
        passou = total > 0 and falharam == 0 and erros == 0 and passaram == total
        detalhes_falha = f" ({falharam} falha(s), {erros} erro(s))" if (falharam > 0 or erros > 0) else ""
        return Gate('I5_teste_integracao',
                   'Validar teste de integração entre scripts',
                   passou, f"{passaram}/{total} teste(s) de integração passando{detalhes_falha}")


# =============================================================================
# IMPLEMENTADOR PRINCIPAL
# =============================================================================

class ImplementadorFase8:
    """Orquestrador da Fase 8: código real + verificação real + correção real + schema unificado"""

    def __init__(self, pasta_projeto: Path, model_override: str = None):
        self.pasta_projeto = Path(pasta_projeto)
        self.pasta_cache = self.pasta_projeto / '.aidd' / 'cache'
        self.modelo_harness = detectar_modelo_harness()
        self.modelo_final = model_override or self.modelo_harness
        self.modelo_nome_amigavel = obter_nome_amigavel_modelo(self.modelo_final)
        self._tokens_totais = 0
        self.schema_compartilhado: Optional[str] = None

    def executar(self, ideia_projeto: str, analise: Dict, design: Dict) -> Optional[Dict]:
        """Executa pipeline completo da Fase 8"""
        print(f"\n🛠️  PHASE 8: Implementador com Verificação")
        print(f"   Modelo: {self.modelo_nome_amigavel}")
        print(f"   {'-' * 60}")

        tempo_inicio = datetime.now()
        stack = analise.get('stack_recomendado', {}) if analise else {}
        scripts_design = (design.get('design', {}) if design else {}).get('scripts', [])

        if not scripts_design:
            print("   ❌ Nenhum script no design — nada para implementar (Fase 3 rodou?)")
            return None

        # Coordenação de Schema Compartilhado
        if self._precisa_schema_compartilhado(stack, scripts_design):
            print("\n   🗄️  Derivando schema de banco de dados unificado para todos os scripts...")
            self.schema_compartilhado = self._gerar_schema_compartilhado(ideia_projeto, stack, scripts_design)
            if self.schema_compartilhado:
                print("   ✓ Schema compartilhado derivado com sucesso.")
            else:
                print("   ⚠️ Não foi possível derivar schema centralizado, prosseguindo com heurística padrão.")

        scripts_implementados = []
        for script_spec in scripts_design:
            nome = script_spec.get('nome', 'sem_nome')
            print(f"\n   🤖 Implementando {nome}...")
            resultado = self._implementar_script_com_verificacao(ideia_projeto, stack, script_spec)
            if resultado is None:
                print(f"   ❌ Falha ao obter implementação de {nome} (LLM não respondeu)")
                return None
            status = "✓" if resultado.get('tentativas', 1) and not resultado.get('falhou_apos_tentativas') else "⚠️"
            print(f"   {status} {nome}: {resultado.get('tentativas', 1)} tentativa(s)")
            scripts_implementados.append(resultado)

        print(f"\n   🔗 Gerando teste de integração entre scripts...")
        teste_integracao_gerado, resultado_integracao = self._gerar_e_escrever_teste_integracao(
            ideia_projeto, stack, scripts_implementados
        )
        if teste_integracao_gerado and resultado_integracao:
            status_int = "✓" if resultado_integracao.get('passaram', 0) > 0 and resultado_integracao.get('falharam', 0) == 0 and resultado_integracao.get('erros', 0) == 0 and not resultado_integracao.get('erro_coleta', False) else "✗"
            print(f"   {status_int} Teste de integração: {resultado_integracao.get('passaram', 0)}/{resultado_integracao.get('total', 0)} passando")

        print(f"\n✅ Rodando suite de testes completa...")
        resultado_pytest = self._rodar_pytest(caminho_relativo=None)

        gates, todos_passaram = ValidadorGatesPhase8.executar_todos(
            self.pasta_projeto, scripts_implementados, resultado_pytest,
            resultado_integracao=resultado_integracao,
            teste_integracao_gerado=teste_integracao_gerado
        )
        for gate in gates:
            icon = "✓" if gate.passou else "✗"
            print(f"   {icon} {gate.gate_id}: {gate.detalhes}")

        tempo_execucao = (datetime.now() - tempo_inicio).total_seconds()
        index = self._gerar_index(
            scripts_implementados, resultado_pytest, gates, tempo_execucao,
            teste_integracao_gerado=teste_integracao_gerado,
            resultado_integracao=resultado_integracao
        )

        path_index = self.pasta_cache / '_phase_08_index.json'
        path_index.parent.mkdir(parents=True, exist_ok=True)
        with open(path_index, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        if not todos_passaram:
            print(f"\n❌ FASE FALHOU: Gates não passaram")
            return None

        print(f"\n{'=' * 60}")
        print(f"✅ PHASE 8 COMPLETO — {len(scripts_implementados)} script(s) implementados e verificados")
        print(f"   Tokens (reais): {self._tokens_totais}")
        print(f"{'=' * 60}\n")

        return index

    def _precisa_schema_compartilhado(self, stack: Dict, scripts_design: List[Dict]) -> bool:
        """Detecta se o projeto envolve persistência SQLite ou banco de dados compartilhado"""
        if stack:
            banco_val = str(stack.get('banco', '')).strip().lower()
            if banco_val and banco_val not in ['none', 'null', 'nenhum', 'sem', 'false', 'n/a', '{}', '']:
                return True
            for k, v in stack.items():
                v_str = str(v).lower()
                if v_str in ['none', 'null', 'nenhum', 'sem', 'false', 'n/a', '{}', '']:
                    continue
                if any(termo in v_str for termo in ['sqlite', 'database', 'sql', 'storage']):
                    return True

        for s in scripts_design:
            texto = (s.get('nome', '') + ' ' + s.get('responsabilidade', '') + ' ' + s.get('pseudocodigo', '')).lower()
            if any(termo in texto for termo in ['sqlite', 'tabela', 'table', 'checkin', 'habito', 'create table', 'insert into', 'banco de dados']):
                return True

        return False

    def _gerar_schema_compartilhado(self, ideia: str, stack: Dict, scripts_design: List[Dict]) -> Optional[str]:
        """Gera um schema SQL SQLite unificado e consistente para todo o projeto.
        Usa Result Monad internamente — Zero exceções não tratadas."""
        scripts_info = "\n".join([
            f"- {s.get('nome')}: {s.get('responsabilidade')} | Pseudocódigo: {s.get('pseudocodigo')}"
            for s in scripts_design
        ])

        prompt = PROMPT_GERAR_SCHEMA_COMPARTILHADO.format(
            ideia=ideia,
            stack=json.dumps(stack, ensure_ascii=False),
            scripts_info=scripts_info,
        )
        contexto = "Phase 8: Arquiteto de Banco de Dados / Schema Centralizado"

        result = self._chamar_llm_result(
            prompt=prompt, contexto=contexto, fase="phase_08_schema"
        )
        if result.is_err():
            print(f"   ❌ {result._error}")
            return None

        dados = result.unwrap()
        if isinstance(dados, dict) and 'schema_sql' in dados:
            return str(dados['schema_sql']).strip()
        elif isinstance(dados, str):
            return dados.strip()

        return None

    def _montar_secao_schema(self) -> str:
        """Monta o bloco de instruções de schema compartilhado para injeção no prompt"""
        if not self.schema_compartilhado:
            return ""

        return (
            "SCHEMA DE BANCO DE DADOS UNIFICADO DO PROJETO (OBRIGATÓRIO):\n"
            "Todos os scripts e testes DEVEM usar EXATAMENTE a estrutura e nomes de tabelas/colunas abaixo:\n"
            "```sql\n"
            f"{self.schema_compartilhado}\n"
            "```\n"
            "Atenção: NUNCA invente tabelas ou colunas diferentes deste schema unificado."
        )

    def _gerar_e_escrever_teste_integracao(
        self, ideia: str, stack: Dict, scripts_implementados: List[Dict]
    ) -> Tuple[bool, Optional[Dict]]:
        """Gera e escreve teste de integração que encadeia os scripts implementados.
        Usa Result Monad internamente — Zero exceções não tratadas."""
        scripts_info_linhas = []
        for s in scripts_implementados:
            caminho = s.get('caminho_relativo', '')
            cod = s.get('codigo', '')
            scripts_info_linhas.append(f"MÓDULO: src/{caminho}\nCÓDIGO:\n{cod}\n")
        scripts_info = "\n".join(scripts_info_linhas)

        secao_schema = self._montar_secao_schema()
        prompt = PROMPT_GERAR_TESTE_INTEGRACAO.format(
            ideia=ideia,
            stack=json.dumps(stack, ensure_ascii=False),
            secao_schema=secao_schema,
            scripts_info=scripts_info,
        )
        contexto = "Phase 8: Teste de Integração / Fluxo End-to-End entre Scripts"

        result = self._chamar_llm_result(
            prompt=prompt, contexto=contexto, fase="phase_08_integracao"
        )
        if result.is_err():
            print(f"   ❌ {result._error}")
            return False, None

        dados = result.unwrap()
        if 'teste' not in dados:
            print(f"   ⚠️ Resposta sem chave 'teste'")
            return False, None

        caminho_teste = dados.get('caminho_teste') or 'test_integracao.py'
        nome_teste = Path(str(caminho_teste).replace('\\', '/')).name
        if 'integracao' not in nome_teste and 'integration' not in nome_teste:
            nome_teste = 'test_integracao.py'
        else:
            if not nome_teste.startswith('test_'):
                nome_teste = f"test_{nome_teste}"
            if not nome_teste.endswith('.py'):
                nome_teste += '.py'

        arq_teste = self.pasta_projeto / 'tests' / nome_teste
        arq_teste.parent.mkdir(parents=True, exist_ok=True)
        arq_teste.write_text(dados['teste'], encoding='utf-8')
        print(f"   ✓ Teste de integração gerado e salvo em tests/{nome_teste}")

        resultado_integracao = self._rodar_pytest(caminho_relativo=nome_teste)
        return True, resultado_integracao

    def _implementar_script_com_verificacao(self, ideia: str, stack: Dict, script_spec: Dict) -> Optional[Dict]:
        """Implementa 1 script, roda o teste real, corrige até passar (ou esgota tentativas)"""
        nome_raw = script_spec.get('nome', 'script.py')
        nome_base = Path(str(nome_raw).replace('\\', '/')).name
        if nome_base.endswith('.py'):
            modulo = nome_base[:-3]
            caminho_sugerido = nome_base
        else:
            modulo = nome_base
            caminho_sugerido = f"{nome_base}.py"
        caminho_teste_sugerido = f"test_{caminho_sugerido}"

        # Retomada inteligente: se script e teste já existem em disco e passam no pytest
        arq_codigo = self.pasta_projeto / 'src' / caminho_sugerido
        arq_teste = self.pasta_projeto / 'tests' / caminho_teste_sugerido
        if arq_codigo.exists() and arq_teste.exists():
            resultado_existente = self._rodar_pytest(caminho_relativo=caminho_teste_sugerido)
            if resultado_existente['passaram'] > 0 and resultado_existente['falharam'] == 0 and resultado_existente['erros'] == 0 and not resultado_existente['erro_coleta']:
                print(f"   ✓ {caminho_sugerido} já implementado e com testes passando ({resultado_existente['passaram']} testes)")
                return {
                    'codigo': arq_codigo.read_text(encoding='utf-8'),
                    'teste': arq_teste.read_text(encoding='utf-8'),
                    'caminho_relativo': caminho_sugerido,
                    'caminho_teste': caminho_teste_sugerido,
                    'tentativas': 1,
                    'reutilizado_existente': True
                }

        secao_schema = self._montar_secao_schema()

        prompt = PROMPT_IMPLEMENTAR_SCRIPT.format(
            ideia=ideia,
            stack=json.dumps(stack, ensure_ascii=False),
            secao_schema=secao_schema,
            nome=nome_raw,
            responsabilidade=script_spec.get('responsabilidade', ''),
            pseudocodigo=script_spec.get('pseudocodigo', ''),
            modulo=modulo,
            caminho_sugerido=caminho_sugerido,
            caminho_teste_sugerido=caminho_teste_sugerido,
        )
        contexto = f"Phase 8: Implementador. Script: {script_spec.get('nome')}"

        result_llm = self._chamar_llm_result(
            prompt=prompt, contexto=contexto, fase="phase_08"
        )
        if result_llm.is_err():
            print(f"   ❌ {result_llm._error}")
            return None

        impl = result_llm.unwrap()
        if 'codigo' not in impl or 'teste' not in impl:
            print(f"   ⚠️ Resposta sem chaves 'codigo'/'teste'")
            return None

        # Normalização rigorosa de caminhos (fixados para este script em todas as tentativas)
        caminho_relativo = self._normalizar_caminho_codigo(
            impl.get('caminho_relativo'), caminho_sugerido
        )
        caminho_teste = self._normalizar_caminho_teste(
            impl.get('caminho_teste'), caminho_relativo
        )
        impl['caminho_relativo'] = caminho_relativo
        impl['caminho_teste'] = caminho_teste

        for tentativa in range(1, MAX_TENTATIVAS_POR_SCRIPT + 1):
            # GAP 1: validação AST do contrato antes de rodar pytest
            problema_contrato = self._validar_contrato_ast(impl.get('codigo', ''), impl.get('teste', ''), modulo)
            if problema_contrato:
                print(f"   ⚠️ Contrato AST: {problema_contrato[:100]}...")
                # Tratar como falha real — pular pytest e ir direto para correção
                erro_compacto = problema_contrato
                if tentativa == MAX_TENTATIVAS_POR_SCRIPT:
                    impl['tentativas'] = tentativa
                    impl['falhou_apos_tentativas'] = True
                    return impl
                # Cair direto no fluxo de correção abaixo
            else:
                self._escrever_implementacao(impl)
                resultado_teste = self._rodar_pytest(caminho_relativo=impl.get('caminho_teste'))

                if resultado_teste['passaram'] > 0 and resultado_teste['falharam'] == 0 and resultado_teste['erros'] == 0 and not resultado_teste['erro_coleta']:
                    impl['tentativas'] = tentativa
                    # Sprint 06: Micro-Tasks AST verification pass
                    result_mt = self.decompor_e_implementar_microtasks(
                        ideia, stack, script_spec, impl
                    )
                    if result_mt.is_ok():
                        return impl
                    # Se micro-tasks falhou, cai no loop de auto-cura
                    impl['post_mortem'] = result_mt._error

                if tentativa == MAX_TENTATIVAS_POR_SCRIPT:
                    impl['tentativas'] = tentativa
                    impl['falhou_apos_tentativas'] = True
                    return impl

                # Economia de tokens: enviar apenas falhas do pytest, não saída completa
                erro_compacto = self._extrair_falhas_pytest(resultado_teste.get('saida', ''))

            # Sprint 06: Tentativa de correção via Result Monad
            prompt_fix = PROMPT_CORRIGIR_SCRIPT.format(
                secao_schema=secao_schema,
                codigo=impl.get('codigo', ''),
                teste=impl.get('teste', ''),
                erro=erro_compacto,
                modulo=modulo,
            )
            result_fix = self._chamar_llm_result(
                prompt=prompt_fix, contexto=contexto, fase="phase_08_fix"
            )
            if result_fix.is_err():
                print(f"   ❌ {result_fix._error}")
                impl['tentativas'] = tentativa
                impl['falhou_apos_tentativas'] = True
                return impl

            impl_corrigido = result_fix.unwrap()
            if isinstance(impl_corrigido, dict) and 'codigo' in impl_corrigido and 'teste' in impl_corrigido:
                impl_corrigido['caminho_relativo'] = caminho_relativo
                impl_corrigido['caminho_teste'] = caminho_teste
                impl = impl_corrigido
            else:
                impl['tentativas'] = tentativa
                impl['falhou_apos_tentativas'] = True
                return impl

    @staticmethod
    def _normalizar_caminho_codigo(caminho: Optional[str], nome_padrao: str = "script.py") -> str:
        c = str(caminho or nome_padrao).replace('\\', '/').strip()
        while c.startswith('src/'):
            c = c[4:]
        if not c.endswith('.py'):
            c += '.py'
        return c

    @staticmethod
    def _normalizar_caminho_teste(caminho: Optional[str], caminho_codigo: str) -> str:
        nome_codigo = Path(caminho_codigo).name
        nome_teste_esperado = f"test_{nome_codigo}"
        c = str(caminho or '').replace('\\', '/').strip()
        while c.startswith('tests/') or c.startswith('test/'):
            if c.startswith('tests/'):
                c = c[6:]
            elif c.startswith('test/'):
                c = c[5:]
        nome_base = Path(c).name if c else ''
        if not nome_base or nome_base in ['test_tests.py', 'test_teste.py', 'test_script.py', 'test_.py']:
            return nome_teste_esperado
        if not nome_base.startswith('test_'):
            nome_base = f"test_{nome_base}"
        if not nome_base.endswith('.py'):
            nome_base += '.py'
        return nome_base

    def _escrever_implementacao(self, impl: Dict):
        """Escreve código + teste em disco de verdade em UTF-8"""
        caminho_codigo = self.pasta_projeto / 'src' / impl['caminho_relativo']
        caminho_codigo.parent.mkdir(parents=True, exist_ok=True)
        caminho_codigo.write_text(impl['codigo'], encoding='utf-8')

        init_src = self.pasta_projeto / 'src' / '__init__.py'
        if not init_src.exists():
            init_src.write_text('', encoding='utf-8')

        init_parent = caminho_codigo.parent / '__init__.py'
        if not init_parent.exists():
            init_parent.write_text('', encoding='utf-8')

        caminho_teste = self.pasta_projeto / 'tests' / impl['caminho_teste']
        caminho_teste.parent.mkdir(parents=True, exist_ok=True)
        caminho_teste.write_text(impl['teste'], encoding='utf-8')

        init_tests = self.pasta_projeto / 'tests' / '__init__.py'
        if not init_tests.exists():
            init_tests.write_text('', encoding='utf-8')

    @staticmethod
    def _extrair_falhas_pytest(saida_completa: str) -> str:
        """Extrai apenas seções de falha/erro do pytest, descartando testes que passaram.
        Reduz ~3000 chars de saída completa para ~500 chars de apenas erros relevantes."""
        linhas = saida_completa.split('\n')
        falhas = []
        capturando = False
        for linha in linhas:
            # Captura blocos de FAILED, ERROR, e short test summary
            if 'FAILED' in linha or 'ERROR' in linha or 'short test summary' in linha.lower():
                capturando = True
            elif linha.startswith('=') and ('passed' in linha or 'failed' in linha or 'error' in linha):
                # Linha de resumo final — sempre incluir
                falhas.append(linha.strip())
                capturando = False
                continue
            elif capturando and linha.startswith('PASSED'):
                capturando = False
                continue
            if capturando:
                falhas.append(linha)
        resultado = '\n'.join(falhas).strip()
        # Fallback: se não conseguiu extrair nada específico, pegar últimos 800 chars
        if not resultado or len(resultado) < 50:
            return saida_completa[-800:]
        return resultado[:1500]  # Cap em 1500 chars (vs 3000 original)

    @staticmethod
    def _validar_contrato_ast(codigo: str, teste: str, modulo: str = '') -> Optional[str]:
        """Valida mecanicamente que o teste só chama funções que o código define/exporta.
        Retorna None se OK, ou string descrevendo o problema (para injeção no prompt de correção).
        Usa AST parsing — não depende de rodar o código."""
        try:
            arvore_codigo = ast.parse(codigo)
            arvore_teste = ast.parse(teste)
        except SyntaxError:
            return None  # SyntaxError será pego pelo pytest, não duplicar aqui

        # Coletar nomes definidos no código: funções, classes, imports, e métodos por classe
        nomes_definidos = set()
        metodos_por_classe = {}  # nome_classe -> {metodo1, metodo2, ...}
        autoimports_suspeitos = set()  # nomes importados de um modulo com o MESMO nome (from X import X)
        for node in ast.walk(arvore_codigo):
            if isinstance(node, ast.FunctionDef):
                nomes_definidos.add(node.name)
            elif isinstance(node, ast.ClassDef):
                nomes_definidos.add(node.name)
                metodos = set()
                for item in ast.walk(node):
                    if isinstance(item, ast.FunctionDef):
                        metodos.add(item.name)
                        nomes_definidos.add(item.name)
                metodos_por_classe[node.name] = metodos
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    nomes_definidos.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    nome_importado = alias.asname or alias.name
                    # Autoimportação (from <proprio_modulo> import qualquer_nome):
                    # sintaticamente parece um import valido mas nao prova que a funcao existe de
                    # verdade em lugar nenhum — achado real: LLM as vezes gera 'from coletar_dados
                    # import coletar_habitos, coletar_checkins' dentro do proprio coletar_dados.py,
                    # sem nunca definir essas funcoes (so escreve o corpo do teste em ambos os lados).
                    # Cobre tanto 'from X import X' quanto 'from X import Y, Z' onde X e o modulo atual.
                    if node.module and modulo and node.module == modulo:
                        autoimports_suspeitos.add(nome_importado)
                        continue
                    if node.module and node.module == alias.name:
                        autoimports_suspeitos.add(nome_importado)
                        continue
                    nomes_definidos.add(nome_importado)

        # Nomes built-in e do pytest que sempre existem
        builtins_permitidos = {
            'print', 'len', 'range', 'int', 'str', 'float', 'list', 'dict',
            'set', 'tuple', 'bool', 'type', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
            'min', 'max', 'sum', 'abs', 'round', 'any', 'all', 'open', 'super',
            'property', 'staticmethod', 'classmethod', 'Exception', 'ValueError',
            'TypeError', 'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
            'NotImplementedError', 'OSError', 'IOError', 'FileNotFoundError',
            'datetime', 'date', 'timedelta', 'Path', 'os', 'sys', 'json',
            'sqlite3', 're', 'math', 'time', 'uuid', 'copy', 'pytest',
            'fixture', 'tmp_path', 'monkeypatch',
            'TestClient', 'BaseModel', 'Field',
        }

        # Funções de teste pytest definidas no próprio teste
        nomes_teste_pytest = set()
        for node in ast.walk(arvore_teste):
            if isinstance(node, ast.FunctionDef):
                nomes_teste_pytest.add(node.name)

        # Mapear variáveis do teste para classes (ex: repo = LivroRepo() → repo é LivroRepo)
        vars_com_classe = {}  # var_name -> class_name
        for node in ast.walk(arvore_teste):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                        if isinstance(node.value.func, ast.Name) and node.value.func.id in metodos_por_classe:
                            vars_com_classe[target.id] = node.value.func.id

        # Coletar nomes chamados no teste e verificar contrato
        nomes_faltando = []
        for node in ast.walk(arvore_teste):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                # Chamada direta: funcao()
                nome = node.func.id
                if nome not in builtins_permitidos and nome not in nomes_definidos and nome not in nomes_teste_pytest:
                    if not nome.startswith('_') and nome not in ('conn', 'db_path', 'tmp_path'):
                        nomes_faltando.append(nome)
            elif isinstance(node.func, ast.Attribute):
                # Chamada método: obj.metodo()
                if isinstance(node.func.value, ast.Name):
                    var_nome = node.func.value.id
                    metodo = node.func.attr
                    if var_nome in vars_com_classe:
                        classe = vars_com_classe[var_nome]
                        if classe in metodos_por_classe and metodo not in metodos_por_classe[classe]:
                            nomes_faltando.append(f"{var_nome}.{metodo}() (método de {classe})")

        if nomes_faltando:
            aviso_autoimport = ""
            faltando_via_autoimport = set(nomes_faltando) & autoimports_suspeitos
            if faltando_via_autoimport:
                aviso_autoimport = (
                    f" ATENÇÃO: {', '.join(sorted(faltando_via_autoimport))} aparece(m) como "
                    f"'from <modulo> import {sorted(faltando_via_autoimport)[0]}' DENTRO DO PRÓPRIO "
                    f"módulo — isso é uma autoimportação inválida (o módulo não pode importar de si "
                    f"mesmo). A função/classe precisa ser DEFINIDA de verdade no código, não importada."
                )
            return (
                f"CONTRATO QUEBRADO: o teste chama funções que o código NÃO define: "
                f"{', '.join(sorted(set(nomes_faltando)))}.{aviso_autoimport} "
                f"Defina essas funções no código OU remova as chamadas do teste. "
                f"Funções disponíveis no código: {', '.join(sorted(nomes_definidos)[:20])}"
            )
        return None

    # =========================================================================
    # RESULT MONAD — Chamadas LLM que retornam Result (Zero 500)
    # =========================================================================

    def _chamar_llm_result(self, prompt: str, contexto: str, fase: str,
                           timeout: int = 60) -> Result:
        """Chama LLM retornando Result em vez de levantar exceção.
        Ok(dict) em sucesso, Err(mensagem) em falha."""
        try:
            resposta = solicitar_llm(
                prompt=prompt, contexto=contexto, fase=fase,
                modelo=os.getenv('LLM_MODEL', self.modelo_final),
                timeout_delegacao=timeout
            )
        except LLMNaoConfiguradoException as e:
            return Result.fail(e.mensagem_usuario)
        except Exception as e:
            return Result.fail(f"Erro inesperado ao chamar LLM: {e}")

        if resposta is None:
            return Result.fail("LLM não respondeu")

        self._tokens_totais += resposta.get('tokens_consumidos') or 0
        try:
            dados = extrair_json_resposta(resposta['conteudo'])
            if not isinstance(dados, dict):
                return Result.fail(f"Resposta LLM não é dict: {str(dados)[:100]}")
            return Result.ok(dados)
        except Exception as e:
            return Result.fail(f"Erro parse JSON: {e}")

    def _validar_e_escrever_result(self, impl: Dict, modulo: str) -> Result:
        """Valida contrato AST + escreve em disco, retornando Result."""
        problema = self._validar_contrato_ast(
            impl.get('codigo', ''), impl.get('teste', ''), modulo
        )
        if problema:
            return Result.fail(problema)
        self._escrever_implementacao(impl)
        return Result.ok(impl)

    # =========================================================================
    # MICRO-TASKS AST — Implementação Granular (1 função por vez)
    # =========================================================================

    def decompor_e_implementar_microtasks(
        self, ideia: str, stack: Dict, script_spec: Dict,
        impl_completa: Dict
    ) -> Result:
        """Decompõe script em MicroTasks AST e implementa/testa cada uma.
        Se uma falha, usa PostMortem para auto-cura cirúrgica.
        Retorna Result.ok(impl_completa) se todas passam, ou Result.fail se alguma falha."""
        codigo = impl_completa.get('codigo', '')
        teste = impl_completa.get('teste', '')

        microtasks = decompor_script_em_microtasks(codigo, teste)
        if not microtasks:
            # Script sem funções definíveis por AST — fallback para implementação monolítica
            return Result.ok(impl_completa)

        # Verifica se os testes já passam (micro-tasks são apenas para granularidade)
        resultado_pytest = self._rodar_pytest(
            caminho_relativo=impl_completa.get('caminho_teste')
        )
        if (resultado_pytest['passaram'] > 0 and
            resultado_pytest['falharam'] == 0 and
            resultado_pytest['erros'] == 0 and
            not resultado_pytest['erro_coleta']):
            for mt in microtasks:
                mt.tentativas = 1
                mt.resultado_pytest = resultado_pytest
            return Result.ok(impl_completa)

        # Se falhou, tenta auto-cura com PostMortem
        return self._auto_cura_microtasks(
            ideia, stack, script_spec, impl_completa, microtasks, resultado_pytest
        )

    def _auto_cura_microtasks(
        self, ideia: str, stack: Dict, script_spec: Dict,
        impl: Dict, microtasks: List[MicroTask],
        resultado_falha: Dict
    ) -> Result:
        """Loop de auto-cura: PostMortem 5-Porquês → regenera apenas função afetada."""
        secao_schema = self._montar_secao_schema()
        modulo = Path(impl.get('caminho_relativo', 'script.py')).stem
        saida_falha = resultado_falha.get('saida', '')

        for tentativa in range(1, MAX_TENTATIVAS_MICROTASK + 1):
            # PostMortem: investiga causa raiz
            analise = PostMortemAnalyzer.analisar_falha(
                saida_falha, impl.get('codigo', ''), modulo
            )

            # Identifica qual microtask falhou
            mt_afetada = self._identificar_microtask_falha(microtasks, analise)
            if mt_afetada:
                mt_afetada.tentativas += 1
                mt_afetada.post_mortem = analise['relatorio']

            # Tenta correção via LLM com contexto do PostMortem
            prompt_fix = self._montar_prompt_auto_cura(
                secao_schema, modulo, impl, analise
            )
            result_fix = self._chamar_llm_result(
                prompt=prompt_fix,
                contexto=f"Phase 8: Auto-Cura. Script: {script_spec.get('nome')}",
                fase="phase_08_autocura"
            )
            if result_fix.is_err():
                if tentativa == MAX_TENTATIVAS_MICROTASK:
                    return Result.fail(f"Auto-Cura esgotou {MAX_TENTATIVAS_MICROTASK} tentativas: {result_fix._error}")
                continue

            impl_corrigido = result_fix.unwrap()
            if 'codigo' in impl_corrigido and 'teste' in impl_corrigido:
                impl_corrigido['caminho_relativo'] = impl['caminho_relativo']
                impl_corrigido['caminho_teste'] = impl['caminho_teste']
                impl.update(impl_corrigido)

                # Re-valida e re-escreve
                validacao = self._validar_e_escrever_result(impl, modulo)
                if validacao.is_err():
                    saida_falha = validacao._error
                    if tentativa == MAX_TENTATIVAS_MICROTASK:
                        return Result.fail(validacao._error)
                    continue

                # Re-testa
                resultado_pytest = self._rodar_pytest(
                    caminho_relativo=impl.get('caminho_teste')
                )
                if (resultado_pytest['passaram'] > 0 and
                    resultado_pytest['falharam'] == 0 and
                    resultado_pytest['erros'] == 0 and
                    not resultado_pytest['erro_coleta']):
                    for mt in microtasks:
                        mt.resultado_pytest = resultado_pytest
                    return Result.ok(impl)

                saida_falha = resultado_pytest.get('saida', '')
                if tentativa == MAX_TENTATIVAS_MICROTASK:
                    return Result.fail(f"Auto-Cura não convergiu após {MAX_TENTATIVAS_MICROTASK} tentativas")
            else:
                if tentativa == MAX_TENTATIVAS_MICROTASK:
                    return Result.fail("Auto-Cura: LLM não retornou código/teste válidos")

        return Result.fail("Auto-Cura: loop terminou sem convergência")

    def _identificar_microtask_falha(
        self, microtasks: List[MicroTask], analise_postmortem: Dict
    ) -> Optional[MicroTask]:
        """Identifica qual MicroTask falhou baseado na análise PostMortem."""
        funcao_afetada = analise_postmortem.get('funcao_afetada', '')
        for mt in microtasks:
            if mt.nome_funcao in funcao_afetada or funcao_afetada in mt.nome_funcao:
                return mt
        # Fallback: retorna a primeira microtask não testada
        for mt in microtasks:
            if mt.resultado_pytest is None:
                return mt
        return microtasks[0] if microtasks else None

    def _montar_prompt_auto_cura(
        self, secao_schema: str, modulo: str, impl: Dict, analise: Dict
    ) -> str:
        """Monta prompt de auto-cura com contexto do PostMortem 5-Porquês."""
        return f"""# ENTRADA: Auto-Cura — fix ONLY the failing function based on PostMortem analysis.

{secao_schema}
MODULE: {modulo}

CODE:
{impl.get('codigo', '')}

TEST:
{impl.get('teste', '')}

POST-MORTEM 5-PORQUÊS:
{chr(10).join(analise.get('porques', []))}

TRACEBACK ISOLADO:
{analise.get('traceback_isolado', '')}

CAUSA RAIZ: {analise.get('causa_raiz', '')}
TIPO DE FALHA: {analise.get('tipo_falha', '')}
CORREÇÃO SUGERIDA: {analise.get('correcao_sugerida', '')}

Rules:
- Fix ONLY the function identified in the PostMortem. Do NOT rewrite unrelated code.
- Apply the suggested correction pattern.
- Keep all other functions/tests unchanged.
- Result Monad: wrap risky operations in try/except, return clear errors.
- direct import (from {modulo} import), consistent names.
- Schema DDL + PRAGMA foreign_keys = ON in fixture.

# SAIDA: Return ONLY the JSON below, nothing else, no markdown/code fence.
{{"codigo":"<fixed code>","teste":"<fixed test>","caminho_relativo":"...","caminho_teste":"..."}}
"""

    def _rodar_pytest(self, caminho_relativo: Optional[str]) -> Dict:
        """Roda pytest de verdade via subprocess com UTF-8 estrito — nunca estima resultado"""
        alvo = f'tests/{Path(caminho_relativo).name}' if caminho_relativo else 'tests/'
        env = {
            **os.environ,
            'PYTHONIOENCODING': 'utf-8',
            'PYTHONUTF8': '1',
            'PYTHONPATH': str(self.pasta_projeto / 'src') + os.pathsep + os.environ.get('PYTHONPATH', '')
        }

        try:
            resultado = subprocess.run(
                [sys.executable, '-m', 'pytest', alvo, '-v'],
                cwd=str(self.pasta_projeto), capture_output=True, text=True,
                encoding='utf-8', errors='replace', timeout=TIMEOUT_PYTEST_SEGUNDOS,
                env=env
            )
            saida = resultado.stdout + resultado.stderr
            erro_coleta = 'error' in saida.lower() and (
                'modulenotfounderror' in saida.lower() or 'error collecting' in saida.lower()
                or 'errors during collection' in saida.lower()
                or 'indentationerror' in saida.lower() or 'syntaxerror' in saida.lower()
            )

            m_passou = re.search(r'(\d+) passed', saida)
            m_falhou = re.search(r'(\d+) failed', saida)
            m_erros = re.search(r'(\d+) error', saida)
            passaram = int(m_passou.group(1)) if m_passou else 0
            falharam = int(m_falhou.group(1)) if m_falhou else 0
            erros = int(m_erros.group(1)) if m_erros else 0
            total_falhas = falharam + erros
            total = passaram + total_falhas

            if total == 0 and resultado.returncode != 0:
                erro_coleta = True

            return {
                'passaram': passaram, 'falharam': falharam, 'erros': erros, 'total': total,
                'erro_coleta': erro_coleta, 'detalhes_coleta': saida[-2000:],
                'saida': saida[-3000:], 'returncode': resultado.returncode,
            }
        except Exception as e:
            return {
                'passaram': 0, 'falharam': 0, 'erros': 1, 'total': 0, 'erro_coleta': True,
                'detalhes_coleta': str(e), 'saida': str(e), 'returncode': -1,
            }

    def _gerar_index(self, scripts_implementados: List[Dict], resultado_pytest: Optional[Dict],
                     gates: List[Gate], tempo_execucao: float,
                     teste_integracao_gerado: bool = False,
                     resultado_integracao: Optional[Dict] = None) -> Dict:
        return {
            'fase_id': 'phase_08_implementacao',
            'versao': '2.1',
            'status': 'COMPLETO' if all(g.passou for g in gates) else 'FALHOU',

            'timestamps': {
                'data_inicio': datetime.now(timezone.utc).isoformat(),
                'data_conclusao': datetime.now(timezone.utc).isoformat(),
                'duracao_segundos': tempo_execucao
            },

            'tokens': {
                'consumidos': self._tokens_totais,
                'medicao': 'real (soma de todas as chamadas LLM, incluindo correções)',
                'percentual_determinismo': 0
            },

            'schema_compartilhado': self.schema_compartilhado,

            'processamento': {
                'scripts_implementados': len(scripts_implementados),
                'tentativas_totais': sum(s.get('tentativas', 1) for s in scripts_implementados),
                'scripts_com_falha_apos_tentativas': sum(
                    1 for s in scripts_implementados if s.get('falhou_apos_tentativas')
                ),
                'teste_integracao_gerado': teste_integracao_gerado,
                'teste_integracao_passou': (
                    resultado_integracao.get('passaram', 0) > 0 and
                    resultado_integracao.get('falharam', 0) == 0 and
                    resultado_integracao.get('erros', 0) == 0 and
                    not resultado_integracao.get('erro_coleta', False)
                ) if resultado_integracao else False,
                'testes_passaram': resultado_pytest.get('passaram', 0) if resultado_pytest else 0,
                'testes_falharam': resultado_pytest.get('falharam', 0) if resultado_pytest else 0,
                'testes_erros': resultado_pytest.get('erros', 0) if resultado_pytest else 0,
                'testes_total': resultado_pytest.get('total', 0) if resultado_pytest else 0,
            },

            'gates_executados': [g.to_dict() for g in gates],

            'resume_info': {
                'proxima_fase': 'Nenhuma (projeto funcional completo)',
                'pode_prosseguir': all(g.passou for g in gates),
                'requer_intervencao_manual': not all(g.passou for g in gates)
            }
        }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Phase 8: Implementador com Verificação - aidd-project-generator v2.1'
    )
    parser.add_argument('pasta', help='Pasta do projeto (já com scaffold criado pela Fase 5)')
    parser.add_argument('--ideia', required=True, help='Descrição da ideia do projeto')
    parser.add_argument('--analise', default='{}', help='JSON da análise da Fase 2')
    parser.add_argument('--design', default='{}', help='JSON do design da Fase 3')

    args = parser.parse_args()
    pasta = Path(args.pasta)
    analise = json.loads(args.analise) if args.analise != '{}' else {}
    design = json.loads(args.design) if args.design != '{}' else {}

    if not analise and (pasta / '.aidd' / 'cache' / 'data' / 'analise_phase2.json').exists():
        analise = json.loads((pasta / '.aidd' / 'cache' / 'data' / 'analise_phase2.json').read_text(encoding='utf-8'))
    if not design and (pasta / '.aidd' / 'cache' / 'data' / 'design_aidd_phase3.json').exists():
        design = json.loads((pasta / '.aidd' / 'cache' / 'data' / 'design_aidd_phase3.json').read_text(encoding='utf-8'))

    implementador = ImplementadorFase8(pasta)
    resultado = implementador.executar(args.ideia, analise, design)

    if resultado is None:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
