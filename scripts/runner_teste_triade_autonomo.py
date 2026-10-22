#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
runner_teste_triade_autonomo.py — Execução autônoma sequencial dos 3 fluxos da Tríade AIDD.
Executa Fluxo 1 (Pure) -> Fluxo 2 (Open) -> Fluxo 3 (Freedom) em pasta temporária isolada.
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
BASE_TEMP = ROOT_DIR / "projetos" / "tmp_teste_triade"

def log(msg: str):
    print(f"\n[TRIADE-RUNNER] {msg}", flush=True)

def preparar_origem_freedom(origem_dir: Path):
    """Cria uma fixture mínima e válida de export Lovable/Supabase."""
    origem_dir.mkdir(parents=True, exist_ok=True)
    
    pkg = {
        "name": "miniapp-lovable-export",
        "version": "1.0.0",
        "private": True,
        "dependencies": {
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "react-router-dom": "^6.26.0",
            "@supabase/supabase-js": "^2.45.0"
        }
    }
    (origem_dir / "package.json").write_text(json.dumps(pkg, indent=2), encoding="utf-8")
    
    src_pages = origem_dir / "src" / "pages"
    src_pages.mkdir(parents=True, exist_ok=True)
    
    (src_pages / "Index.tsx").write_text(
        "export default function Index() { return <div>Página Inicial</div>; }\n",
        encoding="utf-8"
    )
    (src_pages / "Tarefas.tsx").write_text(
        "export default function Tarefas() { return <div>Lista de Tarefas</div>; }\n",
        encoding="utf-8"
    )
    
    (origem_dir / "src" / "App.tsx").write_text(
        'import { Routes, Route } from "react-router-dom";\n'
        'import Index from "./pages/Index";\n'
        'import Tarefas from "./pages/Tarefas";\n'
        'export default function App() {\n'
        '  return (\n'
        '    <Routes>\n'
        '      <Route path="/" element={<Index />} />\n'
        '      <Route path="/tarefas" element={<Tarefas />} />\n'
        '    </Routes>\n'
        '  );\n'
        '}\n',
        encoding="utf-8"
    )
    
    migrations = origem_dir / "supabase" / "migrations"
    migrations.mkdir(parents=True, exist_ok=True)
    (migrations / "001_create_tarefas.sql").write_text(
        "CREATE TABLE IF NOT EXISTS public.tarefas (\n"
        "  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n"
        "  titulo TEXT NOT NULL,\n"
        "  concluida BOOLEAN DEFAULT false,\n"
        "  criado_em TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL\n"
        ");\n",
        encoding="utf-8"
    )

def executar_fluxo(cmd: list, label: str) -> dict:
    log(f"Iniciando: {label}")
    t0 = time.time()
    res = subprocess.run(cmd, cwd=str(ROOT_DIR), text=True)
    duracao = round(time.time() - t0, 1)
    status = "SUCESSO" if res.returncode == 0 else f"FALHA (rc={res.returncode})"
    log(f"Finalizado {label} em {duracao}s com status: {status}")
    return {
        "fluxo": label,
        "rc": res.returncode,
        "status": status,
        "duracao_segundos": duracao
    }

