import os, sys, re, math

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PADROES_CONHECIDOS = [
    r'sk-[a-zA-Z0-9]{20,}',
    r'AIza[0-9A-Za-z-_]{35}',
    r'ghp_[a-zA-Z0-9]{36}',
    r'xox[baprs]-[0-9a-zA-Z]{10,48}',
    r'aidd_enterprise_master_jwt_secret_key'
]

def calcular_entropia_shannon(texto: str) -> float:
    if not texto:
        return 0.0
    freq = {}
    for c in texto:
        freq[c] = freq.get(c, 0) + 1
    entropia = 0.0
    for count in freq.values():
        p = count / len(texto)
        entropia -= p * math.log2(p)
    return entropia

def verificar():
    print("[GATE G_SEGREDOS v2.0 - Shannon Entropy Engine] Escaneando codigo por credenciais...")
    vazamentos = 0
    
    for root, dirs, files in os.walk('.'):
        if any(ignored in root for ignored in ['.git', 'node_modules', '.venv', '__pycache__', '.pytest_cache']):
            continue
        for f in files:
            if f == 'G_SEGREDOS.py':
                continue
            if f.endswith(('.py', '.js', '.json', '.md', '.env.example', '.yml', '.yaml')):
                path = os.path.join(root, f)
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                        linhas = fp.readlines()
                        for num, linha in enumerate(linhas, 1):
                            # 1. Regex de prefixos conhecidos
                            for padrao in PADROES_CONHECIDOS:
                                if re.search(padrao, linha):
                                    print(f"[FAIL] Chave com prefixo conhecida detectada em {path}:{num}")
                                    vazamentos += 1
                            # 2. Entropia de Shannon para tokens/hex/base64 suspeitos (sem barras/caminhos)
                            palavras = re.findall(r'\b[A-Za-z0-9_\-+=]{32,}\b', linha)
                            for p in palavras:
                                if calcular_entropia_shannon(p) > 4.6 and not p.isupper():
                                    print(f"[FAIL] String de alta entropia ({calcular_entropia_shannon(p):.2f}) detectada em {path}:{num}")
                                    vazamentos += 1
                except:
                    pass

    if vazamentos > 0:
        print(f"[FAIL] 🚫 Bloqueado: {vazamentos} potenciais vazamentos de segredos detectados!")
        sys.exit(1)
        
    print("[OK] SUCESSO: Zero vazamentos detectados (Scan de Entropia de Shannon aprovado).")
    sys.exit(0)

if __name__ == '__main__':
    verificar()
