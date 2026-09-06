#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_aidd_enterprise_main.py
Bateria 3 - AIDD Enterprise (tools/aidd-enterprise/scripts/aidd.py)
Itens 3.1 a 3.10 (exceto 3.3 TIPO_AMBIGUO puro, que tem prova complementar
em 03_aidd_enterprise_ambiguo.py — este script tambem reprova 3.3 via CLI real).
"""
import os
import sys
import subprocess
import tempfile
import shutil
import json
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = r"C:\Users\trcnologia\Desktop\ecossistema-aidd"
ENT_DIR   = os.path.join(REPO_ROOT, "tools", "aidd-enterprise")
AIDD_CLI  = os.path.join(ENT_DIR, "scripts", "aidd.py")
PYTHON    = sys.executable

RESULTS = []


def run(label, cmd, cwd=None, env=None, timeout=300):
    print(f"\n{'='*70}")
    print(f"  ITEM: {label}")
    print(f"  CMD : {' '.join(str(c) for c in cmd)}")
    print(f"  CWD : {cwd or os.getcwd()}")
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
        print(f"  [TIMEOUT] {label}")
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
    for line in combined.split("\n")[-30:]:
        print(f"  | {line}")
    RESULTS.append({
        "item": label, "exit_code": res.returncode,
        "stdout": (res.stdout or "")[-2000:], "stderr": (res.stderr or "")[-500:],
        "ok": ok, "duration": dur
    })
    return res


def aidd(*args):
    return [PYTHON, AIDD_CLI] + list(args)


def limpar_poluicao_hook_real(nomes):
    """Remove copias canonicas + espelhos multi-harness que 'inject hook'
    grava sempre no monorepo real (por design, ver materializador.py:
    _default_ecossistema_root = Path(__file__).resolve().parents[4]),
    independente do --dir informado na CLI. Mesmo achado da Bateria 2
    (aidd-master), agora confirmado tambem em aidd-enterprise."""
    bases = [
        os.path.join(REPO_ROOT, "componentes", "aidd-enterprise", "hooks"),
        os.path.join(ENT_DIR, ".claude", "hooks"),
        os.path.join(ENT_DIR, ".agent", "hooks"),
        os.path.join(ENT_DIR, ".mimocode", "hooks"),
        os.path.join(ENT_DIR, ".gemini", "hooks"),
        os.path.join(ENT_DIR, ".hooks"),
    ]
    for nome in nomes:
        for base in bases:
            alvo = os.path.join(base, nome)
            if os.path.isdir(alvo):
                shutil.rmtree(alvo, ignore_errors=True)
            alvo_flat = os.path.join(base, f"{nome}.json")
            if os.path.isfile(alvo_flat):
                os.remove(alvo_flat)


def main():
    tmp_base = tempfile.mkdtemp(prefix="aidd_bat3_")
    print(f"\n[*] Diretório temporário base: {tmp_base}")

    dir_init   = os.path.join(tmp_base, "init-teste")
    dir_suite  = os.path.join(tmp_base, "suite-teste-ent")
    dir_plan1  = os.path.join(tmp_base, "plan-teste-1")
    dir_plan2  = os.path.join(tmp_base, "plan-teste-2")
    dir_plan_amb = os.path.join(tmp_base, "plan-teste-ambiguo")
    dir_inject = os.path.join(tmp_base, "inject-teste")
    dir_dryrun = os.path.join(tmp_base, "dryrun-teste")
    dir_remove = os.path.join(tmp_base, "remove-teste")
    dir_orca   = os.path.join(tmp_base, "suite-orca-ent")

    env_base = os.environ.copy()
    ent_src = os.path.join(ENT_DIR, "src", "core")
    ent_scripts = os.path.join(ENT_DIR, "scripts")
    env_base["PYTHONPATH"] = f"{ent_src}{os.pathsep}{ent_scripts}{os.pathsep}{env_base.get('PYTHONPATH', '')}"

    hook_names_para_limpar = []

    try:
        # 3.1 init / compose / add-module / test unit / audit / status
        os.makedirs(dir_init, exist_ok=True)
        run("3.1-init", aidd("init", "ProjetoTesteEnt", "--dir", dir_init), cwd=ENT_DIR, env=env_base)

        r = run("3.1-compose", aidd("compose", dir_suite, "Suite Enterprise E2E", "crm", "erp", "--db", "sqlite"), cwd=ENT_DIR, env=env_base)
        if r and r.returncode == 0:
            RESULTS[-1]["structure_checks"] = {
                "crm": os.path.exists(os.path.join(dir_suite, "src", "modules", "crm")),
                "erp": os.path.exists(os.path.join(dir_suite, "src", "modules", "erp")),
                "tests": os.path.exists(os.path.join(dir_suite, "tests")),
                "plano": os.path.exists(os.path.join(dir_suite, "PLANO-EXECUCAO-ESTRUTURADO.json")),
            }

        run("3.1-add-module", aidd("add-module", "financeiro", "--descricao", "Modulo financeiro", "--dir", dir_suite), cwd=ENT_DIR, env=env_base)
        run("3.1-test-unit", aidd("test", "unit", "--dir", dir_suite), cwd=ENT_DIR, env=env_base, timeout=180)
        run("3.1-audit", aidd("audit", "--dir", dir_suite), cwd=ENT_DIR, env=env_base, timeout=300)
        run("3.1-status", aidd("status", "--dir", dir_suite), cwd=ENT_DIR, env=env_base)

        # 3.2 plan com 2 frases nao ambiguas (dominios diferentes)
        os.makedirs(dir_plan1, exist_ok=True)
        run("3.2-plan-estoque", aidd("plan", "Sistema de gestao de estoque com alertas", "--dir", dir_plan1), cwd=ENT_DIR, env=env_base)
        os.makedirs(dir_plan2, exist_ok=True)
        run("3.2-plan-folha-pagamento", aidd("plan", "crie um modulo de folha de pagamento", "--dir", dir_plan2), cwd=ENT_DIR, env=env_base)

        # 3.3 frase AMBIGUA deliberada via CLI real (nao so via funcao interna)
        # "crie uma regra de hook para governanca" casa com 'rule' E 'hook' ao
        # mesmo tempo em detector_camada.py — provado isoladamente em
        # 03_aidd_enterprise_ambiguo.py. Aqui provamos via CLI de ponta a ponta:
        # o intent_router deve rotear para "inject", detectar_de_texto deve
        # retornar TIPO_AMBIGUO, e o comando deve sair com exit != 0 SEM
        # escrever nenhum arquivo em --dir.
        os.makedirs(dir_plan_amb, exist_ok=True)
        antes = set(os.listdir(dir_plan_amb))
        r = run("3.3-plan-ambiguo-cli",
                aidd("plan", "crie uma regra de hook para governanca", "--dir", dir_plan_amb),
                cwd=ENT_DIR, env=env_base)
        depois = set(os.listdir(dir_plan_amb))
        novos = depois - antes
        if r:
            combined = (r.stdout or "") + (r.stderr or "")
            ambiguo_detectado = "TIPO_AMBIGUO" in combined or "Candidatos" in combined or "candidatos" in combined
            RESULTS[-1]["ok"] = (r.returncode != 0) and ambiguo_detectado and len(novos) == 0
            RESULTS[-1]["notes"] = f"ambiguo_detectado={ambiguo_detectado}, arquivos_novos={list(novos)}, exit={r.returncode}"
            print(f"  [AMBIGUO-CLI] detectado={ambiguo_detectado} arquivos_novos={list(novos)} exit={r.returncode}")

        # 3.4 inject - 7 tipos
        os.makedirs(dir_inject, exist_ok=True)
        run("3.4-inject-hook", aidd("inject", "hook", "pre-commit-ent", "--descricao", "Hook de pre-commit enterprise", "--dir", dir_inject), cwd=ENT_DIR, env=env_base)
        hook_names_para_limpar.append("pre-commit-ent")
        r_skill = run("3.4-inject-skill", aidd("inject", "skill", "seguranca-cibernetica-ent", "--descricao", "Skill de seguranca enterprise", "--dir", dir_inject), cwd=ENT_DIR, env=env_base)
        if r_skill and r_skill.returncode == 0:
            combined = (r_skill.stdout or "")
            pastas_skill = [l.strip() for l in combined.split("\n") if "skills" in l.lower() and (":" not in l or "-" in l)]
            RESULTS[-1]["arquivos_materializados_raw"] = combined[-1200:]

        config_map = os.path.join(tmp_base, "config-map.json")
        with open(config_map, "w", encoding="utf-8") as f:
            json.dump({"configuracoes/app.json": json.dumps({"modo": "producao", "max_conn": 20})}, f)
        run("3.4-inject-config-files-json", aidd("inject", "config", "app-config-ent", "--descricao", "Config enterprise", "--files-json", config_map, "--dir", dir_inject), cwd=ENT_DIR, env=env_base)

        run("3.4-inject-mcp-command", aidd("inject", "mcp", "search-tool-ent", "--descricao", "MCP de busca", "--mcp-command", "python", "--mcp-args", "mcp_server.py", "--dir", dir_inject), cwd=ENT_DIR, env=env_base)
        run("3.4-inject-rule", aidd("inject", "rule", "no-llm-ent", "--descricao", "Regra no-llm enterprise", "--dir", dir_inject), cwd=ENT_DIR, env=env_base)
        run("3.4-inject-spec", aidd("inject", "spec", "api-contrato-ent", "--descricao", "Spec contrato enterprise", "--dir", dir_inject), cwd=ENT_DIR, env=env_base)
        run("3.4-inject-agent", aidd("inject", "agent", "orquestrador-ent", "--descricao", "Agente orquestrador enterprise", "--dir", dir_inject), cwd=ENT_DIR, env=env_base)

        # Confirmar estrutura real das 5 pastas de harness para hook (.json) e skill
        hook_json = os.path.join(dir_inject, "componentes-locais") # nao usado; checagem real abaixo
        hook_checks = {}
        for pasta in (".claude/hooks", ".agent/hooks", ".mimocode/hooks", ".gemini/hooks", ".hooks"):
            caminho_dir = os.path.join(dir_inject, pasta.replace("/", os.sep), "pre-commit-ent")
            caminho_flat = os.path.join(dir_inject, pasta.replace("/", os.sep), "pre-commit-ent.json")
            hook_checks[pasta] = os.path.isfile(os.path.join(caminho_dir, "pre-commit-ent.json")) or os.path.isfile(caminho_flat)
        RESULTS.append({"item": "3.4-inject-hook-5-pastas-json", "exit_code": 0 if all(hook_checks.values()) else 1,
                         "ok": all(hook_checks.values()), "duration": 0, "stdout": "", "stderr": "",
                         "notes": json.dumps(hook_checks)})
        print(f"  [HOOK-5-PASTAS] {hook_checks}")

        skill_checks = {}
        for pasta in (".claude/skills", ".agent/skills", ".mimocode/skills", ".gemini/skills", ".skills"):
            caminho = os.path.join(dir_inject, pasta.replace("/", os.sep), "seguranca-cibernetica-ent", "SKILL.md")
            skill_checks[pasta] = os.path.isfile(caminho)
        RESULTS.append({"item": "3.4-inject-skill-5-pastas", "exit_code": 0 if all(skill_checks.values()) else 1,
                         "ok": all(skill_checks.values()), "duration": 0, "stdout": "", "stderr": "",
                         "notes": json.dumps(skill_checks)})
        print(f"  [SKILL-5-PASTAS] {skill_checks}")

        # 3.5 dry-run + remover (com prova de limpeza do canonico especifico)
        os.makedirs(dir_dryrun, exist_ok=True)
        antes_dry = set(os.listdir(dir_dryrun))
        run("3.5-inject-dry-run", aidd("inject", "hook", "post-merge-ent", "--descricao", "Dry", "--dry-run", "--dir", dir_dryrun), cwd=ENT_DIR, env=env_base)
        depois_dry = set(os.listdir(dir_dryrun))
        novos_dry = depois_dry - antes_dry
        RESULTS[-1]["dry_run_ok"] = len(novos_dry) == 0
        RESULTS[-1]["notes"] = f"arquivos_novos={list(novos_dry)}"

        os.makedirs(dir_remove, exist_ok=True)
        r_inj = run("3.5-inject-hook-para-remover", aidd("inject", "hook", "test-remocao-ent", "--descricao", "Hook de teste remocao", "--dir", dir_remove), cwd=ENT_DIR, env=env_base)
        hook_names_para_limpar.append("test-remocao-ent")

        canonical_ent = os.path.join(REPO_ROOT, "componentes", "aidd-enterprise", "hooks", "test-remocao-ent", "test-remocao-ent.json")
        canonical_existe_antes = os.path.isfile(canonical_ent)

        if r_inj and r_inj.returncode == 0:
            r_rem = run("3.5-inject-remover", aidd("inject", "hook", "test-remocao-ent", "--remover", "--dir", dir_remove), cwd=ENT_DIR, env=env_base)
            canonical_existe_depois = os.path.isfile(canonical_ent)
            local_hooks_dir = os.path.join(dir_remove, ".claude", "hooks", "test-remocao-ent")
            local_existe_depois = os.path.isdir(local_hooks_dir)
            limpeza_ok = canonical_existe_antes and (not canonical_existe_depois) and (not local_existe_depois)
            RESULTS[-1]["ok"] = RESULTS[-1]["ok"] and limpeza_ok
            RESULTS[-1]["notes"] = (f"canonical_antes={canonical_existe_antes} canonical_depois={canonical_existe_depois} "
                                     f"local_depois={local_existe_depois} limpeza_canonico_especifico_ok={limpeza_ok}")
            print(f"  [REMOVER-CANONICO] {RESULTS[-1]['notes']}")
        else:
            RESULTS.append({"item": "3.5-inject-remover", "exit_code": -1, "ok": False, "duration": 0,
                             "stdout": "", "stderr": "injecao previa falhou"})

        # 3.6 G_INJECT.py rodado ISOLADO contra o projeto de teste (nao a real tool dir)
        g_inject_script = os.path.join(ENT_DIR, "scripts", "gates", "G_INJECT.py")
        run("3.6-G_INJECT-limpo", [PYTHON, g_inject_script, "--dir", dir_inject], cwd=ENT_DIR, env=env_base)

        # Editar manualmente um arquivo hash-tracked (via CAPABILITIES.json do projeto) -> drift
        capabilities_path = os.path.join(dir_inject, "CAPABILITIES.json")
        drifted_file = None
        if os.path.isfile(capabilities_path):
            with open(capabilities_path, "r", encoding="utf-8") as f:
                catalogo = json.load(f)
            for tipo, comps in catalogo.items():
                if drifted_file or not isinstance(comps, list):
                    continue
                for comp in comps:
                    hashes = comp.get("arquivos_hashes", {})
                    if hashes:
                        rel = next(iter(hashes.keys()))
                        cand = os.path.join(dir_inject, rel)
                        if os.path.isfile(cand):
                            drifted_file = cand
                            break
        if drifted_file:
            with open(drifted_file, "a", encoding="utf-8") as f:
                f.write("\n// DRIFT MANUAL INJETADO PARA TESTE\n")
            print(f"  [*] Editado manualmente: {drifted_file}")
            r = run("3.6-G_INJECT-divergente", [PYTHON, g_inject_script, "--dir", dir_inject], cwd=ENT_DIR, env=env_base)
            RESULTS[-1]["ok"] = (r.returncode != 0) if r else False
            RESULTS[-1]["notes"] = f"esperado exit != 0 (drift), obtido exit={r.returncode if r else '?'}"
        else:
            RESULTS.append({"item": "3.6-G_INJECT-divergente", "exit_code": -1, "ok": False, "duration": 0,
                             "stdout": "", "stderr": "", "notes": "LIMITACAO: nenhum arquivo hash-tracked encontrado em CAPABILITIES.json do projeto"})

        # 3.7 bench, heal, scaffold-infra
        run("3.7-bench", aidd("bench", "-n", "50", "--dir", dir_suite), cwd=ENT_DIR, env=env_base)
        run("3.7-heal", aidd("heal", "--dir", dir_suite), cwd=ENT_DIR, env=env_base, timeout=300)
        run("3.7-scaffold-infra", aidd("scaffold-infra", "--dir", dir_suite), cwd=ENT_DIR, env=env_base)

        # 3.8 export-frontend, refine-module, deploy docker
        run("3.8-export-frontend", aidd("export-frontend", "--dir", dir_suite), cwd=ENT_DIR, env=env_base, timeout=120)

        feature_crm = os.path.join(dir_suite, "features", "crm.feature")
        feature_exists = os.path.isfile(feature_crm)
        RESULTS.append({"item": "3.8-refine-module-check", "exit_code": 0 if feature_exists else -1,
                         "ok": feature_exists, "duration": 0, "stdout": f"features/crm.feature exists={feature_exists}",
                         "stderr": "", "notes": "compose gera .feature automaticamente" if feature_exists else
                         "LIMITACAO: compose NAO gerou features/*.feature automaticamente"})
        if feature_exists:
            run("3.8-refine-module", aidd("refine-module", "crm", "--dir", dir_suite), cwd=ENT_DIR, env=env_base, timeout=120)

        docker_available = shutil.which("docker") is not None
        compose_file = os.path.join(dir_suite, "docker-compose.yml")
        has_compose_file = os.path.isfile(compose_file)
        if docker_available and has_compose_file:
            run("3.8-deploy-docker", [PYTHON, AIDD_CLI, "deploy", "docker"], cwd=dir_suite, env=env_base, timeout=120)
            subprocess.run(["docker", "compose", "down"], cwd=dir_suite, capture_output=True)
        else:
            RESULTS.append({"item": "3.8-deploy-docker", "exit_code": -1, "ok": False, "duration": 0, "stdout": "", "stderr": "",
                             "notes": f"LIMITACAO DE AMBIENTE: docker_available={docker_available} has_compose_file={has_compose_file}"})

        # 3.9 compose-orca
        os.makedirs(dir_orca, exist_ok=True)
        r = run("3.9-compose-orca", aidd("compose-orca", "--dir", dir_orca, "--suite-name", "Suite Orca Enterprise", "crm", "erp"), cwd=ENT_DIR, env=env_base, timeout=120)
        if r and r.returncode == 0:
            manifest = os.path.join(dir_orca, "COMPOSE-ORCA-MANIFEST.json")
            RESULTS[-1]["manifest_exists"] = os.path.isfile(manifest)

        # 3.10 pytest suite completa
        r = run("3.10-pytest-suite", [PYTHON, "-m", "pytest", "tests/", "-q", "--tb=short"], cwd=ENT_DIR, env=env_base, timeout=600)
        if r:
            combined = (r.stdout or "") + (r.stderr or "")
            for line in combined.split("\n"):
                if "passed" in line or "failed" in line or "error" in line:
                    RESULTS[-1]["pytest_summary"] = line.strip()

    finally:
        print(f"\n[*] Limpando poluição real (hooks canônicos + espelhos): {hook_names_para_limpar}")
        limpar_poluicao_hook_real(hook_names_para_limpar)
        print(f"[*] Limpando temporários: {tmp_base}")
        shutil.rmtree(tmp_base, ignore_errors=True)
        print("[OK] Limpeza concluída.")

    print(f"\n{'='*70}")
    print("RESUMO DA BATERIA 3 (AIDD Enterprise)")
    print(f"{'='*70}")
    passed = sum(1 for r in RESULTS if r.get("ok"))
    failed = sum(1 for r in RESULTS if not r.get("ok"))
    print(f"PASS: {passed}  FAIL: {failed}  TOTAL: {len(RESULTS)}")
    for r in RESULTS:
        icon = "PASS" if r.get("ok") else "FAIL"
        print(f"  [{icon}] {r['item']:40s} exit={r.get('exit_code', '?')}")
        if r.get("notes"):
            print(f"         {str(r['notes'])[:160]}")

    out_path = os.path.join(REPO_ROOT, "docs", "testes", "testes", "_resultados_enterprise.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, ensure_ascii=False, indent=2)
    print(f"\n[*] Resultados salvos: {out_path}")
    return failed


if __name__ == "__main__":
    sys.exit(main())
