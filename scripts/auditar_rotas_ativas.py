import urllib.request
import json

def testar(url, headers=None):
    if headers is None:
        headers = {}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            ct = r.headers.get("Content-Type", "")
            corpo = r.read().decode("utf-8", errors="replace")
            print(f"=== {url} ===")
            print(f"Status: {r.status} | Content-Type: {ct}")
            print(f"Tamanho: {len(corpo)} bytes")
            print(f"Possui class='dark'?: {'class=\"dark\"' in corpo}")
            print(f"Contém paleta do projeto (#0f766e)?: {'#0f766e' in corpo.lower()}")
            if "json" in ct:
                dados = json.loads(corpo)
                print("JSON chaves:", list(dados.keys())[:8])
                if "status" in dados:
                    print("Status JSON:", dados["status"])
            else:
                for linha in corpo.splitlines():
                    if "<title>" in linha:
                        print("Título:", linha.strip())
                        break
    except Exception as e:
        print(f"=== {url} === ERRO: {e}")

if __name__ == "__main__":
    testar("http://localhost:3000/")
    testar("http://localhost:3000/docs")
    testar("http://localhost:3000/webhook")
    testar("http://localhost:3000/mcp")
    testar("http://localhost:3000/api/metrics")
    testar("http://localhost:3000/metrics", headers={"Accept": "text/html"})
    testar("http://localhost:3000/metrics", headers={"Accept": "text/plain"})
