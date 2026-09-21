#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — COMPILADOR DE TICKETS DE PLANO PARA HANDOFF (ISSUE-PIPE-0004)
=============================================================================
Compilador determinístico que processa diretórios de iniciativas de planos
Markdown (docs/planos/PLAN-<NNNN>-<slug>/) e gera o manifesto formal
'handoff_evolution.json' validado contra 'handoff-execucao.schema.json'.

Invariantes e Leis Auditadas:
  1. Determinismo First (Lei #1): Parser determinístico via Regex, AST e ordenação
     topológica de grafo acíclico dirigido (DAG).
  2. Saída Binária (Lei #2): exit 0 = compilação e validação 100% conformes;
     exit 1 = ciclos não resolvíveis, comandos ausentes/triviais ou erro de schema.
  3. Zero Stubs (Lei #5): Rejeição de TODO, FIXME, PLACEHOLDER, comandos triviais.
  4. Separação Estrita de Fases:
     - Tickets com blocked_by: [] e arquivos_alvo disjuntos vão para a fase paralela.
     - Tickets dependentes ou com sobreposição de arquivos vão para a fase sequencial.
  5. Barreira de Sincronização: Quality Gates determinísticos inseridos na junção.

Uso CLI:
  python scripts/compilador_tickets_plano.py --plano docs/planos/PLAN-0029-teste-e2e-ferramentas
  python scripts/compilador_tickets_plano.py -p PLAN-0029-teste-e2e-ferramentas --output custom_handoff.json
=============================================================================
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_PLANOS_DIR = ROOT_DIR / "docs" / "planos"
SPECS_DIR = ROOT_DIR / "componentes" / "compartilhado" / "specs"
SCHEMA_CANONICO = SPECS_DIR / "handoff-execucao.schema.json"
GATE_SCRIPT = ROOT_DIR / "gates" / "G_PIPELINE_HANDOFF.py"

PADRAO_STUB = re.compile(r"(?i)\b(TODO|FIXME|PLACEHOLDER|TBD|stub|dummy)\b")
PADRAO_CMD_TRIVIAL = re.compile(r"^\s*(exit\s+0|echo\s+ok|true|pass)\s*$", re.IGNORECASE)


class CompiladorErro(Exception):
    """Exceção levantada para erros de compilação de tickets e planos."""
    pass


def carregar_schema() -> Dict[str, Any]:
    """Carrega o JSON Schema canônico de handoff de execução."""
    if not SCHEMA_CANONICO.is_file():
        raise FileNotFoundError(f"Schema canônico não encontrado em: {SCHEMA_CANONICO}")
    with open(SCHEMA_CANONICO, "r", encoding="utf-8") as f:
        return json.load(f)


def resolver_diretorio_plano(plano_arg: str | Path) -> Path:
    """
    Resolve o diretório do plano informado, buscando diretamente pelo caminho
    ou pesquisando recursivamente em docs/planos/ por slug ou prefixo PLAN-XXXX.
    """
    p = Path(plano_arg)
    if p.is_dir():
        return p.resolve()

    tentativas_diretas = [
        ROOT_DIR / plano_arg,
        DOCS_PLANOS_DIR / plano_arg,
        DOCS_PLANOS_DIR / "a-fazer" / plano_arg,
        DOCS_PLANOS_DIR / "fazendo" / plano_arg,
        DOCS_PLANOS_DIR / "feitos" / plano_arg,
    ]
    for c in tentativas_diretas:
        if c.is_dir():
            return c.resolve()

    # Busca por correspondência parcial de nome/slug em docs/planos/
    nome_busca = Path(plano_arg).name.lower()
    if DOCS_PLANOS_DIR.is_dir():
        for item in DOCS_PLANOS_DIR.glob(f"**/{nome_busca}*"):
            if item.is_dir() and (item / "00-PROCESSO-E-DECISOES.md").exists():
                return item.resolve()

    raise FileNotFoundError(
        f"Diretório do plano não encontrado: '{plano_arg}'. "
        f"Verifique se o caminho ou slug está correto em docs/planos/."
    )


def extrair_metadados_iniciativa(pasta_plano: Path) -> Dict[str, Any]:
    """
    Extrai metadados da iniciativa a partir de 00-PROCESSO-E-DECISOES.md e do diretório.
    """
    arquivo_decisoes = pasta_plano / "00-PROCESSO-E-DECISOES.md"
    if not arquivo_decisoes.is_file():
        raise CompiladorErro(
            f"Arquivo mandatório não encontrado no plano: '{arquivo_decisoes}'. "
            f"Toda iniciativa deve conter '00-PROCESSO-E-DECISOES.md'."
        )

    conteudo = arquivo_decisoes.read_text(encoding="utf-8", errors="replace")

    # 1. Extração do ID da Iniciativa
    nome_pasta = pasta_plano.name
    m_id = re.search(r"\b(PLAN-\d{4})(?:-[A-Za-z0-9_-]+)?\b", nome_pasta)
    if m_id:
        iniciativa_id = m_id.group(1)
    else:
        # Tenta no texto do arquivo
        m_id_txt = re.search(r"\b(PLAN-\d{4})\b", conteudo)
        iniciativa_id = m_id_txt.group(1) if m_id_txt else f"PLAN-{nome_pasta}"

    # Sanitiza iniciativa_id para cumprir pattern ^[A-Za-z0-9_.-]+$
    iniciativa_id = re.sub(r"[^A-Za-z0-9_.-]", "-", iniciativa_id)

    # 2. Extração do Nome do Projeto
    nome_projeto = ""
    m_titulo = re.search(r"^#\s+PROCESSO\s+E\s+DECIS[OÕ]ES\s*[-—:]\s*(.+)$", conteudo, re.MULTILINE | re.IGNORECASE)
    if m_titulo:
        nome_projeto = m_titulo.group(1).strip()
    else:
        # Extrai da pasta removendo prefixo PLAN-XXXX- se houver
        slug_sem_plan = re.sub(r"^PLAN-\d{4}-?", "", nome_pasta)
        nome_projeto = slug_sem_plan or nome_pasta

    # Sanitiza nome do projeto (sem stubs, minLength 2)
    if PADRAO_STUB.search(nome_projeto) or len(nome_projeto) < 2:
        nome_projeto = f"Iniciativa {iniciativa_id}"

    # 3. Repositório Alvo
    repositorio_alvo = "ecossistema-aidd"
    m_repo = re.search(r"monorepo\s+([A-Za-z0-9_.-]+)", conteudo, re.IGNORECASE)
    if m_repo:
        repositorio_alvo = m_repo.group(1).strip().rstrip(".,;:")

    # 4. Timestamp de Execução
    timestamp_execucao = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 5. Descrição
    descricao = ""
    m_desc = re.search(r"-\s+\*\*Objetivo Principal:\*\*\s*(.+)$", conteudo, re.MULTILINE)
    if m_desc:
        candidato_desc = m_desc.group(1).strip()
        if not PADRAO_STUB.search(candidato_desc) and len(candidato_desc) >= 5 and not candidato_desc.startswith("["):
            descricao = candidato_desc

    if not descricao or len(descricao) < 5 or PADRAO_STUB.search(descricao):
        descricao = f"Execucao formal do plano de evolucao {iniciativa_id} ({nome_projeto})"

    return {
        "nome_projeto": nome_projeto,
        "repositorio_alvo": repositorio_alvo,
        "timestamp_execucao": timestamp_execucao,
        "iniciativa_id": iniciativa_id,
        "descricao": descricao,
    }


def _limpar_caminho(caminho: str) -> str:
    """Limpa caminhos de arquivos removendo crases, aspas, asteriscos e espaços."""
    limpo = caminho.strip().strip("`'\"*_")
    # Normaliza separadores de caminho para barras normais
    return limpo.replace("\\", "/")


def _extrair_linhas_lista(texto_bloco: str) -> List[str]:
    """Extrai itens de uma lista com bullets ou itens separados por vírgula."""
    itens: List[str] = []
    linhas = texto_bloco.strip().splitlines()
    for linha in linhas:
        l = linha.strip()
        if not l:
            continue
        # Remove marcador de bullet se existir
        if l.startswith(("-", "*", "+")):
            l = l.lstrip("-*+ ").strip()
        # Se contiver itens separados por vírgula
        partes = [p.strip() for p in re.split(r",(?=(?:[^`]*`[^`]*`)*[^`]*$)", l) if p.strip()]
        for p in partes:
            item_limpo = _limpar_caminho(p)
            if item_limpo:
                itens.append(item_limpo)
    return itens


def _extrair_comando(texto_valor: str) -> str:
    """Extrai comando de validação de texto inline ou bloco de código."""
    # Se contiver bloco de código ```bash ... ```
    m_code = re.search(r"```(?:bash|sh|ps1|cmd|powershell)?\s*\n([\s\S]+?)\n```", texto_valor)
    if m_code:
        linhas = [ln.strip() for ln in m_code.group(1).splitlines() if ln.strip() and not ln.strip().startswith("#")]
        if linhas:
            return linhas[0]

    # Se estiver delimitado por crases `comando`
    m_inline = re.search(r"`([^`]+)`", texto_valor)
    if m_inline:
        return m_inline.group(1).strip()

    # Linha simples
    primeira_linha = texto_valor.strip().splitlines()[0].strip()
    return primeira_linha.strip("`'\"*_")


def extrair_tickets_de_conteudo(conteudo: str, nome_arquivo_origem: str) -> List[Dict[str, Any]]:
    """
    Extrai tickets estruturados por /aidd-tickets ou itens de trabalho Markdown.
    Suporta blocos de ticket [TICKET-XX], tabelas Markdown e arquivos unitários.
    """
    tickets: List[Dict[str, Any]] = []

    # Padrao 1: Blocos de Tickets explícitos: ### [TICKET-XX] ou ## [TICKET-XX] ou [TICKET-XX]
    padrao_ticket_header = re.compile(
        r"^(?:#{1,4}\s*)?\[(TICKET-[\w.-]+|ITEM-[\w.-]+)\]\s*(.+)$",
        re.MULTILINE,
    )
    matches_headers = list(padrao_ticket_header.finditer(conteudo))

    if matches_headers:
        for idx, match in enumerate(matches_headers):
            ticket_id = match.group(1).strip()
            titulo = match.group(2).strip()

            start_pos = match.end()
            end_pos = matches_headers[idx + 1].start() if idx + 1 < len(matches_headers) else len(conteudo)
            bloco = conteudo[start_pos:end_pos]

            ticket = _processar_bloco_ticket(ticket_id, titulo, bloco, nome_arquivo_origem)
            tickets.append(ticket)
        return tickets

    # Padrao 2: Tabela Markdown com colunas: ID | Titulo | Arquivos Alvo | Comando ...
    padrao_tabela = re.search(
        r"\|[\s]*ID[\s]*\|[\s]*(?:T[ií]tulo|Title)[\s]*\|[\s]*(?:Arquivos Alvo|Target Files)[\s]*\|[\s]*(?:Comando|Validation)[\s\S]*?\n((?:\|[^\n]+\|\n?)+)",
        conteudo,
        re.IGNORECASE,
    )
    if padrao_tabela:
        linhas_tabela = padrao_tabela.group(1).strip().splitlines()
        for linha in linhas_tabela:
            if re.match(r"^\|[\s-:]+\|$", linha.strip()):
                continue
            cols = [c.strip() for c in linha.split("|")[1:-1]]
            if len(cols) >= 4:
                tid = _limpar_caminho(cols[0])
                if not tid:
                    continue
                tit = cols[1].strip()
                alvos = _extrair_linhas_lista(cols[2])
                cmd = _extrair_comando(cols[3])
                deps = _extrair_linhas_lista(cols[4]) if len(cols) >= 5 else []
                deps_filtradas = [d for d in deps if d.lower() not in ("[]", "none", "nenhum", "-", "")]

                ticket = {
                    "id": tid,
                    "titulo": tit,
                    "arquivos_alvo": alvos,
                    "comando_validacao": cmd,
                    "blocked_by": deps_filtradas,
                    "isolamento": "git-worktree",
                }
                tickets.append(ticket)
        if tickets:
            return tickets

    # Padrao 3: Arquivo unitário representando um único ticket/item de trabalho
    m_item = re.search(r"^#\s+(?:Item\s+\d+\s*[-—:]\s*)?(.+)$", conteudo, re.MULTILINE)
    titulo_padrao = m_item.group(1).strip() if m_item else Path(nome_arquivo_origem).stem

    # Deriva ID a partir do nome do arquivo (ex: 01-preparar-terreno.md -> TICKET-01)
    m_num = re.match(r"^(\d{2})-", nome_arquivo_origem)
    num_str = m_num.group(1) if m_num else "01"
    ticket_id = f"TICKET-{num_str}"

    ticket = _processar_bloco_ticket(ticket_id, titulo_padrao, conteudo, nome_arquivo_origem)
    tickets.append(ticket)
    return tickets


def _extrair_campo_bloco(bloco: str, padrao_chave: str) -> str:
    """
    Extrai o valor de um campo dentro de um bloco de ticket linha por linha,
    respeitando os limites de outras chaves de metadados.
    """
    linhas = bloco.splitlines()
    linhas_capturadas: List[str] = []
    capturando = False

    re_chave = re.compile(
        rf"^(?:[-*]\s*)?(?:\*{{2}}|_{{2}})?(?:{padrao_chave}):?(?:\*{{2}}|_{{2}})?:?\s*(.*)$",
        re.IGNORECASE,
    )
    re_qualquer_chave = re.compile(
        r"^(?:[-*]\s*)?(?:\*{2}|_{2})?(?:Target Files|Arquivos Alvo|target_files|arquivos_alvo|"
        r"Validation Command|Comando de Valida[çc][ãa]o|Validation Gate|comando_validacao|validation_gate|"
        r"Blocked By|blocked_by|Depend[êe]ncias|dependencias|"
        r"Comando Red|command_red|Comando Green|command_green|"
        r"Isolamento|isolation):?(?:\*{2}|_{2})?:?",
        re.IGNORECASE,
    )

    for linha in linhas:
        l = linha.strip()
        if not capturando:
            m = re_chave.match(l)
            if m:
                capturando = True
                resto = m.group(1).strip()
                if resto:
                    linhas_capturadas.append(resto)
        else:
            # Se encontrar outra chave de metadados ou outro ticket/seção
            if re_qualquer_chave.match(l) or l.startswith("#") or l.startswith("[TICKET-"):
                break
            if l:
                linhas_capturadas.append(l)

    return "\n".join(linhas_capturadas)


def _processar_bloco_ticket(ticket_id: str, titulo: str, bloco: str, nome_arquivo: str) -> Dict[str, Any]:
    """Processa um bloco de texto markdown extraindo campos contratuais de um ticket."""
    # Limpa título
    titulo = re.sub(r"^\[.*?\]\s*", "", titulo).strip()
    if not titulo:
        titulo = f"Executar {ticket_id}"

    # 1. Arquivos Alvo
    txt_alvos = _extrair_campo_bloco(bloco, r"Target Files|Arquivos Alvo|target_files|arquivos_alvo")
    arquivos_alvo: List[str] = []
    if txt_alvos:
        arquivos_alvo = _extrair_linhas_lista(txt_alvos)
    else:
        # Seção ## Arquivos Alvo
        m_sec_alvos = re.search(
            r"##\s+(?:Arquivos Alvo|Target Files)\s*\n([\s\S]+?)(?=\n##|\Z)",
            bloco,
            re.IGNORECASE,
        )
        if m_sec_alvos:
            arquivos_alvo = _extrair_linhas_lista(m_sec_alvos.group(1))

    # 2. Comando de Validação
    txt_cmd = _extrair_campo_bloco(
        bloco,
        r"Validation Command|Comando de Valida[çc][ãa]o|Validation Gate|comando_validacao|validation_gate",
    )
    comando_validacao = ""
    if txt_cmd:
        comando_validacao = _extrair_comando(txt_cmd)
    else:
        # Tenta extrair da seção ## Comandos estruturados ou ## Definicao de Pronto
        m_sec_cmd = re.search(
            r"##\s+(?:Comandos estruturados|Defini[çc][ãa]o de Pronto|Comando de Valida[çc][ãa]o)\s*\n([\s\S]+?)(?=\n##|\Z)",
            bloco,
            re.IGNORECASE,
        )
        if m_sec_cmd:
            comando_validacao = _extrair_comando(m_sec_cmd.group(1))

    # 3. Blocked By / Dependências
    txt_deps = _extrair_campo_bloco(
        bloco,
        r"Blocked By|blocked_by|Bloqueado\s+por|bloqueado_por|Depend[êe]ncias|dependencias",
    )
    blocked_by: List[str] = []
    if txt_deps:
        raw_deps = txt_deps.strip().strip("[]")
        if raw_deps:
            for d in raw_deps.split(","):
                d_limpo = re.sub(r"^[*_`'\"\[\]]+|[*_`'\"\[\]]+$", "", d).strip()
                if d_limpo and d_limpo.lower() not in ("none", "nenhum", "-", "empty", "[]"):
                    blocked_by.append(d_limpo)

    # 4. Comandos Red / Green opcionais
    txt_red = _extrair_campo_bloco(bloco, r"Comando Red|command_red")
    comando_red: Optional[str] = _extrair_comando(txt_red) if txt_red else None

    txt_green = _extrair_campo_bloco(bloco, r"Comando Green|command_green")
    comando_green: Optional[str] = _extrair_comando(txt_green) if txt_green else None

    # 5. Isolamento
    txt_iso = _extrair_campo_bloco(bloco, r"Isolamento|isolation")
    isolamento = "git-worktree"
    if txt_iso:
        candidato_iso = _limpar_caminho(txt_iso).lower()
        if candidato_iso in ("git-worktree", "processo-isolado", "nenhum"):
            isolamento = candidato_iso

    ticket: Dict[str, Any] = {
        "id": ticket_id,
        "titulo": titulo,
        "arquivos_alvo": arquivos_alvo,
        "comando_validacao": comando_validacao,
        "blocked_by": blocked_by,
        "isolamento": isolamento,
    }
    if comando_red:
        ticket["comando_red"] = comando_red
    if comando_green:
        ticket["comando_green"] = comando_green

    return ticket


def validar_integridade_tickets(tickets: List[Dict[str, Any]]) -> None:
    """
    Valida a integridade semântica dos tickets brutos:
    - IDs únicos.
    - Ausência de comandos de validação vazios ou triviais.
    - Presença obrigatória de arquivos alvo.
    - Existência de dependências declaradas em blocked_by.
    """
    ids_vistos: Set[str] = set()
    for t in tickets:
        tid = t.get("id", "").strip()
        if not tid:
            raise CompiladorErro("Ticket encontrado sem ID válido.")
        if tid in ids_vistos:
            raise CompiladorErro(f"ID duplicado de ticket encontrado no plano: '{tid}'.")
        ids_vistos.add(tid)

        # Validação do título
        titulo = t.get("titulo", "")
        if not titulo or len(titulo) < 3 or PADRAO_STUB.search(titulo):
            raise CompiladorErro(
                f"Ticket [{tid}]: Título inválido ou contém stubs/placeholders: '{titulo}'."
            )

        # Validação de arquivos alvo
        alvos = t.get("arquivos_alvo", [])
        if not alvos:
            raise CompiladorErro(
                f"Ticket [{tid}]: Lista de arquivos alvo vazia ou não informada. "
                f"Cada ticket atômico deve delimitar explicitamente seus arquivos alvo."
            )
        for a in alvos:
            if PADRAO_STUB.search(a):
                raise CompiladorErro(f"Ticket [{tid}]: Arquivo alvo contém stub: '{a}'.")

        # Validação de comando de validação
        cmd = t.get("comando_validacao", "").strip()
        if not cmd:
            raise CompiladorErro(
                f"Ticket [{tid}]: Ausência de comando de validação determinístico. "
                f"Todo ticket deve conter um comando automatizado verificável."
            )
        if PADRAO_CMD_TRIVIAL.match(cmd):
            raise CompiladorErro(
                f"Ticket [{tid}]: Comando de validação trivial proibido (stub): '{cmd}'."
            )
        if PADRAO_STUB.search(cmd):
            raise CompiladorErro(
                f"Ticket [{tid}]: Comando de validação contém stubs/placeholders: '{cmd}'."
            )

    # Verifica consistência das dependências declaradas
    for t in tickets:
        tid = t["id"]
        for dep in t.get("blocked_by", []):
            if dep not in ids_vistos:
                raise CompiladorErro(
                    f"Ticket [{tid}]: Dependência declarada '{dep}' não existe entre os tickets do plano."
                )


def ordenar_topologicamente_dag(tickets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Executa ordenação topológica (Algoritmo de Kahn) sobre o grafo de dependências (blocked_by).
    Levanta CompiladorErro se ciclos não resolvíveis forem detectados.
    """
    ticket_map = {t["id"]: t for t in tickets}
    in_degree: Dict[str, int] = {t["id"]: len(t.get("blocked_by", [])) for t in tickets}
    grafo_dependentes: Dict[str, List[str]] = {t["id"]: [] for t in tickets}

    for t in tickets:
        for dep in t.get("blocked_by", []):
            grafo_dependentes[dep].append(t["id"])

    # Fila com tickets sem dependências (in-degree == 0)
    fila = [t["id"] for t in tickets if in_degree[t["id"]] == 0]
    ordem_topologica: List[str] = []

    while fila:
        atual = fila.pop(0)
        ordem_topologica.append(atual)
        for dep_id in grafo_dependentes[atual]:
            in_degree[dep_id] -= 1
            if in_degree[dep_id] == 0:
                fila.append(dep_id)

    if len(ordem_topologica) < len(tickets):
        ciclicos = [tid for tid, grau in in_degree.items() if grau > 0]
        raise CompiladorErro(
            f"Ciclo não resolvível detectado no grafo de dependências do plano! "
            f"Tickets envolvidos no ciclo: {ciclicos}"
        )

    return [ticket_map[tid] for tid in ordem_topologica]


def particionar_fases(tickets_ordenados: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Particiona tickets ordenados nas fases Canônicas:
    - fase_paralela_assincrona: Tickets com blocked_by: [] e arquivos_alvo disjuntos.
    - fase_sequencial_sincrona: Tickets dependentes ou com sobreposição de arquivos alvo.
    """
    fase_paralela: List[Dict[str, Any]] = []
    fase_sequencial: List[Dict[str, Any]] = []

    arquivos_usados_paralelo: Set[str] = set()

    for t in tickets_ordenados:
        deps = t.get("blocked_by", [])
        alvos = set(t.get("arquivos_alvo", []))

        # Candidato a execução paralela assíncrona: sem dependências e com arquivos disjuntos
        if not deps and (alvos.isdisjoint(arquivos_usados_paralelo)):
            fase_paralela.append(t)
            arquivos_usados_paralelo.update(alvos)
        else:
            fase_sequencial.append(t)

    return fase_paralela, fase_sequencial


def compilar_plano(
    pasta_plano_arg: str | Path,
    output_path_arg: Optional[str | Path] = None,
    barreira_gate_padrao: str = "gates/G_SAIDA_BINARIA.py",
) -> Tuple[Dict[str, Any], Path]:
    """
    Compila determinísticamente um diretório de plano em manifesto handoff_evolution.json.
    """
    pasta_plano = resolver_diretorio_plano(pasta_plano_arg)

    # 1. Metadados de 00-PROCESSO-E-DECISOES.md
    meta = extrair_metadados_iniciativa(pasta_plano)

    # 2. Coleta de arquivos de trabalho (01-*.md, 02-*.md, etc.)
    arquivos_itens = sorted([
        f for f in pasta_plano.glob("*.md")
        if f.name != "00-PROCESSO-E-DECISOES.md"
        and f.name.upper() not in ("INDEX.MD", "README.MD")
    ])

    if not arquivos_itens:
        raise CompiladorErro(
            f"Nenhum arquivo de item de trabalho Markdown (ex: 01-*.md) encontrado em '{pasta_plano}'."
        )

    # 3. Extração dos tickets brutos de todos os arquivos
    tickets_brutos: List[Dict[str, Any]] = []
    for arq in arquivos_itens:
        conteudo = arq.read_text(encoding="utf-8", errors="replace")
        tickets_extraidos = extrair_tickets_de_conteudo(conteudo, arq.name)
        tickets_brutos.extend(tickets_extraidos)

    if not tickets_brutos:
        raise CompiladorErro(
            f"Nenhum ticket com arquivos alvo e comando de validação pôde ser extraído de '{pasta_plano}'."
        )

    # 4. Validação de integridade e contratos
    validar_integridade_tickets(tickets_brutos)

    # 5. Ordenação Topológica e detecção de ciclos (DAG)
    tickets_ordenados = ordenar_topologicamente_dag(tickets_brutos)

    # 6. Particionamento em fase paralela assíncrona e sequencial síncrona
    fase_paralela, fase_sequencial = particionar_fases(tickets_ordenados)

    # 7. Construção do manifesto conforme handoff-execucao.schema.json
    manifesto: Dict[str, Any] = {
        "versao_schema": "1.0.0",
        "origem_plano": "evolucao",
        "fluxo_alvo": "evolution",
        "meta": meta,
    }

    if fase_paralela:
        manifesto["fase_paralela_assincrona"] = fase_paralela
        manifesto["barreira_sincronizacao"] = [barreira_gate_padrao]

    if fase_sequencial:
        manifesto["fase_sequencial_sincrona"] = fase_sequencial

    # 8. Definição do caminho de saída
    if output_path_arg:
        output_path = Path(output_path_arg).resolve()
    else:
        output_path = pasta_plano / "handoff_evolution.json"

    # Salva o arquivo JSON formatado
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, indent=2, ensure_ascii=False)

    return manifesto, output_path


def validar_manifesto_com_gate(caminho_manifesto: Path) -> Tuple[bool, List[str]]:
    """Valida o manifesto compilado contra o Quality Gate G_PIPELINE_HANDOFF."""
    try:
        sys.path.insert(0, str(ROOT_DIR))
        from gates.G_PIPELINE_HANDOFF import auditar_manifesto
        return auditar_manifesto(caminho_manifesto)
    except Exception as ex:
        return False, [f"Falha ao executar auditoria de gate: {ex}"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compilador Determinístico de Tickets de Planos Markdown para Handoff JSON."
    )
    parser.add_argument(
        "--plano",
        "-p",
        required=True,
        type=str,
        help="Caminho ou identificador do diretório de plano (ex: docs/planos/PLAN-0029-teste-e2e-ferramentas).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Caminho do arquivo JSON de destino (padrão: <pasta_plano>/handoff_evolution.json).",
    )
    parser.add_argument(
        "--barreira-gate",
        type=str,
        default="gates/G_SAIDA_BINARIA.py",
        help="Quality gate a inserir na barreira de sincronização (padrão: gates/G_SAIDA_BINARIA.py).",
    )
    parser.add_argument(
        "--no-validar-gate",
        action="store_true",
        help="Ignora a validação final através de gates/G_PIPELINE_HANDOFF.py.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 72)
    print(" ECOSSISTEMA AIDD — COMPILADOR DE TICKETS DE PLANO PARA HANDOFF")
    print(" Compilação Determinística de Planos de Evolução (ISSUE-PIPE-0004)")
    print("=" * 72)

    try:
        manifesto, output_path = compilar_plano(
            pasta_plano_arg=args.plano,
            output_path_arg=args.output,
            barreira_gate_padrao=args.barreira_gate,
        )

        n_paralelo = len(manifesto.get("fase_paralela_assincrona", []))
        n_sequencial = len(manifesto.get("fase_sequencial_sincrona", []))
        total = n_paralelo + n_sequencial

        print(f"[OK] Plano compilado com sucesso a partir de: {args.plano}")
        print(f"     - Total de tickets extraídos: {total}")
        print(f"     - Fase paralela assíncrona:   {n_paralelo} ticket(s)")
        print(f"     - Fase sequencial síncrona:   {n_sequencial} ticket(s)")
        print(f"     - Destino do manifesto:       {output_path}")

        # Validação com G_PIPELINE_HANDOFF
        if not args.no_validar_gate:
            print("Executando validação formal com G_PIPELINE_HANDOFF...")
            conforme, erros = validar_manifesto_com_gate(output_path)
            if not conforme:
                print("\n[FALHA] Manifesto gerado reprovou no Quality Gate G_PIPELINE_HANDOFF:")
                for e in erros:
                    print(f"  - {e}")
                print("=" * 72)
                return 1
            print("[OK] Manifesto 100% conforme com handoff-execucao.schema.json e Quality Gates.")

        print("=" * 72)
        return 0

    except CompiladorErro as ce:
        print(f"\n[ERRO DE COMPILAÇÃO] {ce}")
        print("=" * 72)
        return 1
    except Exception as ex:
        print(f"\n[ERRO INESPERADO] {ex}")
        import traceback
        traceback.print_exc()
        print("=" * 72)
        return 1


if __name__ == "__main__":
    sys.exit(main())
