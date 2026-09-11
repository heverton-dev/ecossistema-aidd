#!/usr/bin/env python3
"""
Gerenciador deterministico de planos de auditoria/evolucao/testes.
Cria a estrutura padrao (00-PROCESSO-E-DECISOES.md e NN-<item>.md) e checa integridade de cercas de codigo.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_PLANOS = ROOT_DIR / "docs" / "planos"

NOTA_NAO_AUDITADA = "NAO AUDITADO"
EVIDENCIA_PENDENTE = "(nota pendente de medicao real - nao preencher com estimativa)"
NOTA_REAL_PENDENTE = "[Pendente - preencher somente apos o fechamento real deste item/iniciativa, via o mesmo mecanismo que mediu a Nota Atual]"


def _valor_por_indice(lista: list[str] | None, idx: int, placeholder: str) -> str:
    """Retorna o valor na posicao idx de uma lista opcional, ou o placeholder
    se a lista for None, mais curta que idx, ou tiver string vazia ali.
    Nunca inventa um numero - a ausencia de dado vira rotulo explicito."""
    if lista and idx < len(lista) and lista[idx]:
        return lista[idx]
    return placeholder


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


# ---------------------------------------------------------------------------
# Leitura e atualizacao de Nota Atual em planos ja existentes (reanalise).
# ---------------------------------------------------------------------------

RE_NOTA_ATUAL_GERAL = re.compile(r"^- \*\*Nota Atual:\*\* (?P<nota>.+?) — evidencia: (?P<evidencia>.+)$", re.MULTILINE)
RE_NOTA_ATUAL_ITEM = re.compile(r"^> \*\*Nota Atual \(0-10\):\*\* (?P<nota>.+?) — evidencia: (?P<evidencia>.+)$", re.MULTILINE)


def _resolver_arquivo_item(pasta_plano: Path, item: str) -> Path | None:
    """Resolve o arquivo NN-<item>.md a partir de numero ('1'/'01'), nome do
    arquivo completo, ou slug/trecho do titulo do item."""
    if item.endswith(".md"):
        candidato = pasta_plano / item
        return candidato if candidato.exists() else None
    try:
        numero = int(item)
    except ValueError:
        numero = None
    if numero is not None:
        prefixo = f"{numero:02d}-"
        encontrados = sorted(pasta_plano.glob(f"{prefixo}*.md"))
        return encontrados[0] if encontrados else None
    slug = slugify(item)
    for arq in sorted(pasta_plano.glob("*.md")):
        if slug and slug in arq.stem:
            return arq
    return None


def ler_nota_geral(pasta_plano: Path) -> dict | None:
    """Le a Nota Atual/evidencia geral de um plano existente. Retorna None se
    o plano nao tiver esse bloco (formato antigo, anterior a esta metrica)."""
    caminho = pasta_plano / "00-PROCESSO-E-DECISOES.md"
    if not caminho.exists():
        return None
    m = RE_NOTA_ATUAL_GERAL.search(caminho.read_text(encoding="utf-8"))
    if not m:
        return None
    return {"nota_atual": m.group("nota").strip(), "evidencia": m.group("evidencia").strip()}


def ler_nota_item(pasta_plano: Path, item: str) -> dict | None:
    """Le a Nota Atual/evidencia de um item especifico. Retorna None se o
    item nao existir ou nao tiver esse bloco (formato antigo)."""
    caminho_item = _resolver_arquivo_item(pasta_plano, item)
    if caminho_item is None:
        return None
    m = RE_NOTA_ATUAL_ITEM.search(caminho_item.read_text(encoding="utf-8"))
    if not m:
        return None
    return {"nota_atual": m.group("nota").strip(), "evidencia": m.group("evidencia").strip()}


def _inserir_apos_marcador(texto: str, padrao_marcador: str, bloco_extra: str) -> str:
    m = re.search(padrao_marcador, texto, flags=re.MULTILINE)
    if not m:
        return texto.rstrip("\n") + "\n\n" + bloco_extra + "\n"
    fim = m.end()
    return texto[:fim] + "\n" + bloco_extra + texto[fim:]


def cmd_atualizar_nota(caminho_plano: str, item: str | None, nota_atual: str | None, evidencia: str | None) -> int:
    """Atualiza APENAS a linha de Nota Atual (geral, ou de um item) de um
    plano ja existente. Nunca mexe em Nota Alvo/Nota Real. Exige evidencia
    real explicita - nunca grava um numero sem prova, mesmo em atualizacao."""
    if not nota_atual or not evidencia:
        print("[ERRO] --nota-atual e --evidencia sao obrigatorios (nunca atualiza nota sem evidencia real).")
        return 1

    pasta_plano = Path(caminho_plano)
    if not pasta_plano.is_absolute():
        pasta_plano = ROOT_DIR / pasta_plano
    if not pasta_plano.is_dir():
        print(f"[ERRO] Pasta de plano nao encontrada: {pasta_plano}")
        return 1

    if item:
        caminho_arquivo = _resolver_arquivo_item(pasta_plano, item)
        if caminho_arquivo is None:
            print(f"[ERRO] Item '{item}' nao encontrado em {pasta_plano}")
            return 1
        conteudo = caminho_arquivo.read_text(encoding="utf-8")
        nova_linha = f"> **Nota Atual (0-10):** {nota_atual} — evidencia: {evidencia}"
        if RE_NOTA_ATUAL_ITEM.search(conteudo):
            conteudo_novo = RE_NOTA_ATUAL_ITEM.sub(lambda _m: nova_linha, conteudo, count=1)
        else:
            bloco_extra = (
                nova_linha + "\n"
                f"> **Nota Alvo (0-10):** {NOTA_NAO_AUDITADA}\n"
                f"> **Nota Real (pos-implementacao):** {NOTA_REAL_PENDENTE}"
            )
            conteudo_novo = _inserir_apos_marcador(conteudo, r"^> \*\*Status:\*\*.*$", bloco_extra)
        caminho_arquivo.write_text(conteudo_novo, encoding="utf-8")
        print(f"[SUCESSO] Nota Atual do item atualizada em {caminho_arquivo}")
        return 0

    caminho_geral = pasta_plano / "00-PROCESSO-E-DECISOES.md"
    if not caminho_geral.exists():
        print(f"[ERRO] {caminho_geral} nao encontrado.")
        return 1
    conteudo = caminho_geral.read_text(encoding="utf-8")
    nova_linha = f"- **Nota Atual:** {nota_atual} — evidencia: {evidencia}"
    if RE_NOTA_ATUAL_GERAL.search(conteudo):
        conteudo_novo = RE_NOTA_ATUAL_GERAL.sub(lambda _m: nova_linha, conteudo, count=1)
    else:
        bloco_extra = (
            "### Metrica da Iniciativa (0-10)\n\n"
            + nova_linha + "\n"
            f"- **Nota Alvo:** {NOTA_NAO_AUDITADA}\n"
            f"- **Nota Real (pos-implementacao):** {NOTA_REAL_PENDENTE}\n"
        )
        if "## 2. Processo Adotado" in conteudo:
            conteudo_novo = conteudo.replace("## 2. Processo Adotado", bloco_extra + "\n## 2. Processo Adotado", 1)
        else:
            conteudo_novo = conteudo.rstrip("\n") + "\n\n" + bloco_extra + "\n"
    caminho_geral.write_text(conteudo_novo, encoding="utf-8")
    print(f"[SUCESSO] Nota Atual geral atualizada em {caminho_geral}")
    return 0


def cmd_ler_nota(caminho_plano: str, item: str | None) -> int:
    """Le e imprime em JSON a Nota Atual/evidencia (geral ou de um item).
    Nunca falha por ausencia de dado - retorna NAO AUDITADO explicito."""
    pasta_plano = Path(caminho_plano)
    if not pasta_plano.is_absolute():
        pasta_plano = ROOT_DIR / pasta_plano
    if not pasta_plano.is_dir():
        print(json.dumps({"erro": f"Pasta de plano nao encontrada: {pasta_plano}"}, ensure_ascii=False))
        return 1

    info = ler_nota_item(pasta_plano, item) if item else ler_nota_geral(pasta_plano)
    if info is None:
        info = {
            "nota_atual": NOTA_NAO_AUDITADA,
            "evidencia": "(plano antigo, anterior a esta metrica, ou item sem nota registrada)",
        }
    print(json.dumps(info, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# Movimentacao de pasta por evento real: aprovacao humana (-> a-fazer/) e
# inicio real de execucao (-> fazendo/). Nunca decide a pasta destino aqui -
# so reescreve o marcador de status; quem decide a pasta e sempre
# atualizar_index_planos.py, a partir do status real do documento.
# ---------------------------------------------------------------------------

def _rodar_atualizador_index() -> None:
    """Roda atualizar_index_planos.py via subprocess.run (nunca os.system —
    em caminhos com espaco, os.system quebra na shell do Windows sem
    reportar exit code de erro nenhum, deixando a pasta sem mover em
    silencio)."""
    atualizador = ROOT_DIR / "scripts" / "atualizar_index_planos.py"
    if atualizador.exists():
        subprocess.run([sys.executable, str(atualizador)], cwd=ROOT_DIR)


def cmd_aprovar(caminho_plano: str) -> int:
    """Aprova TODOS os itens de uma iniciativa de uma vez (aprovacao e um
    evento do plano inteiro, nao item a item). Rescreve [RASCUNHO ...] para
    [APROVADO - Aguardando Execucao] em cada NN-<item>.md e o marcador
    correspondente na tabela de Registro de Progresso, depois aciona o
    atualizador de indice para mover fisicamente para docs/planos/a-fazer/
    (so quando o status agregado realmente virar 'aguardando')."""
    pasta_plano = Path(caminho_plano)
    if not pasta_plano.is_absolute():
        pasta_plano = ROOT_DIR / pasta_plano
    if not pasta_plano.is_dir():
        print(f"[ERRO] Pasta de plano nao encontrada: {pasta_plano}")
        return 1

    itens_aprovados = 0
    for item_arquivo in sorted(pasta_plano.glob("[0-9][0-9]-*.md")):
        conteudo = item_arquivo.read_text(encoding="utf-8")
        if "[RASCUNHO" not in conteudo:
            continue
        conteudo_novo = re.sub(r"\[RASCUNHO[^\]]*\]", "[APROVADO — Aguardando Execucao]", conteudo, count=1)
        item_arquivo.write_text(conteudo_novo, encoding="utf-8")
        itens_aprovados += 1

    caminho_00 = pasta_plano / "00-PROCESSO-E-DECISOES.md"
    if caminho_00.exists():
        conteudo = caminho_00.read_text(encoding="utf-8")
        conteudo_novo = conteudo.replace(
            "⏳ Rascunho gerado, aguardando aprovacao", "🔒 Aprovado, aguardando execucao"
        )
        if conteudo_novo != conteudo:
            caminho_00.write_text(conteudo_novo, encoding="utf-8")

    print(f"[SUCESSO] {itens_aprovados} item(ns) aprovado(s) em {pasta_plano}")
    _rodar_atualizador_index()
    return 0


def cmd_iniciar_execucao(caminho_plano: str) -> int:
    """Marca a iniciativa como EM EXECUCAO de verdade - chamado exatamente no
    momento em que a orquestracao real comeca (nunca em dry-run, nunca antes
    de o usuario confirmar o Plano de Voo). Move fisicamente para
    docs/planos/fazendo/ via atualizar_index_planos.py."""
    pasta_plano = Path(caminho_plano)
    if not pasta_plano.is_absolute():
        pasta_plano = ROOT_DIR / pasta_plano
    if not pasta_plano.is_dir():
        print(f"[ERRO] Pasta de plano nao encontrada: {pasta_plano}")
        return 1

    itens_marcados = 0
    for item_arquivo in sorted(pasta_plano.glob("[0-9][0-9]-*.md")):
        conteudo = item_arquivo.read_text(encoding="utf-8")
        conteudo_novo = re.sub(r"\[APROVADO[^\]]*\]|\[RASCUNHO[^\]]*\]", "[EM EXECUCAO]", conteudo, count=1)
        if conteudo_novo != conteudo:
            item_arquivo.write_text(conteudo_novo, encoding="utf-8")
            itens_marcados += 1

    caminho_00 = pasta_plano / "00-PROCESSO-E-DECISOES.md"
    if caminho_00.exists():
        conteudo = caminho_00.read_text(encoding="utf-8")
        conteudo_novo = conteudo.replace(
            "🔒 Aprovado, aguardando execucao", "🔶 Em execucao"
        ).replace(
            "⏳ Rascunho gerado, aguardando aprovacao", "🔶 Em execucao"
        )
        if conteudo_novo != conteudo:
            caminho_00.write_text(conteudo_novo, encoding="utf-8")

    print(f"[SUCESSO] {itens_marcados} item(ns) marcados como em execucao em {pasta_plano}")
    _rodar_atualizador_index()
    return 0


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


def cmd_init(
    nome: str,
    itens: list[str],
    destino_base: Path | None = None,
    notas_atuais: list[str] | None = None,
    notas_alvo: list[str] | None = None,
    evidencias: list[str] | None = None,
    nota_atual_geral: str | None = None,
    nota_alvo_geral: str | None = None,
    evidencia_geral: str | None = None,
) -> int:
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

    nota_atual_geral_str = nota_atual_geral or NOTA_NAO_AUDITADA
    nota_alvo_geral_str = nota_alvo_geral or NOTA_NAO_AUDITADA
    evidencia_geral_str = evidencia_geral or EVIDENCIA_PENDENTE
    if evidencia_geral_str == EVIDENCIA_PENDENTE:
        # Sem evidencia real, a nota geral nunca vira um numero (mesmo que
        # tenha sido passada) - evita nota "chutada" disfarcada de medida.
        nota_atual_geral_str = NOTA_NAO_AUDITADA

    linhas_tabela_conteudo = []
    linhas_tabela_progresso = []
    arquivos_itens = []

    for idx0, item_titulo in enumerate(itens):
        idx = idx0 + 1
        item_slug = slugify(item_titulo)
        item_arquivo = f"{idx:02d}-{item_slug}.md"
        nota_atual_item = _valor_por_indice(notas_atuais, idx0, NOTA_NAO_AUDITADA)
        nota_alvo_item = _valor_por_indice(notas_alvo, idx0, NOTA_NAO_AUDITADA)
        evidencia_item = _valor_por_indice(evidencias, idx0, EVIDENCIA_PENDENTE)
        if evidencia_item == EVIDENCIA_PENDENTE:
            # Mesma regra da nota geral: sem evidencia real, nunca vira numero.
            nota_atual_item = NOTA_NAO_AUDITADA
        linhas_tabela_conteudo.append(f"| {idx} | {item_titulo} | `{item_arquivo}` |")
        linhas_tabela_progresso.append(
            f"| {idx} | {item_titulo} | ⏳ Rascunho gerado, aguardando aprovacao | "
            f"{nota_atual_item} | {nota_alvo_item} | {NOTA_REAL_PENDENTE} | `{item_arquivo}` |"
        )
        arquivos_itens.append((idx, item_titulo, item_arquivo, nota_atual_item, nota_alvo_item, evidencia_item))

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

### Metrica da Iniciativa (0-10)

- **Nota Atual:** {nota_atual_geral_str} — evidencia: {evidencia_geral_str}
- **Nota Alvo:** {nota_alvo_geral_str}
- **Nota Real (pos-implementacao):** {NOTA_REAL_PENDENTE}

Nunca preencher Nota Atual sem evidencia real (relatorio de auditoria, comando ou
teste efetivamente rodado). Sem evidencia, o campo permanece `{NOTA_NAO_AUDITADA}`.

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

| # | Item | Status | Nota Atual | Nota Alvo | Nota Real | Documento |
|---|---|---|---|---|---|---|
{tabela_progresso_str}

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real.
A coluna Nota Real so e preenchida no fechamento de cada item, rodando o MESMO
mecanismo real que mediu a Nota Atual (nunca um comando "parecido").
"""

    (pasta_destino / "00-PROCESSO-E-DECISOES.md").write_text(processo_md, encoding="utf-8")

    for idx, item_titulo, item_arquivo, nota_atual_item, nota_alvo_item, evidencia_item in arquivos_itens:
        item_md = f"""# Item {idx} — {item_titulo}

> **Escopo:** [Descrever o que entra e o que nao entra neste item]
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Nota Atual (0-10):** {nota_atual_item} — evidencia: {evidencia_item}
> **Nota Alvo (0-10):** {nota_alvo_item}
> **Nota Real (pos-implementacao):** {NOTA_REAL_PENDENTE}

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
    for _, _, item_arquivo, *_resto in arquivos_itens:
        print(f"  - {item_arquivo}")

    if base == DOCS_PLANOS:
        _rodar_atualizador_index()

    return 0


def main():
    parser = argparse.ArgumentParser(description="Gerenciador deterministico de planos do ecossistema AIDD")
    subparsers = parser.add_subparsers(dest="subcomando", required=True)

    parser_init = subparsers.add_parser("init", help="Cria o esqueleto de uma nova iniciativa de plano")
    parser_init.add_argument("nome", help="Nome da iniciativa (ex: refatoracao-auth)")
    parser_init.add_argument("--itens", nargs="+", default=[], help="Lista de titulos de itens para a iniciativa")
    parser_init.add_argument("--notas-atuais", nargs="+", default=[],
                              help="Nota atual (0-10) de cada item, na mesma ordem de --itens. "
                                   "Exige evidencia real em --evidencias na mesma posicao.")
    parser_init.add_argument("--notas-alvo", nargs="+", default=[],
                              help="Nota alvo (0-10) de cada item, na mesma ordem de --itens")
    parser_init.add_argument("--evidencias", nargs="+", default=[],
                              help="Evidencia real (relatorio, comando ou teste rodado) que sustenta "
                                   "a nota atual de cada item, na mesma ordem de --itens")
    parser_init.add_argument("--nota-atual-geral", default=None,
                              help="Nota atual (0-10) da iniciativa como um todo")
    parser_init.add_argument("--nota-alvo-geral", default=None,
                              help="Nota alvo (0-10) da iniciativa como um todo")
    parser_init.add_argument("--evidencia-geral", default=None,
                              help="Evidencia real que sustenta a nota atual geral da iniciativa")

    parser_check = subparsers.add_parser("check-fences", help="Valida se cercas de codigo markdown estao balanceadas")
    parser_check.add_argument("caminho", help="Arquivo ou pasta markdown a verificar")

    parser_ler_nota = subparsers.add_parser("ler-nota", help="Le (JSON) a Nota Atual/evidencia de um plano existente - geral ou de um item")
    parser_ler_nota.add_argument("caminho", help="Caminho da pasta do plano (ex: docs/planos/a-fazer/<nome>)")
    parser_ler_nota.add_argument("--item", default=None, help="Numero/slug/arquivo do item (omitir para a nota geral)")

    parser_atualizar = subparsers.add_parser("atualizar-nota", help="Atualiza a Nota Atual (geral ou de um item) de um plano existente - nunca mexe em Nota Alvo/Real")
    parser_atualizar.add_argument("caminho", help="Caminho da pasta do plano (ex: docs/planos/a-fazer/<nome>)")
    parser_atualizar.add_argument("--item", default=None, help="Numero/slug/arquivo do item (omitir para a nota geral)")
    parser_atualizar.add_argument("--nota-atual", required=True, help="Nova Nota Atual (0-10)")
    parser_atualizar.add_argument("--evidencia", required=True, help="Evidencia real que sustenta a nova nota (obrigatorio)")

    parser_aprovar = subparsers.add_parser("aprovar", help="Aprova TODOS os itens de um plano de uma vez (rascunho -> aprovado) e move para docs/planos/a-fazer/")
    parser_aprovar.add_argument("caminho", help="Caminho da pasta do plano (ex: docs/planos/<nome>)")

    parser_iniciar = subparsers.add_parser("iniciar-execucao", help="Marca um plano como EM EXECUCAO de verdade e move para docs/planos/fazendo/ - chamar so no momento real do inicio da orquestracao")
    parser_iniciar.add_argument("caminho", help="Caminho da pasta do plano (ex: docs/planos/a-fazer/<nome>)")

    args = parser.parse_args()

    if args.subcomando == "init":
        sys.exit(cmd_init(
            args.nome,
            args.itens,
            notas_atuais=args.notas_atuais,
            notas_alvo=args.notas_alvo,
            evidencias=args.evidencias,
            nota_atual_geral=args.nota_atual_geral,
            nota_alvo_geral=args.nota_alvo_geral,
            evidencia_geral=args.evidencia_geral,
        ))
    elif args.subcomando == "check-fences":
        sys.exit(cmd_check_fences(args.caminho))
    elif args.subcomando == "ler-nota":
        sys.exit(cmd_ler_nota(args.caminho, args.item))
    elif args.subcomando == "atualizar-nota":
        sys.exit(cmd_atualizar_nota(args.caminho, args.item, args.nota_atual, args.evidencia))
    elif args.subcomando == "aprovar":
        sys.exit(cmd_aprovar(args.caminho))
    elif args.subcomando == "iniciar-execucao":
        sys.exit(cmd_iniciar_execucao(args.caminho))


if __name__ == "__main__":
    main()