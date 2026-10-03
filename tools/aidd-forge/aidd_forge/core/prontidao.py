"""Prontidao do terreno antes de passar o bastao (Ticket 10, D2, contrato C1).

`forge init` so entrega o bastao ao planner quando TODOS os itens abaixo
foram testados de verdade. Qualquer falha => exit 1 com dica de correcao e
SEM gravar `.aidd/HANDOFF_FORGE_PLANNER.json` (handoff velho e removido,
para evidencia morta nao passar por prontidao).

Regra do usuario (sobre o ticket): o ecossistema NUNCA tem LLM ou API key
proprios — o modelo e sempre o do harness em execucao (claude, agy, mimo,
opencode...), via protocolo delegado `_llm_request`/`_llm_response`. Logo:

1. ausencia de API key / `capacidade_llm: "nenhuma"` NAO reprova;
2. o item de IA confere que o protocolo delegado ao harness esta
   disponivel (harness ativo + sonda de ida e volta no cache do projeto);
3. NUNCA e feita chamada de API — a unica ida e volta e a do proprio
   protocolo de arquivos; quando uma resposta real chega, o valor gravado
   vira `capacidade_llm: "delegado_com_resposta"`.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from aidd_forge.core.almoxarifado import _encontrar_raiz, carregar_catalogo
from aidd_forge.core.harness_manifest import carregar_skill_dirs_canonicos

HANDOFF_NOME = "HANDOFF_FORGE_PLANNER.json"
SCHEMA_NOME = "handoff-forge-to-planner.schema.json"

# Dependencias que o proprio forge precisa para validar o contrato C1.
DEPS_FORGE = ("click", "jsonschema")

# Variaveis de ambiente que indicam um harness (ADE) ativo na sessao.
# Mesma familia de deteccao do modo delegado do ecossistema (utils_delegacao).
HARNESS_ENV_VARS = (
    "CLAUDECODE",
    "MIMOCODE",
    "MIMO_SESSION",
    "MIMO_WORKSPACE",
    "OPENCODE",
    "OPENCODE_SESSION",
    "OPENCODE_CONFIG_DIR",
    "ANTIGRAVITY_CLI",
    "AGY_SESSION",
    "ANTIGRAVITY_AGENT",
    "GEMINI_SESSION",
    "GEMINI_CLI",
    "ORCA_WORKSPACE",
    "ORCA_WORKTREE_ID",
    "ORCA_TERMINAL_HANDLE",
    "AIDD_HARNESS_NAME",
)

PASTAS_ESPERADAS = ("gates", "skills", "pipeline_phases", "governance")

_DICA_GATES = "rode 'forge init --force' para reinstalar os gates na versao do almoxarifado"
_DICA_HARNESSES = "rode 'forge init --force' para espelhar as skills em todos os harnesses"
_DICA_IA = (
    "nenhuma IA disponivel: abra o projeto numa ADE/harness ativo "
    "(protocolo delegado _llm_request/_llm_response); o ecossistema nao usa API key"
)


@dataclass(frozen=True)
class ItemProntidao:
    """Um item do checklist, com prova observada e dica de correcao."""

    nome: str
    ok: bool
    detalhe: str
    dica: str = ""


@dataclass
class ResultadoProntidao:
    """Resultado consolidado da prontidao: itens, handoff e capacidade."""

    itens: list[ItemProntidao] = field(default_factory=list)
    handoff: dict | None = None
    handoff_path: Path | None = None
    capacidade_llm: str = "nenhuma"

    @property
    def ok(self) -> bool:
        return bool(self.itens) and all(item.ok for item in self.itens)


def detectar_harness(env: dict[str, str] | None = None) -> list[str]:
    """Lista as variaveis de ambiente que provam um harness ativo."""
    fonte = os.environ if env is None else env
    ativos = []
    for var in HARNESS_ENV_VARS:
        valor = str(fonte.get(var, "")).strip()
        if not valor or valor.lower() in {"0", "false"}:
            continue
        ativos.append(var)
    return sorted(set(ativos))


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _importavel(nome: str) -> bool:
    """Prova real de import: `find_spec` acha o modulo top-level do pacote."""
    candidatos = dict.fromkeys(
        (nome.replace("-", "_"), nome.replace("-", "."), nome)
    )
    for candidato in candidatos:
        if not candidato.isidentifier():
            continue
        try:
            if importlib.util.find_spec(candidato) is not None:
                return True
        except (ImportError, ValueError, ModuleNotFoundError):
            continue
    return False


def _versao_instalada(nome: str) -> str:
    try:
        return importlib.metadata.version(nome)
    except importlib.metadata.PackageNotFoundError:
        return "indefinida"


def _git(target: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=target,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


class ProntidaoForge:
    """Executa o checklist de prontidao do C1 sobre o projeto alvo."""

    def __init__(self, target: Path):
        self.target = Path(target).resolve()

    def executar(self) -> ResultadoProntidao:
        resultado = ResultadoProntidao(handoff_path=self.target / ".aidd" / HANDOFF_NOME)

        item_git, hash_commit = self._checar_git()
        resultado.itens.append(item_git)
        item_deps, dependencias = self._checar_dependencias()
        resultado.itens.append(item_deps)
        item_gates, leis = self._checar_gates()
        resultado.itens.append(item_gates)
        item_espelhos, harnesses = self._checar_espelhos()
        resultado.itens.append(item_espelhos)
        item_almox, almoxarifado = self._checar_almoxarifado()
        resultado.itens.append(item_almox)
        item_ia, capacidade = self._checar_ia()
        resultado.itens.append(item_ia)
        resultado.capacidade_llm = capacidade

        if not all(item.ok for item in resultado.itens):
            # handoff de uma rodada anterior deixou de ser evidencia
            resultado.handoff_path.unlink(missing_ok=True)
            return resultado

        resultado.handoff_path.parent.mkdir(parents=True, exist_ok=True)
        estrutura, pastas = self._checar_estrutura()
        resultado.itens.append(estrutura)
        if not estrutura.ok:
            resultado.handoff_path.unlink(missing_ok=True)
            return resultado

        resultado.handoff = {
            "versao_schema": "1.0.0",
            "projeto_dir": str(self.target),
            "git": {"inicializado": True, "commit_inicial": hash_commit},
            "dependencias": dependencias,
            "leis_e_guardas": leis,
            "harnesses": harnesses,
            "almoxarifado": almoxarifado,
            "capacidade_llm": capacidade,
            "estrutura_projeto": {"pastas_criadas": pastas},
        }

        item_c1 = self._validar_e_gravar_c1(resultado.handoff)
        resultado.itens.append(item_c1)
        if not item_c1.ok:
            resultado.handoff = None
            resultado.handoff_path.unlink(missing_ok=True)
        return resultado

    # --- itens -------------------------------------------------------------

    def _checar_git(self) -> tuple[ItemProntidao, str | None]:
        """Commit inicial: `git rev-parse HEAD` precisa responder."""
        if shutil.which("git") is None:
            return (
                ItemProntidao("git", False, "git nao encontrado no PATH",
                              "instale o git e rode 'forge init' de novo"),
                None,
            )

        if not (self.target / ".git").exists():
            init = _git(self.target, "init")
            if init.returncode != 0:
                detalhe = f"git init falhou: {(init.stderr or init.stdout).strip()[:200]}"
                return (
                    ItemProntidao("git", False, detalhe,
                                  "corrija as permissoes do projeto e rode 'forge init' de novo"),
                    None,
                )

        head = _git(self.target, "rev-parse", "HEAD")
        if head.returncode != 0:
            _git(self.target, "add", "-A")
            commit = _git(
                self.target,
                "-c", "user.email=aidd-forge@localhost",
                "-c", "user.name=aidd-forge",
                "commit", "--no-verify",
                "-m", "chore: commit inicial (aidd-forge init)",
            )
            if commit.returncode != 0:
                detalhe = f"commit inicial falhou: {(commit.stderr or commit.stdout).strip()[:200]}"
                return (
                    ItemProntidao("git", False, detalhe,
                                  "resolva o erro do git acima e rode 'forge init' de novo"),
                    None,
                )
            head = _git(self.target, "rev-parse", "HEAD")
            if head.returncode != 0:
                return (
                    ItemProntidao("git", False, "git rev-parse HEAD nao responde apos o commit",
                                  "verifique o repositorio git do projeto manualmente"),
                    None,
                )

        hash_commit = head.stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{7,40}", hash_commit):
            return (
                ItemProntidao("git", False, f"hash de HEAD invalido: {hash_commit!r}",
                              "verifique o repositorio git do projeto manualmente"),
                None,
            )
        return ItemProntidao("git", True, f"HEAD {hash_commit[:12]} (commit inicial)"), hash_commit

    def _checar_dependencias(self) -> tuple[ItemProntidao, list[dict[str, str]]]:
        """`import` real de cada dependencia; requirements do projeto se houver."""
        pacotes: list[str] = list(DEPS_FORGE)
        requisitos = self.target / "requirements.txt"
        if requisitos.is_file():
            for linha in requisitos.read_text(encoding="utf-8").splitlines():
                linha = linha.strip()
                if not linha or linha.startswith(("#", "-")):
                    continue
                nome = re.split(r"[<>=!~;\s\[]", linha, maxsplit=1)[0].strip()
                if nome:
                    pacotes.append(nome)
        pacotes = list(dict.fromkeys(pacotes))

        faltando = [p for p in pacotes if not _importavel(p)]
        if faltando:
            detalhe = f"nao importam: {', '.join(faltando)}"
            dica = f"instale as dependencias faltantes: pip install {' '.join(faltando)}"
            return ItemProntidao("dependencias", False, detalhe, dica), []

        evidencia = [
            {"pacote": nome, "versao": _versao_instalada(nome)} for nome in pacotes
        ]
        return ItemProntidao("dependencias", True,
                             f"{len(evidencia)} importaveis ("
                             f"{', '.join(d['pacote'] for d in evidencia[:4])}"
                             f"{'...' if len(evidencia) > 4 else ''})"), evidencia

    def _checar_gates(self) -> tuple[ItemProntidao, list[dict[str, str]]]:
        """Gates instalados conferidos com o sha256 da peca do almoxarifado.

        Mesma resolucao da instalacao (`_pecas_de_gates_do_almoxarifado`):
        variante aidd-forge primeiro, principal depois. Gate sem peca no
        catalogo (ex.: G_INJECT) nao entra na evidencia.
        """
        from aidd_forge.core.git_hooks import _pecas_de_gates_do_almoxarifado

        try:
            carregar_catalogo()
        except (FileNotFoundError, json.JSONDecodeError) as err:
            return (
                ItemProntidao("leis_e_guardas", False, f"catalogo ilegivel: {err}",
                              "restaure componentes/compartilhado/CATALOGO.json na raiz do ecossistema"),
                [],
            )

        pecas = _pecas_de_gates_do_almoxarifado()
        diretorio = self.target / "gates"
        instalados = sorted(diretorio.glob("G_*.py")) if diretorio.is_dir() else []
        if not instalados:
            return (
                ItemProntidao("leis_e_guardas", False, "nenhum gate instalado em gates/",
                              "rode 'forge init' de novo para instalar os quality gates"),
                [],
            )

        evidencia: list[dict[str, str]] = []
        divergentes: list[str] = []
        for gate in instalados:
            arquivo_peca = pecas.get(gate.name)
            if arquivo_peca is None:
                continue  # gate interno do forge, fora do almoxarifado (ex.: G_INJECT)
            esperado = _sha256(arquivo_peca)
            if _sha256(gate) != esperado:
                divergentes.append(gate.name)
            else:
                evidencia.append({"gate": gate.name, "sha256": esperado})

        if divergentes:
            detalhe = f"divergentes do catalogo: {', '.join(divergentes)}"
            return ItemProntidao("leis_e_guardas", False, detalhe, _DICA_GATES), []
        if not evidencia:
            return (
                ItemProntidao("leis_e_guardas", False,
                              "nenhum gate instalado confere com o catalogo", _DICA_GATES),
                [],
            )
        return ItemProntidao("leis_e_guardas", True,
                             f"{len(evidencia)} gates na versao do catalogo"), evidencia

    def _checar_espelhos(self) -> tuple[ItemProntidao, list[str]]:
        """Espelhos de skills nos harnesses presentes e conferidos."""
        esperados = carregar_skill_dirs_canonicos()
        presentes = []
        for relativo in esperados:
            pasta = self.target / relativo
            if not pasta.is_dir():
                continue
            tem_skill = any(
                filho.is_dir() and (filho / "SKILL.md").is_file()
                for filho in pasta.iterdir()
            )
            if tem_skill:
                presentes.append(relativo)
        if not presentes:
            detalhe = f"espelhos ausentes: {', '.join(esperados) or '(manifesto vazio)'}"
            return ItemProntidao("harnesses", False, detalhe, _DICA_HARNESSES), []
        return ItemProntidao("harnesses", True,
                             f"{len(presentes)}/{len(esperados)} espelhos presentes"), presentes

    def _checar_almoxarifado(self) -> tuple[ItemProntidao, dict | None]:
        """CATALOGO.json abre e TODAS as pecas listadas abrem."""
        try:
            catalogo = carregar_catalogo()
        except (FileNotFoundError, json.JSONDecodeError) as err:
            return (
                ItemProntidao("almoxarifado", False, f"catalogo ilegivel: {err}",
                              "restaure componentes/compartilhado/CATALOGO.json na raiz do ecossistema"),
                None,
            )

        raiz = _encontrar_raiz()
        catalogo_path = raiz / "componentes" / "compartilhado" / "CATALOGO.json"
        abertas: list[str] = []
        faltantes: list[str] = []
        for peca in catalogo.get("pecas", []):
            caminho = peca.get("caminho")
            if caminho and (raiz / caminho).is_file():
                abertas.append(str(peca.get("nome")))
            else:
                faltantes.append(str(peca.get("nome")))

        if faltantes:
            detalhe = f"pecas que nao abrem: {', '.join(faltantes[:5])}"
            dica = "restaure as pecas faltantes em componentes/compartilhado/"
            return ItemProntidao("almoxarifado", False, detalhe, dica), None
        if not abertas:
            return (
                ItemProntidao("almoxarifado", False, "catalogo sem pecas validas",
                              "restaure componentes/compartilhado/CATALOGO.json"),
                None,
            )

        evidencia = {
            "catalogo_sha256": _sha256(catalogo_path),
            "pecas_disponiveis": abertas,
        }
        return ItemProntidao("almoxarifado", True,
                             f"{len(abertas)} pecas abrem; catalogo "
                             f"{evidencia['catalogo_sha256'][:12]}"), evidencia

    def _checar_ia(self) -> tuple[ItemProntidao, str]:
        """Protocolo delegado ao harness disponivel (NUNCA chamada de API)."""
        ativos = detectar_harness()
        if not ativos:
            detalhe = "nenhuma IA disponivel: nenhum harness ativo nesta sessao"
            return ItemProntidao("protocolo delegado de IA", False, detalhe, _DICA_IA), "nenhuma"

        cache = self.target / ".aidd" / "cache"
        cache.mkdir(parents=True, exist_ok=True)
        req_id = uuid.uuid4().hex[:12]
        req_path = cache / f"_llm_request_{req_id}.json"
        resp_path = cache / f"_llm_response_{req_id}.json"
        req_path.write_text(
            json.dumps(
                {
                    "id": req_id,
                    "fase": "prontidao_forge",
                    "prompt": "responda apenas: pong",
                    "contexto": "sonda de ida e volta do checklist C1 do aidd-forge",
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    "origem": "aidd-forge/prontidao",
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        try:
            timeout = max(float(os.environ.get("AIDD_FORGE_PROBE_TIMEOUT_S", "0")), 0.0)
        except ValueError:
            timeout = 0.0
        deadline = time.monotonic() + timeout
        resposta: dict | None = None
        while True:
            if resp_path.is_file():
                try:
                    dados = json.loads(resp_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    dados = None
                if isinstance(dados, dict) and "conteudo" in dados:
                    resposta = dados
                    break
            if time.monotonic() >= deadline:
                break
            time.sleep(0.1)

        if resposta is None:
            req_path.unlink(missing_ok=True)
            capacidade = "nenhuma"
            detalhe = (
                f"harness ativo ({', '.join(ativos)}); protocolo delegado disponivel; "
                f"sonda sem resposta em {timeout:.0f}s"
            )
            return ItemProntidao("protocolo delegado de IA", True, detalhe), capacidade

        capacidade = "delegado_com_resposta"
        detalhe = (
            f"harness ativo ({', '.join(ativos)}); round trip pedido->resposta id {req_id}"
        )
        return ItemProntidao("protocolo delegado de IA", True, detalhe), capacidade

    def _checar_estrutura(self) -> tuple[ItemProntidao, list[str]]:
        """Pastas em que o planner desenha existem de verdade."""
        candidatas: list[str] = list(PASTAS_ESPERADAS)
        candidatas.extend(carregar_skill_dirs_canonicos())
        candidatas.append(".aidd")
        existem = list(dict.fromkeys(p for p in candidatas if (self.target / p).is_dir()))
        if not existem:
            return (
                ItemProntidao(
                    "estrutura_projeto", False, "nenhuma pasta esperada existe no projeto",
                    "rode 'forge init' de novo para provisionar a arvore do projeto",
                ),
                [],
            )
        return (
            ItemProntidao("estrutura_projeto", True,
                          "pastas: " + ", ".join(existem)),
            existem,
        )

    def _validar_e_gravar_c1(self, handoff: dict) -> ItemProntidao:
        """Schema + gravacao atomica do contrato C1."""
        try:
            import jsonschema
        except ImportError:
            return ItemProntidao(
                "contrato C1", False, "jsonschema indisponivel",
                "pip install jsonschema e rode 'forge init' de novo",
            )

        schema_path = (
            _encontrar_raiz() / "componentes" / "compartilhado" / "specs" / SCHEMA_NOME
        )
        if not schema_path.is_file():
            return ItemProntidao(
                "contrato C1", False, f"schema ausente: {schema_path}",
                "restaure componentes/compartilhado/specs/ na raiz do ecossistema",
            )

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        try:
            jsonschema.validate(instance=handoff, schema=schema)
        except jsonschema.ValidationError as err:
            return ItemProntidao(
                "contrato C1", False, f"handoff viola o schema: {err.message}",
                "abra um issue com esta saida; o handoff nao foi gravado",
            )

        destino = self.target / ".aidd" / HANDOFF_NOME
        destino.write_text(
            json.dumps(handoff, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return ItemProntidao("contrato C1", True, f"gravado em {HANDOFF_NOME}")
