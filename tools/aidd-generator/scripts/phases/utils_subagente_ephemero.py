#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UTILS: Context-Purge Engine — Subagentes Efêmeros com Descarte Imediato
aidd-project-generator v2.1

Separa Mecânica Determinística (Zero Token) de Cognição Descartável:
- Detecta necessidade de cognição (gerar código, sintetizar lógica)
- Instancia Subagente Efêmero com prompt limpo (~1000 tokens)
- Subagente gera artefato e salva no disco
- Orquestrador valida via AST e DESTRÓI imediatamente a sessão
- Ganho: Zero acúmulo de memória entre fases

Uso:
    from utils_subagente_ephemero import SubagenteEphemero, ContextPurgeEngine

    engine = ContextPurgeEngine()
    resultado = engine.executar_subagente(
        prompt="Implemente...",
        contexto="Phase 8: script habit_service.py",
        fase="phase_08",
        validador_fn=lambda code: ast.parse(code) is not None,
    )
    # resultado.conteudo disponível; contexto do subagente já foi descartado
"""

import sys
import os
import ast
import json
import uuid
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable, List

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))
from utils_delegacao import solicitar_llm, extrair_json_resposta


# =============================================================================
# DATA CLASSES — Estruturas de resultado
# =============================================================================

@dataclass
class ResultadoSubagente:
    """Resultado de uma execução efêmera de subagente."""
    id: str
    conteudo: Optional[str] = None
    dados_parseados: Optional[Dict[str, Any]] = None
    sucesso: bool = False
    erro: Optional[str] = None
    tokens_consumidos: int = 0
    modelo_usado: str = "desconhecido"
    duracao_segundos: float = 0.0
    tentativas: int = 0
    validacao_passou: bool = False
    validacao_detalhes: str = ""
    timestamp_inicio: str = ""
    timestamp_fim: str = ""
    contexto_purgado: bool = False  # Confirma que o contexto foi descartado

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'sucesso': self.sucesso,
            'erro': self.erro,
            'tokens_consumidos': self.tokens_consumidos,
            'modelo_usado': self.modelo_usado,
            'duracao_segundos': round(self.duracao_segundos, 2),
            'tentativas': self.tentativas,
            'validacao_passou': self.validacao_passou,
            'validacao_detalhes': self.validacao_detalhes,
            'contexto_purgado': self.contexto_purgado,
            'timestamp_inicio': self.timestamp_inicio,
            'timestamp_fim': self.timestamp_fim,
        }


@dataclass
class MetricasPurge:
    """Métricas acumuladas do engine de descarte."""
    total_subagentes_criados: int = 0
    total_subagentes_bem_sucedidos: int = 0
    total_subagentes_falharam: int = 0
    total_tokens_consumidos: int = 0
    total_contextos_purgados: int = 0
    total_duracao_segundos: float = 0.0
    historico: List[Dict[str, Any]] = field(default_factory=list)

    def registrar(self, resultado: ResultadoSubagente):
        self.total_subagentes_criados += 1
        if resultado.sucesso:
            self.total_subagentes_bem_sucedidos += 1
        else:
            self.total_subagentes_falharam += 1
        self.total_tokens_consumidos += resultado.tokens_consumidos
        if resultado.contexto_purgado:
            self.total_contextos_purgados += 1
        self.total_duracao_segundos += resultado.duracao_segundos
        self.historico.append(resultado.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_subagentes_criados': self.total_subagentes_criados,
            'total_bem_sucedidos': self.total_subagentes_bem_sucedidos,
            'total_falharam': self.total_subagentes_falharam,
            'total_tokens_consumidos': self.total_tokens_consumidos,
            'total_contextos_purgados': self.total_contextos_purgados,
            'total_duracao_segundos': round(self.total_duracao_segundos, 2),
            'taxa_sucesso': round(
                self.total_subagentes_bem_sucedidos / max(self.total_subagentes_criados, 1) * 100, 1
            ),
        }


# =============================================================================
# VALIDADORES MECÂNICOS (Zero Token)
# =============================================================================

def validar_ast_python(codigo: str) -> tuple[bool, str]:
    """Valida se o código Python é sintaticamente correto via AST parse."""
    if not codigo or not isinstance(codigo, str):
        return False, "Código vazio ou inválido"
    try:
        ast.parse(codigo)
        return True, "AST parse OK"
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} (linha {e.lineno})"


def validar_json_estruturado(texto: str) -> tuple[bool, str]:
    """Valida se a resposta contém JSON parseável com campos obrigatórios."""
    try:
        dados = extrair_json_resposta(texto)
        if not isinstance(dados, dict):
            return False, "Resposta não é um dict JSON"
        return True, f"JSON válido com {len(dados)} campos"
    except (ValueError, json.JSONDecodeError) as e:
        return False, f"JSON inválido: {e}"


def validar_codigo_com_campos_obrigatorios(codigo: str, campos: List[str]) -> tuple[bool, str]:
    """Valida que o código contém definições para todos os campos obrigatórios."""
    if not codigo:
        return False, "Código vazio"
    ast_ok, ast_msg = validar_ast_python(codigo)
    if not ast_ok:
        return False, ast_msg

    tree = ast.parse(codigo)
    nomes_definidos = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nomes_definidos.add(node.name)
        elif isinstance(node, ast.ClassDef):
            nomes_definidos.add(node.name)

    faltando = [c for c in campos if c not in nomes_definidos]
    if faltando:
        return False, f"Definições ausentes: {faltando}"
    return True, f"Todas as {len(campos)} definições encontradas"


def validar_teste_pytest(codigo_teste: str) -> tuple[bool, str]:
    """Valida que o código de teste é pytest-válido (AST + tem test_ functions)."""
    if not codigo_teste:
        return False, "Código de teste vazio"
    ast_ok, ast_msg = validar_ast_python(codigo_teste)
    if not ast_ok:
        return False, ast_msg

    tree = ast.parse(codigo_teste)
    test_functions = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')
    ]
    if not test_functions:
        return False, "Nenhuma função test_* encontrada no teste"
    return True, f"{len(test_functions)} função(ões) de teste encontrada(s)"


# =============================================================================
# CONTEXT-PURGE ENGINE
# =============================================================================

class SubagenteEphemero:
    """
    Subagente que existe apenas para UMA tarefa cognitiva.
    Após gerar o artefato, seu contexto é descartado imediatamente.

    Ciclo de vida:
    1. __init__ com prompt limpo (~1000 tokens)
    2. executar() → chama LLM, valida resultado
    3. purgar_contexto() → limpa referências internas
    4. Resultado devolvido ao orquestrador; subagente pode ser deletado
    """

    def __init__(self, prompt: str, contexto: str, fase: str,
                 validador_fn: Optional[Callable] = None,
                 modelo: Optional[str] = None,
                 max_tentativas: int = 3):
        self.id = str(uuid.uuid4())[:8]
        self.prompt = prompt
        self.contexto = contexto
        self.fase = fase
        self.validador_fn = validador_fn
        self.modelo = modelo
        self.max_tentativas = max_tentativas
        self._resultado: Optional[ResultadoSubagente] = None
        self._purgado = False

    def executar(self) -> ResultadoSubagente:
        """Executa o subagente: chama LLM, valida, retorna resultado."""
        t0 = time.time()
        timestamp_inicio = datetime.now(timezone.utc).isoformat()

        resultado = ResultadoSubagente(
            id=self.id,
            timestamp_inicio=timestamp_inicio,
        )

        tokens_acumulados = 0
        ultimo_erro = None

        for tentativa in range(1, self.max_tentativas + 1):
            resultado.tentativas = tentativa

            # Prompt enriquecido com erro da tentativa anterior (se houver)
            prompt_tentativa = self.prompt
            if ultimo_erro:
                prompt_tentativa += f"\n\nTENTATIVA ANTERIOR FALHOU:\n{ultimo_erro}\nCorrija e tente novamente."

            try:
                resposta = solicitar_llm(
                    prompt=prompt_tentativa,
                    contexto=self.contexto,
                    fase=self.fase,
                    modelo=self.modelo,
                )

                if resposta is None:
                    ultimo_erro = "LLM não respondeu (timeout ou erro de conexão)"
                    continue

                conteudo = resposta.get('conteudo', '')
                tokens = resposta.get('tokens_consumidos', 0) or 0
                tokens_acumulados += tokens

                resultado.conteudo = conteudo
                resultado.modelo_usado = resposta.get('modelo_usado', 'desconhecido')

                # Tentar parsear JSON se aplicável
                try:
                    dados = extrair_json_resposta(conteudo)
                    resultado.dados_parseados = dados
                except (ValueError, json.JSONDecodeError):
                    resultado.dados_parseados = None

                # Validar (se validador fornecido)
                if self.validador_fn:
                    try:
                        if resultado.dados_parseados:
                            valido, detalhes = self.validador_fn(resultado.dados_parseados)
                        else:
                            valido, detalhes = self.validador_fn(conteudo)
                        resultado.validacao_passou = valido
                        resultado.validacao_detalhes = detalhes

                        if valido:
                            resultado.sucesso = True
                            break
                        else:
                            ultimo_erro = f"Validação falhou: {detalhes}"
                    except Exception as e:
                        ultimo_erro = f"Erro no validador: {type(e).__name__}: {e}"
                else:
                    resultado.sucesso = bool(conteudo)
                    resultado.validacao_passou = True
                    resultado.validacao_detalhes = "Sem validador — conteúdo presente"
                    if resultado.sucesso:
                        break

            except Exception as e:
                ultimo_erro = f"Exceção: {type(e).__name__}: {e}"

        resultado.tokens_consumidos = tokens_acumulados
        resultado.duracao_segundos = time.time() - t0
        resultado.timestamp_fim = datetime.now(timezone.utc).isoformat()
        resultado.erro = ultimo_erro if not resultado.sucesso else None

        # PURGAR CONTEXTO IMEDIATAMENTE após execução
        self.purgar_contexto()
        resultado.contexto_purgado = True

        self._resultado = resultado
        return resultado

    def purgar_contexto(self):
        """Destrói referências internas — contexto do subagente vai para o GC."""
        if not self._purgado:
            self.prompt = None
            self.contexto = None
            self._purgado = True

    @property
    def resultado(self) -> Optional[ResultadoSubagente]:
        return self._resultado

    @property
    def contexto_purgado(self) -> bool:
        return self._purgado


class ContextPurgeEngine:
    """
    Motor de subagentes efêmeros com descarte imediato de contexto.

    Responsabilidades:
    1. Criar subagentes efêmeros com prompts limpos e isolados
    2. Executar e validar cada subagente
    3. Purgar contexto imediatamente após cada execução
    4. Acumular métricas de uso (tokens, tempo, sucesso/falha)
    5. Persistir métricas em disco para rastreabilidade

    Uso típico:
        engine = ContextPurgeEngine(pasta_cache=Path('.aidd/cache'))

        # Subagente para gerar código
        resultado = engine.executar_subagente(
            prompt="Implemente o serviço...",
            contexto="Phase 8: habit_service.py",
            fase="phase_08",
            validador_fn=validar_ast_python,
        )

        # Subagente para gerar schema
        resultado_schema = engine.executar_subagente(
            prompt="Defina o schema...",
            contexto="Phase 8: schema DDL",
            fase="phase_08_schema",
            validador_fn=validar_json_estruturado,
        )

        # Métricas acumuladas
        engine.persistir_metricas()
    """

    def __init__(self, pasta_cache: Optional[Path] = None):
        self.pasta_cache = pasta_cache or Path('.aidd/cache')
        self.metricas = MetricasPurge()
        self._resultados: List[ResultadoSubagente] = []

    def executar_subagente(
        self,
        prompt: str,
        contexto: str,
        fase: str,
        validador_fn: Optional[Callable] = None,
        modelo: Optional[str] = None,
        max_tentativas: int = 3,
        descricao: str = "",
    ) -> ResultadoSubagente:
        """
        Cria, executa e purga um subagente efêmero.

        Args:
            prompt: Prompt limpo para o subagente (~1000 tokens ideal)
            contexto: Contexto executivo (ex: "Phase 8: script X")
            fase: ID da fase (para logs e métricas)
            validador_fn: Função de validação mecânica (Zero Token)
                         Assinatura: (conteudo) -> (bool, str)
            modelo: Modelo a usar (None = auto-detectar)
            max_tentativas: Máximo de tentativas com correção
            descricao: Descrição legível para logs

        Returns:
            ResultadoSubagente com conteudo, sucesso, métricas
        """
        desc = descricao or contexto
        print(f"\n   ⚡ Subagente Efêmero: {desc}")
        print(f"      ID: {str(uuid.uuid4())[:8]}")
        print(f"      Prompt: ~{len(prompt)} chars")

        subagente = SubagenteEphemero(
            prompt=prompt,
            contexto=contexto,
            fase=fase,
            validador_fn=validador_fn,
            modelo=modelo,
            max_tentativas=max_tentativas,
        )

        resultado = subagente.executar()

        # Registrar métricas
        self.metricas.registrar(resultado)
        self._resultados.append(resultado)

        # Log de resultado
        if resultado.sucesso:
            print(f"      ✓ Sucesso ({resultado.tentativas} tentativa(s), "
                  f"{resultado.tokens_consumidos} tokens, "
                  f"{resultado.duracao_segundos:.1f}s)")
        else:
            print(f"      ✗ Falhou ({resultado.tentativas} tentativa(s), "
                  f"erro: {resultado.erro})")

        # Confirmar descarte
        print(f"      🗑️  Contexto purgado: {subagente.contexto_purgado}")

        return resultado

    def executar_lote_paralelo(
        self,
        tarefas: List[Dict[str, Any]],
        max_workers: int = 5,
    ) -> List[ResultadoSubagente]:
        """
        Executa múltiplos subagentes em paralelo (ThreadPoolExecutor).
        Cada tarefa é um dict com: prompt, contexto, fase, validador_fn, descricao.

        Todos os contextos são purgados imediatamente após cada execução.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        print(f"\n   ⚡ Lote Paralelo: {len(tarefas)} subagentes efêmeros (max_workers={max_workers})")

        resultados = []

        def _executar_tarefa(tarefa):
            subagente = SubagenteEphemero(
                prompt=tarefa['prompt'],
                contexto=tarefa['contexto'],
                fase=tarefa.get('fase', 'batch'),
                validador_fn=tarefa.get('validador_fn'),
                modelo=tarefa.get('modelo'),
                max_tentativas=tarefa.get('max_tentativas', 3),
            )
            return subagente.executar()

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_executar_tarefa, t): t.get('descricao', t['contexto'])
                for t in tarefas
            }

            for future in as_completed(futures):
                desc = futures[future]
                try:
                    resultado = future.result()
                    self.metricas.registrar(resultado)
                    self._resultados.append(resultado)
                    resultados.append(resultado)

                    status = "✓" if resultado.sucesso else "✗"
                    print(f"      {status} {desc}: {resultado.tokens_consumidos} tokens, "
                          f"contexto purgado={resultado.contexto_purgado}")
                except Exception as e:
                    print(f"      ✗ {desc}: exceção — {e}")

        return resultados

    def persistir_metricas(self, nome_arquivo: str = '_context_purge_metrics.json'):
        """Persiste métricas acumuladas em disco para rastreabilidade."""
        caminho = self.pasta_cache / 'data' / nome_arquivo
        caminho.parent.mkdir(parents=True, exist_ok=True)

        dados = {
            'engine': 'ContextPurgeEngine',
            'versao': '2.1',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metricas': self.metricas.to_dict(),
            'historico': self.metricas.historico,
        }

        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)

        print(f"\n   📊 Métricas do Context-Purge salvas: {caminho}")
        return caminho

    @property
    def tokens_totais(self) -> int:
        return self.metricas.total_tokens_consumidos

    @property
    def taxa_sucesso(self) -> float:
        total = self.metricas.total_subagentes_criados
        if total == 0:
            return 0.0
        return self.metricas.total_subagentes_bem_sucedidos / total * 100


