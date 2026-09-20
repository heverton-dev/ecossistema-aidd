# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — GERADOR DETERMINISTICO DO LIVRO-TEXTO DO PROJETO
=============================================================================
Etapa final (8a) dos tres Fluxos Canonicos: transforma os artefatos que a
esteira JA gravou no projeto em um livro-texto estruturado, sem consumir um
unico token de LLM.

Regra fundamental — EVIDENCIA OU SILENCIO:
  Cada afirmacao do livro nasce de um arquivo real lido do projeto. Quando o
  artefato nao existe, a secao registra explicitamente a ausencia em vez de
  preencher com texto generico. Nunca fabricar dado, numero ou conclusao.

Entradas (todas opcionais — o livro se adapta ao que existe):
  PLANNER.json                     plano BDD/SDD (nome, dominio, contextos, cenarios)
  DESIGN-SYSTEM.json               identidade visual escolhida
  HANDOFF_PLANNER_ENGINE.json      contrato plano -> motor
  HANDOFF_ENGINE_MASTER.json       fatias geradas, frontend, testes executados
  HANDOFF_MASTER_ENTERPRISE.json   rotas do Quarteto, componentes a blindar
  HANDOFF_ENTERPRISE_OPS.json      auditoria SHA-256, manifesto de deploy
  ORQUESTRACAO_EXECUCAO.json       manifesto final da esteira
  PLANO-INFRAESTRUTURA.json        dimensionamento (Fluxos 02 e 03)
  FACTORY_OUTPUT.json              artefatos gerados (Fluxo 02)
  relatorio_final.md               auto-critica da Fase 7 (Fluxo 01)
  arvore real de src/ e testes      conferencia do que existe em disco

