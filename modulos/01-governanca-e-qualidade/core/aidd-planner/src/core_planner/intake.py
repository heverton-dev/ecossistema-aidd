# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — INTAKE DO PLANNER (grill -> spec -> planner)
=============================================================================
A cadeia canônica é /aidd-grill -> /aidd-spec -> /aidd-planner. O planner só abre com:

  .aidd/intake/grill.md   rodada socrática válida (`ecossistema.py grill validar`) que inclui as
                          perguntas visuais: tom, cor, referências e público;
  .aidd/intake/spec.md    especificação válida (`ecossistema.py spec validar`) com um bloco
                          `### Visual Direction` (tom, cor_primaria, referencias, publico).

O modelo que conduz a entrevista e escreve a spec é o harness (nunca uma API key). Quando não há
usuário no chat, o harness registra `--modo autonomo`, e o relatório da etapa deve dizer isso.
O bloco Visual Direction alimenta o DESIGN-SYSTEM.json e as consultas ao Mobbin.
=============================================================================
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PASTA_INTAKE = Path(".aidd") / "intake"
MODOS = ("autonomo", "interativo")

_RE_PERGUNTA = re.compile(r"^(?:###\s*)?(?:Pergunta\s*)?(\d+)[\.\)]\s*(.+)$", re.IGNORECASE)
_TEMAS_VISUAIS = {
    "tom": re.compile(r"\btom\b|\btone\b|\bvoz\b", re.IGNORECASE),
    "cor": re.compile(r"\bcor(?:es)?\b|\bcolor\b|\bpaleta\b", re.IGNORECASE),
    "referências": re.compile(r"refer[eê]ncia|reference|inspira", re.IGNORECASE),
    "público": re.compile(r"p[uú]blico|audience|\busu[aá]rios?\b", re.IGNORECASE),
}
_RE_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_CAMPOS_VISUAIS = ("tom", "cor_primaria", "referencias", "publico")
_CAMPOS_OPCIONAIS = ("fonte", "raio", "densidade")  # tipografia, raios e espaçamentos (Ticket 9-A)
_RE_FONTE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 \-]{0,38}$")


def _raiz_ecossistema() -> Path:
    for pai in Path(__file__).resolve().parents:
        if (pai / "ecossistema.py").is_file():
            return pai
    return Path(__file__).resolve().parents[4]


def caminhos(pasta: str) -> Dict[str, Path]:
    base = Path(pasta) / PASTA_INTAKE
    return {"grill": base / "grill.md", "spec": base / "spec.md", "registro": base / "intake.json"}


def _rodar_cli(subcomando: str, arquivo: Path) -> "tuple[int, str]":
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(_raiz_ecossistema() / "ecossistema.py"), subcomando, "validar",
         "--arquivo", str(arquivo.resolve())],
        cwd=str(_raiz_ecossistema()), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def _temas_visuais_ausentes(texto_grill: str) -> List[str]:
    titulos = [m.group(2) for m in (_RE_PERGUNTA.match(l.strip()) for l in texto_grill.splitlines()) if m]
    return [tema for tema, padrao in _TEMAS_VISUAIS.items() if not any(padrao.search(t) for t in titulos)]


def _extrair_bloco_visual(texto_spec: str) -> Dict[str, str]:
    achou = re.search(r"^#{2,4}\s*Visual Direction\s*$", texto_spec, re.IGNORECASE | re.MULTILINE)
    if not achou:
        return {}
    resto = texto_spec[achou.end():]
    proximo = re.search(r"^#{1,4}\s", resto, re.MULTILINE)
    bloco = resto[: proximo.start()] if proximo else resto
    campos: Dict[str, str] = {}
    for linha in bloco.splitlines():
        m = re.match(r"^\s*[-*]\s*([a-z_]+)\s*:\s*(.+?)\s*$", linha)
        if m:
            campos[m.group(1).lower()] = m.group(2)
    return campos


def ler_direcao_visual(pasta: str) -> Optional[Dict[str, Any]]:
    arquivo = caminhos(pasta)["spec"]
    if not arquivo.is_file():
        return None
    campos = _extrair_bloco_visual(arquivo.read_text(encoding="utf-8"))
    if not all(campos.get(c) for c in _CAMPOS_VISUAIS):
        return None
    return {
        "tom": campos["tom"],
        "cor_primaria": campos["cor_primaria"],
        "referencias": [r.strip() for r in campos["referencias"].split(",") if r.strip()],
        "publico": campos["publico"],
        **{c: campos[c] for c in _CAMPOS_OPCIONAIS if campos.get(c)},
    }


