# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — GERADOR MECÂNICO DE TEMPLATES DE GATES (Item 3)
=============================================================================
Gera `tools/<ferramenta>/templates/gates/*.py` a partir da fonte viva
`tools/<ferramenta>/scripts/gates/*.py`, eliminando a manutenção manual
dupla decidida no Item 3 do plano codigo-limpo-profundo-ecossistema.

Papéis (Decisão Registrada do item 3):
- `scripts/gates/`  = fonte viva da própria ferramenta (editável).
- `templates/gates/` = instantâneo de distribuição entregue a cada projeto
  novo gerado (provision_project.py e compose_suite.py copiam o diretório
  inteiro). NUNCA mais editado a mão — sempre regenerado por este módulo.

Exclusões (`GATES_NAO_TEMPLATED`): gates que validam o motor interno da
própria ferramenta (dependem de paths/regras do repositório) e portanto não
fazem sentido dentro de um projeto de cliente. Hoje: G_INJECT.py, que
escaneia `src/core` do motor do injetor e cujo conteúdo diverge por design
entre master e enterprise.

Uso:
  python ecossistema.py gates sync [--ferramenta <nome>] [--dry-run]
  python ecossistema.py gates verify [--ferramenta <nome>]

`verify` é determinístico e compara SHA-256: exit 0 = templates em sync;
exit 1 = template ausente/divergente/orfão.
"""

import hashlib
import os
import shutil
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS_DIR = os.path.join(ROOT_DIR, "tools")

# Gates específicos da ferramenta — NUNCA viram template de projeto de cliente.
GATES_NAO_TEMPLATED = {"G_INJECT.py"}

FERRAMENTAS_PADRAO = ("aidd-master", "aidd-enterprise")


def _hash_arquivo(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _gerar_para_ferramenta(ferramenta, dry_run=False):
    """Gera templates/gates de UMA ferramenta. Retorna lista de erros (str)."""
    fonte = os.path.join(TOOLS_DIR, ferramenta, "scripts", "gates")
    destino = os.path.join(TOOLS_DIR, ferramenta, "templates", "gates")
    erros = []

    if not os.path.isdir(fonte):
        erros.append(f"{ferramenta}: fonte ausente: {fonte}")
        return erros

    esperados = sorted(
        f for f in os.listdir(fonte)
        if f.endswith(".py") and f not in GATES_NAO_TEMPLATED and f != "__init__.py"
    )

    if not dry_run:
        os.makedirs(destino, exist_ok=True)

    # 1. Copiar/regenerar cada gate templated
    for nome in esperados:
        src = os.path.join(fonte, nome)
        dst = os.path.join(destino, nome)
        if os.path.isfile(dst) and _hash_arquivo(src) == _hash_arquivo(dst):
            print(f"  [OK] {ferramenta}/templates/gates/{nome} já sincronizado")
            continue
        if dry_run:
            print(f"  [DRY-RUN] {ferramenta}/templates/gates/{nome} seria (re)gerado")
            continue
        shutil.copyfile(src, dst)
        print(f"  [GERADO] {ferramenta}/templates/gates/{nome}")

    # 2. Remover órfãos (arquivos em templates/gates que não deveriam existir)
    if os.path.isdir(destino):
        for nome in sorted(os.listdir(destino)):
            if not nome.endswith(".py"):
                continue
            if nome in esperados:
                continue
            if dry_run:
                print(f"  [DRY-RUN] órfão {ferramenta}/templates/gates/{nome} seria removido")
                continue
            os.remove(os.path.join(destino, nome))
            print(f"  [REMOVIDO] órfão {ferramenta}/templates/gates/{nome}")

    return erros


def _verificar_ferramenta(ferramenta):
    """Verificação determinística (SHA-256). Retorna lista de erros (str)."""
    fonte = os.path.join(TOOLS_DIR, ferramenta, "scripts", "gates")
    destino = os.path.join(TOOLS_DIR, ferramenta, "templates", "gates")
    erros = []

    if not os.path.isdir(fonte):
        erros.append(f"{ferramenta}: fonte ausente: {fonte}")
        return erros

    esperados = sorted(
        f for f in os.listdir(fonte)
        if f.endswith(".py") and f not in GATES_NAO_TEMPLATED and f != "__init__.py"
    )

    # 1. Todo gate templated deve existir e ser idêntico à fonte
    for nome in esperados:
        dst = os.path.join(destino, nome)
        if not os.path.isfile(dst):
            erros.append(f"{ferramenta}/templates/gates/{nome}: AUSENTE — rode 'ecossistema.py gates sync'")
        elif _hash_arquivo(os.path.join(fonte, nome)) != _hash_arquivo(dst):
            erros.append(
                f"{ferramenta}/templates/gates/{nome}: DIVERGE da fonte scripts/gates — "
                "templates/gates não é mais editado a mão; rode 'ecossistema.py gates sync'"
            )

    # 2. Nenhum órfão em templates/gates
    if os.path.isdir(destino):
        for nome in sorted(os.listdir(destino)):
            if nome.endswith(".py") and nome not in esperados:
                erros.append(
                    f"{ferramenta}/templates/gates/{nome}: ÓRFÃO (não existe em scripts/gates "
                    "ou está na lista de exclusão) — rode 'ecossistema.py gates sync'"
                )

    return erros


def _resolver_ferramentas(nome):
    if not nome or nome == "todas":
        return list(FERRAMENTAS_PADRAO)
    if nome not in FERRAMENTAS_PADRAO:
        raise ValueError(
            f"Ferramenta desconhecida '{nome}'. Use uma de: {', '.join(FERRAMENTAS_PADRAO)} ou 'todas'."
        )
    return [nome]


def cmd_gates(args):
    """Entry point chamado por ecossistema.py ('gates sync|verify')."""
    if not args or args[0] not in ("sync", "verify"):
        print("Uso: python ecossistema.py gates sync|verify [--ferramenta <nome|todas>] [--dry-run]")
        return 1
    acao = args[0]
    restantes = args[1:]

    ferramenta = "todas"
    dry_run = False
    it = iter(restantes)
    for token in it:
        if token == "--ferramenta":
            ferramenta = next(it, None)
            if not ferramenta:
                print("Erro: --ferramenta exige um valor (nome da ferramenta ou 'todas').")
                return 1
        elif token == "--dry-run":
            dry_run = True
        else:
            print(f"Erro: argumento desconhecido '{token}' para 'gates {acao}'.")
            return 1

    try:
        ferramentas = _resolver_ferramentas(ferramenta)
    except ValueError as exc:
        print(f"Erro: {exc}")
        return 1

    print("=" * 70)
    print(f" [ECOSSISTEMA] gates {acao} — geração mecânica de templates/gates")
    print("=" * 70)

    erros = []
    for ferr in ferramentas:
        if acao == "sync":
            erros.extend(_gerar_para_ferramenta(ferr, dry_run=dry_run))
        else:
            erros.extend(_verificar_ferramenta(ferr))

    print()
    if erros:
        print(f" [FALHA] {len(erros)} problema(s) encontrado(s):")
        for err in erros:
            print(f"  - {err}")
        return 1
    if acao == "verify":
        print(" [SUCESSO] templates/gates sincronizado com scripts/gates nas 2 ferramentas.")
    else:
        print(" [SUCESSO] Geração concluída.")
    return 0


if __name__ == "__main__":
    sys.exit(cmd_gates(sys.argv[1:]))
