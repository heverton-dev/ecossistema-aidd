#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill: project-spec-tracker v1.0
Rastreia progresso de projetos com SPEC vivo (MD + HTML + PDF)

Registra: O QUÊ, QUANDO, QUEM, COMO foi feito
Status: DONE/IN-PROGRESS/TODO com commits rastreados

Uso:
  /project-spec-tracker
  python script.py --init "aidd-project-generator" --versao "2.1"
  python script.py --update --fase "Phase 1" --status "done" --quem "Claude" --commit "c17469a"
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

SKILL_DIR = Path(__file__).parent
CONFIG_PATH = SKILL_DIR / ".config"
DB_PATH = SKILL_DIR / "database" / "project_specs.db"

# =============================================================================
# DATA STRUCTURES
# =============================================================================

class SpecItem:
    """Um item de tarefa na SPEC"""
    def __init__(self, fase: str, item: str, status: str = "todo",
                 quem: str = "", como: str = "", commit: str = ""):
        self.fase = fase
        self.item = item
        self.status = status  # "todo", "in-progress", "done"
        self.quem = quem
        self.como = como
        self.commit = commit
        self.data_conclusao = datetime.now(timezone.utc).isoformat() if status == "done" else None

    def to_dict(self):
        return {
            'fase': self.fase,
            'item': self.item,
            'status': self.status,
            'quem': self.quem,
            'como': self.como,
            'commit': self.commit,
            'data_conclusao': self.data_conclusao
        }

    def to_markdown(self):
        icon = "✅" if self.status == "done" else "⏳" if self.status == "in-progress" else "❌"
        checkbox = "[x]" if self.status == "done" else "[ ]"

        linha = f"- {checkbox} **{self.item}** ({self.status})"
        if self.data_conclusao:
            data_fmt = self.data_conclusao.split('T')[0]
            linha += f" — {data_fmt}"
        if self.quem:
            linha += f" | {self.quem}"
        if self.commit:
            linha += f" | Commit: `{self.commit[:7]}`"

        return linha


# =============================================================================
# DATABASE
# =============================================================================