def main():
    log("Iniciando bateria sequencial autônoma dos 3 fluxos da Tríade...")
    
    if BASE_TEMP.exists():
        log(f"Limpando diretório temporário anterior: {BASE_TEMP}")
        try:
            shutil.rmtree(BASE_TEMP, ignore_errors=True)
        except Exception as e:
            log(f"Aviso ao limpar pasta: {e}")
            
    BASE_TEMP.mkdir(parents=True, exist_ok=True)
    
    resultados = []
    
    # -------------------------------------------------------------
    # 1. FLUXO 01 — PURE (Do Zero)
    # -------------------------------------------------------------
    dir_pure = BASE_TEMP / "fluxo_01_pure"
    cmd_pure = [
        sys.executable, "ecossistema.py", "run-fluxo",
        "--fluxo", "pure",
        "--nome", "Mini App Pure",
        "--slug", "mini-app-pure",
        "--dominio", "tasks",
        "--pasta", str(dir_pure),
        "--modo-intake", "autonomo",
        "--mobbin", "1"
    ]
    r1 = executar_fluxo(cmd_pure, "Fluxo 01 - AIDD-PURE")
    resultados.append(r1)
    
    # -------------------------------------------------------------
    # 2. FLUXO 02 — OPEN (Motores Abertos)
    # -------------------------------------------------------------
    dir_open = BASE_TEMP / "fluxo_02_open"
    cmd_open = [
        sys.executable, "ecossistema.py", "run-fluxo",
        "--fluxo", "open",
        "--nome", "Mini App Open",
        "--slug", "mini-app-open",
        "--dominio", "crm",
        "--pasta", str(dir_open),
        "--modo-intake", "autonomo",
        "--mobbin", "1"
    ]
    r2 = executar_fluxo(cmd_open, "Fluxo 02 - AIDD-OPEN")
    resultados.append(r2)
    
    # -------------------------------------------------------------
    # 3. FLUXO 03 — FREEDOM (Desacoplamento Low-Code)
    # -------------------------------------------------------------
    origem_freedom = BASE_TEMP / "origem_freedom"
    preparar_origem_freedom(origem_freedom)
    dir_freedom = BASE_TEMP / "fluxo_03_freedom"
    
    cmd_freedom = [
        sys.executable, "ecossistema.py", "run-fluxo",
        "--fluxo", "freedom",
        "--origem", str(origem_freedom),
        "--pasta", str(dir_freedom),
        "--nome", "Mini App Freedom",
        "--slug", "mini-app-freedom",
        "--dominio", "tarefas",
        "--modo-intake", "autonomo",
        "--mobbin", "1"
    ]
    r3 = executar_fluxo(cmd_freedom, "Fluxo 03 - AIDD-FREEDOM")
    resultados.append(r3)
    
    # -------------------------------------------------------------
    # Consolidação do Relatório
    # -------------------------------------------------------------
    relatorio_md = BASE_TEMP / "RELATORIO_FINAL_TRIADE.md"
    linhas = [
        "# Relatório da Execução Autônoma da Tríade AIDD\n",
        f"**Diretório Base:** `{BASE_TEMP}`\n",
        "| Fluxo | Duração (s) | Código de Saída | Status |",
        "|---|---|---|---|"
    ]
    for r in resultados:
        linhas.append(f"| {r['fluxo']} | {r['duracao_segundos']}s | {r['rc']} | **{r['status']}** |")
    
    linhas.append("\n## Verificação de Artefatos Gerados:")
    for nome, d in [("Fluxo 01 (Pure)", dir_pure), ("Fluxo 02 (Open)", dir_open), ("Fluxo 03 (Freedom)", dir_freedom)]:
        linhas.append(f"\n### {nome}")
        if d.exists():
            itens = [p.name for p in d.iterdir() if not p.name.startswith(".")]
            linhas.append(f"- **Pasta:** `{d}`")
            linhas.append(f"- **Itens principais:** {', '.join(itens[:10])}")
        else:
            linhas.append("- Diretório não encontrado!")
            
    relatorio_md.write_text("\n".join(linhas), encoding="utf-8")
    log(f"Relatório consolidado gravado em: {relatorio_md}")
    
    # Grava flag de conclusão e emite sinal de término
    flag = ROOT_DIR / ".aidd" / "PIPELINE_CONCLUIDO.flag"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text("Bateria da Tríade concluída com sucesso.", encoding="utf-8")
    
    print("\n" + "=" * 60)
    print("🛑 [TERMINATION_SIGNAL] BATERIA DA TRÍADE CONCLUÍDA")
    print("=" * 60, flush=True)

if __name__ == "__main__":
    main()
