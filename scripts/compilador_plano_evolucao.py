import argparse
import json
import re
import sys
from pathlib import Path

CAMPOS_EXECUCAO = ("harness", "model", "comando_terminal")

# Palavras frequentes em PT-BR que não existem em inglês: detector determinístico
# para a regra "prompts_tickets só em inglês telegráfico imperativo".
PALAVRAS_PT = {
    "de", "da", "das", "dos", "que", "para", "com", "um", "uma", "nao", "ao",
    "na", "em", "pelo", "pela", "se", "teste", "testes", "crie", "adicione",
    "implemente", "execute", "rode", "arquivo", "arquivos", "deve", "sem", "cada",
}


def carregar_rotativo(config_file: Path) -> list:
    """Lê 'pipeline_evolucao_rotativo'; reprova se ausente ou incompleto (sem padrão inventado)."""
    try:
        config = json.loads(Path(config_file).read_text(encoding="utf-8"))
    except (OSError, TypeError, json.JSONDecodeError) as erro:
        raise ValueError(f"CONFIG-EXECUCAO-USUARIO.json ilegível em {config_file}: {erro}") from erro

    rotativo = config.get("pipeline_evolucao_rotativo") or []
    if not rotativo:
        raise ValueError("CONFIG-EXECUCAO-USUARIO.json sem 'pipeline_evolucao_rotativo'")
    for i, entrada in enumerate(rotativo):
        faltando = [c for c in CAMPOS_EXECUCAO if not str((entrada or {}).get(c, "")).strip()]
        if faltando:
            raise ValueError(
                f"CONFIG-EXECUCAO-USUARIO.json: pipeline_evolucao_rotativo[{i}] sem {', '.join(faltando)}"
            )
    return [{c: e[c] for c in CAMPOS_EXECUCAO} for e in rotativo]


def extrair_prompt_ingles(num: str, corpo: str, md_path: Path) -> str:
    """Bloco '**Construtor Prompt (EN):**' do ticket; reprova se ausente ou não-inglês."""
    bloco = re.search(r"\*\*Construtor Prompt \(EN\):\*\*[ \t]*\n((?:[ \t]+-[^\n]*\n?)+)", corpo)
    if not bloco:
        raise ValueError(f"Ticket {num} sem bloco '- **Construtor Prompt (EN):**' em {md_path}")
    passos = [linha.strip()[1:].strip() for linha in bloco.group(1).splitlines() if linha.strip()]
    texto = "\n".join(f"- {p}" for p in passos)
    # Só palavras soltas contam: caminhos, identificadores e flags (G_PORTAO_PROVA_QUE_MORDE,
    # docs/diagnosticos/, --sintoma) são nomes próprios do repo, não idioma.
    palavras_soltas = {
        tok.strip(".,:;!?\"'()").lower()
        for tok in texto.split()
        if not re.search(r"[_/\\=<>`]|^-|\.\w", tok)
    }
    palavras_pt = sorted(palavras_soltas & PALAVRAS_PT)
    if not texto.isascii() or palavras_pt:
        raise ValueError(
            f"Ticket {num}: Construtor Prompt (EN) não está em inglês "
            f"(não-ASCII={not texto.isascii()}, palavras PT={palavras_pt}) em {md_path}"
        )
    return texto


