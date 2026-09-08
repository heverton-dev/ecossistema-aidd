# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — QUALITY GATE: G_HONESTIDADE_ROTULO
=============================================================================
Verificacao mecanica da Regra de Ouro #9 (AGENTS.md §2, "Honestidade de
Rotulo"): nenhuma mensagem de saida de gate/CLI pode usar linguagem que
sugira certificacao/seguranca maior do que a cobertura real testada.

Origem real do achado que motivou a regra: tools/aidd-master/scripts/gates/
G_SEGURANCA.py e tools/aidd-enterprise/scripts/gates/G_SEGURANCA.py imprimem
"Score de Blindagem: 100.0% (NOTA A+)" para um gate onde apenas ~4 dos 21
checks sao funcionais reais (o resto e grep/config estatico) — ver
docs/planos/fazendo/01-correcao-pos-auditoria-sem-maquiagem/
07-corrigir-gate-de-seguranca-rotulado-blindagem-militar-rotulo-ou-cobertura-real.md.
A correcao do rotulo/cobertura desse gate especifico e escopo do Item 7
citado acima (decisao de rota pendente de aprovacao humana); este gate aqui
so precisa DETECTAR o padrao, nao corrigi-lo.

Usa `ast.parse` (nao regex ingenua sobre o arquivo inteiro) e restringe a
checagem a strings que sao argumento de uma chamada `print(...)` ou fazem
parte da construcao da excecao de um `raise ...(...)` — mesma tecnica de
escopo de gates/G_CLI_HELP_CONSISTENCIA.py, que por construcao ignora
docstrings, comentarios e strings gravadas em arquivo (nunca impressas nem
levantadas ao usuario).

Diretorios auditados (gates/ da raiz e scripts/gates/ ou gates/ de cada
ferramenta — templates/gates do aidd-forge inclusos porque sao carimbados
literalmente em todo projeto gerado pela ferramenta):
  - gates/
  - tools/aidd-master/scripts/gates/
  - tools/aidd-enterprise/scripts/gates/
  - tools/aidd-generator/scripts/gates/
  - tools/aidd-ops/gates/
  - tools/aidd-forge/aidd_forge/templates/gates/
