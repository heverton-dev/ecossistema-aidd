#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_aidd_master_compose.py
Bateria 2 - Items 2.1 a 2.7, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16
Testa: init, compose, add-module, test unit, audit, status, plan, prompt,
       bench, heal, scaffold-infra, export-frontend, refine-module,
       deploy, compose-orca
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

def run(label, cmd, cwd=None, env=None, capture=True, timeout=300):
    """Executa comando real e registra resultado."""
    print(f"\n{'='*70}")
    print(f"  ITEM: {label}")
    print(f"  CMD : {' '.join(str(c) for c in cmd)}")
    print(f"  CWD : {cwd or os.getcwd()}")
    print(f"{'='*70}")
    t0 = time.time()
    try:
        res = subprocess.run(
            cmd, cwd=cwd, env=env,
            capture_output=capture, text=True, errors="replace",
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        RESULTS.append({"item": label, "exit_code": -99, "stdout": "", "stderr": "TIMEOUT", "ok": False, "duration": timeout})
        print(f"  [TIMEOUT] {label}")
        return None
    except Exception as e:
        RESULTS.append({"item": label, "exit_code": -1, "stdout": "", "stderr": str(e), "ok": False, "duration": 0})
        print(f"  [EXCEPTION] {e}")
        return None
    dur = round(time.time() - t0, 2)
    stdout = res.stdout or ""
    stderr = res.stderr or ""
    ok = res.returncode == 0
    icon = "PASS" if ok else "FAIL"
    print(f"  [{icon}] exit={res.returncode}  dur={dur}s")
    # Print relevant output lines
    combined = (stdout + stderr).strip()
    lines = combined.split("\n")
    for line in lines[-30:]:
        print(f"  | {line}")
    RESULTS.append({
        "item": label, "exit_code": res.returncode,
        "stdout": stdout[-2000:], "stderr": stderr[-500:],
        "ok": ok, "duration": dur
    })
    return res

def aidd(*args, cwd=None, env=None, capture=True, timeout=300):
    return [PYTHON, AIDD_CLI] + list(args)

def main():
    tmp_base = tempfile.mkdtemp(prefix="aidd_bat2_")
    print(f"\n[*] Diretório temporário base: {tmp_base}")

    dir_suite    = os.path.join(tmp_base, "suite-teste")
    dir_plan     = os.path.join(tmp_base, "plan-teste")
    dir_prompt   = os.path.join(tmp_base, "prompt-teste")
    dir_orca     = os.path.join(tmp_base, "suite-orca")
    dir_init     = os.path.join(tmp_base, "init-teste")

    env_base = os.environ.copy()
    # Adiciona scripts ao PYTHONPATH do aidd-master
    master_src = os.path.join(REPO_ROOT, "tools", "aidd-master", "src", "core")
    master_scripts = os.path.join(REPO_ROOT, "tools", "aidd-master", "scripts")
    env_base["PYTHONPATH"] = f"{master_src}{os.pathsep}{master_scripts}{os.pathsep}{env_base.get('PYTHONPATH', '')}"

    try:
        # -------------------------------------------------------
        # 2.1 init
        # -------------------------------------------------------
        os.makedirs(dir_init, exist_ok=True)
        r = run("2.1-init",
                aidd("init", "ProjetoTesteInit", "--dir", dir_init),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base)
        if r:
            # Verifica estrutura mínima
            src_dir = os.path.join(dir_init, "ProjetoTesteInit")
            if not os.path.exists(src_dir):
                # init pode criar dentro do dir direto
                src_dir = dir_init
            exists = os.path.exists(src_dir)
            RESULTS[-1]["notes"] = f"dir_exists={exists}, contents={os.listdir(dir_init) if os.path.exists(dir_init) else []}"

        # -------------------------------------------------------
        # 2.2 compose
        # -------------------------------------------------------
        r = run("2.2-compose",
                aidd("compose", dir_suite, "Suite Teste E2E", "crm", "erp", "--db", "sqlite"),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base, timeout=300)
        # Verificar estrutura
        if r and r.returncode == 0:
            checks = {
                "crm": os.path.exists(os.path.join(dir_suite, "src", "modules", "crm")),
                "erp": os.path.exists(os.path.join(dir_suite, "src", "modules", "erp")),
                "tests": os.path.exists(os.path.join(dir_suite, "tests")),
                "plano": os.path.exists(os.path.join(dir_suite, "PLANO-EXECUCAO-ESTRUTURADO.json")),
            }
            RESULTS[-1]["structure_checks"] = checks
            print(f"  [STRUCT] {checks}")

        # -------------------------------------------------------
        # 2.3 add-module
        # -------------------------------------------------------
        r = run("2.3-add-module",
                aidd("add-module", "estoque", "--descricao", "Modulo de controle de estoque com alertas", "--dir", dir_suite),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base)
        if r and r.returncode == 0:
            est_dir = os.path.join(dir_suite, "src", "modules", "estoque")
            RESULTS[-1]["notes"] = f"estoque_exists={os.path.exists(est_dir)}"

        # -------------------------------------------------------
        # 2.4 test unit
        # -------------------------------------------------------
        r = run("2.4-test-unit",
                aidd("test", "unit", "--dir", dir_suite),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base, timeout=180)
        if r:
            combined = (r.stdout or "") + (r.stderr or "")
            # Captura linha de resumo pytest
            for line in combined.split("\n"):
                if "passed" in line or "failed" in line or "error" in line:
                    RESULTS[-1]["pytest_summary"] = line.strip()
                    break

        # -------------------------------------------------------
        # 2.5 audit
        # -------------------------------------------------------
        r = run("2.5-audit",
                aidd("audit", "--dir", dir_suite),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base, timeout=300)

        # -------------------------------------------------------
        # 2.6 status
        # -------------------------------------------------------
        r = run("2.6-status",
                aidd("status", "--dir", dir_suite),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base)

        # -------------------------------------------------------
        # 2.7a plan (linguagem natural)
        # -------------------------------------------------------
        os.makedirs(dir_plan, exist_ok=True)
        r = run("2.7a-plan",
                aidd("plan", "Sistema de gestao de estoque com alertas", "--dir", dir_plan),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base)
        if r:
            combined = (r.stdout or "") + (r.stderr or "")
            for line in combined.split("\n"):
                if "Mecanismo" in line or "dominio" in line.lower() or "reconhecido" in line.lower():
                    RESULTS[-1]["detection"] = line.strip()
                    break

        # -------------------------------------------------------
        # 2.7b prompt (linguagem natural)
        # -------------------------------------------------------
        os.makedirs(dir_prompt, exist_ok=True)
        r = run("2.7b-prompt",
                aidd("prompt", "crie um crm simples para gestao de leads e vendas", "--dir", dir_prompt),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base)
        if r:
            combined = (r.stdout or "") + (r.stderr or "")
            for line in combined.split("\n"):
                if "Mecanismo" in line or "crm" in line.lower() or "reconhecido" in line.lower():
                    RESULTS[-1]["detection"] = line.strip()
                    break

        # -------------------------------------------------------
        # 2.10 bench
        # -------------------------------------------------------
        r = run("2.10-bench",
                aidd("bench", "-n", "50", "--dir", dir_suite),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base)
        if r:
            combined = (r.stdout or "") + (r.stderr or "")
            for line in combined.split("\n"):
                if "Throughput" in line or "RPS" in line or "req/s" in line:
                    RESULTS[-1]["throughput"] = line.strip()
                    break

        # -------------------------------------------------------
        # 2.11 heal
        # -------------------------------------------------------
        r = run("2.11-heal",
                aidd("heal", "--dir", dir_suite),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base, timeout=300)

        # -------------------------------------------------------
        # 2.12 scaffold-infra
        # -------------------------------------------------------
        r = run("2.12-scaffold-infra",
                aidd("scaffold-infra", "--dir", dir_suite),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base)
        if r and r.returncode == 0:
            infra_dir = os.path.join(dir_suite, "infra")
            infra_files = []
            if os.path.exists(infra_dir):
                for root, dirs, files in os.walk(infra_dir):
                    for f in files:
                        infra_files.append(os.path.relpath(os.path.join(root, f), dir_suite))
            RESULTS[-1]["infra_files"] = infra_files[:20]
            print(f"  [INFRA] {infra_files[:10]}")

        # -------------------------------------------------------
        # 2.13 export-frontend
        # -------------------------------------------------------
        r = run("2.13-export-frontend",
                aidd("export-frontend", "--dir", dir_suite),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base, timeout=120)
        if r:
            combined = (r.stdout or "") + (r.stderr or "")
            RESULTS[-1]["notes"] = combined[-500:]

        # -------------------------------------------------------
        # 2.14 refine-module (verificar se compose gerou .feature)
        # -------------------------------------------------------
        feature_crm = os.path.join(dir_suite, "features", "crm.feature")
        feature_exists = os.path.exists(feature_crm)
        RESULTS.append({
            "item": "2.14-refine-module-check",
            "exit_code": 0 if feature_exists else -1,
            "stdout": f"features/crm.feature exists={feature_exists}",
            "stderr": "",
            "ok": feature_exists,
            "duration": 0,
            "notes": "compose gera .feature automaticamente" if feature_exists else "LIMITACAO: compose NAO gerou features/*.feature automaticamente — refine-module nao pode ser exercitado via caminho de ouro puro sem fabricar arquivo fake"
        })
        print(f"\n  [2.14] features/crm.feature exists={feature_exists}")
        if feature_exists:
            r = run("2.14-refine-module",
                    aidd("refine-module", "crm", "--dir", dir_suite),
                    cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                    env=env_base, timeout=120)

        # -------------------------------------------------------
        # 2.15 deploy docker (verificar disponibilidade)
        # -------------------------------------------------------
        docker_available = shutil.which("docker") is not None
        docker_compose_file = os.path.join(dir_suite, "docker-compose.yml")
        has_compose_file = os.path.exists(docker_compose_file)
        
        print(f"\n  [2.15] docker={docker_available}, docker-compose.yml={has_compose_file}")
        
        if docker_available and has_compose_file:
            r = run("2.15-deploy-docker",
                    [PYTHON, AIDD_CLI, "deploy", "docker"],
                    cwd=dir_suite,  # cwd=dir_suite (nao --dir flag)
                    env=env_base, timeout=120)
            # Sempre derrubar container ao final
            subprocess.run(["docker", "compose", "down"], cwd=dir_suite, capture_output=True)
            print("  [OK] docker compose down executado")
        else:
            reason = []
            if not docker_available:
                reason.append("docker nao encontrado no PATH")
            if not has_compose_file:
                reason.append(f"docker-compose.yml nao gerado em {dir_suite}")
            RESULTS.append({
                "item": "2.15-deploy-docker",
                "exit_code": -1,
                "stdout": "",
                "stderr": "",
                "ok": False,
                "duration": 0,
                "notes": f"LIMITACAO DE AMBIENTE: {'; '.join(reason)} — docker nao testado"
            })
            print(f"  [SKIP] deploy docker: {'; '.join(reason)}")

        # -------------------------------------------------------
        # 2.16 compose-orca
        # -------------------------------------------------------
        os.makedirs(dir_orca, exist_ok=True)
        r = run("2.16-compose-orca",
                aidd("compose-orca", "--dir", dir_orca, "--suite-name", "Suite Orca", "crm", "erp"),
                cwd=os.path.join(REPO_ROOT, "tools", "aidd-master"),
                env=env_base, timeout=120)
        if r and r.returncode == 0:
            manifest = os.path.join(dir_orca, "COMPOSE-ORCA-MANIFEST.json")
            RESULTS[-1]["manifest_exists"] = os.path.exists(manifest)
            if os.path.exists(manifest):
                with open(manifest, "r", encoding="utf-8") as f:
                    data = json.load(f)
                RESULTS[-1]["manifest_summary"] = {k: data.get(k) for k in ["total_modules", "success", "status"]}
                print(f"  [MANIFEST] {RESULTS[-1]['manifest_summary']}")

    finally:
        # Limpar diretórios temporários
        print(f"\n[*] Limpando temporários: {tmp_base}")
        try:
            shutil.rmtree(tmp_base, ignore_errors=True)
            print("[OK] Temporários removidos.")
        except Exception as e:
            print(f"[WARN] Falha ao remover temporários: {e}")

    # Resumo
    print(f"\n{'='*70}")
    print("RESUMO DA BATERIA (itens 2.1-2.7, 2.10-2.16)")
    print(f"{'='*70}")
    passed = sum(1 for r in RESULTS if r.get("ok"))
    failed = sum(1 for r in RESULTS if not r.get("ok"))
    print(f"PASS: {passed}  FAIL: {failed}  TOTAL: {len(RESULTS)}")
    for r in RESULTS:
        icon = "PASS" if r.get("ok") else "FAIL"
        print(f"  [{icon}] {r['item']:40s} exit={r.get('exit_code', '?')}")
        if r.get("notes"):
            print(f"         {r['notes'][:120]}")

    # Salvar JSON de resultados parciais para o relatório final
    out_path = os.path.join(REPO_ROOT, "docs", "testes", "testes", "_resultados_compose.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2)
    print(f"\n[*] Resultados parciais salvos: {out_path}")
    return failed

if __name__ == "__main__":
    sys.exit(main())
