#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_INJECT — Validação Mecânica do Injetor Universal de Componentes

Valida, de forma 100% determinística (zero LLM):
  1. O schema `schema_injector_request.json` é JSON válido e rejeita
     payloads incompletos/incorretos com erros estruturados.
  2. `profiles_registry` resolve os 5 tipos suportados para 'aidd-generator'.
  3. Um ciclo real de materialização (staging -> publicação) funciona.
  4. Um ciclo real de rollback (falha forçada a meio da publicação) não
     deixa nenhum arquivo órfão em disco.

Uso:
    python scripts/gates/G_INJECT.py
    python scripts/verificar_gates.py --apenas inject
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.core.injector.contrato import validar_request, carregar_schema, TIPOS_VALIDOS
from scripts.core.injector.profiles_registry import PROFILES, resolver_rota
from scripts.core.injector.materializador import materializar


def _checar_schema() -> bool:
    print("🔍 [1/4] Validando schema_injector_request.json...")
    try:
        schema = carregar_schema()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"   ❌ schema inválido/ilegível: {exc}")
        return False

    if schema.get("type") != "object" or "properties" not in schema:
        print("   ❌ schema não define um objeto com 'properties'")
        return False

    payload_bom = {
        "tipo": "skill",
        "nome": "auditoria-seguranca-dependencias",
        "descricao": "Audita dependencias do projeto em busca de vulnerabilidades conhecidas.",
    }
    resultado_bom = validar_request(payload_bom)
    if not resultado_bom.valido:
        print(f"   ❌ payload válido foi rejeitado: {resultado_bom.erros}")
        return False

    payloads_ruins = [
        {},
        {"tipo": "skill"},
        {"tipo": "tipo-inexistente", "nome": "x", "descricao": "descricao valida aqui"},
        {"tipo": "skill", "nome": "AB", "descricao": "descricao valida aqui"},
        {"tipo": "skill", "nome": "nome-valido", "descricao": "curta"},
    ]
    for payload_ruim in payloads_ruins:
        resultado_ruim = validar_request(payload_ruim)
        if resultado_ruim.valido or not resultado_ruim.erros:
            print(f"   ❌ payload incompleto foi aceito indevidamente: {payload_ruim}")
            return False

    print("   ✅ schema válido — payloads bons aceitos, ruins rejeitados com erros estruturados")
    return True


def _checar_profiles() -> bool:
    print("🔍 [2/4] Validando profiles_registry para 'aidd-generator'...")
    profile = PROFILES.get("aidd-generator")
    if profile is None:
        print("   ❌ profile 'aidd-generator' não encontrado")
        return False

    for tipo in TIPOS_VALIDOS:
        if tipo not in profile:
            print(f"   ❌ tipo '{tipo}' não mapeado no profile 'aidd-generator'")
            return False
        rota = resolver_rota("aidd-generator", tipo, "componente-teste")
        if not rota.dest:
            print(f"   ❌ rota vazia para tipo '{tipo}'")
            return False

    print(f"   ✅ profile 'aidd-generator' resolve todos os {len(TIPOS_VALIDOS)} tipos")
    return True


def _checar_materializacao_e_rollback() -> bool:
    print("🔍 [3/4] Validando materialização real (staging -> publicação)...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        arquivos = {
            "skills/gate-teste/SKILL.md": "# Skill de teste do gate G_INJECT\n",
            ".claude/skills/gate-teste/SKILL.md": "# Skill de teste do gate G_INJECT\n",
        }
        resultado = materializar(root, arquivos)
        if not resultado.sucesso:
            print(f"   ❌ materialização falhou inesperadamente: {resultado.erro}")
            return False
        for rel_path in arquivos:
            if not (root / rel_path).exists():
                print(f"   ❌ arquivo esperado não foi publicado: {rel_path}")
                return False
    print("   ✅ materialização real publicou todos os arquivos esperados")

    print("🔍 [4/4] Validando rollback (falha forçada a meio da publicação)...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        arquivos = {
            "skills/gate-rollback/SKILL.md": "# Skill A\n",
            "skills/gate-rollback/EXTRA.md": "# Skill B\n",
        }

        chamadas = {"n": 0}
        os_replace_original = __import__("os").replace

        def _replace_com_falha_na_segunda_chamada(src, dst):
            chamadas["n"] += 1
            if chamadas["n"] == 2:
                raise OSError("falha de I/O simulada para provar o rollback")
            return os_replace_original(src, dst)

        with mock.patch("scripts.core.injector.materializador.os.replace", side_effect=_replace_com_falha_na_segunda_chamada):
            resultado = materializar(root, arquivos)

        if resultado.sucesso:
            print("   ❌ materialização deveria ter falhado (falha simulada não propagou)")
            return False

        orfaos = list(root.rglob("*")) if root.exists() else []
        orfaos = [p for p in orfaos if p.is_file()]
        if orfaos:
            print(f"   ❌ arquivos órfãos encontrados após rollback: {orfaos}")
            return False

    print("   ✅ rollback removeu toda a transação — zero arquivos órfãos")
    return True


def executar_gate(pasta: Path = None) -> int:
    """Executa o gate completo. `pasta` é aceito por convenção (verificar_gates.py) mas não é mutado."""
    print("\n" + "=" * 70)
    print("GATE: G_INJECT — Validação do Injetor Universal de Componentes")
    print("=" * 70 + "\n")

    checagens = [
        _checar_schema(),
        _checar_profiles(),
        _checar_materializacao_e_rollback(),
    ]

    print("\n" + "=" * 70)
    if all(checagens):
        print("✅ GATE PASSOU — Injetor Universal de Componentes íntegro")
        print("=" * 70 + "\n")
        return 0

    print("❌ GATE FALHOU — ver detalhes acima")
    print("=" * 70 + "\n")
    return 1


def main() -> int:
    return executar_gate(Path("."))


if __name__ == "__main__":
    sys.exit(main())