# =============================================================================
# HELPERS DE PROMPT — Templates enxutos para subagentes efêmeros
# =============================================================================

def construir_prompt_ephemero(
    tarefa: str,
    regras: List[str],
    formato_saida: str,
    contexto_minimo: Optional[str] = None,
) -> str:
    """
    Constrói um prompt enxuto para subagente efêmero (~1000 tokens).
    Elimina redundância e foca no essencial.

    Args:
        tarefa: Descrição da tarefa (1-2 frases)
        regras: Lista de regras obrigatórias (bullet points)
        formato_saida: Descrição do formato JSON esperado
        contexto_minimo: Contexto essencial (schema, stack, etc.)
    """
    partes = [tarefa]

    if contexto_minimo:
        partes.append(f"\nCONTEXTO:\n{contexto_minimo}")

    if regras:
        partes.append("\nREGRAS:")
        for i, regra in enumerate(regras, 1):
            partes.append(f"{i}. {regra}")

    partes.append(f"\nSAÍDA: {formato_saida}")

    return "\n".join(partes)


def prompt_codigo_ephemero(nome_script: str, responsabilidade: str,
                            pseudocodigo: str, schema: str = "",
                            stack: str = "") -> str:
    """Prompt enxuto para gerar um script Python via subagente efêmero."""
    contexto = ""
    if schema:
        contexto += f"SCHEMA:\n{schema}\n"
    if stack:
        contexto += f"STACK: {stack}\n"

    return construir_prompt_ephemero(
        tarefa=f"Implemente {nome_script}: {responsabilidade}",
        regras=[
            "Código real, funcional, sem TODO/pass",
            "Teste pytest completo (test_*), import direto",
            "CONTRATO: teste só chama funções que código define",
            "SQLite: PRAGMA foreign_keys=ON, valide FK antes de INSERT",
            "Saída: APENAS JSON, sem markdown/code fence",
        ],
        formato_saida='{"codigo":"...","teste":"...","caminho_relativo":"...","caminho_teste":"..."}',
        contexto_minimo=contexto + f"\nPSEUDOCÓDIGO:\n{pseudocodigo}",
    )


