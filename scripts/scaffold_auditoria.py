import argparse
import json
import re
import shutil
import sys
from pathlib import Path

GATE_15D_CODE = '''import os
import re
import sys

CICLO_RE = re.compile(r"^ciclo-(\\d+)$")


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


def laudo_do_ciclo_vigente(raiz):
    """Sem argumento, valida o ciclo mais recente: revisado se existir, senão o inicial."""
    ciclos = sorted(
        (int(m.group(1)), nome)
        for nome in os.listdir(raiz)
        if (m := CICLO_RE.match(nome)) and os.path.isdir(os.path.join(raiz, nome))
    )
    if not ciclos:
        return os.path.join(raiz, "LAUDO-15D-INICIAL.md")
    ciclo = os.path.join(raiz, ciclos[-1][1])
    revisado = os.path.join(ciclo, "LAUDO-15D-REVISADO.md")
    return revisado if os.path.exists(revisado) else os.path.join(ciclo, "LAUDO-15D-INICIAL.md")


if __name__ == "__main__":
    raiz = os.path.dirname(os.path.abspath(__file__))
    target = sys.argv[1] if len(sys.argv) > 1 else laudo_do_ciclo_vigente(raiz)
    run_gate(target)
'''

PAPEIS_4F = ("inspetor", "arquiteto", "construtor", "retorno")
CAMPOS_EXECUCAO = ("harness", "model", "comando_terminal")
CICLO_RE = re.compile(r"^ciclo-(\d+)$")

# Artefatos que pertencem a UMA rodada (vivem em <f>/ciclo-NN/).
# G_auditoria_15D.py é compartilhado e fica na raiz da ferramenta.
ARTEFATOS_DO_CICLO = (
    "DOD.md", "MANIFESTO-4F.json",
    "PROMPT-FASE-1-INSPETOR.txt", "PROMPT-FASE-2-ARQUITETO.txt",
    "PROMPT-FASE-3-CONSTRUTOR.txt", "PROMPT-FASE-4-RETORNO.txt",
    "LAUDO-15D-INICIAL.md", "PLANO-EVOLUCAO.md", "PLANO-EVOLUCAO.json", "prompts_tickets",
    "RELATORIO-CONSTRUTOR.md", "LAUDO-15D-REVISADO.md",
    "RESUMO-USUARIO.md", "RELATORIO-TECNICO.md",
)
EXTENSOES_TEXTO = (".md", ".json", ".txt")

# Gate que cada fase precisa passar ANTES do commit (orquestrador_4f.py) e bateria
# completa que roda uma única vez no fim, antes de liberar a aprovação humana.
GATE_TESTES = "python -m pytest -q -p no:cacheprovider tests"
GATE_FINAL = "python ecossistema.py audit"


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


def listar_ciclos(tool_dir: Path) -> list:
    """Pastas ciclo-NN da ferramenta, em ordem numérica."""
    if not tool_dir.is_dir():
        return []
    ciclos = [(int(m.group(1)), p) for p in tool_dir.iterdir() if p.is_dir() and (m := CICLO_RE.match(p.name))]
    return [p for _, p in sorted(ciclos)]


def ciclo_vigente(tool_dir: Path):
    """Ciclo mais recente (ou None se a ferramenta nunca foi auditada)."""
    ciclos = listar_ciclos(tool_dir)
    return ciclos[-1] if ciclos else None


def ciclo_concluido(ciclo_dir: Path) -> bool:
    """Um ciclo termina quando a Fase 4 entrega o laudo revisado."""
    revisado = ciclo_dir / "LAUDO-15D-REVISADO.md"
    return revisado.is_file() and revisado.stat().st_size > 0


def nome_ciclo(numero: int) -> str:
    return f"ciclo-{numero:02d}"


def migrar_layout_legado(tool_dir: Path, tool_name: str) -> bool:
    """Move o layout plano antigo (artefatos na raiz) para ciclo-01, reescrevendo caminhos."""
    legados = [nome for nome in ARTEFATOS_DO_CICLO if (tool_dir / nome).exists()]
    if not legados:
        return False
    if listar_ciclos(tool_dir):
        raise ValueError(
            f"{tool_dir}: há artefatos na raiz ({', '.join(legados)}) e também pastas ciclo-NN; resolva manualmente."
        )

    destino = tool_dir / nome_ciclo(1)
    destino.mkdir(parents=True)
    for nome in legados:
        shutil.move(str(tool_dir / nome), str(destino / nome))

    nomes = "|".join(re.escape(n) for n in ARTEFATOS_DO_CICLO)
    padrao = re.compile(rf"docs/auditoria/{re.escape(tool_name)}/(?=(?:{nomes})\b)")
    novo_prefixo = f"docs/auditoria/{tool_name}/{destino.name}/"
    for arquivo in destino.rglob("*"):
        if arquivo.is_file() and arquivo.suffix in EXTENSOES_TEXTO:
            texto = arquivo.read_text(encoding="utf-8")
            reescrito = padrao.sub(novo_prefixo, texto)
            if reescrito != texto:
                arquivo.write_text(reescrito, encoding="utf-8")
    print(f"[MIGRADO] Layout plano -> {destino.name}/: {', '.join(legados)}")
    return True


