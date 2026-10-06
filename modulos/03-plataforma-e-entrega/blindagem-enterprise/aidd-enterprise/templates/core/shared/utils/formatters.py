import re

def formatar_moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_telefone(telefone: str) -> str:
    limpo = re.sub(r'\D', '', telefone)
    if len(limpo) == 11:
        return f"({limpo[:2]}) {limpo[2:7]}-{limpo[7:]}"
    elif len(limpo) == 10:
        return f"({limpo[:2]}) {limpo[2:6]}-{limpo[6:]}"
    return limpo

def sanitizar_whatsapp(telefone: str) -> str:
    limpo = re.sub(r'\D', '', telefone)
    if not limpo.startswith("55") and len(limpo) in [10, 11]:
        limpo = "55" + limpo
    return limpo
