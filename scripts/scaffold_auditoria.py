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

def criar_scaffold_auditoria(tool_name: str, repo_root: Path = None):
    if not repo_root:
        repo_root = Path.cwd()
        
    auditoria_root = repo_root / "docs" / "auditoria"
    target_dir = auditoria_root / tool_name
    target_dir.mkdir(parents=True, exist_ok=True)
    
    config_user_path = auditoria_root / "CONFIG-EXECUCAO-USUARIO.json"
    user_config = {}
    if config_user_path.exists():
        try:
            with open(config_user_path, "r", encoding="utf-8") as cf:
                user_config = json.load(cf)
        except Exception:
            pass
            
    papeis = user_config.get("papeis_pipeline_4f", {})
    padrao = user_config.get("padrao_geral", {
        "harness": "agy",
        "model": "gemini-3.8-flash-high",
        "comando_terminal": "agy --model gemini-3.8-flash-high --dangerously-skip-permissions"
    })
    
    inspetor = papeis.get("inspetor", padrao)
    arquiteto = papeis.get("arquiteto", padrao)
    construtor = papeis.get("construtor", padrao)
    retorno = papeis.get("retorno", padrao)

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
docs/protocolos/TEMPLATE-AUDITORIA-FERRAMENTA.md
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

    # 3. PROMPT-FASE-4-RETORNO.txt
    prompt_f4 = target_dir / "PROMPT-FASE-4-RETORNO.txt"
    if not prompt_f4.exists():
        prompt_f4_content = f"""Invoque um subagente Flash para auditar a ferramenta '{tool_name}' e mande a ele estritamente a seguinte instrução:

You are a strict System Auditor. Execute the Lens 15-D Architectural Audit on the '{tool_name}' skill.
1. Use your tools to read the canonical template file located exactly at:
docs/protocolos/TEMPLATE-AUDITORIA-FERRAMENTA.md
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

    # 5. MANIFESTO-4F.json
    manifesto_file = target_dir / "MANIFESTO-4F.json"
    if not manifesto_file.exists():
        manifesto_data = {
            "pipeline_id": f"auditoria-{tool_name}",
            "target_tool": tool_name,
            "session_id": "auto_generated",
            "definition_of_done": f"docs/auditoria/{tool_name}/DOD.md",
            "config_usuario_ref": "docs/auditoria/CONFIG-EXECUCAO-USUARIO.json",
            "fases": [
                {
                    "nome": "Fase_1_Inspetor",
                    "harness": inspetor.get("harness", "mimo"),
                    "model": inspetor.get("model", "xiaomi-token-plan-sgp/mimo-v2.6-flash"),
                    "input_prompt": f"docs/auditoria/{tool_name}/PROMPT-FASE-1-INSPETOR.txt",
                    "comando_terminal": inspetor.get("comando_terminal", "mimo --pure -m xiaomi-token-plan-sgp/mimo-v2.6-flash"),
                    "output_handoff": f"docs/auditoria/{tool_name}/LAUDO-15D-INICIAL.md"
                },
                {
                    "nome": "Fase_2_Arquiteto",
                    "harness": arquiteto.get("harness", "opencode"),
                    "model": arquiteto.get("model", "opencode/big-pickle"),
                    "input_prompt": "docs/protocolos/auditoria/input_fase_2_arquiteto.txt",
                    "comando_terminal": arquiteto.get("comando_terminal", "opencode --pure --auto --agent -m opencode/big-pickle"),
                    "output_handoff": f"docs/auditoria/{tool_name}/PLANO-EVOLUCAO.md"
                },
                {
                    "nome": "Fase_3_Construtor",
                    "harness": construtor.get("harness", "agy"),
                    "model": construtor.get("model", "gemini-3.8-flash-high"),
                    "input_prompt": f"docs/auditoria/{tool_name}/PLANO-EVOLUCAO.md",
                    "comando_terminal": construtor.get("comando_terminal", "agy --model gemini-3.8-flash-high --dangerously-skip-permissions"),
                    "output_handoff": f".agents/skills/{tool_name}/scripts/"
                },
                {
                    "nome": "Fase_4_Inspetor_Retorno",
                    "harness": retorno.get("harness", "claude"),
                    "model": retorno.get("model", "opus"),
                    "input_prompt": f"docs/auditoria/{tool_name}/PROMPT-FASE-4-RETORNO.txt",
                    "comando_terminal": retorno.get("comando_terminal", "claude --dangerously-skip-permissions --chrome --model opus"),
                    "output_handoff": f"docs/auditoria/{tool_name}/LAUDO-15D-REVISADO.md"
                }
            ]
        }
        with open(manifesto_file, "w", encoding="utf-8") as mf:
            json.dump(manifesto_data, mf, indent=2, ensure_ascii=False)
        print(f"[+] Criado: {manifesto_file.relative_to(repo_root)}")

    # Atualiza também o template genérico em docs/auditoria/aidd-melhoria/MANIFESTO-4F.json se não existir
    print(f"\n[SUCESSO] Scaffold agêntico de '{tool_name}' concluído em: docs/auditoria/{tool_name}/")
    print(f"Para disparar a auditoria:")
    print(f"  python scripts/orquestrador_4f.py --manifest docs/auditoria/{tool_name}/MANIFESTO-4F.json")
    return target_dir

def main():
    parser = argparse.ArgumentParser(description="Scaffolder agêntico de pastas de auditoria do Ecossistema AIDD")
    parser.add_argument("tool", help="Nome da ferramenta (ex: aidd-planner, aidd-generator, aidd-melhoria)")
    args = parser.parse_args()
    
    criar_scaffold_auditoria(args.tool)

if __name__ == "__main__":
    main()
