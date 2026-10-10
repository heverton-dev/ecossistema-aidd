import json
import re
from pathlib import Path
from typing import Dict, Any, Union, Optional

def coletar_custos_sessao(
    harness: str,
    session_id: Optional[str] = None,
    log_path: Optional[Union[str, Path]] = None
) -> Union[str, Dict[str, Any]]:
    """Extrai telemetria factual de tokens, skills e MCPs da sessão.
    
    Lei #8 (Rótulo Honesto): se não houver dados factuais comprováveis,
    retorna estritamente 'nao-medido'. Proibido inventar ou estimar números.
    """
    if not log_path and not session_id:
        return "nao-medido"

    arquivo_log = Path(log_path) if log_path else None
    
    # Se log_path nao fornecido, tentar descobrir pasta padrao do Claude
    if not arquivo_log or not arquivo_log.exists():
        if session_id and harness.lower() == "claude":
            possiveis = [
                Path.home() / ".claude" / "projects",
                Path.home() / "aidd-logs"
            ]
            for pasta in possiveis:
                if pasta.exists():
                    candidatos = list(pasta.glob(f"*{session_id}*.jsonl")) + list(pasta.glob(f"*{session_id}*.log"))
                    if candidatos:
                        arquivo_log = candidatos[0]
                        break

    if not arquivo_log or not arquivo_log.exists():
        return "nao-medido"

    tokens_in = 0
    tokens_out = 0
    skills = set()
    mcps = set()
    tem_dados = False

    try:
        conteudo = arquivo_log.read_text(encoding="utf-8", errors="replace")
        for linha in conteudo.splitlines():
            linha = linha.strip()
            if not linha:
                continue
            try:
                d = json.loads(linha)
                # Extrair tokens
                if "usage" in d or "input_tokens" in d or "output_tokens" in d:
                    u = d.get("usage", d)
                    tokens_in += u.get("input_tokens", 0)
                    tokens_out += u.get("output_tokens", 0)
                    tem_dados = True

                # Extrair ferramentas / tools
                nome_ferramenta = d.get("name") or d.get("tool") or ""
                if nome_ferramenta:
                    if "mcp" in nome_ferramenta.lower():
                        mcps.add(nome_ferramenta)
                        tem_dados = True
                    elif "skill" in nome_ferramenta.lower():
                        # Normalizar nome da skill
                        limpo = re.sub(r"^[sS]kill_?", "", nome_ferramenta).replace("_", "-")
                        skills.add(limpo)
                        tem_dados = True
            except json.JSONDecodeError:
                # Log em texto puro com padroes de tokens
                m_in = re.search(r"input_tokens[:=]\s*(\d+)", linha)
                if m_in:
                    tokens_in += int(m_in.group(1))
                    tem_dados = True
                m_out = re.search(r"output_tokens[:=]\s*(\d+)", linha)
                if m_out:
                    tokens_out += int(m_out.group(1))
                    tem_dados = True

        if not tem_dados and tokens_in == 0 and tokens_out == 0 and not skills and not mcps:
            return "nao-medido"

        return {
            "tokens_entrada": tokens_in,
            "tokens_saida": tokens_out,
            "skills": sorted(list(skills)),
            "mcps": sorted(list(mcps)),
            "fonte": str(arquivo_log)
        }
    except Exception:
        return "nao-medido"