def resolver_ciclo(tool_dir: Path) -> Path:
    """Sem ciclo -> ciclo-01; vigente incompleto -> retoma; vigente concluído -> abre o próximo."""
    vigente = ciclo_vigente(tool_dir)
    if vigente is None:
        return tool_dir / nome_ciclo(1)
    if not ciclo_concluido(vigente):
        return vigente
    return tool_dir / nome_ciclo(int(CICLO_RE.match(vigente.name).group(1)) + 1)


def _dod_padrao(tool_name: str) -> str:
    return f"""# Definição de Pronto (Definition of Done - DoD) — {tool_name}

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


def _prompt_inspetor(tool_name: str, c: str, raiz: str, laudo_saida: str, anterior: str = None) -> str:
    comparacao = ""
    if anterior:
        comparacao = f"""
7. This is a re-audit. Read the previous cycle report first:
{anterior}
For every dimension write "Nota Anterior -> Nota Nova" and state what changed in the code since that report.
"""
    return f"""Invoque um subagente Flash para auditar a ferramenta '{tool_name}' e mande a ele estritamente a seguinte instrução:

You are a strict System Auditor. Execute the Lens 15-D Architectural Audit on the '{tool_name}' skill.
1. Use your tools to read the canonical template file located exactly at:
docs/auditoria/TEMPLATE-AUDITORIA-FERRAMENTA.md
2. Use your tools to read and analyze the entire source code of the target skill at:
.agents/skills/{tool_name}/
3. Based on the source code, meticulously fill out the 15 dimensions of the template. If a dimension is missing in the source code (e.g., no Quality Gate or Fallback logic), explicitly write "FAILED: Not implemented" for that dimension.
4. Save the generated Markdown file exactly at:
{c}/{laudo_saida}
5. Run the Quality Gate script to assert your output:
python {raiz}/G_auditoria_15D.py {c}/{laudo_saida}
6. If the script returns EXIT 1, fix the missing parameters in your Markdown file and re-run the gate until EXIT 0 is achieved.
{comparacao}"""


def _prompt_arquiteto(tool_name: str, c: str) -> str:
    return f"""ROLE: Architect. Phase 2. Audit pipeline 4F. Target tool: '{tool_name}'. Cycle: {c}.

1. Read Phase 1 Lens 15-D report: {c}/LAUDO-15D-INICIAL.md
2. Read Definition of Done: {c}/DOD.md
3. Copy format from: docs/auditoria/aidd-melhoria/ciclo-01/PLANO-EVOLUCAO.md
4. Write plan ONLY at: {c}/PLANO-EVOLUCAO.md
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
python scripts/compilador_plano_evolucao.py --plano {c}/PLANO-EVOLUCAO.md
"""


def _prompt_construtor(tool_name: str, c: str) -> str:
    return f"""ROLE: Builder. Phase 3. Audit pipeline 4F. Target tool: '{tool_name}'. Cycle: {c}.

