import json
import os
import shutil
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

def _parse_data_iso(data_str: str) -> Optional[datetime]:
    if not data_str:
        return None
    try:
        # Tratar formato ISO com Z ou offset
        limpo = data_str.replace("Z", "+00:00")
        return datetime.fromisoformat(limpo)
    except Exception:
        return None

def executar_arquivamento(raiz_aidd: Optional[Path] = None, dias: int = 30, confirmar: bool = False) -> List[Dict[str, Any]]:
    raiz = raiz_aidd or Path(os.environ.get("AIDD_HOME", Path.home() / ".aidd"))
    pasta_execucoes = raiz / "execucoes"
    if not pasta_execucoes.exists():
        return []

    limite = datetime.now(timezone.utc) - timedelta(days=dias)
    candidatos = []

    for estado_file in pasta_execucoes.glob("*/estado.json"):
        try:
            conteudo = json.loads(estado_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        # NUNCA toca execuções ativas
        if conteudo.get("status") == "executando":
            continue

        data_str = conteudo.get("atualizado_em") or conteudo.get("processo", {}).get("inicio")
        dt = _parse_data_iso(data_str)
        if not dt:
            continue

        # Garantir timezone aware para comparacao
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        if dt < limite:
            candidatos.append({
                "run_id": conteudo.get("run_id", estado_file.parent.name),
                "pipeline": conteudo.get("pipeline"),
                "titulo": conteudo.get("titulo"),
                "atualizado_em": data_str,
                "pasta": estado_file.parent,
                "arquivo": estado_file,
                "mes": dt.strftime("%Y-%m")
            })

    if not confirmar:
        return candidatos

    # Execução real: compactar em arquivo/<AAAA-MM>.zip e remover pasta
    pasta_arquivo = raiz / "arquivo"
    pasta_arquivo.mkdir(parents=True, exist_ok=True)

    for item in candidatos:
        mes = item["mes"]
        zip_path = pasta_arquivo / f"{mes}.zip"
        run_id = item["run_id"]
        
        # Gravar no zip com caminho relativo <run_id>/estado.json
        with zipfile.ZipFile(zip_path, "a", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(item["arquivo"], arcname=f"{run_id}/estado.json")

        # Remover pasta original
        try:
            shutil.rmtree(item["pasta"])
        except Exception as e:
            pass

    return candidatos
