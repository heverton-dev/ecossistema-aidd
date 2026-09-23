import argparse
import json
import re
import sys
from pathlib import Path

def parse_plano_evolucao_md(md_path: Path):
    if not md_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {md_path}")
        
    content = md_path.read_text(encoding="utf-8")
    
    # Extrai tickets usando regex: ### Ticket N: Título (Refere-se a D_ / DoD _)
    ticket_pattern = re.compile(
        r"###\s+(Ticket\s+(\d+):\s+([^\n]+))\n(.*?)(?=(?:###\s+Ticket|\Z))",
        re.DOTALL
    )
    
    matches = ticket_pattern.findall(content)
    tickets = []
    
    for full_title, num, titulo_limpo, corpo in matches:
        # Extrai dimensão 15D
        dim_match = re.search(r"\*\*Falha 15-D:\*\*\s*`?([^`\n]+)`?", corpo)
        dimensao = dim_match.group(1).strip() if dim_match else "D3. Raio de Impacto"
        
        # Extrai handoff esperado ou script alvo
        handoff_match = re.search(r"(`(?:[a-zA-Z0-9_\-\./\\]+\.(?:py|md|json|txt))`|tests/test_[a-zA-Z0-9_]+\.py|gates/G_[a-zA-Z0-9_]+\.py)", corpo)
        handoff = handoff_match.group(1).strip("`") if handoff_match else f"tests/test_ticket_{num}.py"
        
        nome_fase = f"Fase_{num}_Ticket_{num}_{re.sub(r'[^a-zA-Z0-9_]', '_', titulo_limpo.split('(')[0].strip())}"
        
        tickets.append({
            "ticket_id": f"TICKET-{int(num):02d}",
            "nome": nome_fase,
            "titulo": titulo_limpo.strip(),
            "dimensao_15d": dimensao,
            "input_prompt": f"{md_path.as_posix()}#ticket-{num}",
            "output_handoff": handoff,
            "harness": "auto",
            "model": "auto",
            "comando_terminal": "auto"
        })
        
    return tickets

def compilar_plano_evolucao(md_file: Path, config_file: Path = None, output_file: Path = None):
    tool_dir = md_file.parent
    tool_name = tool_dir.name
    
    tickets = parse_plano_evolucao_md(md_file)
    
    # Carrega config do usuário com suporte a revezamento cíclico (Round-Robin)
    user_config = {}
    if config_file and config_file.exists():
        with open(config_file, "r", encoding="utf-8") as cf:
            user_config = json.load(cf)
            
    lista_rotativa = user_config.get("pipeline_evolucao_rotativo")
    if not lista_rotativa:
        construtor = user_config.get("pipeline_auditoria_4f", {}).get("construtor") or user_config.get("padrao_geral", {})
        lista_rotativa = [construtor] if construtor else [{
            "harness": "agy",
            "model": "gemini-3.8-flash-high",
            "comando_terminal": "agy --model gemini-3.8-flash-high --dangerously-skip-permissions"
        }]
    
    num_opcoes = len(lista_rotativa)
    fases = []
    for i, t in enumerate(tickets):
        config_fase = lista_rotativa[i % num_opcoes]
        fases.append({
            "ticket_id": t["ticket_id"],
            "nome": t["nome"],
            "dimensao_15d": t["dimensao_15d"],
            "harness": config_fase.get("harness", "agy"),
            "model": config_fase.get("model", "gemini-3.8-flash-high"),
            "comando_terminal": config_fase.get("comando_terminal", "agy --model gemini-3.8-flash-high --dangerously-skip-permissions"),
            "input_prompt": t["input_prompt"],
            "output_handoff": t["output_handoff"]
        })
        
    manifesto = {
        "pipeline_id": f"evolucao-{tool_name}",
        "target_tool": tool_name,
        "descricao": f"Plano de Evolução Tática montado a partir dos {len(fases)} tickets de {md_file.name}",
        "config_usuario_ref": config_file.as_posix() if config_file else None,
        "definition_of_done": (tool_dir / "DOD.md").as_posix(),
        "fases": fases
    }
    
    if not output_file:
        output_file = tool_dir / "PLANO-EVOLUCAO.json"
        
    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(manifesto, out, indent=2, ensure_ascii=False)
        
    print(f"[OK] Manifesto compilado com sucesso: {output_file} ({len(fases)} fases montadas)")
    return output_file

def main():
    parser = argparse.ArgumentParser(description="Compilador determinístico de PLANO-EVOLUCAO.md para PLANO-EVOLUCAO.json")
    parser.add_argument("--plano", required=True, help="Caminho para o PLANO-EVOLUCAO.md")
    parser.add_argument("--config", default="docs/auditoria/CONFIG-EXECUCAO-USUARIO.json", help="Caminho para CONFIG-EXECUCAO-USUARIO.json")
    parser.add_argument("--out", help="Arquivo JSON de saída")
    args = parser.parse_args()
    
    compilar_plano_evolucao(Path(args.plano), Path(args.config), Path(args.out) if args.out else None)

if __name__ == "__main__":
    main()