def prompt_schema_ephemero(ideia: str, stack: str, scripts_info: str) -> str:
    """Prompt enxuto para gerar schema DDL via subagente efêmero."""
    return construir_prompt_ephemero(
        tarefa=f"Defina o SCHEMA SQLite DDL unificado para: {ideia}",
        regras=[
            "CREATE TABLE IF NOT EXISTS, todas as tabelas/colunas/PK/FK",
            "Nomes autoexplicativos, idempotente em SQLite",
            "Saída: APENAS JSON, sem markdown/code fence",
        ],
        formato_saida='{"schema_sql":"<DDL completo>","tabelas":["t1","t2"]}',
        contexto_minimo=f"STACK: {stack}\nSCRIPTS:\n{scripts_info}",
    )


def prompt_correcao_ephemero(modulo: str, codigo: str, teste: str,
                              erro: str, schema: str = "") -> str:
    """Prompt enxuto para correção de código/teste com falha."""
    return construir_prompt_ephemero(
        tarefa=f"Corrija o código/teste que falhou no pytest para {modulo}",
        regras=[
            "Import direto (from modulo import)",
            "Schema DDL + PRAGMA foreign_keys=ON na fixture",
            "conn=None opcional, NUNCA conn.close() se recebido",
            ":memory: ou tmp_path (nunca os.remove)",
            "FK: valide existência antes de INSERT, retorne erro claro",
            "Saída: APENAS JSON, sem markdown/code fence",
        ],
        formato_saida='{"codigo":"...","teste":"...","caminho_relativo":"...","caminho_teste":"..."}',
        contexto_minimo=(
            f"{'SCHEMA: ' + schema + chr(10) if schema else ''}"
            f"CÓDIGO ATUAL:\n{codigo}\n\nTESTE ATUAL:\n{teste}\n\nERROS:\n{erro}"
        ),
    )