1. Read compiled plan: {c}/PLANO-EVOLUCAO.json
2. Execute tickets in listed order. One ticket at a time.
3. For each ticket read its prompt: {c}/prompts_tickets/PROMPT-TICKET-<NN>.txt
4. Work inside ephemeral Git Worktree only. Never write in main working tree.
5. TDD: write failing test first. Run it. Assert exit 1. Implement. Run again. Assert exit 0.
6. Deliver exactly the ticket output_handoff file. Zero stubs. Real pytest tests.
7. Capture real exit codes: redirect output to file, read $? on same line. Never trust pipes.
8. NEVER edit docs/auditoria/CONFIG-EXECUCAO-USUARIO.json.
9. Stop on first ticket failure. Report ticket id, command, exit code.
10. Finish by writing {c}/RELATORIO-CONSTRUTOR.md: one row per ticket with ticket id, delivered file, test command, exit code before fix, exit code after fix.
"""


def criar_scaffold_auditoria(tool_name: str, repo_root: Path = None) -> Path:
    """Cria/retoma o ciclo de auditoria da ferramenta e devolve a pasta do ciclo."""
    if not repo_root:
        repo_root = Path.cwd()

    auditoria_root = repo_root / "docs" / "auditoria"
    tool_dir = auditoria_root / tool_name

    # Soberania do usuário: harness/model/comando_terminal vêm SOMENTE do config
    # (editado só por humano, nunca por este script). Sem valores padrão inventados.
    papeis = carregar_papeis_4f(auditoria_root / "CONFIG-EXECUCAO-USUARIO.json")
    inspetor, arquiteto, construtor, retorno = (papeis[p] for p in PAPEIS_4F)

    migrar_layout_legado(tool_dir, tool_name)
    anterior = ciclo_vigente(tool_dir)
    ciclo_dir = resolver_ciclo(tool_dir)
    novo = not ciclo_dir.exists()
    ciclo_dir.mkdir(parents=True, exist_ok=True)
    print(f"[CICLO] {'Aberto' if novo else 'Retomado'}: {ciclo_dir.relative_to(repo_root)}")

    raiz = f"docs/auditoria/{tool_name}"
    c = f"{raiz}/{ciclo_dir.name}"
    anterior_revisado = None
    if anterior is not None and anterior != ciclo_dir:
        anterior_revisado = f"{raiz}/{anterior.name}/LAUDO-15D-REVISADO.md"

    # Gate compartilhado na raiz da ferramenta
    gate_file = tool_dir / "G_auditoria_15D.py"
    if not gate_file.exists():
        gate_file.write_text(GATE_15D_CODE, encoding="utf-8")
        print(f"[+] Criado: {gate_file.relative_to(repo_root)}")

    # DoD: herdado do ciclo anterior (critérios evoluem entre rodadas) ou padrão
    dod_file = ciclo_dir / "DOD.md"
    if not dod_file.exists():
        if anterior is not None and anterior != ciclo_dir and (anterior / "DOD.md").exists():
            shutil.copyfile(anterior / "DOD.md", dod_file)
        else:
            dod_file.write_text(_dod_padrao(tool_name), encoding="utf-8")
        print(f"[+] Criado: {dod_file.relative_to(repo_root)}")

    prompts = {
        "PROMPT-FASE-1-INSPETOR.txt": _prompt_inspetor(tool_name, c, raiz, "LAUDO-15D-INICIAL.md", anterior_revisado),
        "PROMPT-FASE-2-ARQUITETO.txt": _prompt_arquiteto(tool_name, c),
        "PROMPT-FASE-3-CONSTRUTOR.txt": _prompt_construtor(tool_name, c),
        "PROMPT-FASE-4-RETORNO.txt": _prompt_inspetor(tool_name, c, raiz, "LAUDO-15D-REVISADO.md"),
    }
    for nome, conteudo in prompts.items():
        arquivo = ciclo_dir / nome
        if not arquivo.exists():
            arquivo.write_text(conteudo, encoding="utf-8")
            print(f"[+] Criado: {arquivo.relative_to(repo_root)}")

    # MANIFESTO-4F.json — artefato DERIVADO do config: sempre regerado, nunca editado à mão.
    # Todos os output_handoff ficam dentro do ciclo: o cache do orquestrador vale por ciclo.
    gate15 = f"python {raiz}/G_auditoria_15D.py"
    fases_4f = [
        ("Fase_1_Inspetor", inspetor, "PROMPT-FASE-1-INSPETOR.txt", "LAUDO-15D-INICIAL.md",
         f"{gate15} {c}/LAUDO-15D-INICIAL.md"),
        ("Fase_2_Arquiteto", arquiteto, "PROMPT-FASE-2-ARQUITETO.txt", "PLANO-EVOLUCAO.md",
         f"python scripts/compilador_plano_evolucao.py --plano {c}/PLANO-EVOLUCAO.md"),
        ("Fase_3_Construtor", construtor, "PROMPT-FASE-3-CONSTRUTOR.txt", "RELATORIO-CONSTRUTOR.md", GATE_TESTES),
        ("Fase_4_Inspetor_Retorno", retorno, "PROMPT-FASE-4-RETORNO.txt", "LAUDO-15D-REVISADO.md",
         f"{gate15} {c}/LAUDO-15D-REVISADO.md"),
    ]
    manifesto_data = {
        "pipeline_id": f"auditoria-{tool_name}-{ciclo_dir.name}",
        "target_tool": tool_name,
        "ciclo": ciclo_dir.name,
        "session_id": "auto_generated",
        "definition_of_done": f"{c}/DOD.md",
        "config_usuario_ref": "docs/auditoria/CONFIG-EXECUCAO-USUARIO.json",
        "gate_final": GATE_FINAL,
        "fases": [
            {
                "nome": nome,
                "harness": papel["harness"],
                "model": papel["model"],
                "input_prompt": f"{c}/{prompt}",
                "comando_terminal": papel["comando_terminal"],
                "output_handoff": f"{c}/{handoff}",
                "gate_fase": gate,
            }
            for nome, papel, prompt, handoff, gate in fases_4f
        ],
    }
    manifesto_file = ciclo_dir / "MANIFESTO-4F.json"
    with open(manifesto_file, "w", encoding="utf-8") as mf:
        json.dump(manifesto_data, mf, indent=2, ensure_ascii=False)
    print(f"[+] Regerado a partir do config: {manifesto_file.relative_to(repo_root)}")

    print(f"\n[SUCESSO] Scaffold agêntico de '{tool_name}' pronto em: {c}/")
    print("Para disparar a auditoria:")
    print(f"  python scripts/orquestrador_4f.py --manifest {c}/MANIFESTO-4F.json")
    return ciclo_dir


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
