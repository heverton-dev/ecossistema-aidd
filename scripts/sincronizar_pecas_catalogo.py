import os
import json
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CATALOGO_PATH = ROOT_DIR / "componentes" / "compartilhado" / "CATALOGO.json"

def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return "sha256-" + h.hexdigest()

def sincronizar():
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        catalogo = json.load(f)

    pecas_modificadas = 0
    copias_atualizadas = 0

    for peca in catalogo.get("pecas", []):
        caminho_rel = peca.get("caminho", "")
        caminho_peca = ROOT_DIR / caminho_rel
        if not caminho_peca.is_file():
            continue

        novo_sha = sha256_arquivo(caminho_peca)
        if peca.get("sha256") != novo_sha:
            peca["sha256"] = novo_sha
            pecas_modificadas += 1

        # Sincronizar cópias para serem byte-idênticas à peça
        conteudo_peca = caminho_peca.read_bytes()
        for copia_rel in peca.get("copias", []):
            caminho_copia = ROOT_DIR / copia_rel
            if caminho_copia.is_file():
                if caminho_copia.read_bytes() != conteudo_peca:
                    caminho_copia.write_bytes(conteudo_peca)
                    copias_atualizadas += 1
                    print(f"[COPIA SYNC] {copia_rel} atualizada a partir de {caminho_rel}")

    with open(CATALOGO_PATH, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Sincronização concluída: {pecas_modificadas} selos atualizados em CATALOGO.json, {copias_atualizadas} cópias sincronizadas.")

if __name__ == "__main__":
    sincronizar()
