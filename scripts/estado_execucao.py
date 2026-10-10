import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSAO = "aidd.quadro.estado/2"

def _agora_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _gerar_run_id(pipeline: str, chave: str, pid: int) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dt%H%M%Sz")
    base = f"{pipeline}-{chave}-{timestamp}-{pid}".lower()
    limpo = re.sub(r"[^a-z0-9-]", "-", base)
    limpo = re.sub(r"-+", "-", limpo).strip("-")
    return limpo[:120]

def _obter_raiz_aidd() -> Path | None:
    if os.environ.get("AIDD_QUADRO") == "0":
        return None
    if "PYTEST_CURRENT_TEST" in os.environ and "AIDD_HOME" not in os.environ:
        return None
    caminho = os.environ.get("AIDD_HOME")
    if caminho:
        return Path(caminho)
    return Path.home() / ".aidd"

class Execucao:
    def __init__(self, pipeline: str, chave: str, titulo: str, comando: str | None = None, pai: str | None = None):
        self.pipeline = pipeline
        self.chave = chave
        self.titulo = titulo
        self.comando = comando
        self.pid = os.getpid()
        self.run_id = _gerar_run_id(pipeline, chave, self.pid)
        self.pai = pai or os.environ.get("AIDD_EXECUCAO_PAI")
        self.inicio = _agora_iso()
        self.status = "executando"
        self.etapa_atual = None
        self.etapas = []
        self.historico = [{"em": self.inicio, "etapa": None, "evento": "aberta", "mensagem": "execucao iniciada"}]
        self.parada = None
        self.humano = None
        self.fim = None
        self.exit_code = None
        self.seq = 1
        self._aviso_emitido = False
        self._raiz = _obter_raiz_aidd()
        self._arquivo = (self._raiz / "execucoes" / self.run_id / "estado.json") if self._raiz else None

    @classmethod
    def abrir(cls, pipeline: str, chave: str, titulo: str, comando: str | None = None) -> "Execucao":
        instancia = cls(pipeline=pipeline, chave=chave, titulo=titulo, comando=comando)
        os.environ["AIDD_EXECUCAO_PAI"] = instancia.run_id
        instancia.salvar()
        return instancia

    def __enter__(self) -> "Execucao":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        agora = _agora_iso()
        self.fim = agora
        if exc_type is None:
            if self.status == "executando":
                self.status = "concluido"
                self.exit_code = 0
                self.historico.append({"em": agora, "etapa": self.etapa_atual, "evento": "concluida", "mensagem": "finalizado com sucesso"})
        elif issubclass(exc_type, KeyboardInterrupt):
            self.status = "cancelado"
            self.exit_code = 130
            self.historico.append({"em": agora, "etapa": self.etapa_atual, "evento": "cancelado", "mensagem": "interrompido pelo usuario"})
        elif issubclass(exc_type, SystemExit):
            codigo = exc_val.code if isinstance(exc_val.code, int) else (0 if exc_val.code is None else 1)
            self.exit_code = codigo
            self.status = "concluido" if codigo == 0 else "falhou"
            self.historico.append({"em": agora, "etapa": self.etapa_atual, "evento": self.status, "mensagem": f"saida com exit code {codigo}"})
        else:
            self.status = "falhou"
            self.exit_code = 1
            msg = str(exc_val)
            self.parada = {"motivo": msg, "comando": self.comando or "", "log": ""}
            self.historico.append({"em": agora, "etapa": self.etapa_atual, "evento": "falha", "mensagem": msg})
        
        self.salvar()
        # Retorna False para propagar a exceção original
        return False

    def etapa(self, etapa_id: str, status: str, **kwargs):
        self.etapa_atual = etapa_id
        agora = _agora_iso()
        
        existente = None
        for e in self.etapas:
            if e["id"] == etapa_id:
                existente = e
                break
                
        if existente:
            existente["status"] = status
            existente.update(kwargs)
        else:
            novo = {"id": etapa_id, "status": status, "inicio": agora}
            novo.update(kwargs)
            self.etapas.append(novo)
            
        self.historico.append({
            "em": agora,
            "etapa": etapa_id,
            "evento": f"etapa_{status}",
            "mensagem": f"etapa {etapa_id} status {status}"
        })
        self.salvar()

    def pedir_humano(self, motivo: str, comando: str):
        self.humano = {"motivo": motivo, "comando": comando}
        self.historico.append({
            "em": _agora_iso(),
            "etapa": self.etapa_atual,
            "evento": "humano",
            "mensagem": motivo
        })
        self.salvar()

    def parar(self, motivo: str, comando: str | None = None, log: str | None = None):
        self.status = "falhou"
        self.parada = {
            "motivo": motivo,
            "comando": comando or self.comando or "",
            "log": log or ""
        }
        self.historico.append({
            "em": _agora_iso(),
            "etapa": self.etapa_atual,
            "evento": "parada",
            "mensagem": motivo
        })
        self.salvar()

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA_VERSAO,
            "run_id": self.run_id,
            "pipeline": self.pipeline,
            "chave": self.chave,
            "titulo": self.titulo,
            "comando": self.comando,
            "pai": self.pai,
            "processo": {"pid": self.pid, "inicio": self.inicio},
            "status": self.status,
            "etapa_atual": self.etapa_atual,
            "etapas": self.etapas,
            "historico": self.historico,
            "parada": self.parada,
            "humano": self.humano,
            "fim": self.fim,
            "exit_code": self.exit_code,
            "seq": self.seq,
            "atualizado_em": _agora_iso()
        }

    def salvar(self):
        if not self._arquivo:
            return
        self.seq += 1
        conteudo = json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        try:
            self._arquivo.parent.mkdir(parents=True, exist_ok=True)
            temp = self._arquivo.with_suffix(".tmp")
            for tentativa in range(5):
                try:
                    temp.write_text(conteudo + "\n", encoding="utf-8")
                    temp.replace(self._arquivo)
                    break
                except (PermissionError, OSError):
                    time.sleep(0.05)
        except Exception as e:
            if not self._aviso_emitido:
                sys.stderr.write(f"[aidd-quadro] aviso: falha ao gravar estado da execucao {self.run_id}: {e}\n")
                self._aviso_emitido = True