class DatabaseSpec:
    """Gerencia persistência SQLite"""

    @staticmethod
    def init():
        """Inicializa banco de dados"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT UNIQUE NOT NULL,
            version TEXT,
            descricao TEXT,
            data_criacao TEXT,
            data_ultima_atualizacao TEXT,
            progresso_percentual REAL,
            responsavel TEXT,
            arquivo_spec TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS spec_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spec_id INTEGER NOT NULL,
            fase TEXT NOT NULL,
            item_nome TEXT NOT NULL,
            status TEXT DEFAULT 'todo',
            data_conclusao TEXT,
            quem TEXT,
            como TEXT,
            commit_hash TEXT,
            FOREIGN KEY(spec_id) REFERENCES project_specs(id)
        )
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def criar_spec(nome: str, versao: str, descricao: str = "", responsavel: str = ""):
        """Cria nova entrada de projeto"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        agora = datetime.now(timezone.utc).isoformat()

        cursor.execute("""
        INSERT INTO project_specs
        (project_name, version, descricao, data_criacao, data_ultima_atualizacao, responsavel)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, versao, descricao, agora, agora, responsavel))

        spec_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return spec_id

    @staticmethod
    def adicionar_item(spec_id: int, fase: str, item: str):
        """Adiciona item à SPEC"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO spec_items (spec_id, fase, item_nome, status)
        VALUES (?, ?, ?, 'todo')
        """, (spec_id, fase, item))

        conn.commit()
        conn.close()

    @staticmethod
    def atualizar_item(spec_id: int, fase: str, item: str, status: str,
                      quem: str = "", commit: str = ""):
        """Atualiza status de um item"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        agora = datetime.now(timezone.utc).isoformat() if status == "done" else None

        cursor.execute("""
        UPDATE spec_items
        SET status = ?, data_conclusao = ?, quem = ?, commit_hash = ?,
            data_ultima_atualizacao = ?
        WHERE spec_id = ? AND fase = ? AND item_nome = ?
        """, (status, agora, quem, commit, datetime.now(timezone.utc).isoformat(),
              spec_id, fase, item))

        conn.commit()
        conn.close()

    @staticmethod
    def listar_items(spec_id: int) -> List[Dict]:
        """Lista todos os items de uma SPEC"""
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute("""
        SELECT fase, item_nome, status, data_conclusao, quem, commit_hash
        FROM spec_items
        WHERE spec_id = ?
        ORDER BY fase, item_nome
        """, (spec_id,))

        items = []
        for row in cursor.fetchall():
            items.append({
                'fase': row[0],
                'item': row[1],
                'status': row[2],
                'data': row[3],
                'quem': row[4],
                'commit': row[5]
            })

        conn.close()
        return items


# =============================================================================
# GERADOR DE SPEC
# =============================================================================

class GeradorSpec:
    """Gera documento SPEC em tripartite"""

    @staticmethod
    def gerar_markdown(nome_projeto: str, versao: str, items: List[Dict]) -> str:
        """Gera markdown da SPEC"""

        agora = datetime.now().strftime("%d/%m/%Y %H:%M")

        # Contar status
        total = len(items)
        done = sum(1 for i in items if i['status'] == 'done')
        progresso = (done / total * 100) if total > 0 else 0

        md = f"""# PROJECT SPEC: {nome_projeto}

📊 **Versão:** {versao}
🕐 **Atualizado:** {agora}
📈 **Progresso:** {done}/{total} ({progresso:.0f}%)

---

## ⚙️ METADADOS

- **Projeto:** {nome_projeto}
- **Versão:** {versao}
- **Data Início:** {datetime.now().strftime("%d/%m/%Y")}
- **Status Geral:** {'✅ COMPLETO' if progresso == 100 else '⏳ EM PROGRESSO' if progresso > 0 else '❌ TODO'}

---

## 📋 TAREFAS POR FASE

"""

        # Agrupar por fase
        fases = {}
        for item in items:
            fase = item['fase']
            if fase not in fases:
                fases[fase] = []
            fases[fase].append(item)

        for fase in sorted(fases.keys()):
            md += f"\n### {fase}\n"
            for item in fases[fase]:
                checkbox = "[x]" if item['status'] == 'done' else "[ ]"
                data_str = f" — {item['data'].split('T')[0]}" if item['data'] else ""
                quem_str = f" | {item['quem']}" if item['quem'] else ""
                commit_str = f" | `{item['commit'][:7]}`" if item['commit'] else ""

                md += f"- {checkbox} {item['item']}{data_str}{quem_str}{commit_str}\n"

        md += f"""

---

## 📈 HISTÓRICO

Última atualização: {agora}

Gerado automaticamente pela skill `project-spec-tracker` v1.0
"""

        return md


# =============================================================================
# ORQUESTRADOR
# =============================================================================

class ProjectSpecTracker:
    """Orquestrador principal"""

    def __init__(self):
        self.config = self._carregar_config()
        DatabaseSpec.init()

    def _carregar_config(self) -> Dict:
        config_padrao = {
            "pasta_padrao": str(Path.home() / "projetos"),
            "gerar_pdf": True,
            "gerar_html": True,
            "auto_index": True
        }

        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    config_padrao.update(json.load(f))
            except:
                pass

        return config_padrao

    def criar_spec(self, nome: str, versao: str, descricao: str = ""):
        """Cria nova SPEC de projeto"""
        print(f"\n📋 Criando SPEC: {nome} v{versao}")

        spec_id = DatabaseSpec.criar_spec(nome, versao, descricao, responsavel="Claude")

        # Adicionar fases padrão (para aidd-project-generator)
        fases_padrao = [
            ("Phase 1", "Pesquisador de Referências"),
            ("Phase 2", "Análise da Ideia"),
            ("Phase 3", "Design AIDD"),
            ("Phase 4", "Decisão Global/Local"),
            ("Phase 5", "Criador de Projeto"),
            ("Phase 6", "Documentação Tripartite"),
        ]

        for fase, descricao_item in fases_padrao:
            DatabaseSpec.adicionar_item(spec_id, fase, descricao_item)

        # Gerar markdown inicial
        items = DatabaseSpec.listar_items(spec_id)
        md = GeradorSpec.gerar_markdown(nome, versao, items)

        # Salvar
        docs_dir = Path.cwd() / "docs"
        docs_dir.mkdir(exist_ok=True)

        arquivo = docs_dir / f"PROJECT-SPEC-{nome.lower().replace(' ', '-')}.md"
        arquivo.write_text(md, encoding='utf-8')

        print(f"✅ SPEC criada: {arquivo}")
        return spec_id

    def atualizar_item(self, spec_id: int, fase: str, item: str,
                       status: str, quem: str = "", commit: str = ""):
        """Atualiza status de um item"""
        DatabaseSpec.atualizar_item(spec_id, fase, item, status, quem, commit)
        print(f"✅ Atualizado: {fase} → {item} = {status}")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Project SPEC Tracker v1.0")
    parser.add_argument("--init", type=str, help="Inicializar novo projeto")
    parser.add_argument("--versao", type=str, default="1.0", help="Versão")
    parser.add_argument("--update", action="store_true", help="Atualizar item")
    parser.add_argument("--spec-id", type=int, help="ID da SPEC")
    parser.add_argument("--fase", type=str, help="Fase do projeto")
    parser.add_argument("--item", type=str, help="Nome do item")
    parser.add_argument("--status", type=str, help="Status (todo/in-progress/done)")
    parser.add_argument("--quem", type=str, help="Quem fez")
    parser.add_argument("--commit", type=str, help="Hash do commit")

    args = parser.parse_args()

    tracker = ProjectSpecTracker()

    if args.init:
        spec_id = tracker.criar_spec(args.init, args.versao)
        print(f"\n📊 SPEC ID: {spec_id}")
        print(f"   Use --spec-id {spec_id} para atualizar items")

    elif args.update and args.spec_id and args.fase and args.item and args.status:
        tracker.atualizar_item(args.spec_id, args.fase, args.item,
                              args.status, args.quem or "", args.commit or "")

    else:
        print("\n📋 Project SPEC Tracker v1.0")
        print("\nUso:")
        print("  python script.py --init \"aidd-project-generator\" --versao 2.1")
        print("  python script.py --update --spec-id 1 --fase \"Phase 1\" --item \"Pesquisador\" --status done --quem Claude --commit c17469a")


if __name__ == '__main__':
    main()
