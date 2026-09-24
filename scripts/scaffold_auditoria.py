import argparse
import json
import os
import sys
from pathlib import Path

GATE_15D_CODE = '''import os
import sys

def run_gate(markdown_path):
    print(f"[{__file__}] Iniciando Quality Gate na entrega: {markdown_path}")
    
    if not os.path.exists(markdown_path):
        print(f"EXIT 1: Arquivo de laudo '{markdown_path}' não encontrado.")
        sys.exit(1)

    try:
        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"EXIT 1: Falha ao ler o arquivo. Erro: {e}")
        sys.exit(1)

    falhas = []
    for i in range(1, 16):
        dim_key = f"D{i}."
        if dim_key not in content:
            falhas.append(f"Falta a dimensão: {dim_key}")

    if "Matriz de Avaliação da Execução" not in content:
        falhas.append("Falta a 'Matriz de Avaliação da Execução'.")

    if falhas:
        print("EXIT 1: O Laudo 15-D foi rejeitado. As seguintes métricas estão ausentes:")
        for falha in falhas:
            print(f" - {falha}")
        print("\\nO Agente deve reconstruir o arquivo garantindo a aderência exata ao TEMPLATE-AUDITORIA-FERRAMENTA.md.")
        sys.exit(1)

    print("EXIT 0: Laudo 15-D perfeito. Todas as 15 dimensões estão presentes.")
    sys.exit(0)

if __name__ == "__main__":
    revisado_target = os.path.join(os.path.dirname(__file__), "LAUDO-15D-REVISADO.md")
    inicial_target = os.path.join(os.path.dirname(__file__), "LAUDO-15D-INICIAL.md")
    default_target = revisado_target if os.path.exists(revisado_target) else inicial_target
    target = sys.argv[1] if len(sys.argv) > 1 else default_target
    run_gate(target)
'''

PAPEIS_4F = ("inspetor", "arquiteto", "construtor", "retorno")
CAMPOS_EXECUCAO = ("harness", "model", "comando_terminal")


def carregar_papeis_4f(config_path: Path) -> dict:
    """Lê 'pipeline_auditoria_4f' do config; reprova se papel/campo faltar."""
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        raise ValueError(f"CONFIG-EXECUCAO-USUARIO.json ilegível em {config_path}: {erro}") from erro

    papeis = config.get("pipeline_auditoria_4f") or {}
    faltando = [
        f"{papel}.{campo}"
        for papel in PAPEIS_4F
        for campo in CAMPOS_EXECUCAO
        if not str((papeis.get(papel) or {}).get(campo, "")).strip()
    ]
    if faltando:
        raise ValueError(
            f"CONFIG-EXECUCAO-USUARIO.json sem 'pipeline_auditoria_4f' completo; faltam: {', '.join(faltando)}"
        )
    return {p: {c: papeis[p][c] for c in CAMPOS_EXECUCAO} for p in PAPEIS_4F}


