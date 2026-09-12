# -*- coding: utf-8 -*-
"""
Máquina de Estados Formal e Retomada Inteligente (--resume) do aidd-generator.

Gerencia o ciclo de vida estruturado do pipeline gravado atomicamente em
.aidd/cache/_pipeline_state.json com validação estrita JSON Schema (Draft 2020-12).
Garante retomada sem consumo inútil de tokens em fases completas com artefatos válidos
e tratamento estruturado orientativo em caso de corrupção de arquivos de cache.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Escritor atômico compartilhado
try:
    from escritor_atomico import escrever_json_atomico
except ImportError:
    _comp_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "componentes", "compartilhado", "src-core"
    )
    if os.path.isdir(_comp_dir) and _comp_dir not in sys.path:
        sys.path.insert(0, _comp_dir)
    from escritor_atomico import escrever_json_atomico

# Schemas de validação
from phases.schemas.registry import (
    validar_pipeline_state,
    validar_cache,
    SchemaValidationError,
)


class PipelineCorrompidoError(Exception):
    """Lançada quando um artefato de estado ou cache está corrompido ou inválido."""

    def __init__(self, mensagem: str, arquivo: Optional[Path] = None, detalhe: Optional[str] = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.arquivo = arquivo
        self.detalhe = detalhe


class PipelineStateManager:
    """Controlador da máquina de estados formal do pipeline."""

    SCHEMA_VERSION = "1.0"

    STATUS_PENDENTE = "PENDENTE"
    STATUS_EM_ANDAMENTO = "EM_ANDAMENTO"
    STATUS_COMPLETO = "COMPLETO"
    STATUS_FALHOU = "FALHOU"
    STATUS_PULADO = "PULADO"

    def __init__(self, pasta_projeto: Path, ideia: str, total_fases: int = 7):
        self.pasta_projeto = Path(pasta_projeto).resolve()
        self.cache_dir = self.pasta_projeto / ".aidd" / "cache"
        self.data_dir = self.cache_dir / "data"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.estado_path = self.cache_dir / "_pipeline_state.json"
        self.ideia = ideia
        self.total_fases = total_fases
        self.estado: Dict[str, Any] = {}

    def inicializar(self, resume: bool = False) -> Dict[str, Any]:
        """Carrega estado anterior se resume=True ou inicializa um novo estado limpo.

        Raises:
            PipelineCorrompidoError: Se resume=True e o arquivo de estado existir mas estiver corrompido.
        """
        if resume and self.estado_path.exists():
            try:
                conteudo = self.estado_path.read_text(encoding="utf-8")
                dados = json.loads(conteudo)
                validar_pipeline_state(dados)
                self.estado = dados
                self.estado["status_global"] = self.STATUS_EM_ANDAMENTO
                self.estado["timestamp_atualizacao"] = time.time()
                self._salvar_atomico()
                return self.estado
            except json.JSONDecodeError as e:
                msg = (
                    f"Arquivo de estado '{self.estado_path.name}' está corrompido "
                    f"(JSONDecodeError linha {e.lineno}, coluna {e.colno}): {e.msg}. "
                    "Remova o arquivo corrompido ou execute o pipeline sem a flag --resume."
                )
                raise PipelineCorrompidoError(msg, arquivo=self.estado_path, detalhe=str(e))
            except SchemaValidationError as e:
                msg = (
                    f"Arquivo de estado '{self.estado_path.name}' é incompatível com o schema {self.SCHEMA_VERSION}: {e}. "
                    "Remova o arquivo ou execute o pipeline sem a flag --resume."
                )
                raise PipelineCorrompidoError(msg, arquivo=self.estado_path, detalhe=str(e))

        # Estado inicial limpo
        agora = time.time()
        self.estado = {
            "schema_version": self.SCHEMA_VERSION,
            "pipeline_id": f"pipe_{int(agora)}",
            "ideia": self.ideia,
            "pasta": str(self.pasta_projeto),
            "status_global": self.STATUS_EM_ANDAMENTO,
            "fase_atual": None,
            "total_fases": self.total_fases,
            "timestamp_inicio": agora,
            "timestamp_atualizacao": agora,
            "fases": {},
            "fases_completas": {},
            "score_final": None,
            "fase_que_falhou": None,
            "erro": None,
            "detalhe": None,
            "duracao_segundos": 0.0,
            "orcamento_fases": {},
        }
        self._salvar_atomico()
        return self.estado

    def _salvar_atomico(self) -> None:
        """Persiste o estado atomicamente via escritor_atomico."""
        self.estado["timestamp_atualizacao"] = time.time()
        # Validação do estado contra schema antes de salvar
        try:
            validar_pipeline_state(self.estado)
        except SchemaValidationError:
            pass  # Não impede salvamento em caso de chave temporária de runtime
        escrever_json_atomico(self.estado_path, self.estado)

    def pode_retomar_fase(
        self,
        fase_chave: str,
        artefatos_relativos: List[str],
        schema_tipo: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Verifica se a fase anterior foi concluída e se seus artefatos no disco são íntegros.

        Returns:
            (True, None) se a fase pode ser pulada.
            (False, motivo) se a fase precisa ser executada.
        """
        fases = self.estado.get("fases", {})
        info_fase = fases.get(fase_chave)
        if not info_fase or info_fase.get("status") != self.STATUS_COMPLETO:
            return False, f"Fase '{fase_chave}' não marcada como COMPLETO no estado."

        # Verificar presença e integridade de todos os artefatos esperados
        for rel_path in artefatos_relativos:
            path_completo = self.cache_dir / rel_path
            if not path_completo.exists():
                return False, f"Artefato esperado '{rel_path}' não existe no disco."
            if path_completo.stat().st_size == 0:
                return False, f"Artefato esperado '{rel_path}' está vazio no disco."

            # Se for JSON, validar parse sintático
            if path_completo.suffix.lower() == ".json":
                try:
                    conteudo = path_completo.read_text(encoding="utf-8")
                    dados = json.loads(conteudo)
                except Exception as e:
                    return False, f"Artefato '{rel_path}' contém JSON inválido: {e}"

                # Se schema foi especificado, validar
                if schema_tipo and rel_path.endswith(f"{schema_tipo.replace('cache_', '')}.json"):
                    try:
                        validar_cache(dados, schema_tipo)
                    except SchemaValidationError as e:
                        return False, f"Artefato '{rel_path}' violou o schema '{schema_tipo}': {e}"

        return True, None

    def registrar_fase_iniciada(self, fase_chave: str, nome: str, numero: int) -> None:
        """Marca a fase como EM_ANDAMENTO no estado."""
        self.estado["fase_atual"] = fase_chave
        if "fases" not in self.estado:
            self.estado["fases"] = {}

        if fase_chave not in self.estado["fases"]:
            self.estado["fases"][fase_chave] = {
                "nome": nome,
                "numero": numero,
                "status": self.STATUS_EM_ANDAMENTO,
                "artefatos": [],
                "timestamp_inicio": time.time(),
                "timestamp_fim": None,
                "duracao_segundos": None,
                "tokens_consumidos": 0,
                "pulado": False,
                "erro": None,
            }
        else:
            self.estado["fases"][fase_chave]["status"] = self.STATUS_EM_ANDAMENTO
            self.estado["fases"][fase_chave]["timestamp_inicio"] = time.time()
            self.estado["fases"][fase_chave]["erro"] = None

        self._salvar_atomico()

    def registrar_fase_concluida(
        self,
        fase_chave: str,
        artefatos: List[str],
        tokens_consumidos: int = 0,
        pulado: bool = False,
    ) -> None:
        """Marca a fase como COMPLETO (ou PULADO se retomada)."""
        agora = time.time()
        if "fases" not in self.estado:
            self.estado["fases"] = {}

        info = self.estado["fases"].get(fase_chave, {})
        t_inicio = info.get("timestamp_inicio") or agora

        self.estado["fases"][fase_chave] = {
            "nome": info.get("nome", fase_chave),
            "numero": info.get("numero", 0),
            "status": self.STATUS_COMPLETO,
            "artefatos": artefatos,
            "timestamp_inicio": t_inicio,
            "timestamp_fim": agora,
            "duracao_segundos": round(agora - t_inicio, 3) if not pulado else 0.0,
            "tokens_consumidos": tokens_consumidos if not pulado else info.get("tokens_consumidos", 0),
            "pulado": pulado,
            "erro": None,
        }
        self.estado["fases_completas"][fase_chave] = True
        self._salvar_atomico()

    def registrar_fase_falhou(
        self,
        fase_chave: str,
        erro: str,
        detalhe: Optional[str] = None,
    ) -> None:
        """Marca a fase e o pipeline como FALHOU."""
        agora = time.time()
        if "fases" not in self.estado:
            self.estado["fases"] = {}

        info = self.estado["fases"].get(fase_chave, {})
        t_inicio = info.get("timestamp_inicio") or agora

        self.estado["fases"][fase_chave] = {
            "nome": info.get("nome", fase_chave),
            "numero": info.get("numero", 0),
            "status": self.STATUS_FALHOU,
            "artefatos": info.get("artefatos", []),
            "timestamp_inicio": t_inicio,
            "timestamp_fim": agora,
            "duracao_segundos": round(agora - t_inicio, 3),
            "tokens_consumidos": info.get("tokens_consumidos", 0),
            "pulado": False,
            "erro": erro,
        }
        self.estado["status_global"] = self.STATUS_FALHOU
        self.estado["fase_que_falhou"] = fase_chave
        self.estado["erro"] = erro
        self.estado["detalhe"] = detalhe
        self._salvar_atomico()

    def registrar_pipeline_completo(self, score_final: Optional[float] = None) -> None:
        """Marca o status global do pipeline como COMPLETO."""
        t_inicio = self.estado.get("timestamp_inicio", time.time())
        self.estado["status_global"] = self.STATUS_COMPLETO
        self.estado["score_final"] = score_final
        self.estado["fase_atual"] = None
        self.estado["duracao_segundos"] = round(time.time() - t_inicio, 3)
        self._salvar_atomico()