def prompt_integracao_ephemero(ideia: str, stack: str, scripts_info: str,
                                 schema: str = "") -> str:
    """Prompt enxuto para gerar teste de integração."""
    return construir_prompt_ephemero(
        tarefa=f"Gere teste de integração pytest encadeando scripts do projeto: {ideia}",
        regras=[
            "Encadeie funções: criar -> usar retorno -> executar ação -> validar estado",
            "Imports diretos, src/ no PYTHONPATH",
            "SQLite: :memory: ou tmp_path, PRAGMA foreign_keys=ON",
            "NUNCA subprocess.run nos testes",
            "CONTRATO: chame apenas funções que scripts definem",
            "Normalize tipos pós-JSON round-trip",
            "Saída: APENAS JSON, sem markdown/code fence",
        ],
        formato_saida='{"teste":"<código pytest completo>","caminho_teste":"test_integracao.py"}',
        contexto_minimo=(
            f"{'SCHEMA: ' + schema + chr(10) if schema else ''}"
            f"STACK: {stack}\nSCRIPTS:\n{scripts_info}"
        ),
    )


# =============================================================================
# TESTE RÁPIDO
# =============================================================================

if __name__ == '__main__':
    print("=== Context-Purge Engine — Teste Rápido ===\n")

    # Teste 1: Validadores mecânicos (Zero Token)
    print("1. Validadores mecânicos:")
    ok, msg = validar_ast_python("def foo(): return 42")
    print(f"   AST válido: {ok} — {msg}")

    ok, msg = validar_ast_python("def foo(: return 42")
    print(f"   AST inválido: {ok} — {msg}")

    ok, msg = validar_teste_pytest("def test_foo(): assert True")
    print(f"   Teste válido: {ok} — {msg}")

    ok, msg = validar_teste_pytest("def foo(): pass")
    print(f"   Sem test_*: {ok} — {msg}")

    # Teste 2: Construção de prompts enxutos
    print("\n2. Prompts efêmeros:")
    p = prompt_codigo_ephemero("habit_service.py", "CRUD de hábitos", "criar, listar, deletar")
    print(f"   Prompt código: ~{len(p)} chars (~{len(p)//4} tokens)")

    p = prompt_schema_ephemero("rastreador de hábitos", "Python+SQLite", "habit_service, cli")
    print(f"   Prompt schema: ~{len(p)} chars (~{len(p)//4} tokens)")

    # Teste 3: Engine sem LLM real (só estrutura)
    print("\n3. Engine (sem LLM real):")
    engine = ContextPurgeEngine()
    metricas = engine.metricas.to_dict()
    print(f"   Métricas iniciais: {metricas}")
    print(f"   Tokens totais: {engine.tokens_totais}")
    print(f"   Taxa sucesso: {engine.taxa_sucesso}%")

    print("\n✓ Todos os componentes do Context-Purge Engine OK")