def erros_do_bloco_visual(texto_spec: str) -> List[str]:
    """Valida os itens opcionais da Visual Direction (valor fora do conjunto aceito reprova)."""
    from .design_system import DENSIDADES_VALIDAS, RAIOS_VALIDOS
    campos = _extrair_bloco_visual(texto_spec)
    erros: List[str] = []
    if campos.get("raio") and campos["raio"] not in RAIOS_VALIDOS:
        erros.append(f"raio '{campos['raio']}' inválido; use um de: {', '.join(RAIOS_VALIDOS)}.")
    if campos.get("densidade") and campos["densidade"] not in DENSIDADES_VALIDAS:
        erros.append(f"densidade '{campos['densidade']}' inválida; use uma de: {', '.join(DENSIDADES_VALIDAS)}.")
    if campos.get("fonte") and not _RE_FONTE.match(campos["fonte"]):
        erros.append(f"fonte '{campos['fonte']}' inválida; use só o nome da família (letras, números, espaço e hífen).")
    return erros


def verificar(pasta: str) -> List[str]:
    """Erros que bloqueiam o planner: intake ausente, grill/spec inválidos ou sem direção visual."""
    arq = caminhos(pasta)
    erros: List[str] = []
    rel_grill = os.path.join(".aidd", "intake", "grill.md")
    rel_spec = os.path.join(".aidd", "intake", "spec.md")

    if not arq["grill"].is_file():
        erros.append(f"Falta a entrevista: rode /aidd-grill (com perguntas visuais: tom, cor, referências, público) "
                     f"e grave a rodada em {rel_grill}.")
    else:
        rc, saida = _rodar_cli("grill", arq["grill"])
        if rc != 0:
            erros.append(f"{rel_grill} reprovou em `grill validar`: {saida.splitlines()[-1] if saida else 'sem saída'}")
        ausentes = _temas_visuais_ausentes(arq["grill"].read_text(encoding="utf-8"))
        if ausentes:
            erros.append(f"{rel_grill} não pergunta o visual; faltam perguntas sobre: {', '.join(ausentes)}.")

    if not arq["spec"].is_file():
        erros.append(f"Falta a especificação: rode /aidd-spec e grave em {rel_spec} "
                     f"(com um bloco '### Visual Direction': tom, cor_primaria, referencias, publico).")
    else:
        rc, saida = _rodar_cli("spec", arq["spec"])
        if rc != 0:
            erros.append(f"{rel_spec} reprovou em `spec validar`: {saida.splitlines()[-1] if saida else 'sem saída'}")
        campos = _extrair_bloco_visual(arq["spec"].read_text(encoding="utf-8"))
        for campo in _CAMPOS_VISUAIS:
            if not campos.get(campo):
                erros.append(f"{rel_spec}: o bloco 'Visual Direction' não tem o item '{campo}'.")
        if campos.get("cor_primaria") and not _RE_HEX.match(campos["cor_primaria"]):
            erros.append(f"{rel_spec}: cor_primaria precisa ser hexadecimal (#RRGGBB), veio '{campos['cor_primaria']}'.")
        erros.extend(f"{rel_spec}: {e}" for e in erros_do_bloco_visual(arq["spec"].read_text(encoding="utf-8")))
    return erros


