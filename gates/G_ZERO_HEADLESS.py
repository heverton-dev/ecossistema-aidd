#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_ZERO_HEADLESS (Lei Canônica #7 e #8)
=============================================================================
Gate de Enforcement Real contra Subagentes Headless e Concorrência Paralela
Silenciosa.

Em conformidade com a Lei #7 (Zero Subagentes Headless / Execução Interativa)
e Lei #8 (Honestidade de Rótulo — nenhuma cobertura é alegada além do testado).

Diferente de uma verificação estática superficial, este gate EXERCITA em runtime
o hook de interceptação (`anti_headless_subagent_hook.py`):
1. Exercita a tentativa de disparo de múltiplos subagentes em paralelo sem confirmação:
   reprova se o hook não bloquear ativamente.
2. Exercita a tentativa de disparo concorrente com subagente ativo em execução:
   reprova se o hook não barrar a corrida.
3. Exercita o caminho legítimo com autorização explícita do usuário:
   reprova se o hook bloquear indevidamente a solicitação do operador.
4. Audita a presença e configuração do hook no harness (.claude/settings.json).

Limite Conhecido (Lei #8):
  Processos externos rodando fora do controle deste repositório (ex.: processos
  órfãos de ferramentas de terceiros sobrevivendo ao fechamento de SO/app) não
  são contidos por este hook. Nenhuma blindagem contra processos externos não-
  intermediados pelo harness é declarada.

Saída:
  exit 0 = Hook intercepta tentativas não autorizadas e permite as autorizadas.
  exit 1 = Falha no hook, evasão de bloqueio ou configuração ausente.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
HOOK_COMPARTILHADO = ROOT_DIR / "componentes" / "compartilhado" / "hooks" / "anti_headless_subagent_hook.py"
HOOK_CLAUDE = ROOT_DIR / ".claude" / "hooks" / "anti_headless_subagent_hook.py"
CLAUDE_SETTINGS = ROOT_DIR / ".claude" / "settings.json"


def auditar(root: Path = ROOT_DIR) -> int:
    print("=" * 70)
    print(" [GATE] G_ZERO_HEADLESS — Enforcement Real Anti-Headless / Subagentes Paralelos")
    print("=" * 70)

    erros = []

    hook_compartilhado = root / "componentes" / "compartilhado" / "hooks" / "anti_headless_subagent_hook.py"
    hook_claude = root / ".claude" / "hooks" / "anti_headless_subagent_hook.py"
    claude_settings = root / ".claude" / "settings.json"
    engine = root / "componentes" / "compartilhado" / "skills" / "orca-plan-orchestrator" / "scripts" / "orchestrator_engine.py"
    eco = root / "ecossistema.py"

    # 1. Presença física do hook canônico e de harness
    if not hook_compartilhado.is_file():
        erros.append(f"Hook canônico ausente: {hook_compartilhado}")
    if not hook_claude.is_file():
        erros.append(f"Hook do harness Claude ausente: {hook_claude}")

    # 2. Configuração no settings.json do assistente
    if not claude_settings.is_file():
        erros.append(f"Configuração do assistente ausente: {claude_settings}")
    else:
        try:
            cfg = json.loads(claude_settings.read_text(encoding="utf-8"))
            pre_hooks = cfg.get("hooks", {}).get("PreToolUse", [])
            hook_configurado = any(
                "anti_headless_subagent_hook" in json.dumps(h)
                for h in pre_hooks
            )
            if not hook_configurado:
                erros.append("Hook anti_headless_subagent_hook não registrado em PreToolUse no settings.json.")
        except Exception as e:
            erros.append(f"Erro ao ler {claude_settings}: {e}")

    # 3. Presença das convenções estáticas no motor (camada de defesa em profundidade)
    if engine.is_file():
        if "interactive: bool = True" not in engine.read_text(encoding="utf-8"):
            erros.append("orchestrator_engine.py deve ter interactive: bool = True como padrão obrigatório.")
    if eco.is_file():
        eco_txt = eco.read_text(encoding="utf-8")
        if "@click.option(\"--dangerously-force-headless\"" not in eco_txt and "add_argument('--dangerously-force-headless'" not in eco_txt:
            erros.append("ecossistema.py deve declarar a opção --dangerously-force-headless para qualquer execução não-interativa.")

    # Se já há erros estruturais de configuração, interrompe antes da execução do hook
    if erros:
        print(f"\n[FALHA] Quality Gate REPROVADO na configuração estrutural ({len(erros)} erro(s)):")
        for e in erros:
            print(f"  - {e}")
        print("=" * 70)
        return 1

    # 4. EXERCÍCIO EM RUNTIME DO HOOK (Reprodução Real)
    hook_exec = hook_compartilhado if hook_compartilhado.is_file() else hook_claude

    with tempfile.TemporaryDirectory() as tmp_dir:
        lock_file = Path(tmp_dir) / "subagent_teste.lock"

        env_exec = {**os.environ, "PYTHONIOENCODING": "utf-8"}

        # TESTE 1: Tentativa de disparar subagentes em paralelo sem confirmação
        payload_paralelo = {
            "tool_name": "Task",
            "tool_input": {
                "subagents": [
                    {"name": "worker-1", "task": "tarefa_a"},
                    {"name": "worker-2", "task": "tarefa_b"}
                ],
                "user_confirmed": False
            }
        }
        res_paralelo = subprocess.run(
            [sys.executable, str(hook_exec), "--lock-file", str(lock_file)],
            input=json.dumps(payload_paralelo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env_exec
        )
        saida_combinada_p = ((res_paralelo.stdout or "") + "\n" + (res_paralelo.stderr or "")).strip()

        if res_paralelo.returncode == 0:
            erros.append("Hook FALHOU em bloquear tentativa de disparo paralelo sem confirmação (saiu com exit 0).")
        elif "[BLOQUEIO G_ZERO_HEADLESS]" not in saida_combinada_p:
            erros.append(f"Hook bloqueou mas não emitiu '[BLOQUEIO G_ZERO_HEADLESS]'. Saída:\n{saida_combinada_p}")
        else:
            print("[OK] Teste de Reprodução 1: Tentativa paralela sem confirmação foi EFETIVAMENTE BLOQUEADA.")

        # TESTE 2: Tentativa de concorrência com subagente já ativo sem confirmação
        # Registra um agente ativo fictício
        lock_data = {
            "pid": os.getpid(),  # processo atual que está vivo
            "agent_name": "agente-preexistente",
            "timestamp": 9999999999.0
        }
        lock_file.write_text(json.dumps(lock_data), encoding="utf-8")

        # Dispara com outro PID simulado no payload sequencial sem confirm
        payload_concorrente = {
            "tool_name": "Agent",
            "tool_input": {
                "prompt": "Executar tarefa concorrente"
            },
            "user_confirmed": False
        }
        # Rodar via subprocess para ter PID diferente do lockfile
        res_concorrente = subprocess.run(
            [sys.executable, str(hook_exec), "--lock-file", str(lock_file)],
            input=json.dumps(payload_concorrente),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env_exec
        )
        saida_combinada_c = ((res_concorrente.stdout or "") + "\n" + (res_concorrente.stderr or "")).strip()

        if res_concorrente.returncode == 0:
            erros.append("Hook FALHOU em barrar concorrência de subagente com agente ativo no lockfile.")
        elif "[BLOQUEIO G_ZERO_HEADLESS]" not in saida_combinada_c:
            erros.append(f"Hook não emitiu mensagem de bloqueio em concorrência ativa. Saída:\n{saida_combinada_c}")
        else:
            print("[OK] Teste de Reprodução 2: Concorrência com subagente ativo foi EFETIVAMENTE BLOQUEADA.")

        # TESTE 3: Caminho legítimo solicitado com autorização explícita
        # Remove lock anterior
        if lock_file.exists():
            lock_file.unlink()

        payload_legitimo = {
            "tool_name": "Task",
            "tool_input": {
                "subagents": [
                    {"name": "worker-1", "task": "tarefa_a"}
                ],
                "user_confirmed": True
            }
        }
        res_legitimo = subprocess.run(
            [sys.executable, str(hook_exec), "--lock-file", str(lock_file)],
            input=json.dumps(payload_legitimo),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env_exec
        )
        saida_combinada_l = ((res_legitimo.stdout or "") + "\n" + (res_legitimo.stderr or "")).strip()

        if res_legitimo.returncode != 0:
            erros.append(f"Hook bloqueou indevidamente lançamento legítimo autorizado (código {res_legitimo.returncode}). Saída:\n{saida_combinada_l}")
        elif "[PERMITIDO]" not in saida_combinada_l:
            erros.append(f"Hook aprovou mas não emitiu confirmação '[PERMITIDO]'. Saída:\n{saida_combinada_l}")
        else:
            print("[OK] Teste de Reprodução 3: Caminho legítimo autorizado pelo operador PASSOU com sucesso.")

    if erros:
        print(f"\n[FALHA] Quality Gate G_ZERO_HEADLESS REPROVADO com {len(erros)} erro(s):")
        for e in erros:
            print(f"  - {e}")
        print("=" * 70)
        return 1

    print("\n-----------------------------------------------------------------------")
    print(" [LIMITE CONHECIDO — LEI #8 / INCIDENTE HISTÓRICO]:")
    print("   O bloqueio atua sobre as chamadas do assistente interceptadas pelo hook.")
    print("   Processos ou ferramentas externas disparadas fora do controle do repositório")
    print("   (ex.: instâncias avulsas de opencode em desk ORCA que sobrevivem ao fechar do app)")
    print("   estão fora do alcance do hook. Nenhuma proteção além da testada é reivindicada.")
    print("-----------------------------------------------------------------------")
    print("\n=======================================================================")
    print(" [SUCESSO] Quality Gate G_ZERO_HEADLESS APROVADO")
    print("   Hook de intercepção validado em runtime contra paralelismo e concorrência.")
    print("=======================================================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(auditar())
