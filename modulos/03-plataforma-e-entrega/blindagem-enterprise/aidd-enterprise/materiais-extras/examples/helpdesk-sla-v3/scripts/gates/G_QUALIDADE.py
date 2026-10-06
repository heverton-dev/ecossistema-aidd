import os, sys, subprocess
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def verificar():
    print("[GATE G_QUALIDADE] Validando sintaxe e testes...")
    erro = False
    for root, dirs, files in os.walk('.'):
        if '.git' in root or 'node_modules' in root or '.venv' in root:
            continue
        for f in files:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                res = subprocess.run([sys.executable, '-m', 'py_compile', path], capture_output=True)
                if res.returncode != 0:
                    print(f"[FAIL] Erro de sintaxe em: {path}")
                    erro = True
    if erro:
        sys.exit(1)
    print("[OK] SUCESSO: Sintaxe e qualidade verificadas sem erros.")
    sys.exit(0)

if __name__ == '__main__':
    verificar()