def parse_plano_evolucao_md(md_path: Path):
    if not md_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {md_path}")

    content = md_path.read_text(encoding="utf-8")

    # Extrai tickets usando regex: ### Ticket N: Título (Refere-se a D_ / DoD _)
    ticket_pattern = re.compile(
        r"###\s+(Ticket\s+(\d+):\s+([^\n]+))\n(.*?)(?=(?:###\s+Ticket|\Z))",
        re.DOTALL
    )

    tickets = []
    for full_title, num, titulo_limpo, corpo in ticket_pattern.findall(content):
        dim_match = re.search(r"\*\*Falha 15-D:\*\*\s*`?([^`\n]+)`?", corpo)
        dimensao = dim_match.group(1).strip() if dim_match else "D3. Raio de Impacto"

        # Handoff declarado pelo Arquiteto no próprio ticket (sem mapa fixo por ferramenta)
        handoff_match = re.search(r"\*\*Artefato de Handoff:\*\*\s*`([^`\n]+)`", corpo)
        if not handoff_match:
            raise ValueError(
                f"Ticket {num} sem '- **Artefato de Handoff:** `<caminho>`' em {md_path}"
            )

        tickets.append({
            "num": int(num),
            "titulo": titulo_limpo.strip(),
            "dimensao_15d": dimensao,
            "output_handoff": handoff_match.group(1).strip(),
            "prompt_en": extrair_prompt_ingles(num, corpo, md_path),
            "nome": f"Fase_{num}_Ticket_{num}_{re.sub(r'[^a-zA-Z0-9_]', '_', titulo_limpo.split('(')[0].strip())}",
        })
    return tickets


def codigo_dimensao(dimensao: str) -> str:
    """'D11. Tratamento de Exceções' -> 'D11' (o nome da dimensão é PT-BR; o prompt não)."""
    m = re.match(r"\s*(D\d+)", dimensao)
    return m.group(1) if m else "UNSPECIFIED"


def escrever_prompt_ticket(prompts_dir: Path, tool_name: str, t: dict) -> Path:
    """Prompt do Construtor em inglês telegráfico imperativo (regra inquebrável)."""
    prompt_file = prompts_dir / f"PROMPT-TICKET-{t['num']:02d}.txt"
    prompt_file.write_text(f"""ROLE: Builder. Ecosystem AIDD. Ticket {t['num']}. Target tool: {tool_name}.
DIMENSION: {codigo_dimensao(t['dimensao_15d'])}
DELIVER: {t['output_handoff']}

STEPS:
{t['prompt_en']}

RULES:
1. Write failing test first. Run. Assert exit 1.
2. Implement. Zero stubs. Real pytest tests. Run. Assert exit 0.
3. Work inside ephemeral Git Worktree only.
4. Capture real exit code: redirect to file, read $? same line. Never trust pipes.
5. NEVER edit docs/auditoria/CONFIG-EXECUCAO-USUARIO.json.
6. Deliver exactly: {t['output_handoff']}
""", encoding="utf-8")
    return prompt_file


def compilar_plano_evolucao(md_file: Path, config_file: Path = None, output_file: Path = None):
    tool_dir = md_file.parent
    tool_name = tool_dir.name

    # Valida tudo ANTES de escrever qualquer arquivo (falha não deixa prompt parcial)
    lista_rotativa = carregar_rotativo(config_file)
    tickets = parse_plano_evolucao_md(md_file)

    prompts_dir = tool_dir / "prompts_tickets"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    fases = []
    repo_root = Path.cwd()
    for i, t in enumerate(tickets):
        config_fase = lista_rotativa[i % len(lista_rotativa)]  # rodízio (Round-Robin)
        prompt_file = escrever_prompt_ticket(prompts_dir, tool_name, t)
        try:
            input_rel = prompt_file.relative_to(repo_root).as_posix()
        except ValueError:
            input_rel = prompt_file.as_posix()

        fases.append({
            "ticket_id": f"TICKET-{t['num']:02d}",
            "nome": t["nome"],
            "dimensao_15d": t["dimensao_15d"],
            "harness": config_fase["harness"],
            "model": config_fase["model"],
            "comando_terminal": config_fase["comando_terminal"],
            "input_prompt": input_rel,
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
    
    try:
        compilar_plano_evolucao(Path(args.plano), Path(args.config), Path(args.out) if args.out else None)
    except (FileNotFoundError, ValueError) as erro:
        print(f"[ERRO] {erro}")
        sys.exit(1)

if __name__ == "__main__":
    main()
