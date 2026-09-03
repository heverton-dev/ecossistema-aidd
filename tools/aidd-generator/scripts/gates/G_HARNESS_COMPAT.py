#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_HARNESS_COMPAT — Verificação de Compatibilidade de Harness

Detecta automaticamente se o harness atual suporta:
  1. Orquestração via protocolo delegado (arquivo + resposta)
  2. Fallback headless (litellm com credencial)

Atualiza HARNESS-COMPAT.json com resultado real.

Princípio AIDD: Universalidade — cada harness auto-detecta suas capacidades.
"""

import sys
import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


# =============================================================================
# DETECÇÃO DE HARNESS
# =============================================================================

def detectar_harness():
    """Identifica qual harness está rodando este script."""

    # Claude Code
    if os.environ.get('CLAUDECODE') == '1':
        return 'claude-code', os.environ.get('CLAUDE_CODE_EXECPATH', 'desconhecido')

    # Antigravity / Gemini
    if os.environ.get('ANTIGRAVITY_AGENT') or os.environ.get('GEMINI_CLI') or 'antigravity' in os.environ.get('GEMINI_SYSTEM_INSTRUCTIONS_PATH', '').lower():
        return 'antigravity', 'detectado'

    # Codex (futuro)
    if any(k.startswith('CODEX') for k in os.environ.keys()):
        return 'codex', 'detectado'

    # Gemini CLI (futuro)
    if any(k.startswith('GEMINI') for k in os.environ.keys()):
        return 'gemini-cli', 'detectado'

    # Fallback: desconhecido
    return 'antigravity' if 'antigravity' in str(Path.cwd()).lower() or Path('.gemini').exists() or Path('../../.gemini').exists() else 'desconhecido', 'auto'


# =============================================================================
# TESTE DE ORQUESTRAÇÃO
# =============================================================================

def testar_orquestracao(timeout=5):
    """
    Testa se o harness consegue responder a uma requisição delegada.

    Fluxo:
    1. Escrever arquivo de requisição fake
    2. Aguardar resposta (timeout segundos)
    3. Se arquivo de resposta aparecer: ✅ SUPORTADO
    4. Se timeout: ⏳ NÃO SUPORTADO

    Returns:
        (bool, str) — (sucesso, mensagem)
    """

    print(f"🔍 Testando orquestração (timeout {timeout}s)...")

    # 1. Criar requisição fake
    req_id = str(uuid.uuid4())[:8]
    cache_dir = Path('.aidd/cache')
    cache_dir.mkdir(parents=True, exist_ok=True)

    req_file = cache_dir / f'_harness_compat_test_{req_id}.json'
    resp_file = cache_dir / f'_harness_compat_resp_{req_id}.json'

    try:
        with open(req_file, 'w', encoding='utf-8') as f:
            json.dump({
                'request_id': req_id,
                'prompt': 'Compat check',
                'timestamp': time.time()
            }, f)

        # Aguardar resposta
        t_inicio = time.time()
        while time.time() - t_inicio < timeout:
            if resp_file.exists():
                return True, "Resposta recebida do harness"
            time.sleep(0.5)

        return False, f"Timeout (nenhuma resposta em {timeout}s)"

    finally:
        # Cleanup
        if req_file.exists():
            req_file.unlink()
        if resp_file.exists():
            resp_file.unlink()


# =============================================================================
# TESTE DE HEADLESS
# =============================================================================

def testar_headless():
    """Testa se litellm está disponível para modo headless."""
    print("🔍 Testando headless (litellm)...")

    modelo = os.environ.get('LLM_MODEL', 'claude-opus-5')
    print(f"  ℹ️ Modelo: {modelo}")

    try:
        import litellm
        print("  ✓ litellm importado com sucesso")
        return True, f"litellm disponível (modelo: {modelo})"
    except ImportError:
        return False, "litellm não instalado (instale com: pip install litellm)"


# =============================================================================
# ATUALIZAR HARNESS-COMPAT.JSON
# =============================================================================

def atualizar_compat(harness_nome, orquestracao_ok, headless_ok):
    """Atualiza HARNESS-COMPAT.json com resultado real."""

    compat_path = Path('HARNESS-COMPAT.json')

    if not compat_path.exists():
        print("⚠️  HARNESS-COMPAT.json não encontrado")
        return False

    with open(compat_path, 'r', encoding='utf-8') as f:
        compat_data = json.load(f)

    if harness_nome not in compat_data['harness_compatibility']:
        compat_data['harness_compatibility'][harness_nome] = {
            "nome": harness_nome.capitalize(),
            "orquestracao": "⏳ NÃO TESTADO",
            "protocolo_delegado": None,
            "fallback_headless": True,
            "modo_padrao": "headless",
            "data_teste": None,
            "versao_testada": None,
            "nota": "Auto-adicionado pelo teste de compatibilidade",
            "instrucoes": ""
        }

    entry = compat_data['harness_compatibility'][harness_nome]

    # Atualizar resultado
    entry['orquestracao'] = '✅ SUPORTADO' if orquestracao_ok else '⏳ NÃO SUPORTADO'
    entry['protocolo_delegado'] = orquestracao_ok
    entry['fallback_headless'] = headless_ok
    entry['data_teste'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    entry['versao_testada'] = '2.1'
    entry['modo_padrao'] = 'delegado' if orquestracao_ok else 'headless'

    # Atualizar metadata
    compat_data['metadata']['ultima_atualizacao'] = datetime.now(timezone.utc).isoformat()

    # Salvar
    with open(compat_path, 'w', encoding='utf-8') as f:
        json.dump(compat_data, f, indent=2, ensure_ascii=False)

    print(f"✅ HARNESS-COMPAT.json atualizado")
    return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Executa gate de compatibilidade."""

    print("\n" + "="*70)
    print("GATE: G_HARNESS_COMPAT — Detecção Automática de Compatibilidade")
    print("="*70 + "\n")

    # 1. Detectar harness
    harness_nome, harness_versao = detectar_harness()
    print(f"🔍 Harness detectado: {harness_nome}")
    print(f"   Versão/Path: {harness_versao}\n")

    # 2. Testar orquestração
    orq_ok, orq_msg = testar_orquestracao(timeout=5)
    print(f"{orq_msg}\n")

    # 3. Testar headless
    headless_ok, headless_msg = testar_headless()
    print(f"{headless_msg}\n")

    # 4. Determinar modo padrão
    if orq_ok:
        modo = 'delegado'
        print(f"✅ Modo recomendado: DELEGADO (orquestração)")
    elif headless_ok:
        modo = 'headless'
        print(f"⚠️  Modo recomendado: HEADLESS (fallback)")
    else:
        modo = 'erro'
        print(f"❌ Nenhum modo suportado")

    print("")

    # 5. Atualizar HARNESS-COMPAT.json
    atualizar_compat(harness_nome, orq_ok, headless_ok)

    print("\n" + "="*70)
    if orq_ok and headless_ok:
        print("✅ GATE PASSOU — Harness totalmente compatível")
        print(f"   Orquestração: ✅")
        print(f"   Headless: ✅")
        return 0
    elif headless_ok:
        print("⚠️  GATE PASSOU (MODO DEGRADADO) — Apenas headless")
        print(f"   Orquestração: ❌")
        print(f"   Headless: ✅")
        return 0
    else:
        print("❌ GATE FALHOU — Nenhum modo suportado")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
