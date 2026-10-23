import os
import re

def patch_paleta():
    caminhos_html = [
        "componentes/compartilhado/moldes/quarteto/webhook_studio.html",
        "componentes/compartilhado/moldes/quarteto/mcp_studio.html",
        "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/core/webhook_studio.html",
        "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/core/mcp_studio.html",
        "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/webhook_studio.html",
        "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/mcp_studio.html",
        "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/src/core/webhook_studio.html",
        "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/src/core/mcp_studio.html",
        "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/v2/webhook_studio.html",
        "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/v2/mcp_studio.html",
    ]

    for p in caminhos_html:
        if os.path.isfile(p):
            conteudo = open(p, "r", encoding="utf-8").read()
            conteudo = re.sub(r"--primary:\s*(?:#[0-9a-fA-F]+|__PRIMARY__);", "--primary: __PRIMARY__;", conteudo)
            conteudo = re.sub(r"--primary-hover:\s*(?:#[0-9a-fA-F]+|__PRIMARY_HOVER__);", "--primary-hover: __PRIMARY_HOVER__;", conteudo)
            open(p, "w", encoding="utf-8").write(conteudo)
            print(f"[OK] Placeholders __PRIMARY__ garantidos em {p}")

    caminhos_webhooks = [
        "componentes/compartilhado/moldes/quarteto/webhooks.py",
        "componentes/compartilhado/src-core/webhooks.py",
        "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/core/webhooks.py",
        "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/webhooks.py",
        "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/src/core/webhooks.py",
        "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/v2/webhooks.py",
    ]

    for p in caminhos_webhooks:
        if os.path.isfile(p):
            conteudo = open(p, "r", encoding="utf-8").read()
            # Assegurar substituição de __PRIMARY__ e fallback regex
            bloco_antigo = """        if primary:
            _html = _html.replace("--primary: #0284c7;", f"--primary: {primary};")
        if primary_hover:
            _html = _html.replace("--primary-hover: #0369a1;", f"--primary-hover: {primary_hover};")"""
            bloco_novo = """        cor_primaria = primary or "#0f766e"
        cor_primaria_hover = primary_hover or "#115e59"
        _html = _html.replace("__PRIMARY__", str(cor_primaria))
        _html = _html.replace("__PRIMARY_HOVER__", str(cor_primaria_hover))
        if primary:
            _html = re.sub(r"--primary:\s*#[0-9a-fA-F]+;", f"--primary: {primary};", _html)
        if primary_hover:
            _html = re.sub(r"--primary-hover:\s*#[0-9a-fA-F]+;", f"--primary-hover: {primary_hover};", _html)"""
            if bloco_antigo in conteudo:
                conteudo = conteudo.replace(bloco_antigo, bloco_novo)
                open(p, "w", encoding="utf-8").write(conteudo)
                print(f"[OK] webhooks.py atualizado em {p}")
            else:
                # Se já tiver __PRIMARY__
                if "_html = _html.replace(\"__PRIMARY__\"" not in conteudo:
                    conteudo = conteudo.replace(
                        'return _html',
                        'cor_primaria = primary or "#0f766e"\n        cor_primaria_hover = primary_hover or "#115e59"\n        _html = _html.replace("__PRIMARY__", str(cor_primaria))\n        _html = _html.replace("__PRIMARY_HOVER__", str(cor_primaria_hover))\n        return _html'
                    )
                    open(p, "w", encoding="utf-8").write(conteudo)
                    print(f"[OK] webhooks.py modificado em {p}")

    caminhos_mcp = [
        "componentes/compartilhado/moldes/quarteto/mcp_server.py",
        "componentes/compartilhado/src-core/mcp_server.py",
        "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/src/core/mcp_server.py",
        "modulos/03-plataforma-e-entrega/fatiamento-master/aidd-master/templates/v2/mcp_server.py",
        "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/src/core/mcp_server.py",
        "modulos/03-plataforma-e-entrega/blindagem-enterprise/aidd-enterprise/templates/v2/mcp_server.py",
    ]

    for p in caminhos_mcp:
        if os.path.isfile(p):
            conteudo = open(p, "r", encoding="utf-8").read()
            # Atualizar assinatura se for def get_studio_html(self, title: str = "AIDD Enterprise — MCP Server Studio") -> str:
            conteudo = re.sub(
                r'def get_studio_html\(\s*self,\s*title:\s*str\s*=\s*"[^"]*"\s*\)\s*->\s*str:',
                'def get_studio_html(\n        self,\n        title: str = "AIDD Enterprise — MCP Server Studio",\n        primary: str = "#0f766e",\n        primary_hover: str = "#115e59",\n    ) -> str:',
                conteudo
            )
            if "_html.replace(\"__PRIMARY__\"" not in conteudo:
                conteudo = conteudo.replace(
                    '_html = _html.replace("__TOOLS_JSON__", str(json.dumps(tools, ensure_ascii=False)))',
                    '_html = _html.replace("__TOOLS_JSON__", str(json.dumps(tools, ensure_ascii=False)))\n        cor_primaria = primary or "#0f766e"\n        cor_primaria_hover = primary_hover or "#115e59"\n        _html = _html.replace("__PRIMARY__", str(cor_primaria))\n        _html = _html.replace("__PRIMARY_HOVER__", str(cor_primaria_hover))\n        if primary:\n            _html = re.sub(r"--primary:\\s*#[0-9a-fA-F]+;", f"--primary: {primary};", _html)\n        if primary_hover:\n            _html = re.sub(r"--primary-hover:\\s*#[0-9a-fA-F]+;", f"--primary-hover: {primary_hover};", _html)'
                )
            open(p, "w", encoding="utf-8").write(conteudo)
            print(f"[OK] mcp_server.py atualizado em {p}")

if __name__ == "__main__":
    patch_paleta()