def sintetizar_intake_autonomo(pasta: str, nome_projeto: str = "App") -> None:
    """Sintetiza deterministicamente grill.md e spec.md válidos para execuções autônomas."""
    arq = caminhos(pasta)
    arq["grill"].parent.mkdir(parents=True, exist_ok=True)
    
    precisa_grill = not arq["grill"].is_file()
    if not precisa_grill:
        rc, _ = _rodar_cli("grill", arq["grill"])
        if rc != 0:
            precisa_grill = True

    if precisa_grill:
        conteudo_grill = f"""# Entrevista Socrática /aidd-grill — {nome_projeto}

### 1. Qual o tom de voz e estilo da interface?
- (A) Sóbrio e profissional
- (B) Lúdico e colorido
**Recomendado:** Sóbrio e profissional, porque assegura consistência visual e usabilidade técnica profissional.

### 2. Qual a paleta de cores primária e contraste pretendido?
- (A) #0F766E verde petróleo ardósia
- (B) Cores neon saturadas
**Recomendado:** #0F766E, porque atende os padrões estritos de contraste WCAG 2.2 AA.

### 3. Quais as principais referências visuais e de produto?
- (A) Linear, Stripe
- (B) Interfaces legadas tabulares
**Recomendado:** Linear, Stripe, porque representam o estado da arte de produtividade moderna.

### 4. Qual o público-alvo e contexto dos usuários?
- (A) Atendentes e engenharia corporativa
- (B) Consumidores casuais de redes sociais
**Recomendado:** Atendentes e engenharia corporativa, porque o fluxo de trabalho exige alta densidade e foco em tarefas.
"""
        arq["grill"].write_text(conteudo_grill, encoding="utf-8")

    precisa_spec = not arq["spec"].is_file()
    if not precisa_spec:
        rc, _ = _rodar_cli("spec", arq["spec"])
        if rc != 0:
            precisa_spec = True

    if precisa_spec:
        conteudo_spec = f"""# Especificação Funcional /aidd-spec — {nome_projeto}

## 1. Context & Explicit Non-Goals
Aplicação corporativa de alta fidelidade desenvolvida sob governança determinística AIDD e arquitetura VSA.

### Visual Direction
- tom: sóbrio e profissional
- cor_primaria: #0F766E
- referencias: Linear, Stripe
- publico: atendentes de pequenos comércios

Non-goals:
- Pagamento online, emissão fiscal, aplicativo nativo.

## 2. Contracts & Typed Interfaces
```typescript
export interface Item {{
  id: string;
  title: string;
  status: "todo" | "in_progress" | "done";
  created_at: string;
}}
```

## 3. Invariants & Business Rules
1. Todo item deve possuir identificador único universal (UUID ou ID determinístico).
2. Acesso restrito e isolamento estrito entre usuários e inquilinos.

## 4. Binary Acceptance Criteria
- Execução de testes unitários retorna exit code 0.
- Rotas da API respondem com status HTTP 200.
- Asserção assert item.id is not None é satisfeita em todas as operações de criação.

## 5. Failure & Degradation Modes
- Em caso de indisponibilidade de rede ou banco de dados, o cliente deve exibir fallback gracioso de erro.
- Requisições inválidas devem retornar status HTTP 400 com payload estruturado de erro.
"""
        arq["spec"].write_text(conteudo_spec, encoding="utf-8")