Fora do escopo (deliberado): tools/*/materiais-extras/examples/** (material
de documentacao/exemplo, nao script vivo) e tools/aidd-forge/sandbox-forge-teste/
(saida gerada de um teste manual, nao fonte).

Lista de termos proibidos em gates/termos_proibidos_marketing.json (edita-se
o JSON, nao este script, pra adicionar/remover termo).

Uso:
  python gates/G_HONESTIDADE_ROTULO.py
      exit 0 = nenhum termo proibido encontrado em print()/raise() dos
               scripts de gate auditados.
      exit 1 = ao menos 1 termo proibido encontrado (arquivo, linha, termo
               e trecho sao impressos).
"""

import ast
import json
import os
import sys
import unicodedata

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERMOS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "termos_proibidos_marketing.json")

DIRETORIOS_AUDITADOS = [
    "gates",
    "tools/aidd-master/scripts/gates",
    "tools/aidd-enterprise/scripts/gates",
    "tools/aidd-generator/scripts/gates",
    "tools/aidd-ops/gates",
    "tools/aidd-forge/aidd_forge/templates/gates",
]

# Arquivos utilitarios/de teste dentro dos diretorios de gate não são o
# script do gate em si (não geram mensagem de saída pro usuário do gate).
PREFIXOS_IGNORADOS = ("test_", "_")


def _normalizar(texto):
    """Casefold + remove acentos (NFKD), pra 'produção' bater com 'producao'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acento.casefold()


def _carregar_termos_proibidos():
    with open(TERMOS_PATH, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return [_normalizar(termo) for termo in dados.get("termos", [])]


def _listar_arquivos_gate(diretorio_rel):
    diretorio_abs = os.path.join(ROOT_DIR, diretorio_rel)
    if not os.path.isdir(diretorio_abs):
        return None
    arquivos = []
    for nome in sorted(os.listdir(diretorio_abs)):
        if not nome.endswith(".py"):
            continue
        if nome.startswith(PREFIXOS_IGNORADOS):
            continue
        arquivos.append(os.path.join(diretorio_rel, nome).replace("\\", "/"))
    return arquivos


def _e_mensagem_ao_usuario(ancestrais):
    """True se a string esta dentro de um print(...), em qualquer profundidade
    (cobre f-strings e concatenacao), ou e/contem a construcao da excecao de
    um `raise Excecao(...)`. Docstrings, comentarios e strings gravadas em
    arquivo nunca satisfazem nenhuma das duas condicoes."""
    calls_no_caminho = [n for n in ancestrais if isinstance(n, ast.Call)]

    for chamada in calls_no_caminho:
        func = chamada.func
        nome = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if nome == "print":
            return True

    if calls_no_caminho:
        construcao_excecao = calls_no_caminho[-1]
        idx = ancestrais.index(construcao_excecao)
        pai_da_chamada = ancestrais[idx - 1] if idx > 0 else None
        if isinstance(pai_da_chamada, ast.Raise):
            return True

    return False


def _extrair_mensagens(arvore):
    """Retorna [(texto_original, linha)] de toda string que e argumento de
    print(...) ou parte de raise Excecao(...)."""
    mensagens = []
    pais_por_no = {}
    pilha = [(arvore, [])]
    while pilha:
        no, ancestrais = pilha.pop()
        pais_por_no[id(no)] = ancestrais
        for filho in ast.iter_child_nodes(no):
            pilha.append((filho, ancestrais + [no]))

    for no in ast.walk(arvore):
        if not (isinstance(no, ast.Constant) and isinstance(no.value, str)):
            continue
        ancestrais = pais_por_no.get(id(no), [])
        if not _e_mensagem_ao_usuario(ancestrais):
            continue
        mensagens.append((no.value, getattr(no, "lineno", "?")))
    return mensagens


def _auditar_arquivo(caminho_rel, termos_proibidos):
    caminho_abs = os.path.join(ROOT_DIR, caminho_rel)
    with open(caminho_abs, "r", encoding="utf-8-sig") as f:
        fonte = f.read()

    try:
        arvore = ast.parse(fonte, filename=caminho_rel)
    except SyntaxError as exc:
        return [f"{caminho_rel}: SyntaxError ao fazer parse — {exc}"]

    erros = []
    for texto, linha in _extrair_mensagens(arvore):
        texto_normalizado = _normalizar(texto)
        for termo in termos_proibidos:
            if termo in texto_normalizado:
                trecho = texto.strip()[:100]
                erros.append(
                    f"{caminho_rel}:{linha} — termo de marketing proibido '{termo}' "
                    f"em mensagem de gate. Trecho: \"{trecho}\""
                )
    return erros


def checar():
    print("=" * 70)
    print(" [GATE] G_HONESTIDADE_ROTULO — Zero linguagem de marketing em gate/CLI")
    print("=" * 70)

    termos_proibidos = _carregar_termos_proibidos()
    erros_totais = []
    total_arquivos = 0

    for diretorio_rel in DIRETORIOS_AUDITADOS:
        arquivos = _listar_arquivos_gate(diretorio_rel)
        if arquivos is None:
            print(f"[SKIP] {diretorio_rel}/ nao existe neste checkout")
            continue
        for caminho_rel in arquivos:
            total_arquivos += 1
            erros = _auditar_arquivo(caminho_rel, termos_proibidos)
            if erros:
                erros_totais.extend(erros)
                print(f"[FALHA] {caminho_rel} — {len(erros)} termo(s) proibido(s)")
            else:
                print(f"[OK] {caminho_rel}")

    print("\n" + "=" * 70)
    if erros_totais:
        print(f" [FALHA] Quality Gate REPROVADO com {len(erros_totais)} erro(s):")
        for err in erros_totais:
            print(f"  - {err}")
        print("=" * 70)
        return 1

    print(f" [SUCESSO] Quality Gate G_HONESTIDADE_ROTULO APROVADO ({total_arquivos} arquivo(s) auditado(s), 0 termo proibido)!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(checar())