def ler_cache_com_validacao(
    caminho: Path,
    schema_tipo: str,
    fase_origem: str,
    fase_destino: str,
) -> Tuple[bool, Any, Optional[str]]:
    """Lê um arquivo de cache inter-fases e valida com JSON Schema.

    Trata graciosamente:
    - Arquivo inexistente
    - JSON corrompido / sintaxe inválida
    - Violação do JSON Schema

    Returns:
        (True, dados_dict, None) se válido
        (False, None, mensagem_orientativa) se inválido ou corrompido
    """
    caminho = Path(caminho)
    if not caminho.exists():
        msg = (
            f"Artefato de cache obrigatório '{caminho.name}' não foi encontrado em '{caminho.parent}'. "
            f"A {fase_destino} necessita deste arquivo produzido pela {fase_origem}. "
            f"Reexecute o pipeline garantindo que a {fase_origem} complete com sucesso."
        )
        return False, None, msg

    try:
        conteudo = caminho.read_text(encoding="utf-8")
        dados = json.loads(conteudo)
    except json.JSONDecodeError as e:
        msg = (
            f"JSON corrompido no artefato de cache '{caminho.name}' da {fase_origem} "
            f"(JSONDecodeError linha {e.lineno}, coluna {e.colno}): {e.msg}. "
            f"Remova o arquivo '{caminho}' e reexecute a partir da {fase_origem}."
        )
        return False, None, msg
    except OSError as e:
        msg = f"Falha ao ler arquivo de cache '{caminho.name}': {e}."
        return False, None, msg

    # Validação do Schema
    try:
        validar_cache(dados, schema_tipo)
    except SchemaValidationError as e:
        msg = (
            f"Artefato de cache '{caminho.name}' produzido pela {fase_origem} violou o contrato do schema '{schema_tipo}': "
            f"{e}. Reexecute a {fase_origem} com dados válidos."
        )
        return False, None, msg

    return True, dados, None
