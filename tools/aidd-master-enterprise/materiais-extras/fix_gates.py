import re

with open('scripts/gates/G_QUALIDADE.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add check for docs.html
docs_check = """
    # 4. Check for generated docs.html
    static_dir = os.path.join(src_dir, "static")
    docs_file = os.path.join(static_dir, "docs.html")
    if os.path.isfile(docs_file):
        with open(docs_file, "r", encoding="utf-8") as df:
            dhtml = df.read()
            if not dhtml.strip():
                erros.append("O arquivo docs.html foi gerado em branco (tela branca).")
            # Validação anti-mock legacy
            legados = ["PEP", "Manchester", "TISS", "TUSS", "Prontuário"]
            for leg in legados:
                if leg in dhtml:
                    erros.append(f"Termo legado detectado na documentação final: {leg}")

    if erros:
"""

content = content.replace("    if erros:", docs_check)

with open('scripts/gates/G_QUALIDADE.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("scripts/gates/G_QUALIDADE.py atualizado para validar docs.html.")
