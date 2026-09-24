import os
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
        print("\nO Agente deve reconstruir o arquivo garantindo a aderência exata ao TEMPLATE-AUDITORIA-FERRAMENTA.md.")
        sys.exit(1)

    print("EXIT 0: Laudo 15-D perfeito. Todas as 15 dimensões estão presentes.")
    sys.exit(0)

if __name__ == "__main__":
    revisado_target = os.path.join(os.path.dirname(__file__), "LAUDO-15D-REVISADO.md")
    inicial_target = os.path.join(os.path.dirname(__file__), "LAUDO-15D-INICIAL.md")
    default_target = revisado_target if os.path.exists(revisado_target) else inicial_target
    target = sys.argv[1] if len(sys.argv) > 1 else default_target
    run_gate(target)