def criar_scaffold_auditoria(tool_name: str, repo_root: Path = None):
    if not repo_root:
        repo_root = Path.cwd()
        
    auditoria_root = repo_root / "docs" / "auditoria"
    target_dir = auditoria_root / tool_name

    # Soberania do usuário: harness/model/comando_terminal vêm SOMENTE do config
    # (editado só por humano, nunca por este script). Sem valores padrão inventados.
    papeis = carregar_papeis_4f(auditoria_root / "CONFIG-EXECUCAO-USUARIO.json")
    inspetor, arquiteto, construtor, retorno = (papeis[p] for p in PAPEIS_4F)
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. DOD.md
    dod_file = target_dir / "DOD.md"
    if not dod_file.exists():
        dod_content = f"""# Definição de Pronto (Definition of Done - DoD) — {tool_name}

> Critérios estáticos de conformidade arquitetural baseados no framework Lens 15-D.

## Critérios Obrigatórios de Aceite

1. **DoD 1: CLI Fallback e Fractalidade (D4)**
   - A ferramenta deve possuir invocação declarativa via CLI (`python ecossistema.py {tool_name.replace('aidd-', '')}`) ou scripts locais em Python, com interface agnóstica.

2. **DoD 2: Isolamento de Raio de Impacto (D3)**
   - O código não pode realizar operações de I/O em arquivos fora de seu escopo permitido sem estar contido em Git Worktree efêmera.

3. **DoD 3: Motor Analítico Determinístico (D8)**
   - Proibida dependência de inferência livre de LLM sem envelope ou validação de JSON Schema estrito.

4. **DoD 4: Resiliência Operacional (D11)**
   - Mecanismos de retry com backoff e tratamento estruturado de falhas implementados.

5. **DoD 5: Observabilidade e Frugalidade (D12)**
   - Rastreamento de métricas e tempos de execução persistidos de forma auditável.

6. **DoD 6: Quality Gate e Rótulo Honesto (D13)**
   - Portão determinístico `gates/G_{tool_name.replace('-', '_')}.py` implementado provando que barra saídas ilusórias (Lei #8 e Lei #13).

7. **DoD 7: Limpeza e Rollback (D14)**
   - Em caso de exceção ou rejeição, nenhum arquivo corrompido ou temporário sobrevive no repositório.

8. **DoD 8: Output Consolidado e Handoff (D15)**
   - Emissão de manifesto formal estruturado e laudo 15-D aprovado com EXIT 0.
"""
        dod_file.write_text(dod_content, encoding="utf-8")
        print(f"[+] Criado: {dod_file.relative_to(repo_root)}")

    # 2. PROMPT-FASE-1-INSPETOR.txt
    prompt_f1 = target_dir / "PROMPT-FASE-1-INSPETOR.txt"
    if not prompt_f1.exists():
        prompt_f1_content = f"""Invoque um subagente Flash para auditar a ferramenta '{tool_name}' e mande a ele estritamente a seguinte instrução:

You are a strict System Auditor. Execute the Lens 15-D Architectural Audit on the '{tool_name}' skill.
1. Use your tools to read the canonical template file located exactly at:
docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md
2. Use your tools to read and analyze the entire source code of the target skill at:
.agents/skills/{tool_name}/
3. Based on the source code, meticulously fill out the 15 dimensions of the template. If a dimension is missing in the source code (e.g., no Quality Gate or Fallback logic), explicitly write "FAILED: Not implemented" for that dimension.
4. Save the generated Markdown file exactly at:
docs/auditoria/{tool_name}/LAUDO-15D-INICIAL.md
5. Run the Quality Gate script to assert your output:
python docs/auditoria/{tool_name}/G_auditoria_15D.py docs/auditoria/{tool_name}/LAUDO-15D-INICIAL.md
6. If the script returns EXIT 1, fix the missing parameters in your Markdown file and re-run the gate until EXIT 0 is achieved.
"""
        prompt_f1.write_text(prompt_f1_content, encoding="utf-8")
        print(f"[+] Criado: {prompt_f1.relative_to(repo_root)}")

    # 2b. PROMPT-FASE-2-ARQUITETO.txt (closed prompt, telegraphic English, no placeholder)
    prompt_f2 = target_dir / "PROMPT-FASE-2-ARQUITETO.txt"
    if not prompt_f2.exists():
        prompt_f2_content = f"""ROLE: Architect. Phase 2. Audit pipeline 4F. Target tool: '{tool_name}'.

1. Read Phase 1 Lens 15-D report: docs/auditoria/{tool_name}/LAUDO-15D-INICIAL.md
2. Read Definition of Done: docs/auditoria/{tool_name}/DOD.md
3. Copy format from: docs/auditoria/aidd-melhoria/PLANO-EVOLUCAO.md
4. Write plan ONLY at: docs/auditoria/{tool_name}/PLANO-EVOLUCAO.md
5. NEVER write any artifact of this audit under docs/planos/.
6. One atomic ticket per dimension marked "FAILED: Not implemented". One ticket per severe finding.
7. Ticket format (compiler parses by regex; keep exact labels):

### Ticket N: <Title> (Refere-se a D<x> / DoD <y>)
- **Falha 15-D:** `D<x>. <Dimension name>`
- **Artefato de Handoff:** `<file the Builder delivers>`
- **Requisito TDD (Red):** <test that fails with exit 1 before fix>
- **Implementação Técnica:**
  - <step>
- **Verificação (Green):** <proof of fix>
- **Construtor Prompt (EN):**
  - <imperative telegraphic English step. ASCII only. No Portuguese.>

8. Require TDD Red-Green-Refactor. Require ephemeral Git Worktree isolation.
9. NEVER edit docs/auditoria/CONFIG-EXECUCAO-USUARIO.json. Harness/model/command come from it only.
10. Compile. Assert exit 0:
python scripts/compilador_plano_evolucao.py --plano docs/auditoria/{tool_name}/PLANO-EVOLUCAO.md
"""
        prompt_f2.write_text(prompt_f2_content, encoding="utf-8")
        print(f"[+] Criado: {prompt_f2.relative_to(repo_root)}")

    # 2c. PROMPT-FASE-3-CONSTRUTOR.txt (closed prompt, telegraphic English)
    prompt_f3 = target_dir / "PROMPT-FASE-3-CONSTRUTOR.txt"
    if not prompt_f3.exists():
        prompt_f3_content = f"""ROLE: Builder. Phase 3. Audit pipeline 4F. Target tool: '{tool_name}'.

1. Read compiled plan: docs/auditoria/{tool_name}/PLANO-EVOLUCAO.json
2. Execute tickets in listed order. One ticket at a time.
3. For each ticket read its prompt: docs/auditoria/{tool_name}/prompts_tickets/PROMPT-TICKET-<NN>.txt
4. Work inside ephemeral Git Worktree only. Never write in main working tree.
5. TDD: write failing test first. Run it. Assert exit 1. Implement. Run again. Assert exit 0.
6. Deliver exactly the ticket output_handoff file. Zero stubs. Real pytest tests.
7. Capture real exit codes: redirect output to file, read $? on same line. Never trust pipes.
8. NEVER edit docs/auditoria/CONFIG-EXECUCAO-USUARIO.json.
9. Stop on first ticket failure. Report ticket id, command, exit code.
"""
        prompt_f3.write_text(prompt_f3_content, encoding="utf-8")
        print(f"[+] Criado: {prompt_f3.relative_to(repo_root)}")

    # 3. PROMPT-FASE-4-RETORNO.txt
    prompt_f4 = target_dir / "PROMPT-FASE-4-RETORNO.txt"
    if not prompt_f4.exists():
        prompt_f4_content = f"""Invoque um subagente Flash para auditar a ferramenta '{tool_name}' e mande a ele estritamente a seguinte instrução:

You are a strict System Auditor. Execute the Lens 15-D Architectural Audit on the '{tool_name}' skill.
1. Use your tools to read the canonical template file located exactly at:
docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md
2. Use your tools to read and analyze the entire source code of the target skill at:
.agents/skills/{tool_name}/
3. Based on the source code, meticulously fill out the 15 dimensions of the template. If a dimension is missing in the source code (e.g., no Quality Gate or Fallback logic), explicitly write "FAILED: Not implemented" for that dimension.
4. Save the generated Markdown file exactly at:
docs/auditoria/{tool_name}/LAUDO-15D-REVISADO.md
5. Run the Quality Gate script to assert your output:
python docs/auditoria/{tool_name}/G_auditoria_15D.py docs/auditoria/{tool_name}/LAUDO-15D-REVISADO.md
6. If the script returns EXIT 1, fix the missing parameters in your Markdown file and re-run the gate until EXIT 0 is achieved.
"""
        prompt_f4.write_text(prompt_f4_content, encoding="utf-8")
        print(f"[+] Criado: {prompt_f4.relative_to(repo_root)}")

    # 4. G_auditoria_15D.py
    gate_file = target_dir / "G_auditoria_15D.py"
    if not gate_file.exists():
        gate_file.write_text(GATE_15D_CODE, encoding="utf-8")
        print(f"[+] Criado: {gate_file.relative_to(repo_root)}")

    # 5. MANIFESTO-4F.json — artefato DERIVADO do config: sempre regerado, nunca editado à mão
    fases_4f = [
        ("Fase_1_Inspetor", inspetor, "PROMPT-FASE-1-INSPETOR.txt", f"docs/auditoria/{tool_name}/LAUDO-15D-INICIAL.md"),
        ("Fase_2_Arquiteto", arquiteto, "PROMPT-FASE-2-ARQUITETO.txt", f"docs/auditoria/{tool_name}/PLANO-EVOLUCAO.md"),
        ("Fase_3_Construtor", construtor, "PROMPT-FASE-3-CONSTRUTOR.txt", f".agents/skills/{tool_name}/scripts/"),
        ("Fase_4_Inspetor_Retorno", retorno, "PROMPT-FASE-4-RETORNO.txt", f"docs/auditoria/{tool_name}/LAUDO-15D-REVISADO.md"),
    ]
    manifesto_data = {
        "pipeline_id": f"auditoria-{tool_name}",
        "target_tool": tool_name,
        "session_id": "auto_generated",
        "definition_of_done": f"docs/auditoria/{tool_name}/DOD.md",
        "config_usuario_ref": "docs/auditoria/CONFIG-EXECUCAO-USUARIO.json",
        "fases": [
            {
                "nome": nome,
                "harness": papel["harness"],
                "model": papel["model"],
                "input_prompt": f"docs/auditoria/{tool_name}/{prompt}",
                "comando_terminal": papel["comando_terminal"],
                "output_handoff": handoff,
            }
            for nome, papel, prompt, handoff in fases_4f
        ],
    }
    manifesto_file = target_dir / "MANIFESTO-4F.json"
    with open(manifesto_file, "w", encoding="utf-8") as mf:
        json.dump(manifesto_data, mf, indent=2, ensure_ascii=False)
    print(f"[+] Regerado a partir do config: {manifesto_file.relative_to(repo_root)}")

    print(f"\n[SUCESSO] Scaffold agêntico de '{tool_name}' concluído em: docs/auditoria/{tool_name}/")
    print(f"Para disparar a auditoria:")
    print(f"  python scripts/orquestrador_4f.py --manifest docs/auditoria/{tool_name}/MANIFESTO-4F.json")
    return target_dir

def main():
    parser = argparse.ArgumentParser(description="Scaffolder agêntico de pastas de auditoria do Ecossistema AIDD")
    parser.add_argument("tool", help="Nome da ferramenta (ex: aidd-planner, aidd-generator, aidd-melhoria)")
    args = parser.parse_args()
    
    try:
        criar_scaffold_auditoria(args.tool)
    except ValueError as erro:
        print(f"[ERRO] {erro}")
        sys.exit(1)

if __name__ == "__main__":
    main()
