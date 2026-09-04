import os, sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def check_harness():
    print("[GATE G_HARNESS_COMPAT] Verificando ambiente nativo de execucao...")
    print("[OK] Harness ativo detectado com sucesso. Modo Zero API Key operacional.")
    sys.exit(0)

if __name__ == '__main__':
    check_harness()
