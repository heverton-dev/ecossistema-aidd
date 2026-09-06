#!/usr/bin/env python3
"""
Gerenciador deterministico de planos de auditoria/evolucao/testes.
Cria a estrutura padrao (00-PROCESSO-E-DECISOES.md e NN-<item>.md) e checa integridade de cercas de codigo.
"""

import argparse
import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_PLANOS = ROOT_DIR / "docs" / "planos"


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def verificar_cercas_arquivo(caminho: Path) -> tuple[bool, str]:
    """Verifica se as cercas de codigo (```) ocorrem em pares isolados e nao aninhados."""
    if not caminho.exists():
        return False, f"Arquivo nao encontrado: {caminho}"

    linhas = caminho.read_text(encoding="utf-8").splitlines()
    in_fence = False
    fence_start = 0

    for idx, linha in enumerate(linhas, start=1):
        stripped = linha.strip()
        if stripped.startswith("```"):
            if not in_fence:
                in_fence = True
                fence_start = idx
            else:
                in_fence = False

    if in_fence:
        return False, f"Cerca aberta na linha {fence_start} nao foi fechada!"

    return True, "Cercas balanceadas com sucesso."


def cmd_check_fences(caminho_alvo: str) -> int:
    alvo = Path(caminho_alvo)
    if not alvo.is_absolute():
        alvo = ROOT_DIR / alvo

    if alvo.is_file():
        arquivos = [alvo]
    elif alvo.is_dir():
        arquivos = sorted(alvo.glob("*.md"))
    else:
        print(f"[ERRO] Caminho invalido: {alvo}")
        return 1

    erros = 0
    for arq in arquivos:
        ok, msg = verificar_cercas_arquivo(arq)
        if ok:
            print(f"[OK] {arq.name}: {msg}")
        else:
            print(f"[FALHA] {arq.name}: {msg}")
            erros += 1

    return 1 if erros > 0 else 0


def cmd_init(nome: str, itens: list[str], destino_base: Path | None = None) -> int:
    if not nome:
        print("[ERRO] Nome da iniciativa e obrigatorio.")
        return 1

    pasta_nome = slugify(nome)
    base = destino_base or DOCS_PLANOS
    pasta_destino = base / pasta_nome

    if pasta_destino.exists():
        print(f"[ERRO] Pasta ja existe: {pasta_destino}")
        return 1

    pasta_destino.mkdir(parents=True, exist_ok=True)

    if not itens:
        itens = ["Estruturacao Inicial e Diagnostico"]

    linhas_tabela_conteudo = []
    linhas_tabela_progresso = []
    arquivos_itens = []

    for idx, item_titulo in enumerate(itens, start=1):
        item_slug = slugify(item_titulo)
        item_arquivo = f"{idx:02d}-{item_slug}.md"
        linhas_tabela_conteudo.append(f"| {idx} | {item_titulo} | `{item_arquivo}` |")
        linhas_tabela_progresso.append(f"| {idx} | {item_titulo} | ⏳ Rascunho gerado, aguardando aprovacao | `{item_arquivo}` |")
        arquivos_itens.append((idx, item_titulo, item_arquivo))

    tabela_conteudo_str = "\n".join(linhas_tabela_conteudo)
    tabela_progresso_str = "\n".join(linhas_tabela_progresso)

    processo_md = f"""# PROCESSO E DECISOES — {nome}

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

Defina aqui os objetivos claros, escopo e limites desta iniciativa.
- **Objetivo Principal:** [Descrever objetivo]
- **Limites de Escopo:** Nao inclui decisoes nao aprovadas por humano.

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
{tabela_conteudo_str}

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
{tabela_progresso_str}

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
"""

    (pasta_destino / "00-PROCESSO-E-DECISOES.md").write_text(processo_md, encoding="utf-8")

    for idx, item_titulo, item_arquivo in arquivos_itens:
        item_md = f"""# Item {idx} — {item_titulo}

> **Escopo:** [Descrever o que entra e o que nao entra neste item]
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]

---

## Contexto ja investigado

- Fatos e arquivos relevantes identificados no ecossistema.

## Definicao de Pronto

1. [Criterio 1 checavel e deterministico]
2. [Criterio 2 checavel e deterministico]
3. Testes executados com exit 0 e conformidade com os Quality Gates.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item {idx}: {item_titulo}.
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item {idx}: {item_titulo}.
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
"""
        (pasta_destino / item_arquivo).write_text(item_md, encoding="utf-8")

    erros = 0
    for arq in pasta_destino.glob("*.md"):
        ok, msg = verificar_cercas_arquivo(arq)
        if not ok:
            print(f"[ERRO DE CERCA] {arq.name}: {msg}")
            erros += 1

    if erros > 0:
        print("[ALERTA] Foram encontrados erros nas cercas de codigo geradas.")
        return 1

    print(f"[SUCESSO] Iniciativa '{pasta_nome}' criada com sucesso em:")
    print(f"  {pasta_destino}")
    print(f"  - 00-PROCESSO-E-DECISOES.md")
    for _, _, item_arquivo in arquivos_itens:
        print(f"  - {item_arquivo}")

    if base == DOCS_PLANOS:
        atualizador = ROOT_DIR / "scripts" / "atualizar_index_planos.py"
        if atualizador.exists():
            os.system(f'"{sys.executable}" "{atualizador}"')

    return 0


def main():
    parser = argparse.ArgumentParser(description="Gerenciador deterministico de planos do ecossistema AIDD")
    subparsers = parser.add_subparsers(dest="subcomando", required=True)

    parser_init = subparsers.add_parser("init", help="Cria o esqueleto de uma nova iniciativa de plano")
    parser_init.add_argument("nome", help="Nome da iniciativa (ex: refatoracao-auth)")
    parser_init.add_argument("--itens", nargs="+", default=[], help="Lista de titulos de itens para a iniciativa")

    parser_check = subparsers.add_parser("check-fences", help="Valida se cercas de codigo markdown estao balanceadas")
    parser_check.add_argument("caminho", help="Arquivo ou pasta markdown a verificar")

    args = parser.parse_args()

    if args.subcomando == "init":
        sys.exit(cmd_init(args.nome, args.itens))
    elif args.subcomando == "check-fences":
        sys.exit(cmd_check_fences(args.caminho))


if __name__ == "__main__":
    main()