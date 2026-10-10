import json
import os
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Any

def _pid_vivo(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1040, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except (OSError, Exception):
        return False

class QuadroLeitor:
    def __init__(self, raiz_aidd: Optional[Path] = None, raiz_repo: Optional[Path] = None):
        self.raiz_aidd = raiz_aidd or Path(os.environ.get("AIDD_HOME", Path.home() / ".aidd"))
        self.raiz_repo = raiz_repo or Path(__file__).resolve().parent.parent
        self.contrato_pipelines_path = self.raiz_repo / "modulos" / "04-nucleo-compartilhado" / "contracts" / "PIPELINES.json"

    def carregar_contrato_pipelines(self) -> Dict[str, Any]:
        if self.contrato_pipelines_path.exists():
            try:
                return json.loads(self.contrato_pipelines_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"pipelines": []}

    def listar_execucoes(self, incluir_arquivo: bool = False) -> List[Dict[str, Any]]:
        execucoes = []
        pasta_execucoes = self.raiz_aidd / "execucoes"
        if pasta_execucoes.exists():
            for estado_file in pasta_execucoes.glob("*/estado.json"):
                try:
                    conteudo = json.loads(estado_file.read_text(encoding="utf-8"))
                    # Verificar se o processo morreu (interrompido derivado)
                    if conteudo.get("status") == "executando":
                        pid = conteudo.get("processo", {}).get("pid")
                        if pid and not _pid_vivo(pid):
                            conteudo["status"] = "interrompido"
                            if not conteudo.get("parada"):
                                conteudo["parada"] = {
                                    "motivo": f"Processo PID {pid} encerrou sem sinal de conclusao",
                                    "comando": conteudo.get("comando", ""),
                                    "log": ""
                                }
                    execucoes.append(conteudo)
                except Exception:
                    continue

        if incluir_arquivo:
            pasta_arquivo = self.raiz_aidd / "arquivo"
            if pasta_arquivo.exists():
                for estado_file in pasta_arquivo.glob("*/estado.json"):
                    try:
                        conteudo = json.loads(estado_file.read_text(encoding="utf-8"))
                        execucoes.append(conteudo)
                    except Exception:
                        pass
                for zip_path in pasta_arquivo.glob("*.zip"):
                    try:
                        with zipfile.ZipFile(zip_path, "r") as zf:
                            for name in zf.namelist():
                                if name.endswith("estado.json"):
                                    try:
                                        conteudo = json.loads(zf.read(name).decode("utf-8"))
                                        execucoes.append(conteudo)
                                    except Exception:
                                        pass
                    except Exception:
                        pass

        # Ordenar por atualizado_em decrescente
        execucoes.sort(key=lambda x: x.get("atualizado_em", x.get("processo", {}).get("inicio", "")), reverse=True)
        return execucoes

    def arquivar_execucoes(self, status_alvos: Optional[List[str]] = None) -> int:
        import shutil
        alvos = set(status_alvos or ["concluido", "falhou", "interrompido", "cancelado"])
        pasta_execucoes = self.raiz_aidd / "execucoes"
        pasta_arquivo = self.raiz_aidd / "arquivo"
        pasta_arquivo.mkdir(parents=True, exist_ok=True)
        total_movidos = 0

        if not pasta_execucoes.exists():
            return 0

        for pasta_run in list(pasta_execucoes.iterdir()):
            if not pasta_run.is_dir():
                continue
            estado_file = pasta_run / "estado.json"
            if not estado_file.exists():
                continue
            try:
                conteudo = json.loads(estado_file.read_text(encoding="utf-8"))
                st = conteudo.get("status", "")
                if st in alvos:
                    destino = pasta_arquivo / pasta_run.name
                    if destino.exists():
                        shutil.rmtree(destino, ignore_errors=True)
                    shutil.move(str(pasta_run), str(destino))
                    total_movidos += 1
            except Exception:
                continue
        return total_movidos

    def obter_execucao(self, run_id: str) -> Optional[Dict[str, Any]]:
        # Tenta em execucoes ativas
        arquivo = self.raiz_aidd / "execucoes" / run_id / "estado.json"
        if arquivo.exists():
            try:
                conteudo = json.loads(arquivo.read_text(encoding="utf-8"))
                if conteudo.get("status") == "executando":
                    pid = conteudo.get("processo", {}).get("pid")
                    if pid and not _pid_vivo(pid):
                        conteudo["status"] = "interrompido"
                return conteudo
            except Exception:
                pass

        # Tenta na pasta descompactada de arquivo
        arquivo_historico = self.raiz_aidd / "arquivo" / run_id / "estado.json"
        if arquivo_historico.exists():
            try:
                return json.loads(arquivo_historico.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Tenta nos arquivos .zip
        pasta_arquivo = self.raiz_aidd / "arquivo"
        if pasta_arquivo.exists():
            for zip_path in pasta_arquivo.glob("*.zip"):
                try:
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        nome_esperado = f"{run_id}/estado.json"
                        for name in zf.namelist():
                            if name.endswith(nome_esperado) or name == "estado.json":
                                try:
                                    conteudo = json.loads(zf.read(name).decode("utf-8"))
                                    if conteudo.get("run_id") == run_id:
                                        return conteudo
                                except Exception:
                                    pass
                except Exception:
                    pass
        return None

    def resumo_pipelines(self) -> Dict[str, Any]:
        contrato = self.carregar_contrato_pipelines()
        execucoes = self.listar_execucoes(incluir_arquivo=False)
        
        resultado = {}
        for pipe in contrato.get("pipelines", []):
            pid = pipe["id"]
            resultado[pid] = {
                "id": pid,
                "nome": pipe.get("nome", pid),
                "comando": pipe.get("comando", ""),
                "total": 0,
                "executando": 0,
                "concluido": 0,
                "falhou": 0,
                "precisa_humano": 0,
                "etapas_contagem": {et["id"]: 0 for et in pipe.get("etapas", [])}
            }

        for ex in execucoes:
            pid = ex.get("pipeline")
            if pid not in resultado:
                resultado[pid] = {
                    "id": pid,
                    "nome": pid,
                    "comando": ex.get("comando", ""),
                    "total": 0,
                    "executando": 0,
                    "concluido": 0,
                    "falhou": 0,
                    "precisa_humano": 0,
                    "etapas_contagem": {}
                }
            r = resultado[pid]
            r["total"] += 1
            st = ex.get("status")
            if st == "executando":
                r["executando"] += 1
            elif st == "concluido":
                r["concluido"] += 1
            elif st in ("falhou", "cancelado", "interrompido"):
                r["falhou"] += 1

            if ex.get("humano"):
                r["precisa_humano"] += 1

            etapa = ex.get("etapa_atual")
            if etapa:
                r["etapas_contagem"][etapa] = r["etapas_contagem"].get(etapa, 0) + 1

            if st == "executando":
                gate = ex.get("gate_atual") or ex.get("detalhes", {}).get("gate_atual")
                prog = ex.get("progresso_gates") or ex.get("detalhes", {}).get("progresso_gates")
                pct = ex.get("percentual") if ex.get("percentual") is not None else ex.get("detalhes", {}).get("percentual")
                if gate:
                    r["gate_atual"] = gate
                if prog:
                    r["progresso_gates"] = prog
                if pct is not None:
                    r["percentual"] = pct

        return resultado
