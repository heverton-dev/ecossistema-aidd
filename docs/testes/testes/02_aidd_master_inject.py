#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_aidd_master_inject.py
Bateria 2 - Item 2.8 e 2.9
Testa: inject (7 tipos via CLI direta), --dry-run, --remover,
       config com --conteudo-file, mcp com --mcp-command,
       verificar-drift (caso limpo e caso com drift real).
"""
import os
import sys
import subprocess
import tempfile
import shutil
import json
import time

REPO_ROOT = r"C:\Users\trcnologia\Desktop\ecossistema-aidd"
AIDD_CLI  = os.path.join(REPO_ROOT, "tools", "aidd-master", "scripts", "aidd.py")
PYTHON    = sys.executable

RESULTS = []

def run(label, cmd, cwd=None, env=None, timeout=120):
    print(f"\n{'='*70}")
    print(f"  ITEM: {label}")
    print(f"  CMD : {' '.join(str(c) for c in cmd)}")
    print(f"{'='*70}")
    t0 = time.time()
    try:
        res = subprocess.run(
            cmd, cwd=cwd, env=env,
            capture_output=True, text=True, errors="replace",
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        RESULTS.append({"item": label, "exit_code": -99, "stdout": "", "stderr": "TIMEOUT", "ok": False, "duration": timeout})
        print(f"  [TIMEOUT]")
        return None
    except Exception as e:
        RESULTS.append({"item": label, "exit_code": -1, "stdout": "", "stderr": str(e), "ok": False, "duration": 0})
        print(f"  [EXCEPTION] {e}")
        return None
    dur = round(time.time() - t0, 2)
    ok = res.returncode == 0
    icon = "PASS" if ok else "FAIL"
    print(f"  [{icon}] exit={res.returncode}  dur={dur}s")
    combined = ((res.stdout or "") + (res.stderr or "")).strip()
    for line in combined.split("\n")[-20:]:
        print(f"  | {line}")
    RESULTS.append({
        "item": label, "exit_code": res.returncode,
        "stdout": (res.stdout or "")[-1500:], "stderr": (res.stderr or "")[-300:],
        "ok": ok, "duration": dur
    })
    return res

def aidd_inject(tipo, nome, extra_args=None, dir_path=None, env=None, label=None, cwd=None, timeout=120):
    cmd = [PYTHON, AIDD_CLI, "inject", tipo, nome]
    if extra_args:
        cmd.extend(extra_args)
    if dir_path:
        cmd.extend(["--dir", dir_path])
    lbl = label or f"2.8-inject-{tipo}"
    return run(lbl, cmd, cwd=cwd or os.path.join(REPO_ROOT, "tools", "aidd-master"), env=env, timeout=timeout)

def main():
    tmp_base = tempfile.mkdtemp(prefix="aidd_inject_")
    dir_inject = os.path.join(tmp_base, "inject-teste")
    os.makedirs(dir_inject, exist_ok=True)
    print(f"\n[*] Diretório temporário: {tmp_base}")

    env_base = os.environ.copy()
    master_src = os.path.join(REPO_ROOT, "tools", "aidd-master", "src", "core")
    master_scripts = os.path.join(REPO_ROOT, "tools", "aidd-master", "scripts")
    env_base["PYTHONPATH"] = f"{master_src}{os.pathsep}{master_scripts}{os.pathsep}{env_base.get('PYTHONPATH', '')}"

    cwd_master = os.path.join(REPO_ROOT, "tools", "aidd-master")

    try:
        # -------------------------------------------------------
        # 2.8 - inject 7 tipos (1 injeção cada)
        # -------------------------------------------------------

        # skill
        aidd_inject("skill", "analise-de-dados",
                    ["--descricao", "Skill de analise de dados em PT-BR"],
                    dir_inject, env_base, label="2.8-inject-skill", cwd=cwd_master)

        # mcp (com --mcp-command)
        aidd_inject("mcp", "servidor-dados-ext",
                    ["--descricao", "Servidor MCP externo de dados",
                     "--mcp-command", "python",
                     "--mcp-args", '["mcp_server.py", "--port", "9999"]'],
                    dir_inject, env_base, label="2.8-inject-mcp-command", cwd=cwd_master)

        # rule
        aidd_inject("rule", "seguranca-api",
                    ["--descricao", "Regra de seguranca para endpoints de API"],
                    dir_inject, env_base, label="2.8-inject-rule", cwd=cwd_master)

        # spec
        aidd_inject("spec", "contrato-crm",
                    ["--descricao", "Especificacao OpenAPI do modulo CRM"],
                    dir_inject, env_base, label="2.8-inject-spec", cwd=cwd_master)

        # config (com --conteudo-file contendo JSON com multiplos campos)
        config_content = {
            "database_url": "sqlite:///app.db",
            "debug_mode": False,
            "max_connections": 20,
            "log_level": "INFO",
            "feature_flags": {"crm": True, "erp": True}
        }
        config_file = os.path.join(tmp_base, "config_payload.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_content, f, indent=2)

        aidd_inject("config", "app-config-principal",
                    ["--descricao", "Configuracao principal da aplicacao",
                     "--conteudo-file", config_file],
                    dir_inject, env_base, label="2.8-inject-config-with-file", cwd=cwd_master)

        # agent
        aidd_inject("agent", "orquestrador-financeiro",
                    ["--descricao", "Agente orquestrador do modulo financeiro"],
                    dir_inject, env_base, label="2.8-inject-agent", cwd=cwd_master)

        # hook
        aidd_inject("hook", "pre-commit-lint",
                    ["--descricao", "Hook de pre-commit para linting automatico"],
                    dir_inject, env_base, label="2.8-inject-hook", cwd=cwd_master)

        # -------------------------------------------------------
        # 2.8 - dry-run (confirma que nenhum arquivo é escrito)
        # -------------------------------------------------------
        dir_dryrun = os.path.join(tmp_base, "dryrun-teste")
        os.makedirs(dir_dryrun, exist_ok=True)
        before_files = set(os.listdir(dir_dryrun))
        r = aidd_inject("skill", "skill-dryrun-test",
                        ["--descricao", "Skill dryrun", "--dry-run"],
                        dir_dryrun, env_base, label="2.8-inject-dry-run", cwd=cwd_master)
        after_files = set(os.listdir(dir_dryrun))
        new_files = after_files - before_files
        RESULTS[-1]["dry_run_new_files"] = list(new_files)
        RESULTS[-1]["dry_run_ok"] = len(new_files) == 0
        print(f"  [DRY-RUN] Novos arquivos escritos: {list(new_files)} (esperado: nenhum)")

        # -------------------------------------------------------
        # 2.8 - --remover (injeta e remove)
        # -------------------------------------------------------
        dir_remove = os.path.join(tmp_base, "remove-teste")
        os.makedirs(dir_remove, exist_ok=True)
        # Injeta hook para depois remover
        r_inject = aidd_inject("hook", "hook-para-remover",
                               ["--descricao", "Hook que sera removido"],
                               dir_remove, env_base, label="2.8-inject-hook-para-remover", cwd=cwd_master)
        # Agora remove
        if r_inject and r_inject.returncode == 0:
            r_rem = run("2.8-inject-remover",
                        [PYTHON, AIDD_CLI, "inject", "hook", "hook-para-remover", "--remover", "--dir", dir_remove],
                        cwd=cwd_master, env=env_base)
        else:
            RESULTS.append({"item": "2.8-inject-remover", "exit_code": -1, "stdout": "",
                            "stderr": "injecao previa falhou", "ok": False, "duration": 0})

        # -------------------------------------------------------
        # 2.9 - verificar-drift ANTES de qualquer edição (caso limpo)
        # -------------------------------------------------------
        r = run("2.9-verificar-drift-clean",
                [PYTHON, AIDD_CLI, "verificar-drift", "--dir", dir_inject],
                cwd=cwd_master, env=env_base)
        drift_clean_exit = r.returncode if r else -1
        RESULTS[-1]["expected_exit"] = 0
        RESULTS[-1]["ok"] = drift_clean_exit == 0

        # -------------------------------------------------------
        # 2.9 - Editar manualmente um arquivo injetado → drift
        # -------------------------------------------------------
        # O drift so e rastreado para os arquivos listados em
        # "arquivos_hashes" dentro de CAPABILITIES.json (os arquivos
        # MATERIALIZADOS pelo componente) — arquivos de sincronizacao
        # multi-harness (AGENTS.md, templates/core/CLAUDE.md, etc.) NAO
        # sao hash-tracked, entao editar um deles nunca gera drift.
        # Ler CAPABILITIES.json e escolher um arquivo realmente rastreado.
        drifted_file = None
        capabilities_path = os.path.join(dir_inject, "CAPABILITIES.json")
        if os.path.isfile(capabilities_path):
            with open(capabilities_path, "r", encoding="utf-8") as f:
                catalogo = json.load(f)
            for tipo, componentes in catalogo.items():
                if drifted_file:
                    break
                if not isinstance(componentes, list):
                    continue
                for comp in componentes:
                    hashes = comp.get("arquivos_hashes", {})
                    if hashes:
                        rel_path = next(iter(hashes.keys()))
                        candidate = os.path.join(dir_inject, rel_path)
                        if os.path.isfile(candidate):
                            drifted_file = candidate
                            break

        if drifted_file:
            print(f"\n  [*] Editando manualmente: {drifted_file}")
            with open(drifted_file, "a", encoding="utf-8") as f:
                f.write("\n# DRIFT MANUAL INJETADO PARA TESTE\n")
            r = run("2.9-verificar-drift-divergente",
                    [PYTHON, AIDD_CLI, "verificar-drift", "--dir", dir_inject],
                    cwd=cwd_master, env=env_base)
            drift_div_exit = r.returncode if r else -1
            # Esperamos exit 1 (drift detectado)
            RESULTS[-1]["expected_exit"] = 1
            RESULTS[-1]["ok"] = drift_div_exit == 1
            RESULTS[-1]["notes"] = f"SYNC_DIVERGENTE esperado: exit={drift_div_exit} (ok={drift_div_exit == 1})"
            print(f"  [DRIFT] exit={drift_div_exit} esperado=1 ok={drift_div_exit == 1}")
        else:
            RESULTS.append({
                "item": "2.9-verificar-drift-divergente",
                "exit_code": -1, "stdout": "", "stderr": "",
                "ok": False, "duration": 0,
                "notes": "LIMITACAO: nenhum arquivo .py/.md/.yaml encontrado para editar em dir_inject"
            })

    finally:
        # ACHADO REAL (bateria 2, item 2.8): o tipo "hook" grava uma copia
        # CANONICA no monorepo real (componentes/{alvo_projeto}/hooks/{nome}/hook.sh)
        # e espelhos multi-harness (tools/aidd-master/.claude|.agent|.gemini/hooks/{nome}/)
        # SEMPRE, independente de --dir (materializador.py:_default_ecossistema_root
        # resolve a partir de __file__, nao do cwd/--dir) — isso e por design
        # (integracao canonica "Package 7"), nao um bug do script de teste. Alem
        # disso, "--remover" limpa o arquivo canonico mas NAO limpa os espelhos
        # multi-harness sincronizados (orfaos reais confirmados nesta bateria).
        # Por isso este script precisa limpar manualmente essa pegada no repo
        # real apos cada execucao, para nao violar a regra de nunca poluir o
        # repositorio real.
        for nome_hook in ("pre-commit-lint", "hook-para-remover", "skill-dryrun-test"):
            for base in (
                os.path.join(REPO_ROOT, "componentes", "aidd-master", "hooks", nome_hook),
                os.path.join(REPO_ROOT, "tools", "aidd-master", ".claude", "hooks", nome_hook),
                os.path.join(REPO_ROOT, "tools", "aidd-master", ".agent", "hooks", nome_hook),
                os.path.join(REPO_ROOT, "tools", "aidd-master", ".gemini", "hooks", nome_hook),
            ):
                if os.path.isdir(base):
                    shutil.rmtree(base, ignore_errors=True)
        print(f"\n[*] Limpando temporários: {tmp_base}")
        shutil.rmtree(tmp_base, ignore_errors=True)
        print("[OK] Temporários removidos.")

    # Resumo
    print(f"\n{'='*70}")
    print("RESUMO - ITEMS 2.8 e 2.9 (inject + verificar-drift)")
    print(f"{'='*70}")
    passed = sum(1 for r in RESULTS if r.get("ok"))
    failed = sum(1 for r in RESULTS if not r.get("ok"))
    print(f"PASS: {passed}  FAIL: {failed}  TOTAL: {len(RESULTS)}")
    for r in RESULTS:
        icon = "PASS" if r.get("ok") else "FAIL"
        print(f"  [{icon}] {r['item']:45s} exit={r.get('exit_code', '?')}")
        if r.get("notes"):
            print(f"         {r['notes'][:120]}")

    out_path = os.path.join(REPO_ROOT, "docs", "testes", "testes", "_resultados_inject.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2)
    print(f"\n[*] Resultados salvos: {out_path}")
    return failed

if __name__ == "__main__":
    sys.exit(main())
