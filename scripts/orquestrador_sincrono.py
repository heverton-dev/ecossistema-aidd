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
planner_tools = ROOT_DIR / "tools" / "aidd-planner"
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
        dry_run: bool = False
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

        cmd = [
            sys.executable, "ecossistema.py", "planner", "init",
            "--fluxo", str(self.fluxo),
            "--nome", self.nome,
            "--slug", self.slug,
            "--dominio", self.dominio,
            "--pasta", str(self.pasta)
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

    def etapa_03_engine(self) -> bool:
        """Etapa 3: Execução da Engine correspondente ao Fluxo."""
        env_construtor = self._env_tickets(self.nome_fluxo)
        if self.fluxo == 1:
            self.log("INICIANDO ETAPA 3: aidd-pure (Engine Fluxo 01: Do Zero Puro)", "ETAPA")
            cmd = [
                sys.executable, "ecossistema.py", "pure-motor",
                f"{self.nome}: sistema para {self.dominio}",
                "--pasta", str(self.pasta),
                "--implementar-codigo"
            ]
        elif self.fluxo == 2:
            self.log("INICIANDO ETAPA 3: aidd-open (Engine Fluxo 02: Open-Source)", "ETAPA")
            # A factory recebe a planta do planner (C2): a entrada dela mora
            # em entrada_construtor.plano_motores. Nada de plano inventado.
            cmd = [
                sys.executable, "ecossistema.py", "open-motor",
                "--plano", str(self.pasta / CONTRATOS["C2"][0]),
                "--pasta", str(self.pasta)
            ]
        else:
            self.log("INICIANDO ETAPA 3: aidd-freedom (Engine Fluxo 03: Low-Code Bridge)", "ETAPA")
            origem = str(self.origem_export or (self.pasta / "origem"))
            cmd = [
                sys.executable, "ecossistema.py", "freedom-motor", "scan",
                origem
            ]
        rc = self._executar_comando(cmd, env_extra=env_construtor)
        if rc != 0:
            self.log(f"Falha na execução do {self.nome_fluxo}", "ERRO")
            return False

        # Contrato C3 (engine -> master): gravado pelo construtor.
        if not self._ler_contrato("C3", self.nome_fluxo):
            return False

        self.log("Engine especialista concluída com sucesso!", "OK")
        return True

    def etapa_04_master(self) -> bool:
        """Etapa 4: Despacho das fatias VSA + harmonização no Monólito Modular."""
        self.log("INICIANDO ETAPA 4: aidd-master (Monólito Modular VSA)", "ETAPA")
        env_master = self._env_tickets("aidd-master")

        # Despacho determinístico de fatias VSA em Git Worktrees efêmeras:
        # começo da etapa do master (integração), não da do construtor.
        vsa_manifest = self.pasta / VSA_DISPATCH_NOME
        if not vsa_manifest.is_file() and (self.pasta / "PLANNER.json").is_file():
            vsa_manifest = self.pasta / "PLANNER.json"
        if not self.dry_run and not vsa_manifest.is_file():
            self.log(f"aidd-planner não gravou {VSA_DISPATCH_NOME}: nada para despachar", "ERRO")
            return False

        self.log("Invocando motor de despacho VSA via CLI do ecossistema")
        cmd_disp = [
            sys.executable, "ecossistema.py", "dispatch",
            "--dispatch", str(vsa_manifest),
            "--target-dir", str(self.pasta),
        ]
        if self.dry_run:
            cmd_disp.append("--dry-run")
        rc = self._executar_comando(cmd_disp, env_extra=env_master)
        if rc != 0:
            self.log("Falha no despacho de fatias VSA em Git worktrees", "ERRO")
            return False

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

        # master add-module com a fatia vertical principal
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

        self.log("aidd-master concluído com sucesso!", "OK")
        return True

    def etapa_05_enterprise(self) -> bool:
        """Etapa 5: Blindagem SHA-256 e detecção de drift."""
        self.log("INICIANDO ETAPA 5: aidd-enterprise (Blindagem SHA-256)", "ETAPA")
        env_enterprise = self._env_tickets("aidd-enterprise")

        # Injeta regra de integridade
        cmd_inject = [
            sys.executable, "ecossistema.py", "enterprise", "inject",
            "rule", f"regra-integridade-{self.slug}",
            "--dir", str(self.pasta)
        ]
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

    def etapa_06_ops(self) -> bool:
        """Etapa 6: Infraestrutura, Docker Compose e Validação de Portas."""
        self.log("INICIANDO ETAPA 6: aidd-ops (Infraestrutura e Provisionamento)", "ETAPA")

        cmd = [
            sys.executable, "ecossistema.py", "ops", "plan",
            f"Provisionar infraestrutura para {self.nome}",
            "--pasta", str(self.pasta)
        ]
        rc = self._executar_comando(cmd, env_extra=self._env_tickets("aidd-ops"))
        if rc != 0:
            self.log("Falha na execução do aidd-ops", "ERRO")
            return False

        # Verifica presença de Dockerfile e docker-compose.yml
        dockerfile = self.pasta / "Dockerfile"
        compose = self.pasta / "docker-compose.yml"
        if not self.dry_run and not (dockerfile.exists() and compose.exists()):
            self.log("Arquivos Docker de infraestrutura não encontrados na pasta", "ERRO")
            return False

        self.log("Manifestos Docker validados e prontos para orquestração!", "OK")
        return True

    def etapa_07_auditoria(self) -> bool:
        """Etapa 7: Auditoria de conformidade do projeto gerado (não do monorepo)."""
        self.log("INICIANDO ETAPA 7: Auditoria de Conformidade Final", "ETAPA")

        cmd_audit = [sys.executable, "ecossistema.py", "forge", "audit", str(self.pasta)]
        rc = self._executar_comando(cmd_audit)
        if rc != 0:
            self.log("Falha na auditoria de conformidade do projeto (forge audit)", "ERRO")
            return False

        # Manifesto da orquestração: registra só o que foi lido de verdade.
        manifesto_final = {
            "fluxo": self.fluxo,
            "nome": self.nome,
            "slug": self.slug,
            "dominio": self.dominio,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "auditoria": {"comando": "ecossistema.py forge audit", "projeto": str(self.pasta), "exit_code": rc},
            "contratos_lidos": list(self.contratos_lidos),
            "etapas_concluidas": [
                "aidd-forge",
                "aidd-planner",
                "engine_especialista",
                "aidd-master",
                "aidd-enterprise",
                "aidd-ops",
                "auditoria_final"
            ]
        }
        if not self.dry_run:
            manifesto_path = self.pasta / "ORQUESTRACAO_EXECUCAO.json"
            with open(manifesto_path, "w", encoding="utf-8") as f:
                json.dump(manifesto_final, f, indent=2, ensure_ascii=False)

        self.log("Auditoria do projeto concluída (forge audit exit 0).", "OK")
        return True

    def executar_fluxo_completo(self) -> bool:
        """Execução síncrona contínua do pipeline completo."""
        self.log(f"Iniciando Tríade Canônica: {self.nome_fluxo.upper()} (FLUXO 0{self.fluxo}) em modo SÍNCRONO", "INFO")
        t_inicio = time.time()

        etapas = [
            ("Etapa 1: aidd-forge", self.etapa_01_forge),
            ("Etapa 2: aidd-planner", self.etapa_02_planner),
            ("Etapa 3: Engine Especialista", self.etapa_03_engine),
            ("Etapa 4: aidd-master", self.etapa_04_master),
            ("Etapa 5: aidd-enterprise", self.etapa_05_enterprise),
            ("Etapa 6: aidd-ops", self.etapa_06_ops),
            ("Etapa 7: Auditoria Final", self.etapa_07_auditoria)
        ]

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
                        "forge", "planner", "engine", "master",
                        "enterprise", "ops", "auditoria",
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
        dry_run=args.dry_run
    )

    sucesso = orquestrador.executar_fluxo_completo()
    sys.exit(0 if sucesso else 1)


if __name__ == "__main__":
    main()
