import os, sys, json, shutil

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def check_harness():
    print("[GATE G_HARNESS_COMPAT v5.1] Verificando compatibilidade multi-harness...")
    erros = []
    
    # 1. Scripts de automação essenciais
    for s in ["scripts/aidd.py", "scripts/add_module.py"]:
        if not os.path.exists(s):
            erros.append(f"Script de automação ausente: {s}")

    # 2. Detecção Híbrida do Ambiente de Orquestração (ORCA vs Subagentes Nativos)
    orca_bin = shutil.which("orca")
    if orca_bin:
        print("  [INFO] Modo de Orquestração Detectado: ORCA ADE (Mesas Isoladas via Worktree)")
    else:
        print("  [INFO] Modo de Orquestração Detectado: Subagentes Nativos / Git Worktree Standard (Fallback Automático)")

    # 3. Validação do Manifesto
    if os.path.exists("PLANO-EXECUCAO-ESTRUTURADO.json"):
        try:
            with open("PLANO-EXECUCAO-ESTRUTURADO.json", "r", encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            erros.append(f"PLANO-EXECUCAO-ESTRUTURADO.json corrompido: {e}")

    if erros:
        print("\n[FAIL] Incompatibilidade detectada:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
        
    print("[OK] SUCESSO: Ambiente 100% compatível (Zero API Key nativo).")
    sys.exit(0)

if __name__ == '__main__':
    check_harness()
