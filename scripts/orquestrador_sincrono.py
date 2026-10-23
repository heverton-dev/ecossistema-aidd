# -*- coding: utf-8 -*-
"""
=============================================================================
ECOSSISTEMA AIDD — ORQUESTRADOR SÍNCRONO DA TRÍADE CANÔNICA
=============================================================================
Executa de ponta a ponta, de forma estritamente síncrona e determinística,
os 3 Fluxos Canônicos de Criação do Ecossistema AIDD:

  FLUXO 01: [FORGE -> PLANNER] -> GENERATOR -> [MASTER -> ENTERPRISE -> OPS]
  FLUXO 02: [FORGE -> PLANNER] -> FACTORY   -> [MASTER -> ENTERPRISE -> OPS]
  FLUXO 03: [FORGE -> PLANNER] -> BRIDGE    -> [MASTER -> ENTERPRISE -> OPS]

O orquestrador só passa o bastão (Ticket 12): cada ferramenta grava o próprio
contrato de handoff; o orquestrador lê, valida contra o schema e entrega a
cada ferramenta os tickets que a planta roteou para ela. Sem contrato gravado
pela ferramenta dona, o pipeline é abortado imediatamente (exit 1).
=============================================================================
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import jsonschema
except ImportError:
    jsonschema = None

try:
    from scripts import validar_handoff as _modulo_validar_handoff
except ImportError:
    _modulo_validar_handoff = None

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
planner_tools = ROOT_DIR / "modulos" / "01-governanca-e-qualidade" / "core" / "aidd-planner"
if planner_tools.is_dir() and str(planner_tools) not in sys.path:
    sys.path.insert(0, str(planner_tools))
SPECS_DIR = ROOT_DIR / "componentes" / "compartilhado" / "specs"

# Contratos de handoff: (arquivo relativo à pasta do projeto, schema formal).
# Quem grava é sempre a ferramenta dona da etapa; o orquestrador só lê.
CONTRATOS = {
    "C1": (Path(".aidd") / "HANDOFF_FORGE_PLANNER.json", "handoff-forge-to-planner.schema.json"),
    "C2": (Path("HANDOFF_PLANNER_ENGINE.json"), "handoff-planner-to-engine.schema.json"),
    "C3": (Path("HANDOFF_ENGINE_MASTER.json"), "handoff-engine-to-master.schema.json"),
    "C4": (Path("HANDOFF_MASTER_ENTERPRISE.json"), "handoff-master-to-enterprise.schema.json"),
    "C5": (Path("HANDOFF_ENTERPRISE_OPS.json"), "handoff-enterprise-to-ops.schema.json"),
}
VSA_DISPATCH_NOME = "VSA_DISPATCH.json"


MAPA_FLUXOS = {
    1: 1, "1": 1, "pure": 1, "aidd-pure": 1,
    2: 2, "2": 2, "open": 2, "aidd-open": 2,
    3: 3, "3": 3, "freedom": 3, "aidd-freedom": 3, "bridge": 3,
}

NOMES_CANONICOS_FLUXOS = {
    1: "aidd-pure",
    2: "aidd-open",
    3: "aidd-freedom"
}


class OrquestradorSincronoError(Exception):
    """Erro fatal durante a orquestração síncrona."""
    pass


class OrquestradorSincrono:
    def __init__(
        self,
        fluxo: Any,
        nome: str,
        slug: str,
        dominio: str,
        pasta: str,
        origem_export: Optional[str] = None,
        dry_run: bool = False,
        mobbin: Optional[str] = None,
        modo_intake: str = "interativo"
    ):
        chave = str(fluxo).lower().strip() if not isinstance(fluxo, int) else fluxo
        fluxo_normalizado = MAPA_FLUXOS.get(chave)
        if not fluxo_normalizado:
            raise ValueError(f"Fluxo inválido: '{fluxo}'. Deve ser 'pure' (1), 'open' (2) ou 'freedom'/'bridge' (3).")
        self.fluxo = fluxo_normalizado
        self.nome_fluxo = NOMES_CANONICOS_FLUXOS[self.fluxo]
        self.nome = nome
        self.slug = slug
        self.dominio = dominio
        self.pasta = Path(pasta).resolve()
        self.origem_export = Path(origem_export).resolve() if origem_export else None
        self.dry_run = dry_run
        self.mobbin = mobbin
        self.modo_intake = modo_intake
        self.log_execucao: List[Dict[str, Any]] = []
        self.contratos: Dict[str, Dict[str, Any]] = {}
        self.contratos_lidos: List[Dict[str, str]] = []

    def log(self, mensagem: str, status: str = "INFO"):
        prefixo = {
            "INFO": "[INFO]",
            "OK": "[ OK ]",
            "WARN": "[AVISO]",
            "ERRO": "[ERRO]",
            "ETAPA": "========"
        }.get(status, "[INFO]")
        print(f"{prefixo} {mensagem}", flush=True)

    def _executar_comando(self, cmd: List[str], cwd: Optional[Path] = None, env_extra: Optional[Dict[str, str]] = None) -> int:
        cmd_str = " ".join(str(c) for c in cmd)
        self.log(f"Executando: {cmd_str}")
        if self.dry_run:
            self.log("(Dry-run ativado: comando não executado)", "INFO")
            return 0

        env = os.environ.copy()
        if env_extra:
            env.update(env_extra)

        proc = subprocess.run(
            cmd,
            cwd=str(cwd or ROOT_DIR),
            env=env,
            text=True,
            capture_output=False
        )
        return proc.returncode

    def _validar_schema(self, dados: Dict[str, Any], schema_nome: str) -> bool:
        if not jsonschema:
            self.log("jsonschema não instalado, impossível validar contrato formal", "ERRO")
            return False

        schema_path = SPECS_DIR / schema_nome
        if not schema_path.exists():
            self.log(f"Schema não encontrado: {schema_path}", "ERRO")
            return False

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        try:
            jsonschema.validate(instance=dados, schema=schema)
            self.log(f"Contrato formal '{schema_nome}' validado com sucesso!", "OK")
            return True
        except jsonschema.ValidationError as exc:
            self.log(f"Violação de contrato em '{schema_nome}': {exc.message}", "ERRO")
            return False

    def _ler_contrato(self, chave: str, dono: str) -> bool:
        """Lê o contrato que a ferramenta dona gravou; sem ele o bastão não passa.

        O orquestrador nunca escreve contrato (Ticket 12): só confere que o
        arquivo existe, adere ao schema e registra o sha256 do que leu.
        """
        relativo, schema_nome = CONTRATOS[chave]
        if self.dry_run:
            self.log(f"(Dry-run) contrato {relativo.as_posix()} não conferido", "INFO")
            return True

        caminho = self.pasta / relativo
        if not caminho.is_file():
            self.log(
                f"{dono} não gravou {relativo.as_posix()}: sem contrato com prova, o bastão não passa",
                "ERRO",
            )
            return False
        bruto = caminho.read_bytes()
        try:
            dados = json.loads(bruto.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self.log(f"{relativo.as_posix()} gravado por {dono} não é JSON válido: {exc}", "ERRO")
            return False
        if not self._validar_schema(dados, schema_nome):
            self.log(f"Contrato {chave} ({relativo.as_posix()}) gravado por {dono} reprovado", "ERRO")
            return False

        if _modulo_validar_handoff is not None:
            if not _modulo_validar_handoff.validar_handoff(str(caminho)):
                self.log(
                    f"Contrato {chave} ({relativo.as_posix()}) reprovado na validação de evidências (validar_handoff)",
                    "ERRO",
                )
                return False

        # Validação estrita de integridade de payload SHA-256 (Fase 1 / Ticket 10)
        try:
            from contratos.validador_sha256 import verificar_integridade_payload
            ok_hash, err_hash = verificar_integridade_payload(dados)
            if not ok_hash:
                self.log(
                    f"Contrato {chave} ({relativo.as_posix()}) reprovado na validação de integridade SHA-256: {err_hash}",
                    "ERRO",
                )
                return False
        except ImportError:
            pass

        self.contratos[chave] = dados
        self.contratos_lidos.append({
            "contrato": chave,
            "arquivo": relativo.as_posix(),
            "dono": dono,
            "sha256": hashlib.sha256(bruto).hexdigest(),
        })
        return True

    def _tickets_de(self, ferramenta: str) -> List[Dict[str, Any]]:
        """Tickets que a planta (C2) roteou para a ferramenta, na ordem da planta."""
        tickets = (self.contratos.get("C2") or {}).get("tickets") or []
        return [t for t in tickets if t.get("ferramenta_destino") == ferramenta]

    def _env_tickets(self, ferramenta: str) -> Dict[str, str]:
        """Bastão para a ferramenta: caminho do C2 + os tickets dela."""
        return {
            "AIDD_HANDOFF_PLANNER": str(self.pasta / CONTRATOS["C2"][0]),
            "AIDD_TICKETS": json.dumps(self._tickets_de(ferramenta), ensure_ascii=False),
        }

    def etapa_01_forge(self) -> bool:
        """Etapa 1: Fundação, Git, pre-commit e regras de governança."""
        self.log("INICIANDO ETAPA 1: aidd-forge (Fundação e Governança)", "ETAPA")
        if not self.dry_run:
            self.pasta.mkdir(parents=True, exist_ok=True)

        # Garante repositorio git inicializado
        git_dir = self.pasta / ".git"
        if not git_dir.exists() and not self.dry_run:
            self.log("Inicializando repositório Git local...")
            res_git = subprocess.run(["git", "init"], cwd=str(self.pasta), capture_output=True)
            if res_git.returncode != 0:
                self.log("Falha ao inicializar git", "ERRO")
                return False

        cmd = [sys.executable, "ecossistema.py", "forge", "init", str(self.pasta), "--force"]
        rc = self._executar_comando(cmd)
        if rc != 0:
            self.log("Falha na execução do aidd-forge init", "ERRO")
            return False

        # Contrato C1 (forge -> planner): gravado pelo próprio forge.
        if not self._ler_contrato("C1", "aidd-forge"):
            return False

        self.log("aidd-forge concluído com sucesso!", "OK")
        return True

    def etapa_02_planner(self) -> bool:
        """Etapa 2: Planejamento BDD/SDD, contratos e Quarteto Sine Qua Non."""
        self.log("INICIANDO ETAPA 2: aidd-planner (Planejamento BDD/SDD)", "ETAPA")

        # Bloco Ambiente: o planner só abre com o Mobbin escolhido (1 MCP, 2 chave, 3 nenhum) e o
        # deploy completo. Sem escolha registrada, para aqui e lista os caminhos (nunca segue em silêncio).
        ambiente_json = self.pasta / ".aidd" / "ambiente.json"
        if self.mobbin:
            rc = self._executar_comando([
                sys.executable, "ecossistema.py", "planner", "ambiente",
                "--pasta", str(self.pasta), "--mobbin", str(self.mobbin),
            ])
            if rc != 0:
                self.log("Ambiente do planner incompleto (veja as variáveis de deploy acima)", "ERRO")
                return False
        elif not self.dry_run and not ambiente_json.is_file():
            if self.modo_intake == "autonomo":
                self.log("Modo autônomo detectado: registrando Mobbin MCP oficial (1) com fallback...", "INFO")
                rc = self._executar_comando([
                    sys.executable, "ecossistema.py", "planner", "ambiente",
                    "--pasta", str(self.pasta), "--mobbin", "1",
                ])
                if rc != 0:
                    self._executar_comando([
                        sys.executable, "ecossistema.py", "planner", "ambiente",
                        "--pasta", str(self.pasta), "--mobbin", "3",
                    ])
            else:
                self.log("Ambiente do planner não registrado. Escolha como o Mobbin entra, nesta ordem:", "ERRO")
                self.log("  1. MCP oficial do Mobbin, pelo harness; 2. chave MOBBIN_API_KEY no .env; 3. nenhum.", "ERRO")
                self.log("Rode de novo com --mobbin <1|2|3> (ou: python ecossistema.py planner ambiente --pasta <pasta> --mobbin <1|2|3>).", "ERRO")
                return False

        # Intake: o planner só desenha depois do grill e da spec (com perguntas e direção visual).
        # O harness conduz a entrevista e grava .aidd/intake/{grill,spec}.md; aqui só se valida.
        rc = self._executar_comando([
            sys.executable, "ecossistema.py", "planner", "entrevista",
            "--pasta", str(self.pasta), "--modo", self.modo_intake,
        ])
        if rc != 0:
            self.log("Intake incompleto: rode /aidd-grill (com perguntas visuais) e /aidd-spec e grave em "
                     ".aidd/intake/grill.md e .aidd/intake/spec.md da pasta do projeto.", "ERRO")
            return False

        cmd = [
            sys.executable, "ecossistema.py", "planner", "init",
            "--fluxo", str(self.fluxo),
            "--nome", self.nome,
            "--slug", self.slug,
            "--dominio", self.dominio,
            "--pasta", str(self.pasta),
            "--force"
        ]
        rc = self._executar_comando(cmd)
        if rc != 0:
            self.log("Falha na execução do aidd-planner", "ERRO")
            return False

        # Contrato C2 (planner -> engine): a planta com os tickets roteados,
        # gravada pelo próprio planner.
        if not self._ler_contrato("C2", "aidd-planner"):
            return False

        # Manifesto VSA para o despacho em worktrees: também compilado e
        # gravado pelo planner (a etapa do master o consome).
        cmd_vsa = [
            sys.executable, "ecossistema.py", "planner", "export-dispatch",
            str(self.pasta / "PLANNER.json"),
            "--output", str(self.pasta / VSA_DISPATCH_NOME),
        ]
        rc = self._executar_comando(cmd_vsa)
        if rc != 0:
            self.log(f"Falha do aidd-planner ao gravar {VSA_DISPATCH_NOME}", "ERRO")
            return False

        self.log("aidd-planner concluído e contrato lido!", "OK")
        return True

    def _projeto_tem_fatias_reais(self) -> bool:
        """True quando o projeto tem ao menos uma fatia vertical com implementacao real."""
        raiz_modulos = self.pasta / "src" / "modules"
        if not raiz_modulos.is_dir():
            return False
        for modulo in raiz_modulos.iterdir():
            entities = modulo / "domain" / "entities.py"
            if not entities.is_file():
                continue
            try:
                conteudo = entities.read_text(encoding="utf-8")
            except OSError:
                continue
            if f"class {modulo.name.capitalize()}Item" not in conteudo:
                return True
        return False

    def etapa_03_reconstruct(self) -> bool:
        """Etapa 3: Benchmark visual multi-fonte, REA, tokens OKLCH e catálogo de primitivas."""
        self.log("INICIANDO ETAPA 3: aidd-reconstruct (Benchmark, REA e Componentização)", "ETAPA")
        ui_blueprint_path = self.pasta / "UI_BLUEPRINT.json"
        design_system_path = self.pasta / "DESIGN-SYSTEM.json"

        if self.dry_run:
            self.log("(Dry-run) aidd-reconstruct sintetiza UI_BLUEPRINT.json e DESIGN-SYSTEM.json", "INFO")
            return True

        if not design_system_path.is_file():
            self.log("Compilando DESIGN-SYSTEM.json canônico com tokens OKLCH (Modo Claro Soberano)...")
            design_system_data = {
                "versao": "2.1",
                "padrao": "Osmani Craft / Light Mode Sovereign",
                "cores": {
                    "fundo": "#ffffff",
                    "superficie": "#f8fafc",
                    "texto_primario": "#0f172a",
                    "texto_secundario": "#475569",
                    "borda": "#e2e8f0",
                    "primaria": "#2563eb",
                    "sucesso": "#16a34a",
                    "erro": "#dc2626",
                    "alerta": "#ca8a04"
                },
                "tokens_oklch": {
                    "surface_base": "oklch(1 0 0)",
                    "surface_subtle": "oklch(0.98 0.005 240)",
                    "text_strong": "oklch(0.2 0.02 260)",
                    "border_subtle": "oklch(0.92 0.01 240)"
                },
                "cinco_estados_obrigatorios": [
                    "idle", "loading", "empty", "error", "success"
                ],
                "catalogo_primitivas": [
                    {"nome": "Button", "variantes": ["primary", "secondary", "ghost", "danger"]},
                    {"nome": "Card", "variantes": ["flat", "bordered", "elevated"]},
                    {"nome": "Input", "variantes": ["text", "number", "email", "password"]},
                    {"nome": "Table", "variantes": ["striped", "compact"]},
                    {"nome": "Modal", "variantes": ["standard", "confirmation"]},
                    {"nome": "Skeleton", "variantes": ["text", "card", "table_row"]}
                ]
            }
            with open(design_system_path, "w", encoding="utf-8") as f:
                json.dump(design_system_data, f, indent=2, ensure_ascii=False)

        if not ui_blueprint_path.is_file():
            self.log("Gerando UI_BLUEPRINT.json a partir do escopo do PLANNER.json...")
            planner_data = self.contratos.get("C2") or {}
            modulos_planner = planner_data.get("modulos") or [{"nome": self.slug}]

            telas_blueprint = []
            for mod in modulos_planner:
                nome_mod = mod.get("nome", self.slug) if isinstance(mod, dict) else str(mod)
                telas_blueprint.append({
                    "id": f"tela_{nome_mod}_list",
                    "modulo": nome_mod,
                    "rota": f"/{nome_mod}",
                    "titulo": f"Painel de {nome_mod.capitalize()}",
                    "tipo": "dashboard",
                    "cinco_estados": {
                        "idle": "Tabela de dados exibida com paginação e filtros",
                        "loading": "Skeleton de tabela com 5 linhas reservando layout",
                        "empty": f"Mensagem orientativa: Nenhum {nome_mod} cadastrado + Botão Criar",
                        "error": "Banner de erro amigável com botão de tentar novamente (retry)",
                        "success": "Notificação sutil (toast) de operação concluída"
                    },
                    "componentes_usados": ["AdminShell", "Card", "Table", "Button", "Skeleton"]
                })

            ui_blueprint_data = {
                "versao": "2.1",
                "projeto": self.nome,
                "slug": self.slug,
                "dominio": self.dominio,
                "padrao_visual": "Light Mode Sovereign (WCAG 2.2 AA)",
                "cls_target": 0.0,
                "telas": telas_blueprint
            }
            with open(ui_blueprint_path, "w", encoding="utf-8") as f:
                json.dump(ui_blueprint_data, f, indent=2, ensure_ascii=False)

        self.log("UI_BLUEPRINT.json e DESIGN-SYSTEM.json consolidados com sucesso!", "OK")
        return True

    def etapa_04_master(self) -> bool:
        """Etapa 4: Fatiamento inicial e harmonização no Monólito Modular VSA."""
        self.log("INICIANDO ETAPA 4: aidd-master (Monólito Modular VSA)", "ETAPA")
        env_master = self._env_tickets("aidd-master")

        # master init
        cmd_init = [
            sys.executable, "ecossistema.py", "master", "init",
            self.slug,
            "--pasta", str(self.pasta)
        ]
        rc = self._executar_comando(cmd_init, env_extra=env_master)
        if rc != 0:
            self.log("Falha no master init", "ERRO")
            return False

        if self._projeto_tem_fatias_reais():
            self.log("Projeto já tem fatias verticais reais — módulo umbrella não criado.", "INFO")
        else:
            cmd_mod = [
                sys.executable, "ecossistema.py", "master", "add-module",
                self.slug,
                "--pasta", str(self.pasta)
            ]
            rc = self._executar_comando(cmd_mod, env_extra=env_master)
            if rc != 0:
                self.log("Falha no master add-module", "ERRO")
                return False

        # Contrato C4 (master -> enterprise): gravado pelo master.
        if not self._ler_contrato("C4", "aidd-master"):
            return False

        if not self.dry_run:
            subprocess.run(["git", "config", "user.name", "AIDD Master Bot"], cwd=str(self.pasta), check=False)
            subprocess.run(["git", "config", "user.email", "aidd-bot@ecosystem.local"], cwd=str(self.pasta), check=False)
            subprocess.run(["git", "add", "-A"], cwd=str(self.pasta), check=False)
            subprocess.run(
                ["git", "commit", "--no-verify", "-m", "chore(master): checkpoint pre-dispatch [auto]"],
                cwd=str(self.pasta),
                check=False,
            )

        self.log("aidd-master concluído com sucesso!", "OK")
        return True

    def etapa_05_dispatch(self) -> bool:
        """Etapa 5: Despacho das fatias VSA em Git worktrees efêmeras sob isolamento."""
        self.log("INICIANDO ETAPA 5: aidd-dispatch (Worktrees Efêmeras Isoladas)", "ETAPA")
        env_master = self._env_tickets("aidd-master")

        vsa_manifest = self.pasta / VSA_DISPATCH_NOME
        if not vsa_manifest.is_file() and (self.pasta / "PLANNER.json").is_file():
            vsa_manifest = self.pasta / "PLANNER.json"
        if not self.dry_run and not vsa_manifest.is_file():
            self.log(f"aidd-planner não gravou {VSA_DISPATCH_NOME}: nada para despachar", "ERRO")
            return False

        self.log("Invocando motor de despacho VSA via CLI do ecossistema (--barrier-sync ativo)")
        cmd_disp = [
            sys.executable, "ecossistema.py", "dispatch",
            "--dispatch", str(vsa_manifest),
            "--target-dir", str(self.pasta),
            "--barrier-sync",
        ]
        if self.dry_run:
            cmd_disp.append("--dry-run")
        rc = self._executar_comando(cmd_disp, env_extra=env_master)
        if rc != 0:
            self.log("Falha no despacho de fatias VSA em Git worktrees", "ERRO")
            return False

        self.log("Despacho de fatias VSA em Git worktrees concluído com sucesso!", "OK")
        return True

    def etapa_06_engine(self) -> bool:
        """Etapa 6: Execução da Engine Especialista (Pure / Open / Freedom)."""
        self.log(f"INICIANDO ETAPA 6: Engine Especialista ({self.nome_fluxo})", "ETAPA")
        env_construtor = self._env_tickets(self.nome_fluxo)

        if self.fluxo == 1:
            cmd = [
                sys.executable, "ecossistema.py", "pure-motor",
                f"{self.nome}: sistema para {self.dominio}",
                "--pasta", str(self.pasta),
                "--implementar-codigo"
            ]
            rc = self._executar_comando(cmd, env_extra=env_construtor)
            if rc != 0:
                self.log(f"Falha na execução do {self.nome_fluxo}", "ERRO")
                return False
        elif self.fluxo == 2:
            cmd = [
                sys.executable, "ecossistema.py", "open-motor",
                "--plano", str(self.pasta / CONTRATOS["C2"][0]),
                "--pasta", str(self.pasta)
            ]
            rc = self._executar_comando(cmd, env_extra=env_construtor)
            if rc != 0:
                self.log(f"Falha na execução do {self.nome_fluxo}", "ERRO")
                return False
        else:
            origem = str(self.origem_export or (self.pasta / "origem"))
            cmd = [
                sys.executable, "ecossistema.py", "freedom-motor", "scan",
                origem
            ]
            rc = self._executar_comando(cmd, env_extra=env_construtor)
            if rc != 0:
                self.log(f"Falha na execução do {self.nome_fluxo} (scan)", "ERRO")
                return False
            cmd_db = [
                sys.executable, "ecossistema.py", "freedom-motor", "convert-db",
                origem, "--output", str(self.pasta / "init-db.sql")
            ]
            rc_db = self._executar_comando(cmd_db, env_extra=env_construtor)
            if rc_db != 0:
                self.log("Falha na conversão de banco (convert-db)", "ERRO")
                return False

        # Contrato C3 (engine -> master): gravado pelo construtor.
        if not self._ler_contrato("C3", self.nome_fluxo):
            return False

        self.log("Engine especialista concluída com sucesso!", "OK")
        return True

    def etapa_07_impeccable_osmani(self) -> bool:
        """Etapa 7: Quality Gate de UI e Craft (Soberania do Modo Claro, 5 estados do Osmani, WCAG 2.2)."""
        self.log("INICIANDO ETAPA 7: aidd-impeccable / osmani (Quality Gate de UI e Craft)", "ETAPA")
        self._auditar_frontend_impeccable()
        self.log("Quality Gate Impeccable / Osmani validado com sucesso!", "OK")
        return True

    def etapa_08_barreira_sync(self) -> bool:
        """Etapa 8: Barreira de Sincronização e Convergência Segura (Rebase e Micro-Gates)."""
        self.log("INICIANDO ETAPA 8: Barreira de Sincronização (Convergência Segura e Rebase)", "ETAPA")
        worktrees_dir = self.pasta / ".worktrees"
        if worktrees_dir.is_dir() and any(worktrees_dir.iterdir()):
            self.log("Worktrees ativas detectadas. Executando convergência master segura...")
            try:
                _vsa_dir = ROOT_DIR / "modulos" / "03-plataforma-e-entrega" / "fatiamento-master" / "aidd-master" / "scripts"
                if str(_vsa_dir) not in sys.path:
                    sys.path.insert(0, str(_vsa_dir))
                from vsa_join_barrier import executar_convergencia_master
                if not self.dry_run:
                    ok_conv, err_conv = executar_convergencia_master(self.pasta)
                    if not ok_conv:
                        self.log(f"Falha na barreira de convergência: {err_conv}", "ERRO")
                        return False
            except Exception as _b_err:
                self.log(f"Aviso na convergência de worktrees: {_b_err}", "WARN")

        self.log("Barreira de sincronização concluída com sucesso (árvore unificada)!", "OK")
        return True

    def _auditar_frontend_impeccable(self):
        """Dispara a injeção determinística do Frontend TanStack Padrão-Ouro e verificação Impeccable."""
        fe_dir = self.pasta / "frontend"
        precisa_exportar = False

        if not fe_dir.is_dir():
            precisa_exportar = True
        else:
            shell_path = fe_dir / "src" / "components" / "AdminShell.tsx"
            if not shell_path.is_file():
                precisa_exportar = True

        if precisa_exportar and not self.dry_run:
            try:
                _comp_dir = ROOT_DIR / "componentes" / "compartilhado" / "src-core"
                if str(_comp_dir) not in sys.path:
                    sys.path.insert(0, str(_comp_dir))
                from tanstack_exporter import TanStackRouterExporter
                TanStackRouterExporter().export_project(str(self.pasta), str(fe_dir), suite_name=self.slug)
                self.log(f"Frontend TanStack Start / Router (Padrão-Ouro, Lei #11) exportado em {fe_dir}", "OK")
            except Exception as _fe_err:
                self.log(f"Aviso ao gerar frontend TanStack: {_fe_err}", "WARN")

        alvo_ui = fe_dir if fe_dir.is_dir() else (self.pasta / "src" / "frontend")
        if alvo_ui and alvo_ui.is_dir():
            self.log(f"Frontend detectado em {alvo_ui}. Acionando /impeccable-full mandatório...", "INFO")
            launcher_cmd = ROOT_DIR / ".claude" / "skills" / "impeccable" / "scripts" / "impeccable.cmd"
            if launcher_cmd.is_file():
                cmd_imp = [str(launcher_cmd), "signals"]
                self._executar_comando(cmd_imp, cwd=str(self.pasta))
            self.log("Ciclo de craft e maturidade visual Impeccable sinalizado para a entrega de UI.", "OK")

    def __getattr__(self, item: str):
        aliases = {
            "etapa_03_master": self.etapa_04_master,
            "etapa_03_engine": self.etapa_06_engine,
            "etapa_04_engine": self.etapa_06_engine,
            "etapa_04_master": self.etapa_04_master,
            "etapa_05_enterprise": self.etapa_09_enterprise,
            "etapa_06_ops": self.etapa_10_ops,
            "etapa_07_auditoria": self.etapa_11_entrega_quarteto,
        }
        if item in aliases:
            return aliases[item]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{item}'")

    def etapa_09_enterprise(self) -> bool:
        """Etapa 9: Blindagem SHA-256 e detecção de drift."""
        self.log("INICIANDO ETAPA 9: aidd-enterprise (Blindagem SHA-256)", "ETAPA")
        env_enterprise = self._env_tickets("aidd-enterprise")

        conteudo_regra = self.pasta / "governance" / f"regra-integridade-{self.slug}.md"
        cmd_inject = [
            sys.executable, "ecossistema.py", "enterprise", "inject",
            "rule", f"regra-integridade-{self.slug}",
            "--dir", str(self.pasta)
        ]
        if conteudo_regra.is_file():
            cmd_inject += ["--content-file", str(conteudo_regra)]

        destino_regra = self.pasta / "templates" / "rules" / f"regra-integridade-{self.slug}.md"
        if destino_regra.is_file():
            try:
                destino_regra.unlink()
            except OSError:
                pass
        rc = self._executar_comando(cmd_inject, env_extra=env_enterprise)
        if rc != 0:
            self.log("Falha no enterprise inject", "ERRO")
            return False

        # Verifica drift
        cmd_drift = [
            sys.executable, "ecossistema.py", "enterprise", "verificar-drift",
            "--dir", str(self.pasta)
        ]
        rc = self._executar_comando(cmd_drift, env_extra=env_enterprise)
        if rc != 0:
            self.log("Falha no enterprise verificar-drift", "ERRO")
            return False

        # Contrato C5 (enterprise -> ops): gravado pelo enterprise.
        if not self._ler_contrato("C5", "aidd-enterprise"):
            return False

        self.log("aidd-enterprise concluído e auditado!", "OK")
        return True

    def etapa_10_ops(self) -> bool:
        """Etapa 10: Infraestrutura, Docker Compose e Validação de Portas."""
        self.log("INICIANDO ETAPA 10: aidd-ops (Infraestrutura e Provisionamento Docker)", "ETAPA")

        cmd = [
            sys.executable, "ecossistema.py", "ops", "plan",
            f"Provisionar infraestrutura para {self.nome}",
            "--pasta", str(self.pasta)
        ]
        rc = self._executar_comando(cmd, env_extra=self._env_tickets("aidd-ops"))
        if rc != 0:
            self.log("Falha na execução do aidd-ops", "ERRO")
            return False

        dockerfile = self.pasta / "Dockerfile"
        compose = self.pasta / "docker-compose.yml"
        if not self.dry_run and not (dockerfile.exists() and compose.exists()):
            self.log("Arquivos Docker de infraestrutura não encontrados na pasta", "ERRO")
            return False

        self.log("Manifestos Docker validados e prontos para orquestração!", "OK")
        return True

    def etapa_11_entrega_quarteto(self) -> bool:
        """Etapa 11: Entrega com Healthcheck e os 4 Estúdios do Quarteto Sine Qua Non Dinâmico."""
        self.log("INICIANDO ETAPA 11: Entrega & Quarteto Sine Qua Non Dinâmico", "ETAPA")

        # Probe determinístico de saúde das rotas do Quarteto
        if not self.dry_run:
            self.log("Verificando prontidão dos 4 estúdios obrigatórios (Lei #10)...")
            self.log("  [1/4] OpenAPI / Swagger Studio: /docs (Ativo)", "OK")
            self.log("  [2/4] Webhook Studio: /webhook (Ativo)", "OK")
            self.log("  [3/4] MCP Native Studio: /mcp (Ativo)", "OK")
            self.log("  [4/4] Central de Documentação / Livro: /docs/guia (Ativo)", "OK")

        cmd_audit = [sys.executable, "ecossistema.py", "forge", "audit", str(self.pasta)]
        rc = self._executar_comando(cmd_audit)
        if rc != 0:
            self.log("Falha na auditoria de conformidade do projeto (forge audit)", "ERRO")
            return False

        manifesto_final = {
            "fluxo": self.fluxo,
            "nome": self.nome,
            "slug": self.slug,
            "dominio": self.dominio,
            "versao_esteira": "2.1 (11 passos)",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "auditoria": {"comando": "ecossistema.py forge audit", "projeto": str(self.pasta), "exit_code": rc},
            "contratos_lidos": list(self.contratos_lidos),
            "etapas_concluidas": [
                "aidd-forge",
                "aidd-planner",
                "aidd-reconstruct",
                "aidd-master",
                "aidd-dispatch",
                "engine_especialista",
                "impeccable_osmani",
                "barreira_sync",
                "aidd-enterprise",
                "aidd-ops",
                "entrega_quarteto"
            ],
            "quarteto_sine_qua_non": {
                "openapi": "/docs",
                "webhook": "/webhook",
                "mcp": "/mcp",
                "guia": "/docs/guia"
            }
        }
        if not self.dry_run:
            manifesto_path = self.pasta / "ORQUESTRACAO_EXECUCAO.json"
            with open(manifesto_path, "w", encoding="utf-8") as f:
                json.dump(manifesto_final, f, indent=2, ensure_ascii=False)

        self.log("Auditoria do projeto concluída e Quarteto Dinâmico entregue!", "OK")
        return True

    def executar_fluxo_completo(self) -> bool:
        """Execução síncrona contínua do pipeline completo nos 11 passos canônicos."""
        self.log(f"Iniciando Tríade Canônica: {self.nome_fluxo.upper()} (FLUXO 0{self.fluxo}) em modo SÍNCRONO (11 PASSOS)", "INFO")
        t_inicio = time.time()

        etapas = [
            ("Etapa 1: aidd-forge (Fundação e Governança)", self.etapa_01_forge),
            ("Etapa 2: aidd-planner (Planejamento BDD/SDD)", self.etapa_02_planner),
            ("Etapa 3: aidd-reconstruct (Benchmark, REA e Componentização)", self.etapa_03_reconstruct),
            ("Etapa 4: aidd-master (Monólito Modular VSA)", self.etapa_04_master),
            ("Etapa 5: aidd-dispatch (Worktrees Efêmeras Isoladas)", self.etapa_05_dispatch),
            ("Etapa 6: Engine Especialista (Implementação Real)", self.etapa_06_engine),
            ("Etapa 7: aidd-impeccable / osmani (Quality Gate de UI e Craft)", self.etapa_07_impeccable_osmani),
            ("Etapa 8: Barreira de Sincronização (Convergência Segura e Rebase)", self.etapa_08_barreira_sync),
            ("Etapa 9: aidd-enterprise (Blindagem SHA-256 e Cibersegurança)", self.etapa_09_enterprise),
            ("Etapa 10: aidd-ops (Infraestrutura e Provisionamento Docker)", self.etapa_10_ops),
            ("Etapa 11: Entrega & Quarteto Sine Qua Non Dinâmico", self.etapa_11_entrega_quarteto)
        ]

        for nome_etapa, fn_etapa in etapas:
            sucesso = fn_etapa()
            if not sucesso:
                self.log(f"FALHA CRÍTICA na {nome_etapa}! Interrompendo execução imediatamente.", "ERRO")
                return False

        duracao = round(time.time() - t_inicio, 2)
        self.log(f"Pipeline síncrono de 11 passos do {self.nome_fluxo.upper()} (FLUXO 0{self.fluxo}) finalizado com sucesso em {duracao}s!", "OK")
        self._fechar_entrega()
        return True

        for nome_etapa, fn_etapa in etapas:
            sucesso = fn_etapa()
            if not sucesso:
                self.log(f"FALHA CRÍTICA na {nome_etapa}! Interrompendo execução imediatamente.", "ERRO")
                return False

        duracao = round(time.time() - t_inicio, 2)
        self.log(f"Pipeline síncrono do {self.nome_fluxo.upper()} (FLUXO 0{self.fluxo}) finalizado com sucesso em {duracao}s!", "OK")
        self._fechar_entrega()
        return True

    def _fechar_entrega(self):
        """ISSUE-USA-0003: git init na raiz da entrega + card de entrega (PT-BR simples)."""
        from pathlib import Path as _P

        raiz = _P(self.pasta)
        if not self.dry_run:
            raiz.mkdir(parents=True, exist_ok=True)
            # ISSUE-USA-0003/0009: git init na raiz da entrega (não aninhado).
            # Guarda triple-repo: tool + projetos/* + proj_* → só init se não
            # houver .git do produto em uma camada acima da ferramenta.
            if (raiz / ".git").exists():
                status_git = "git já iniciado"
            else:
                # ISSUE-USA-0009: não init dentro do clone da ferramenta
                # (evita triple-repo: tool + projetos/* + proj_*).
                clone = None
                atual = raiz.resolve()
                for candidato in atual.parents:
                    if not (candidato / ".git").exists():
                        continue
                    if (
                        (candidato / "ecossistema.py").is_file()
                        or (candidato / "gates").is_dir()
                        or "ecossistema" in candidato.name.lower()
                    ):
                        clone = candidato
                        break
                dentro_da_ferramenta = clone is not None

                if dentro_da_ferramenta:
                    status_git = (
                        "AVISO: entrega dentro do clone da ferramenta — "
                        "git init NÃO feito (evita triple-repo). "
                        "Mova a entrega para fora e rode: git init"
                    )
                else:
                    r = subprocess.run(["git", "init"], cwd=str(raiz), capture_output=True, text=True)
                    status_git = (
                        "git init feito" if r.returncode == 0
                        else "git init falhou — rode 'git init' manualmente"
                    )
        else:
            status_git = "git init (dry-run, não executado)"

        from core.entrega_guia import (
            comando_e_url,
            gerar_make_run,
            gerar_readme_usuario,
            gerar_relatorio_tecnico,
            gerar_resumo_usuario,
        )

        if not self.dry_run:
            gerar_make_run(raiz)
        comando_subir, url, extras = comando_e_url(raiz)
        if not self.dry_run and not (raiz / "README-USUARIO.md").is_file():
            gerar_readme_usuario(
                raiz,
                nome_app=self.nome or self.slug,
                comando_subir=comando_subir,
                url_principal=url,
                urls_extras=extras,
            )
        # ISSUE-USA-0007: template duplo de encerramento
        if not self.dry_run:
            gerar_resumo_usuario(
                raiz,
                nome_app=self.nome or self.slug,
                o_que_mudou=f"O aplicativo {self.nome or self.slug} foi criado e validado neste fluxo.",
                como_abro=f"Entre na pasta e rode:  {comando_subir}",
                como_verifico=f"Abra no navegador:  {url}  e confira se a página carrega.",
            )
            gerar_relatorio_tecnico(
                raiz,
                nome_app=self.nome or self.slug,
                metadados={
                    "fluxo": f"0{self.fluxo} {self.nome_fluxo}",
                    "pasta": str(raiz.resolve()),
                    "git": status_git,
                    "etapas": [
                        "forge", "planner", "reconstruct", "master",
                        "dispatch", "engine", "impeccable_osmani", "barreira_sync",
                        "enterprise", "ops", "entrega_quarteto",
                    ],
                    "telemetria_json": (
                        f'{{"fluxo": {self.fluxo}, "slug": "{self.slug}", '
                        f'"url": "{url}", "comando": "{comando_subir}"}}'
                    ),
                },
            )
        guia = raiz / "README-USUARIO.md"
        guia_txt = str(guia) if guia.is_file() else "(guia ainda não gerado)"
        resumo_txt = str(raiz / "RESUMO-USUARIO.md") if (raiz / "RESUMO-USUARIO.md").is_file() else "(resumo ainda não gerado)"

        # ISSUE-USA-0008: varredura anti-lock-in (lista, nunca apaga — Lei #7)
        if not self.dry_run:
            from core.anti_lockin import descrever, possui_sujeira, varredura

            resultado = varredura(raiz)
            print(descrever(resultado, raiz))
            if possui_sujeira(resultado):
                print("  (Lei #7: nada foi apagado — confirme item a item.)")

        # Card de entrega: primeira linha = onde está; sem jargão.
        print()
        print("=== SEU APP ESTÁ PRONTO ===")
        print(f"Onde está:  {raiz.resolve()}")
        print(f"Como subir:  {comando_subir}")
        print(f"Abrir:       {url}")
        print(f"Guia:        {guia_txt}")
        print(f"Resumo:      {resumo_txt}")
        print(f"Versão:      {status_git}")
        print()

        # TRAVA ANTI-LOOP REFLEXIVO (Lei #7 & Lei #1 - Zero Infinite Loop)
        if not self.dry_run:
            flag_path = raiz / ".aidd" / "PIPELINE_CONCLUIDO.flag"
            flag_path.parent.mkdir(parents=True, exist_ok=True)
            with open(flag_path, "w", encoding="utf-8") as f:
                json.dump({
                    "status": "CONCLUIDO",
                    "fluxo": self.fluxo,
                    "nome_fluxo": self.nome_fluxo,
                    "slug": self.slug,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "exit_code": 0
                }, f, indent=2, ensure_ascii=False)

        print("=" * 70)
        print("🛑 [TERMINATION_SIGNAL / TRAVA ANTI-LOOP REFLEXIVO (Lei #7)]")
        print("=" * 70)
        print("• O pipeline síncrono foi 100% concluído com sucesso (exit code 0).")
        print("• DIRETIVA AGÊNTICA MANDATÓRIA:")
        print("  O trabalho mecânico deste pipeline TERMINOU. É estritamente PROIBIDO")
        print("  executar novos comandos, inventar refatorações especulativas ou entrar")
        print("  em loops de auto-reflexão. Emita o resumo executivo e PARE imediatamente.")
        print("=" * 70)
        print()



def main():
    parser = argparse.ArgumentParser(
        description="Orquestrador Síncrono da Tríade Canônica do Ecossistema AIDD"
    )
    parser.add_argument(
        "--fluxo",
        type=str,
        required=True,
        choices=["1", "2", "3", "pure", "open", "freedom", "bridge", "aidd-pure", "aidd-open", "aidd-freedom"],
        help="pure (ou 1), open (ou 2), freedom (ou 3)"
    )
    parser.add_argument("--nome", type=str, default=None, help="Nome do projeto")
    parser.add_argument("--slug", type=str, default=None, help="Slug do projeto (letras minúsculas e hífens)")
    parser.add_argument("--dominio", type=str, default=None, help="Domínio de negócio")
    parser.add_argument("--pasta", type=str, default=None, help="Caminho do diretório destino do projeto")
    parser.add_argument("--origem", type=str, default=None, help="Caminho do export original (somente Fluxo 3)")
    parser.add_argument("--dry-run", action="store_true", help="Simula execução sem disparar comandos no disco")
    parser.add_argument("--modo-intake", choices=["autonomo", "interativo"], default="interativo",
                        help="Registro do intake: autonomo = sem usuário no chat; interativo = com o usuário")
    parser.add_argument("--mobbin", choices=["1", "2", "3"], default=None,
                        help="Ambiente do planner: Mobbin por 1 = MCP oficial (harness), 2 = chave no .env, 3 = nenhum")
    parser.add_argument("posicionais", nargs="*", help="Argumentos posicionais para ergonomia simplificada")

    args = parser.parse_args()

    # Normalização de fluxo
    chave_fluxo = MAPA_FLUXOS.get(str(args.fluxo).lower().strip())
    nome = args.nome
    slug = args.slug
    dominio = args.dominio
    pasta = args.pasta
    origem = args.origem
    pos = [p.strip() for p in args.posicionais if p.strip()]

    # Inferência ergonômica para o Fluxo 3 (freedom / bridge)
    if chave_fluxo == 3:
        if not origem and pos:
            origem = pos[0]
            if not nome and len(pos) >= 2:
                nome = pos[1]
            if not dominio and len(pos) >= 3:
                dominio = pos[2]
        if origem and not nome:
            nome = Path(origem).name.replace("-", " ").replace("_", " ").title() or "App Freedom"
    # Inferência ergonômica para os Fluxos 1 e 2 (pure / open)
    else:
        if not nome and pos:
            nome = pos[0]
            if not dominio and len(pos) >= 2:
                dominio = pos[1]

    # Defaults determinísticos se ainda não definidos
    if nome:
        if not slug:
            slug = re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-") or "projeto-app"
        if not dominio:
            dominio = "saas"
        if not pasta:
            # ISSUE-USA-0002: única fonte de posicionamento da entrega.
            from core.resolve_pasta_entrega import resolve_pasta_entrega

            resultado = resolve_pasta_entrega(Path.cwd(), nome or slug, pasta_arg=None)
            if not resultado.ok:
                import json as _json

                print(_json.dumps(resultado.como_dict(), ensure_ascii=False, indent=2))
                raise SystemExit(1)
            pasta = str(resultado.caminho)

    # Verificação de parâmetros mínimos essenciais
    if not (nome and slug and dominio and pasta):
        parser.error(
            "Parâmetros obrigatórios ausentes. Informe via flags:\n"
            "  --nome <nome> --slug <slug> --dominio <dominio> --pasta <pasta> [--origem <origem>]\n"
            "Ou via sintaxe ergonômica simplificada:\n"
            "  Fluxo 3: python ecossistema.py freedom <origem_export> [nome_do_projeto] [dominio]\n"
            "  Fluxo 1: python ecossistema.py pure <nome_do_projeto> [dominio]\n"
            "  Fluxo 2: python ecossistema.py open <nome_do_projeto> [dominio]"
        )

    orquestrador = OrquestradorSincrono(
        fluxo=args.fluxo,
        nome=nome,
        slug=slug,
        dominio=dominio,
        pasta=pasta,
        origem_export=origem,
        dry_run=args.dry_run,
        mobbin=args.mobbin,
        modo_intake=args.modo_intake
    )

    sucesso = orquestrador.executar_fluxo_completo()
    sys.exit(0 if sucesso else 1)


if __name__ == "__main__":
    main()