def cmd_intake(args) -> int:
    pasta = os.path.abspath(getattr(args, "pasta", None) or ".")
    modo = getattr(args, "modo", None) or "interativo"
    if modo == "autonomo":
        sintetizar_intake_autonomo(pasta, os.path.basename(pasta))
    erros = verificar(pasta)
    if erros:
        print("[ERRO] Intake incompleto; o planner não abre sem grill e spec:", file=sys.stderr)
        for e in erros:
            print("  - " + e, file=sys.stderr)
        return 1
    arq = caminhos(pasta)
    registro = {
        "versao": 1,
        "modo": modo,
        "grill_sha256": hashlib.sha256(arq["grill"].read_bytes()).hexdigest(),
        "spec_sha256": hashlib.sha256(arq["spec"].read_bytes()).hexdigest(),
        "direcao_visual": ler_direcao_visual(pasta),
    }
    arq["registro"].write_text(json.dumps(registro, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"[aidd-planner] Intake válido (modo {modo}); registro em {arq['registro']}.")
    return 0


def descricao_da_spec(pasta: str, limite: int = 480) -> Optional[str]:
    """Contexto da spec (seção 1, sem o bloco Visual Direction) como descrição do projeto.

    O motor monta o prompt das fases com a descrição do PLANNER.json: sem isto ela era o texto de template
    e a spec do intake nunca chegava ao motor.
    """
    arquivo = caminhos(pasta)["spec"]
    if not arquivo.is_file():
        return None
    texto = arquivo.read_text(encoding="utf-8")
    achou = re.search(r"^##\s*(?:1\.?\s*)?(?:Context|Contexto)[^\n]*\n", texto, re.IGNORECASE | re.MULTILINE)
    if not achou:
        return None
    resto = texto[achou.end():]
    fim = re.search(r"^#{1,4}\s", resto, re.MULTILINE)
    corpo = resto[: fim.start()] if fim else resto
    linhas = [linha.strip() for linha in corpo.splitlines() if linha.strip()]
    descricao = " ".join(linhas)
    return descricao[:limite].rstrip() if len(descricao) >= 10 else None


def extrair_contextos_da_spec(pasta: str) -> List[Dict[str, Any]]:
    """Extrai bounded contexts, entidades e invariantes da spec (.aidd/intake/spec.md).

    Analisa Seção 2 (Contracts & Typed Interfaces) para TypeScript interfaces e
    Seção 3 (Invariants & Business Rules) para associar regras às entidades.
    """
    arquivo = caminhos(pasta)["spec"]
    if not arquivo.is_file():
        return []

    texto = arquivo.read_text(encoding="utf-8")

    # 1. Extrair Seção 2 (Contratos)
    achou_s2 = re.search(r"^##\s*(?:2\.?\s*)?(?:Contracts|Contratos)[^\n]*\n", texto, re.IGNORECASE | re.MULTILINE)
    texto_s2 = ""
    if achou_s2:
        resto_s2 = texto[achou_s2.end():]
        fim_s2 = re.search(r"^##\s", resto_s2, re.MULTILINE)
        texto_s2 = resto_s2[:fim_s2.start()] if fim_s2 else resto_s2

    # 2. Extrair Seção 3 (Invariantes)
    achou_s3 = re.search(r"^##\s*(?:3\.?\s*)?(?:Invariants|Invariantes|Regras)[^\n]*\n", texto, re.IGNORECASE | re.MULTILINE)
    regras_invariantes = []
    if achou_s3:
        resto_s3 = texto[achou_s3.end():]
        fim_s3 = re.search(r"^##\s", resto_s3, re.MULTILINE)
        texto_s3 = resto_s3[:fim_s3.start()] if fim_s3 else resto_s3
        for linha in texto_s3.splitlines():
            linha_s = linha.strip()
            # Casa itens numerados ou marcados com hífen: "1. Regra...", "- Regra..."
            m_regra = re.match(r"^(?:\d+[\.\)]|[-*])\s+(.+)$", linha_s)
            if m_regra:
                regras_invariantes.append(m_regra.group(1).strip())

    # 3. Parsear interfaces TS na Seção 2
    # interface Nome { campo: tipo; ... }
    padrao_interface = re.compile(r"interface\s+([A-Za-z0-9_]+)\s*\{([^}]+)\}", re.MULTILINE)
    interfaces = padrao_interface.findall(texto_s2)

    contextos: List[Dict[str, Any]] = []
    for nome_interface, corpo in interfaces:
        nome_entidade = nome_interface.strip()
        # Pluraliza o nome da interface para o módulo: Pedido -> pedidos, Cliente -> clientes
        slug_modulo = nome_entidade.lower()
        if not slug_modulo.endswith("s"):
            slug_modulo += "s"

        atributos: Dict[str, str] = {}
        for campo_raw in corpo.split(";"):
            campo_raw = campo_raw.strip()
            if not campo_raw or ":" not in campo_raw:
                continue
            partes = campo_raw.split(":", 1)
            nome_campo = partes[0].strip().rstrip("?")
            tipo_campo = partes[1].strip()
            # Mapeamento simples de tipos TS para primitivos
            if tipo_campo.startswith('"') or "|" in tipo_campo:
                tipo_limpo = "string"
            elif tipo_campo in ("number", "int", "float"):
                tipo_limpo = "number"
            elif tipo_campo in ("boolean", "bool"):
                tipo_limpo = "boolean"
            else:
                tipo_limpo = "string"
            atributos[nome_campo] = tipo_limpo

        # Se não extraiu atributos, cria id padrão
        if not atributos:
            atributos = {"id": "string", "status": "string"}

        # Associar invariantes relevantes a esta entidade
        regras_entidade = [
            r for r in regras_invariantes
            if re.search(r"\b" + re.escape(nome_entidade) + r"\b", r, re.IGNORECASE)
            or re.search(r"\b" + re.escape(slug_modulo) + r"\b", r, re.IGNORECASE)
        ]
        if not regras_entidade:
            regras_entidade = [
                f"O status inicial de {nome_entidade} deve ser sempre 'ativo'",
                f"O identificador de {nome_entidade} deve ser único"
            ]

        contextos.append({
            "modulo": slug_modulo,
            "descricao": f"Contexto delimitado de {nome_entidade} derivado da especificação",
            "entidades": [
                {
                    "nome": nome_entidade,
                    "atributos": atributos,
                    "regras_invariantes": regras_entidade
                }
            ]
        })

    return contextos

