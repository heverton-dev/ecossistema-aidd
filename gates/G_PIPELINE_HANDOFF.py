#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_PIPELINE_HANDOFF (ISSUE-PIPE-0002)
=============================================================================
Portão determinístico de validação formal de manifestos de handoff de execução
da Tríade Canônica (pure, open, freedom) e Planos de Evolução.

Invariantes e Leis Auditadas:
  1. Determinismo First (Lei #1): Validação estrutural e contratual via JSON Schema
     Draft-7 e regras determinísticas em AST/Python puro.
  2. Saída Binária (Lei #2): exit 0 = 100% conforme; exit 1 = qualquer violação.
  3. Zero Stubs (Lei #5): Rejeição de TODO, FIXME, PLACEHOLDER, TBD, stub, dummy,
     alvos vazios ou comandos de validação triviais.
  4. Resolução de Alvos: Todo arquivo_alvo deve existir ou possuir diretório pai
     válido e resolvível.
  5. Integridade de Gates: Todo Quality Gate referenciado nas barreiras de sincronização
     deve obrigatoriamente existir no repositório.
  6. Prova que Morde (Lei #13): Acompanhado de suíte automatizada test_g_pipeline_handoff.py
     provando reprovação estrita em cenários deliberadamente corrompidos.

Uso:
  python gates/G_PIPELINE_HANDOFF.py --manifesto <caminho_manifesto.json>
  python gates/G_PIPELINE_HANDOFF.py  # Modo auto-descoberta / auditoria de integridade
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
GATES_DIR = ROOT_DIR / "gates"
SPECS_DIR = ROOT_DIR / "componentes" / "compartilhado" / "specs"
SCHEMA_CANONICO = SPECS_DIR / "handoff-execucao.schema.json"

PADRAO_STUB = re.compile(r"(?i)\b(TODO|FIXME|PLACEHOLDER|TBD|stub|dummy)\b")
PADRAO_CMD_TRIVIAL = re.compile(r"^\s*(exit\s+0|echo\s+ok|true|pass)\s*$", re.IGNORECASE)


def carregar_schema() -> Dict[str, Any]:
    """Carrega o JSON Schema canônico de handoff de execução."""
    if not SCHEMA_CANONICO.is_file():
        raise FileNotFoundError(f"Schema canônico não encontrado em: {SCHEMA_CANONICO}")
    with open(SCHEMA_CANONICO, "r", encoding="utf-8") as f:
        return json.load(f)


def validar_contra_schema(manifesto_dados: Dict[str, Any], schema_dados: Dict[str, Any]) -> List[str]:
    """Valida o manifesto contra o JSON schema usando jsonschema."""
    erros: List[str] = []
    try:
        import jsonschema
        validator = jsonschema.Draft7Validator(schema_dados)
        for err in validator.iter_errors(manifesto_dados):
            caminho = " -> ".join(str(p) for p in err.absolute_path) or "raiz"
            erros.append(f"Erro no schema em [{caminho}]: {err.message}")
    except ImportError:
        erros.append("Biblioteca 'jsonschema' não instalada no ambiente Python.")
    return erros


def verificar_stubs_recursivo(obj: Any, caminho: str = "") -> List[str]:
    """Verifica recursivamente a presença de stubs ou placeholders em valores de texto."""
    violacoes: List[str] = []
    if isinstance(obj, str):
        if PADRAO_STUB.search(obj):
            violacoes.append(f"Stub ou placeholder proibido em [{caminho}]: '{obj}'")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            novo_caminho = f"{caminho}.{k}" if caminho else str(k)
            violacoes.extend(verificar_stubs_recursivo(v, novo_caminho))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            novo_caminho = f"{caminho}[{idx}]"
            violacoes.extend(verificar_stubs_recursivo(item, novo_caminho))
    return violacoes


def validar_arquivos_alvo(tickets: List[Dict[str, Any]], base_repo: Path) -> List[str]:
    """Valida se os arquivos alvo existem ou possuem diretório pai resolvível."""
    erros: List[str] = []
    for t in tickets:
        tid = t.get("id", "sem-id")
        alvos = t.get("arquivos_alvo") or t.get("target_files") or []
        if not alvos:
            erros.append(f"Ticket [{tid}]: Lista de arquivos alvo vazia ou não informada.")
            continue

        for alvo in alvos:
            if not isinstance(alvo, str) or not alvo.strip():
                erros.append(f"Ticket [{tid}]: Arquivo alvo inválido ou em branco.")
                continue

            alvo_path = Path(alvo.strip())
            # Se for caminho relativo, resolve a partir de base_repo
            caminho_resolvido = alvo_path if alvo_path.is_absolute() else (base_repo / alvo_path)

            if caminho_resolvido.exists():
                continue  # Arquivo já existe, conforme

            # Se não existe ainda, o diretório pai deve existir
            parent_dir = caminho_resolvido.parent
            if not parent_dir.exists():
                erros.append(
                    f"Ticket [{tid}]: Arquivo alvo '{alvo}' não existe e seu diretório pai "
                    f"'{parent_dir}' não é resolvível/existente."
                )
    return erros


def validar_barreira_gates(barreiras: List[str], base_repo: Path) -> List[str]:
    """Verifica se os Quality Gates referenciados nas barreiras de sincronização existem."""
    erros: List[str] = []
    for gate_ref in barreiras:
        if not isinstance(gate_ref, str) or not gate_ref.strip():
            erros.append("Barreira de sincronização contém entrada vazia ou inválida.")
            continue

        item = gate_ref.strip()
        partes_cmd = shlex.split(item, posix=(os.name != "nt"))
        if not partes_cmd:
            erros.append("Comando de barreira de sincronização vazio.")
            continue

        # Verifica se referencia diretamente um arquivo de gate em gates/
        for parte_cmd in partes_cmd:
            if parte_cmd.endswith(".py"):
                # Testa se é arquivo existente
                p1 = Path(parte_cmd)
                p2 = base_repo / parte_cmd
                p3 = GATES_DIR / parte_cmd
                p4 = GATES_DIR / Path(parte_cmd).name
                if p1.is_file() or p2.is_file() or p3.is_file() or p4.is_file():
                    break
                else:
                    erros.append(
                        f"Gate ou script referenciado na barreira não foi encontrado: '{parte_cmd}'"
                    )
                    break
            elif parte_cmd == "ecossistema.py":
                if not (base_repo / "ecossistema.py").is_file():
                    erros.append(f"Script ecossistema.py referenciado não existe em {base_repo}")
                break
    return erros


def validar_comandos_validacao(tickets: List[Dict[str, Any]]) -> List[str]:
    """Valida que os comandos de validação não sejam vazios ou triviais."""
    erros: List[str] = []
    for t in tickets:
        tid = t.get("id", "sem-id")
        cmd = t.get("comando_validacao") or t.get("validation_gate") or ""
        if not isinstance(cmd, str) or not cmd.strip():
            erros.append(f"Ticket [{tid}]: Ausência de comando de validação determinístico.")
        elif PADRAO_CMD_TRIVIAL.match(cmd.strip()):
            erros.append(
                f"Ticket [{tid}]: Comando de validação trivial proibido (stub): '{cmd.strip()}'"
            )
    return erros


def auditar_manifesto(caminho_manifesto: Path) -> Tuple[bool, List[str]]:
    """Executa a bateria de auditoria determinística completa em um arquivo de manifesto."""
    erros: List[str] = []
    if not caminho_manifesto.is_file():
        return False, [f"Manifesto de handoff não encontrado: {caminho_manifesto}"]

    try:
        with open(caminho_manifesto, "r", encoding="utf-8") as f:
            manifesto = json.load(f)
    except json.JSONDecodeError as jde:
        return False, [f"Manifesto contém JSON malformado/inválido: {jde}"]
    except Exception as ex:
        return False, [f"Falha ao ler manifesto: {ex}"]

    # 1. Validação do Schema
    try:
        schema = carregar_schema()
        erros_schema = validar_contra_schema(manifesto, schema)
        erros.extend(erros_schema)
    except Exception as ex_schema:
        erros.append(f"Erro durante carregamento do schema: {ex_schema}")

    # Se já houver falha de schema básica, podemos acumular com as demais
    # 2. Verificação de Stubs e Placeholders
    erros.extend(verificar_stubs_recursivo(manifesto))

    # Identificar diretório base do repositório
    meta = manifesto.get("meta", {}) if isinstance(manifesto, dict) else {}
    repo_alvo = meta.get("repositorio_alvo") or meta.get("target_repository") or "."
    base_repo = ROOT_DIR if repo_alvo in (".", "ecossistema-aidd", "") else (ROOT_DIR / repo_alvo)
    if not base_repo.exists():
        # Fallback para ROOT_DIR se for caminho relativo inexistente
        base_repo = ROOT_DIR

    # 3. Coleta de tickets de todas as fases
    tickets: List[Dict[str, Any]] = []
    fase_paralela = (
        manifesto.get("fase_paralela_assincrona")
        or manifesto.get("parallel_async_steps")
        or []
    )
    if isinstance(fase_paralela, list):
        tickets.extend(fase_paralela)

    fase_sequencial = (
        manifesto.get("fase_sequencial_sincrona")
        or manifesto.get("sequential_sync_steps")
        or []
    )
    if isinstance(fase_sequencial, list):
        tickets.extend(fase_sequencial)

    # 4. Validação de arquivos alvo
    erros.extend(validar_arquivos_alvo(tickets, base_repo))

    # 5. Validação de comandos de validação
    erros.extend(validar_comandos_validacao(tickets))

    # 6. Validação de gates nas barreiras de sincronização
    barreiras = (
        manifesto.get("barreira_sincronizacao")
        or manifesto.get("join_barrier")
        or []
    )
    if isinstance(barreiras, list):
        erros.extend(validar_barreira_gates(barreiras, base_repo))

    return len(erros) == 0, erros


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="G_PIPELINE_HANDOFF: Validador formal de manifestos de handoff de execução."
    )
    parser.add_argument(
        "--manifesto",
        "--manifest",
        dest="manifesto",
        type=str,
        default=None,
        help="Caminho para o arquivo JSON de manifesto de handoff a validar.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 72)
    print(" ECOSSISTEMA AIDD — QUALITY GATE: G_PIPELINE_HANDOFF")
    print(" Validação Determinística de Handoff de Execução (Leis #1, #2, #5, #13)")
    print("=" * 72)

    alvo_manifesto: Optional[Path] = None
    if args.manifesto:
        alvo_manifesto = Path(args.manifesto).resolve()
    else:
        # Modo de auto-descoberta ou auditoria de rotina do ecossistema
        candidatos_padrao = [
            ROOT_DIR / ".aidd" / "handoff-execucao.json",
            ROOT_DIR / "handoff-execucao.json",
        ]
        for c in candidatos_padrao:
            if c.is_file():
                alvo_manifesto = c
                break

    if alvo_manifesto:
        print(f"Auditando manifesto: {alvo_manifesto}")
        conforme, erros = auditar_manifesto(alvo_manifesto)
        if not conforme:
            print("\n[FALHA] Violações detectadas no manifesto de handoff:")
            for e in erros:
                print(f"  - {e}")
            print("\n" + "=" * 72)
            print(" REGRA CANÔNICA VIOLADA (Leis #1, #2, #5):")
            print(" O manifesto de handoff deve cumprir estritamente handoff-execucao.schema.json,")
            print(" conter zero stubs, ter alvos resolvíveis e apontar gates existentes.")
            print("=" * 72)
            return 1
        print("[OK] Manifesto 100% conforme com handoff-execucao.schema.json e sem stubs.")
        print("=" * 72)
        return 0

    # Se nenhum manifesto ativo foi passado e nenhum arquivo de execução ativo em voo,
    # valida a integridade contínua do próprio schema canônico.
    print("[INFO] Nenhum manifesto de execução ativo em voo especificado.")
    print("Auditando integridade do schema canônico...")
    try:
        schema = carregar_schema()
        import jsonschema
        jsonschema.Draft7Validator.check_schema(schema)
        print("[OK] Schema canônico handoff-execucao.schema.json integro e aderente a Draft-7.")
        print("=" * 72)
        return 0
    except Exception as ex:
        print(f"[FALHA] Schema canônico corrompido: {ex}")
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
