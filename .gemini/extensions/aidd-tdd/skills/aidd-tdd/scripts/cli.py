import argparse
import datetime
import json
import os
import sys
from pathlib import Path

def iniciar_sessao(alvo: str, seam: str, output: str = None) -> int:
    agora = datetime.datetime.now()
    timestamp = agora.strftime("%Y-%m-%d_%H%M%S")
    slug = seam.replace(" ", "_").lower()
    
    if not output:
        output_dir = Path("docs") / "tdd" / f"{timestamp}_{slug}"
        output_dir.mkdir(parents=True, exist_ok=True)
        caminho_sessao = output_dir / "sessao.json"
    else:
        caminho_sessao = Path(output)
        caminho_sessao.parent.mkdir(parents=True, exist_ok=True)
        
    estado = {
        "versao": "1.0",
        "criado_em": agora.isoformat(),
        "alvo": alvo,
        "seam": seam,
        "fase_atual": "SEAM_ACORDADO",
        "historico_fases": [
            {"fase": "SEAM_ACORDADO", "timestamp": agora.isoformat()}
        ],
        "testes": [],
        "tentativas_red_green": 0
    }
    
    with open(caminho_sessao, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
        
    print(f"[OK] Sessão TDD iniciada: {caminho_sessao}")
    return 0

def transicionar(sessao_path: str, nova_fase: str, extra: dict = None) -> int:
    p = Path(sessao_path)
    if not p.exists():
        print(f"Erro: Arquivo de sessão '{sessao_path}' não encontrado.", file=sys.stderr)
        return 1
        
    with open(p, "r", encoding="utf-8") as f:
        estado = json.load(f)
        
    agora = datetime.datetime.now().isoformat()
    registro = {"fase": nova_fase, "timestamp": agora}
    if extra:
        registro.update(extra)
        
    estado["fase_atual"] = nova_fase
    estado["historico_fases"].append(registro)
    if extra and "teste" in extra and extra["teste"] not in estado["testes"]:
        estado["testes"].append(extra["teste"])
        
    with open(p, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
        
    print(f"[OK] Transição para {nova_fase} gravada em {p}")
    return 0

def obter_status(sessao_path: str) -> int:
    p = Path(sessao_path)
    if not p.exists():
        print(f"Erro: Arquivo de sessão '{sessao_path}' não encontrado.", file=sys.stderr)
        return 1
    with open(p, "r", encoding="utf-8") as f:
        estado = json.load(f)
    print(json.dumps(estado, indent=2, ensure_ascii=False))
    return 0

def main(args=None):
    if args is None:
        args = sys.argv[1:]
        
    parser = argparse.ArgumentParser(description="CLI determinística para protocolo AIDD-TDD")
    subparsers = parser.add_subparsers(dest="subcomando", required=True)
    
    # iniciar
    p_iniciar = subparsers.add_parser("iniciar", help="Inicia uma nova sessão de TDD com seam acordado")
    p_iniciar.add_argument("--alvo", required=True, help="Arquivo ou módulo alvo da implementação")
    p_iniciar.add_argument("--seam", required=True, help="Nome do seam público acordado")
    p_iniciar.add_argument("--output", default=None, help="Caminho opcional do arquivo de saída sessao.json")
    
    # red
    p_red = subparsers.add_parser("red", help="Registra transição para estágio RED")
    p_red.add_argument("--sessao", required=True, help="Caminho para sessao.json")
    p_red.add_argument("--teste", required=True, help="Arquivo do teste escrito")
    
    # green
    p_green = subparsers.add_parser("green", help="Registra transição para estágio GREEN")
    p_green.add_argument("--sessao", required=True, help="Caminho para sessao.json")
    
    # refactor
    p_refactor = subparsers.add_parser("refactor", help="Registra transição para estágio REFACTOR")
    p_refactor.add_argument("--sessao", required=True, help="Caminho para sessao.json")
    
    # status
    p_status = subparsers.add_parser("status", help="Exibe status da sessão")
    p_status.add_argument("--sessao", required=True, help="Caminho para sessao.json")
    
    parsed = parser.parse_args(args)
    
    if parsed.subcomando == "iniciar":
        return iniciar_sessao(parsed.alvo, parsed.seam, parsed.output)
    elif parsed.subcomando == "red":
        return transicionar(parsed.sessao, "RED", {"teste": parsed.teste})
    elif parsed.subcomando == "green":
        return transicionar(parsed.sessao, "GREEN")
    elif parsed.subcomando == "refactor":
        return transicionar(parsed.sessao, "REFACTOR")
    elif parsed.subcomando == "status":
        return obter_status(parsed.sessao)
        
    return 1

if __name__ == "__main__":
    sys.exit(main())