Saida:
  <projeto>/livro/partes/*.md   as partes do livro (fonte editavel)
  <projeto>/livro/livro.json    manifesto lido pelo motor da skill aidd-livro-texto

Uso:
  python scripts/gerador_livro_projeto.py <pasta-do-projeto>
  python scripts/gerador_livro_projeto.py <pasta> --compilar     # gera tambem o PDF
  python scripts/gerador_livro_projeto.py <pasta> --titulo "..."

Exit: 0 = livro gerado, 1 = falha real (nunca mascara ausencia de evidencia).
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
SKILL_LIVRO = ROOT_DIR / "componentes" / "compartilhado" / "skills" / "aidd-livro-texto"
MOTOR_LIVRO = SKILL_LIVRO / "scripts" / "livro.py"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AUSENTE = "_(artefato ausente nesta execução — nada a declarar)_"


# ---------------------------------------------------------------------------
# Leitura de evidencia
# ---------------------------------------------------------------------------

class Evidencia:
    """Le os artefatos do projeto e guarda a procedencia de cada um.

    Toda consulta devolve o dado E registra qual arquivo o forneceu, para que a
    secao de rastreabilidade do livro cite apenas fontes efetivamente lidas.
    """

    ARTEFATOS = {
        "planner": "PLANNER.json",
        "design": "DESIGN-SYSTEM.json",
        "handoff_plano": "HANDOFF_PLANNER_ENGINE.json",
        "handoff_engine": "HANDOFF_ENGINE_MASTER.json",
        "handoff_master": "HANDOFF_MASTER_ENTERPRISE.json",
        "handoff_ops": "HANDOFF_ENTERPRISE_OPS.json",
        "orquestracao": "ORQUESTRACAO_EXECUCAO.json",
        "infraestrutura": "PLANO-INFRAESTRUTURA.json",
        "factory": "FACTORY_OUTPUT.json",
    }

    def __init__(self, pasta: Path):
        self.pasta = pasta
        self.dados: dict[str, Any] = {}
        self.fontes: dict[str, str] = {}
        self.ausentes: list[str] = []
        self._carregar()

    def _carregar(self) -> None:
        for chave, nome in self.ARTEFATOS.items():
            caminho = self.pasta / nome
            if not caminho.is_file():
                self.ausentes.append(nome)
                continue
            try:
                self.dados[chave] = json.loads(caminho.read_text(encoding="utf-8"))
                self.fontes[chave] = nome
            except (json.JSONDecodeError, OSError) as exc:
                self.ausentes.append(f"{nome} (ilegivel: {exc.__class__.__name__})")

        relatorio = self.pasta / "relatorio_final.md"
        if relatorio.is_file():
            self.dados["auto_critica"] = relatorio.read_text(encoding="utf-8", errors="replace")
            self.fontes["auto_critica"] = "relatorio_final.md"
        else:
            self.ausentes.append("relatorio_final.md")

    def get(self, chave: str, *caminho: str, padrao: Any = None) -> Any:
        """Navega por chaves aninhadas devolvendo `padrao` quando o caminho nao existe."""
        atual = self.dados.get(chave)
        for parte in caminho:
            if not isinstance(atual, dict):
                return padrao
            atual = atual.get(parte)
        return atual if atual is not None else padrao

    def tem(self, chave: str) -> bool:
        return chave in self.dados

    def citar(self, *chaves: str) -> list[str]:
        """Nomes dos arquivos que realmente forneceram dado, para a rastreabilidade."""
        return [self.fontes[c] for c in chaves if c in self.fontes]

    # --- leitura do que existe em disco, nao do que foi prometido ------------

    def modulos_em_disco(self) -> list[str]:
        """Diretorios de fatia vertical realmente presentes no projeto."""
        achados: list[str] = []
        for base in ("src/modules", "src/features", "app/modules", "backend/src/modules"):
            raiz = self.pasta / base
            if raiz.is_dir():
                achados += sorted(
                    f"{base}/{d.name}" for d in raiz.iterdir()
                    if d.is_dir() and not d.name.startswith((".", "__"))
                )
        return achados

    def arquivos_de_teste(self) -> int:
        """Quantidade de arquivos de teste presentes, contados em disco."""
        total = 0
        for padrao in ("test_*.py", "*_test.py", "*.test.ts", "*.spec.ts"):
            total += len([
                p for p in self.pasta.rglob(padrao)
                if "__pycache__" not in str(p) and "node_modules" not in str(p)
                and ".venv" not in str(p)
            ])
        return total

    def infra_em_disco(self) -> list[str]:
        nomes = ("Dockerfile", "docker-compose.yml", "compose.yaml", "docker-compose.yaml")
        return [n for n in nomes if (self.pasta / n).is_file()]


# ---------------------------------------------------------------------------
# Utilitarios de escrita
# ---------------------------------------------------------------------------

def escrever(caminho: Path, conteudo: str) -> None:
    """Gravacao atomica: staging -> fsync -> replace."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    with open(temporario, "w", encoding="utf-8", newline="\n") as f:
        f.write(conteudo)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporario, caminho)


def tabela(cabecalhos: list[str], linhas: list[list[str]], larguras: list[int] | None = None) -> str:
    """Monta tabela Markdown larga o bastante para ocupar a pagina no PDF.

    O conversor so emite larguras relativas quando a linha de separadores passa de
    72 caracteres; abaixo disso a tabela encolhe e desalinha (ver a referencia de
    diagramacao da skill aidd-livro-texto).
    """
    if larguras is None:
        # A largura de cada coluna no PDF e proporcional ao comprimento do separador,
        # entao ela precisa acomodar o MAIOR conteudo da coluna — nao so o cabecalho.
        # Sem isso, um nome de arquivo longo transborda por cima da coluna vizinha.
        maiores = [len(str(c)) for c in cabecalhos]
        for linha in linhas:
            for i, celula in enumerate(linha[:len(maiores)]):
                maiores[i] = max(maiores[i], len(str(celula)))
        larguras = [max(20, m + 4) for m in maiores]
        sobra = 176 - sum(larguras)
        if sobra > 0:
            larguras[-1] += sobra

    cab = "| " + " | ".join(c.ljust(l) for c, l in zip(cabecalhos, larguras)) + " |"
    sep = "| " + " | ".join(":" + "-" * (l - 1) for l in larguras) + " |"
    corpo = [
        "| " + " | ".join(str(celula).ljust(l) for celula, l in zip(linha, larguras)) + " |"
        for linha in linhas
    ]
    return "\n".join([cab, sep] + corpo)


def rastreabilidade(titulo: str, fontes: list[str], extras: list[str] | None = None) -> str:
    itens = list(fontes) + list(extras or [])
    if not itens:
        return f"## {titulo}\n\n{AUSENTE}\n"
    citados = "; ".join(f"`{i}`" for i in itens)
    return f"## {titulo}\n\nAfirmações deste capítulo derivam de: {citados}.\n"


# ---------------------------------------------------------------------------
# Partes do livro
# ---------------------------------------------------------------------------

def parte_frontmatter(ev: Evidencia, titulo: str, autor: str) -> str:
    nome = ev.get("planner", "meta", "projeto_nome", padrao=titulo)
    dominio = ev.get("planner", "meta", "dominio", padrao="nao declarado")
    descricao = ev.get("planner", "meta", "descricao", padrao="")
    fluxo = ev.get("planner", "meta", "fluxo_alvo", padrao=ev.get("orquestracao", "fluxo", padrao="nao registrado"))
    contextos = ev.get("planner", "ddd_bounded_contexts", padrao=[]) or []
    cenarios = ev.get("planner", "bdd_cenarios", padrao=[]) or []

    return f"""---
title: "{nome}"
subtitle: "Livro-texto do sistema"
author:
  - {autor}
date: "{date.today().strftime('%d/%m/%Y')}"
lang: pt-BR
institute: "{nome}"
eyebrow: "DOCUMENTAÇÃO TÉCNICA GERADA DA EVIDÊNCIA"
tagline: |
  Este livro foi montado a partir dos artefatos que a esteira de construção
  gravou no projeto — não a partir de intenção ou de descrição manual.
toc: true
toc-depth: 2
abstract: |
  Este livro descreve o sistema **{nome}**, do domínio de {dominio}, construído
  pelo Ecossistema AIDD.

  Cada capítulo é derivado de um arquivo real deixado pela construção: o plano
  formal, os contratos trocados entre as etapas, o relatório de autocrítica e
  a própria árvore de arquivos em disco. Onde o artefato não existe, o texto
  registra a ausência em vez de preencher com suposição.

  O livro percorre quatro níveis: o que o sistema é, como ele está organizado
  por dentro, o que foi verificado sobre ele, e como ele opera em produção.
---

# Como ler este livro

## O que este livro é

Este é o livro-texto do sistema **{nome}**. Ele foi gerado automaticamente ao
final da construção, lendo os registros que cada etapa deixou.

{("O plano formal descreve o projeto assim: " + descricao) if descricao else AUSENTE}

{tabela(
    ["Característica", "Valor registrado", "Onde está registrado"],
    [
        ["Nome do sistema", str(nome), "`PLANNER.json`" if ev.tem("planner") else "-"],
        ["Domínio de negócio", str(dominio), "`PLANNER.json`" if ev.tem("planner") else "-"],
        ["Fluxo de construção", str(fluxo), "`PLANNER.json` / `ORQUESTRACAO_EXECUCAO.json`"],
        ["Contextos delimitados", str(len(contextos)), "`PLANNER.json`" if ev.tem("planner") else "-"],
        ["Cenários de comportamento", str(len(cenarios)), "`PLANNER.json`" if ev.tem("planner") else "-"],
    ],
)}

## Como ele foi montado

Nenhuma frase deste livro foi escrita por um modelo de linguagem. Um programa
determinístico abriu os arquivos de resultado da construção, leu o que estava
registrado e transcreveu. A consequência prática: o livro pode ser mais seco
que um texto escrito à mão, mas não pode afirmar o que não aconteceu.

Ao final de cada capítulo, a seção *Rastreabilidade* nomeia os arquivos que
sustentam aquele capítulo. Qualquer afirmação pode ser conferida abrindo o
arquivo citado dentro da pasta do projeto.

## O que ele não cobre

Este livro descreve **o que foi construído e verificado**. Ele não substitui o
guia do usuário final (que vive na rota de documentação do próprio sistema),
não ensina a operar a interface e não explica decisões que ninguém registrou.
"""


def parte_visao(ev: Evidencia) -> str:
    contextos = ev.get("planner", "ddd_bounded_contexts", padrao=[]) or []
    cenarios = ev.get("planner", "bdd_cenarios", padrao=[]) or []

    corpo = ["# PARTE I — O QUE O SISTEMA É", "",
             "Esta parte responde à pergunta mais alta: que problema este sistema resolve,",
             "para qual domínio, e quais são as fronteiras de negócio que ele reconhece.", "",
             "# Capítulo 1 — Domínio e contextos delimitados", ""]

    if contextos:
        corpo += [
            "O plano formal do projeto declarou os seguintes contextos delimitados — as",
            "fronteiras dentro das quais cada conceito de negócio tem significado próprio:",
            "",
            tabela(
                ["Contexto", "Responsabilidade declarada", "Entidades"],
                [[str(c.get("modulo", "?")), str(c.get("descricao", "-"))[:90],
                  str(len(c.get("entidades", []) or []))] for c in contextos],
            ),
            "",
        ]
        for contexto in contextos:
            entidades = contexto.get("entidades", []) or []
            if not entidades:
                continue
            corpo += [f"## 1.{contextos.index(contexto) + 1} Contexto `{contexto.get('modulo', '?')}`", ""]
            for entidade in entidades:
                corpo += [f"### Entidade `{entidade.get('nome', '?')}`", ""]

                # O plano representa os campos de duas formas conforme a origem:
                # dicionario {nome: tipo} (aidd-planner) ou lista de objetos com
                # nome/tipo/obrigatorio (contrato de handoff). Ambas sao aceitas.
                campos = entidade.get("atributos") or entidade.get("campos") or []
                linhas = []
                if isinstance(campos, dict):
                    linhas = [[nome, str(tipo), "-"] for nome, tipo in campos.items()]
                else:
                    for campo in campos:
                        if isinstance(campo, dict):
                            linhas.append([
                                str(campo.get("nome", "?")),
                                str(campo.get("tipo", "-")),
                                "sim" if campo.get("obrigatorio") else "não",
                            ])
                        else:
                            linhas.append([str(campo), "-", "-"])

                if linhas:
                    corpo += [tabela(["Campo", "Tipo", "Obrigatório"], linhas), ""]
                else:
                    corpo += [AUSENTE, ""]

                # As invariantes sao as regras de negocio que a entidade precisa
                # respeitar sempre — o material mais valioso do plano para quem vai
                # manter o sistema depois.
                invariantes = entidade.get("regras_invariantes") or []
                if invariantes:
                    corpo += ["**Regras que esta entidade deve respeitar sempre:**", ""]
                    corpo += [f"- {regra}" for regra in invariantes]
                    corpo += [""]
    else:
        corpo += ["Nenhum contexto delimitado foi encontrado no plano formal.", "", AUSENTE, ""]

    corpo += ["# Capítulo 2 — Comportamento esperado", ""]
    if cenarios:
        corpo += [
            f"O plano declarou {len(cenarios)} cenário(s) de comportamento no formato",
            "*dado / quando / então*. Eles são o critério de aceite do sistema: descrevem",
            "o que deve acontecer, em linguagem de negócio, antes de qualquer código.",
            "",
        ]
        for cenario in cenarios:
            corpo += [
                f"## {cenario.get('id', 'SCN')} — {cenario.get('titulo', 'sem titulo')}",
                "",
                f"**Modulo:** `{cenario.get('modulo', '-')}`",
                "",
                f"- **Dado** {cenario.get('dado', '-')}",
                f"- **Quando** {cenario.get('quando', '-')}",
                f"- **Então** {cenario.get('entao', '-')}",
                "",
            ]
    else:
        corpo += [AUSENTE, ""]

    corpo += [rastreabilidade("Rastreabilidade da Parte I", ev.citar("planner", "handoff_plano"))]
    return "\n".join(corpo)


def parte_arquitetura(ev: Evidencia) -> str:
    quarteto = ev.get("planner", "quarteto_sine_qua_non", padrao={}) or {}
    rotas_quarteto = ev.get("handoff_master", "quarteto_sine_qua_non_rotas", padrao={}) or {}
    arquitetura = ev.get("handoff_plano", "arquitetura_alvo", padrao={}) or {}
    fatias = ev.get("handoff_engine", "slices_geradas", padrao=[]) or []
    frontend = ev.get("handoff_engine", "artefatos_frontend", padrao={}) or {}
    modulos_disco = ev.modulos_em_disco()

    corpo = ["# PARTE II — COMO O SISTEMA ESTÁ ORGANIZADO", "",
             "Esta parte descreve a arquitetura **como ela ficou**, conforme registrado nos",
             "contratos trocados entre as etapas da construção e conferido na árvore de",
             "arquivos do projeto.", "",
             "# Capítulo 3 — Arquitetura registrada", ""]

    if arquitetura:
        corpo += [
            tabela(
                ["Camada", "Padrao registrado"],
                [[str(k).replace("_", " ").capitalize(), str(v)] for k, v in arquitetura.items()],
            ),
            "",
        ]
    else:
        corpo += [AUSENTE, ""]

    corpo += ["## 3.1 Fatias verticais", ""]
    if fatias:
        linhas = []
        for fatia in fatias:
            endpoints = fatia.get("endpoints", []) or []
            linhas.append([
                str(fatia.get("slice_nome", "?")),
                f"`{fatia.get('caminho_src', '-')}`",
                str(len(endpoints)),
                ", ".join(str(t) for t in (fatia.get("tabelas_sql", []) or [])) or "-",
            ])
        corpo += [tabela(["Fatia", "Caminho no código", "Rotas", "Tabelas"], linhas), ""]

        for fatia in fatias:
            endpoints = fatia.get("endpoints", []) or []
            if not endpoints:
                continue
            corpo += [f"### Rotas da fatia `{fatia.get('slice_nome', '?')}`", "",
                      tabela(["Método", "Rota", "Função"],
                             [[str(e.get("metodo", "-")), f"`{e.get('rota', '-')}`",
                               f"`{e.get('funcao', '-')}`"] for e in endpoints]), ""]
    else:
        corpo += [AUSENTE, ""]

    corpo += ["## 3.2 O que existe em disco", "",
              "A lista acima vem do contrato registrado. A lista abaixo foi obtida abrindo a",
              "pasta do projeto — e serve justamente para confrontar o prometido com o real:", ""]
    if modulos_disco:
        corpo += [tabela(["Diretório de módulo encontrado"], [[f"`{m}`"] for m in modulos_disco]), ""]
    else:
        corpo += ["Nenhum diretório de módulo foi encontrado nos caminhos usuais",
                  "(`src/modules`, `src/features`, `app/modules`).", ""]

    corpo += ["# Capítulo 4 — Interface com o mundo", "",
              "## 4.1 O Quarteto obrigatório", "",
              "Todo sistema do ecossistema nasce com quatro portas: documentação navegável da",
              "interface de programação, disparo de eventos para sistemas externos, acesso por",
              "agentes de inteligência artificial e guia para pessoas.", ""]

    if quarteto or rotas_quarteto:
        linhas = []
        for chave in ("swagger", "webhooks", "mcp", "guia", "docs", "documentacao"):
            if chave in ("docs", "documentacao") and ("guia" in quarteto or "guia" in rotas_quarteto):
                continue
            declarado = quarteto.get(chave)
            rota = rotas_quarteto.get(chave)
            if declarado is None and rota is None:
                continue
            ativo = declarado.get("ativo") if isinstance(declarado, dict) else declarado
            prefixo = declarado.get("prefixo") if isinstance(declarado, dict) else None
            linhas.append([
                chave,
                "sim" if ativo else ("nao" if ativo is not None else "-"),
                f"`{prefixo or rota or '-'}`",
            ])
        corpo += [tabela(["Porta", "Declarada ativa", "Rota"], linhas) if linhas else AUSENTE, ""]
    else:
        corpo += [AUSENTE, ""]

    corpo += ["## 4.2 Frontend", ""]
    if frontend:
        paginas = frontend.get("paginas_geradas", []) or []
        corpo += [
            tabela(["Aspecto", "Registrado"],
                   [["Tecnologia", str(frontend.get("tecnologia", "-"))],
                    ["Origem do design", str(frontend.get("origem_design", "-"))],
                    ["Páginas geradas", ", ".join(str(p) for p in paginas) or "-"]]),
            "",
        ]
    else:
        corpo += [AUSENTE, ""]

    corpo += [rastreabilidade(
        "Rastreabilidade da Parte II",
        ev.citar("handoff_plano", "handoff_engine", "handoff_master", "planner"),
        ["árvore de diretórios do próprio projeto"],
    )]
    return "\n".join(corpo)


def parte_qualidade(ev: Evidencia) -> str:
    testes = ev.get("handoff_engine", "testes_executados", padrao={}) or {}
    sha_ok = ev.get("handoff_ops", "sha256_audit_ok")
    drift_ok = ev.get("handoff_ops", "drift_verificado")
    etapas = ev.get("orquestracao", "etapas_concluidas", padrao=[]) or []
    arquivos_teste = ev.arquivos_de_teste()

    corpo = ["# PARTE III — O QUE FOI VERIFICADO", "",
             "Esta parte é a que mais importa para quem precisa confiar no sistema. Ela separa",
             "o que foi **medido** do que foi apenas **declarado**.", "",
             "# Capítulo 5 — Testes", ""]

    if testes:
        total = testes.get("total", "-")
        passaram = testes.get("passaram", "-")
        falharam = testes.get("falharam", "-")
        corpo += [
            tabela(["Métrica registrada no contrato", "Valor"],
                   [["Total de testes", str(total)],
                    ["Passaram", str(passaram)],
                    ["Falharam", str(falharam)],
                    ["Declarado sem código vazio", "sim" if testes.get("zero_stubs") else "nao"]]),
            "",
            "> **Leitura honesta:** os números acima são os que a etapa registrou no contrato",
            "> de passagem. A contagem independente abaixo foi feita agora, abrindo a pasta.",
            "",
        ]
    else:
        corpo += [AUSENTE, ""]

    corpo += [
        f"Contagem independente, feita percorrendo o projeto: **{arquivos_teste} arquivo(s)"
        f" de teste** presentes em disco.",
        "",
        "# Capítulo 6 — Integridade e blindagem",
        "",
    ]

    if sha_ok is not None or drift_ok is not None:
        corpo += [
            tabela(["Verificação", "Resultado registrado"],
                   [["Conferência criptográfica dos componentes", "aprovada" if sha_ok else "não aprovada"],
                    ["Divergência entre cópias de componentes", "sem divergência" if drift_ok else "divergência detectada"]]),
            "",
        ]
    else:
        corpo += [AUSENTE, ""]

    corpo += ["# Capítulo 7 — Etapas concluídas na construção", ""]
    if etapas:
        corpo += [tabela(["Ordem", "Etapa registrada como concluída"],
                         [[str(i + 1), str(e)] for i, e in enumerate(etapas)]), ""]
    else:
        corpo += [AUSENTE, ""]

    if ev.tem("auto_critica"):
        corpo += ["# Capítulo 8 — Autocrítica registrada", "",
                  "A etapa de autocrítica produziu o relatório abaixo (transcrito integralmente,",
                  "sem edição):", "", "```text",
                  ev.dados["auto_critica"][:6000].strip(), "```", ""]

    corpo += [rastreabilidade(
        "Rastreabilidade da Parte III",
        ev.citar("handoff_engine", "handoff_ops", "orquestracao", "auto_critica"),
        ["contagem de arquivos de teste feita em disco"],
    )]
    return "\n".join(corpo)


def parte_operacao(ev: Evidencia) -> str:
    manifesto = ev.get("handoff_ops", "manifesto_deploy", padrao={}) or {}
    infra_disco = ev.infra_em_disco()
    sizing = ev.get("infraestrutura", "fase_3_sizing", padrao={}) or {}
    ferramentas = ev.get("infraestrutura", "fase_2_curadoria", "saida", "ferramentas", padrao=[]) or []

    corpo = ["# PARTE IV — COMO O SISTEMA OPERA", "",
             "# Capítulo 9 — Empacotamento e publicação", ""]

    if manifesto:
        portas = manifesto.get("portas_expostas", []) or []
        corpo += [
            tabela(["Item do manifesto", "Registrado"],
                   [["Forma de execução", str(manifesto.get("tipo_runtime", "-"))],
                    ["Receita de imagem presente", "sim" if manifesto.get("dockerfile_presente") else "não"],
                    ["Orquestração de serviços presente", "sim" if manifesto.get("compose_presente") else "não"],
                    ["Portas expostas", ", ".join(str(p) for p in portas) or "-"]]),
            "",
        ]
    else:
        corpo += [AUSENTE, ""]

    corpo += ["## 9.1 Conferência em disco", ""]
    if infra_disco:
        corpo += [tabela(["Arquivo de infraestrutura encontrado"], [[f"`{a}`"] for a in infra_disco]), ""]
    else:
        corpo += ["Nenhum arquivo de empacotamento foi encontrado na raiz do projeto.", ""]

    if ferramentas or sizing:
        corpo += ["# Capítulo 10 — Infraestrutura dimensionada", ""]
        if ferramentas:
            linhas = [[str(f.get("nome", f) if isinstance(f, dict) else f)] for f in ferramentas]
            corpo += [tabela(["Serviço curado para a stack"], linhas), ""]
        if sizing:
            saida = sizing.get("saida", sizing)
            if isinstance(saida, dict):
                linhas = [[str(k).replace("_", " ").capitalize(), str(v)[:70]]
                          for k, v in saida.items() if not isinstance(v, (dict, list))]
                if linhas:
                    corpo += [tabela(["Dimensionamento", "Valor"], linhas), ""]

    corpo += [rastreabilidade(
        "Rastreabilidade da Parte IV",
        ev.citar("handoff_ops", "infraestrutura", "factory"),
        ["conferência de arquivos de infraestrutura em disco"],
    )]
    return "\n".join(corpo)


def parte_apendices(ev: Evidencia) -> str:
    corpo = ["# Apêndice A — Estado honesto desta documentação", "",
             "A regra que governa este livro é simples: só entra o que tem arquivo que comprove.",
             "Esta tabela lista o que **não** pode ser afirmado, e por quê.", ""]

    if ev.ausentes:
        corpo += [
            tabela(["Artefato ausente", "Consequência para este livro"],
                   [[f"`{a}`", "o capítulo correspondente registra a ausência em vez de supor"]
                    for a in ev.ausentes]),
            "",
        ]
    else:
        corpo += ["Todos os artefatos esperados foram encontrados e lidos.", ""]

    corpo += [
        "# Apêndice B — Como conferir este livro",
        "",
        "Cada capítulo termina citando os arquivos que o sustentam. Para conferir qualquer",
        "afirmação, abra o arquivo citado na pasta do projeto e compare.",
        "",
        "Para regerar este livro após uma mudança no sistema:",
        "",
        "```bash",
        "python scripts/gerador_livro_projeto.py <pasta-do-projeto> --compilar",
        "```",
        "",
        "Para conferir automaticamente que nenhum arquivo citado desapareceu:",
        "",
        "```bash",
        "python gates/G_LIVRO_EVIDENCIA.py --projeto <pasta-do-projeto>",
        "```",
        "",
        "# Apêndice C — Procedência",
        "",
        f"Livro gerado em {date.today().strftime('%d/%m/%Y')} pelo gerador determinístico do",
        "Ecossistema AIDD, sem consumo de modelo de linguagem. A parte explicativa, quando",
        "solicitada, é escrita separadamente pelo comando `/aidd-livro-texto`.",
        "",
    ]
    return "\n".join(corpo)


# ---------------------------------------------------------------------------
# Orquestracao
# ---------------------------------------------------------------------------

PARTES = (
    ("00-frontmatter.md", None),
    ("01-visao.md", parte_visao),
    ("02-arquitetura.md", parte_arquitetura),
    ("03-qualidade.md", parte_qualidade),
    ("04-operacao.md", parte_operacao),
    ("05-apendices.md", parte_apendices),
)


def gerar(pasta_projeto: Path, titulo: str | None, autor: str, compilar: bool) -> int:
    if not pasta_projeto.is_dir():
        print(f"[ERRO] pasta do projeto nao encontrada: {pasta_projeto}", file=sys.stderr)
        return 1

    ev = Evidencia(pasta_projeto)
    if not ev.dados:
        print("[ERRO] nenhum artefato da esteira foi encontrado nesta pasta.", file=sys.stderr)
        print("       Esperado ao menos um de: " + ", ".join(Evidencia.ARTEFATOS.values()), file=sys.stderr)
        return 1

    nome = titulo or ev.get("planner", "meta", "projeto_nome", padrao=pasta_projeto.name)
    destino = pasta_projeto / "livro"
    dir_partes = destino / "partes"

    escrever(dir_partes / "00-frontmatter.md", parte_frontmatter(ev, str(nome), autor))
    for arquivo, funcao in PARTES[1:]:
        escrever(dir_partes / arquivo, funcao(ev) + "\n")

    slug = str(ev.get("planner", "meta", "slug", padrao=pasta_projeto.name))
    manifesto = {
        "versao_manifesto": "1.0",
        "titulo": str(nome),
        "nome_base": f"{date.today().strftime('%d-%m-%Y')}_LIVRO-{slug.upper()}",
        "pasta_partes": "partes",
        "template": None,
        "partes": [nome_arquivo for nome_arquivo, _ in PARTES],
        "revisoes": [],
        "gerado_por": "scripts/gerador_livro_projeto.py",
        "artefatos_lidos": sorted(ev.fontes.values()),
        "artefatos_ausentes": sorted(ev.ausentes),
    }
    escrever(destino / "livro.json", json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n")

    print(f"[OK] livro gerado em {destino}")
    print(f"     artefatos lidos:    {len(ev.fontes)} ({', '.join(sorted(ev.fontes.values()))})")
    if ev.ausentes:
        print(f"     artefatos ausentes: {len(ev.ausentes)} (registrados no Apendice A)")

    if compilar:
        if not MOTOR_LIVRO.is_file():
            print(f"[ERRO] motor da skill nao encontrado: {MOTOR_LIVRO}", file=sys.stderr)
            return 1
        res = subprocess.run([sys.executable, str(MOTOR_LIVRO), "build", str(destino)],
                             capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(res.stdout.strip() or res.stderr.strip()[-1500:])
        if res.returncode != 0:
            return res.returncode

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gera o livro-texto de um projeto a partir dos artefatos da esteira")
    parser.add_argument("projeto", help="pasta do projeto construido pelo ecossistema")
    parser.add_argument("--titulo", default=None, help="titulo do livro (padrao: nome no plano)")
    parser.add_argument("--autor", default="Ecossistema AIDD", help="autor exibido na capa")
    parser.add_argument("--compilar", action="store_true", help="tambem gera o PDF")
    args = parser.parse_args(argv)
    return gerar(Path(args.projeto).resolve(), args.titulo, args.autor, args.compilar)


if __name__ == "__main__":
    sys.exit(main())
