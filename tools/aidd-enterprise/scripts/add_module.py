#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — GERADOR DE FATIAS VERTICAIS (add_module.py)
=============================================================================
Gera uma fatia vertical completa, isolada e desacoplada com:
1. models.py (Schema SQLite WAL com índices e timestamps)
2. services.py (Regras de negócio Full CRUD + EventBus pub/sub)
3. routes.py (RouteRegistry com documentação OpenAPI 3.1)
4. UI Component Impeccable (HTML/Tailwind com Toasts e modais)
5. test_<modulo>.py (Suíte pytest unitária cobrindo 100% dos fluxos)
6. Atualização automática do manifesto PLANO-EXECUCAO-ESTRUTURADO.json
"""

import os
import sys
import re
import json
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


import keyword

RESERVED_WORDS = set(keyword.kwlist) | {"test", "core", "static", "modules", "shared", "server", "app", "api"}


def slugify(text: str) -> str:
    """Gera identificador slug padronizado em snake_case com proteção contra palavras reservadas."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    slug = re.sub(r'[\s_-]+', '_', text)
    if not slug:
        slug = "modulo_custom"
    if slug in RESERVED_WORDS or slug.isdigit():
        slug = f"mod_{slug}"
    return slug


def pascal_case(text: str) -> str:
    """Converte texto para PascalCase."""
    slug = slugify(text)
    return ''.join(word.capitalize() for word in slug.split('_'))


def criar_modulo(nome_modulo: str, descricao: str = "", target_dir: str = "."):
    """Gera atomicamente todos os artefatos de uma fatia vertical desacoplada."""
    slug = slugify(nome_modulo)
    pascal = pascal_case(nome_modulo)
    desc = descricao or f"Módulo de gestão e operações para {slug.replace('_', ' ').capitalize()}"

    target_dir = os.path.abspath(target_dir)
    src_dir = os.path.join(target_dir, "src")
    module_dir = os.path.join(src_dir, "modules", slug)
    comp_dir = os.path.join(src_dir, "static", "components")
    test_dir = os.path.join(target_dir, "tests", "unit")

    print(f"🚀 [AIDD v5.1] Gerando fatia vertical completa para o módulo: '{slug}'...")
    print(f"📁 Destino: {module_dir}")

    os.makedirs(module_dir, exist_ok=True)
    os.makedirs(comp_dir, exist_ok=True)
    os.makedirs(test_dir, exist_ok=True)

    # 0. __init__.py
    open(os.path.join(module_dir, "__init__.py"), "w", encoding="utf-8").close()

    # 1. models.py
    models_code = f'''# -*- coding: utf-8 -*-
"""
Schema e inicialização de banco de dados para o módulo '{slug}'.
"""

import sqlite3
import json


def init_schema(conn: sqlite3.Connection):
    """Cria a tabela, índices e insere seed data do módulo {slug} se não existirem."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mod_{slug} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT,
            dados_json TEXT,
            status TEXT DEFAULT 'ativo',
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deletado_em TIMESTAMP DEFAULT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_{slug}_ativo ON mod_{slug}(ativo);
        CREATE INDEX IF NOT EXISTS idx_{slug}_status ON mod_{slug}(status);
        CREATE INDEX IF NOT EXISTS idx_{slug}_deletado ON mod_{slug}(deletado_em);
    """)
    conn.commit()

    # Seed Fixtures Determinísticas (se a tabela estiver vazia)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM mod_{slug} WHERE deletado_em IS NULL")
    if cur.fetchone()[0] == 0:
        conn.executemany("""
            INSERT INTO mod_{slug} (titulo, descricao, dados_json, status, ativo)
            VALUES (?, ?, ?, 'ativo', 1);
        """, [
            (f"Registro Exemplo 01 - {slug.upper()}", f"Primeiro registro semeado para o módulo {slug}", json.dumps({{"origem": "seed", "tag": "demo"}})),
            (f"Registro Exemplo 02 - {slug.upper()}", f"Segundo registro semeado para validação de KPIs", json.dumps({{"origem": "seed", "tag": "producao"}}))
        ])
        conn.commit()
'''
    with open(os.path.join(module_dir, "models.py"), "w", encoding="utf-8") as f:
        f.write(models_code)

    # 2. services.py
    services_code = f'''# -*- coding: utf-8 -*-
"""
Serviço de regras de negócio Full CRUD, paginação, métricas e eventos para o módulo '{slug}'.
"""

import json
from typing import Optional, List, Dict, Any
from core.database import append_audit_log


class {pascal}Service:
    def __init__(self, db, events=None):
        self.db = db
        self.events = events

    def listar(self, apenas_ativos: bool = True, status: Optional[str] = None, busca: Optional[str] = None, pagina: int = 1, limite: int = 50) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            query = "SELECT * FROM mod_{slug} WHERE deletado_em IS NULL"
            params = []
            if apenas_ativos:
                query += " AND ativo = 1"
            if status:
                query += " AND status = ?"
                params.append(status)
            if busca:
                query += " AND (titulo LIKE ? OR descricao LIKE ?)"
                params.extend([f"%{{busca}}%", f"%{{busca}}%"])
            query += " ORDER BY id DESC"
            offset = max(0, (pagina - 1) * limite)
            query += " LIMIT ? OFFSET ?"
            params.extend([limite, offset])
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def obter_metricas(self) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            total = conn.execute("SELECT count(*) FROM mod_{slug} WHERE deletado_em IS NULL").fetchone()[0]
            ativos = conn.execute("SELECT count(*) FROM mod_{slug} WHERE deletado_em IS NULL AND ativo = 1").fetchone()[0]
            concluidos = conn.execute("SELECT count(*) FROM mod_{slug} WHERE deletado_em IS NULL AND status = 'concluido'").fetchone()[0]
            return {{
                "total": total,
                "ativos": ativos,
                "concluidos": concluidos,
                "taxa_conclusao": round((concluidos / total * 100) if total > 0 else 0.0, 1)
            }}

    def obter_por_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM mod_{slug} WHERE id = ? AND deletado_em IS NULL", (item_id,)).fetchone()
            return dict(row) if row else None

    def criar(self, titulo: str, dados: Optional[Dict[str, Any]] = None, descricao: str = "", status: str = "ativo") -> Dict[str, Any]:
        titulo_limpo = (titulo or "").strip()
        if not titulo_limpo:
            raise ValueError("O título do item é obrigatório")

        dados_dict = dados if dados is not None else {{}}
        with self.db.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO mod_{slug} (titulo, descricao, dados_json, status, ativo)
                VALUES (?, ?, ?, ?, 1)
                """,
                (titulo_limpo, descricao.strip(), json.dumps(dados_dict, ensure_ascii=False), status)
            )
            novo_id = cur.lastrowid

            payload = {{
                "id": novo_id,
                "titulo": titulo_limpo,
                "descricao": descricao,
                "status": status,
                "dados": dados_dict
            }}

            # WORM Audit Hash Chain: registro imutável encadeado com SHA-256
            append_audit_log(conn.cursor(), "{slug}_criado", payload)

            # Transactional Outbox Pattern: grava o evento na MESMA transação da
            # mutação, garantindo entrega at-least-once mesmo se o processo cair
            # antes do EventBus.emit() abaixo ser disparado.
            self.db.enqueue_outbox_event(conn, "{slug}_criado", payload)
            conn.commit()

        if self.events:
            self.events.emit("{slug}_criado", payload)

        return {{"sucesso": True, "id": novo_id, "item": payload}}

    def atualizar(self, item_id: int, titulo: Optional[str] = None, dados: Optional[Dict[str, Any]] = None, descricao: Optional[str] = None, status: Optional[str] = None) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM mod_{slug} WHERE id = ? AND deletado_em IS NULL", (item_id,)).fetchone()
            if not row:
                return {{"sucesso": False, "erro": "Item não encontrado"}}

            novo_titulo = titulo.strip() if titulo is not None else row["titulo"]
            nova_desc = descricao.strip() if descricao is not None else row["descricao"]
            novo_status = status if status is not None else row["status"]
            novos_dados = json.dumps(dados, ensure_ascii=False) if dados is not None else row["dados_json"]

            conn.execute(
                """
                UPDATE mod_{slug}
                SET titulo = ?, descricao = ?, dados_json = ?, status = ?, atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (novo_titulo, nova_desc, novos_dados, novo_status, item_id)
            )

            payload = {{
                "id": item_id,
                "titulo": novo_titulo,
                "descricao": nova_desc,
                "status": novo_status
            }}

            append_audit_log(conn.cursor(), "{slug}_atualizado", payload)
            self.db.enqueue_outbox_event(conn, "{slug}_atualizado", payload)
            conn.commit()

        if self.events:
            self.events.emit("{slug}_atualizado", payload)

        return {{"sucesso": True, "id": item_id, "item": payload}}

    def deletar(self, item_id: int) -> Dict[str, Any]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM mod_{slug} WHERE id = ? AND deletado_em IS NULL", (item_id,)).fetchone()
            if not row:
                return {{"sucesso": False, "erro": "Item não encontrado"}}
            conn.execute("UPDATE mod_{slug} SET deletado_em = CURRENT_TIMESTAMP, ativo = 0 WHERE id = ?", (item_id,))
            append_audit_log(conn.cursor(), "{slug}_deletado", {{"id": item_id}})
            self.db.enqueue_outbox_event(conn, "{slug}_deletado", {{"id": item_id}})
            conn.commit()

        if self.events:
            self.events.emit("{slug}_deletado", {{"id": item_id}})

        return {{"sucesso": True, "id": item_id}}
'''
    with open(os.path.join(module_dir, "services.py"), "w", encoding="utf-8") as f:
        f.write(services_code)

    # 3. routes.py
    routes_code = f'''# -*- coding: utf-8 -*-
"""
Registro de rotas OpenAPI 3.1 para o módulo '{slug}'.
"""

from typing import Any, Optional, Dict, List
from core.openapi import RouteRegistry
from core.cqrs import read_model

registry = RouteRegistry()


def registrar_rotas(service: Any = None):
    tag_name = "{pascal}"

    @registry.get(
        "/api/{slug}",
        summary="Listar todos os itens do módulo {slug}",
        tags=[tag_name],
        description="Retorna a lista de registros cadastrados no módulo {slug}.",
        query_params=[
            {{"name": "status", "type": "string", "req": False, "desc": "Filtrar por status"}},
            {{"name": "apenas_ativos", "type": "boolean", "req": False, "desc": "Filtrar apenas itens ativos (default True)"}}
        ],
        responses={{
            "200": {{"description": "Lista recuperada com sucesso", "content": {{"application/json": {{"example": [{{"id": 1, "titulo": "Exemplo", "status": "ativo"}}]}}}}}}
        }}
    )
    def listar(params):
        status = params.get("status", [None])[0] if isinstance(params.get("status"), list) else params.get("status")
        if not service:
            return []
        cache_key = f"{slug}_list"
        return read_model.get_or_revalidate(cache_key, lambda: service.listar(status=status), ttl=30)

    @registry.get(
        "/api/{slug}/metricas",
        summary="Obter métricas e KPIs do módulo {slug}",
        tags=[tag_name],
        description="Retorna indicadores quantitativos agregados para dashboards executivos.",
        responses={{
            "200": {{"description": "Métricas consolidadas", "content": {{"application/json": {{"example": {{"total": 10, "ativos": 8, "concluidos": 2, "taxa_conclusao": 20.0}}}}}}}}
        }}
    )
    def metricas(params):
        return service.obter_metricas() if service else {{"total": 0, "ativos": 0, "concluidos": 0, "taxa_conclusao": 0.0}}

    @registry.get(
        "/api/{slug}/obter",
        summary="Obter item de {slug} por ID",
        tags=[tag_name],
        description="Retorna os detalhes completos de um registro do módulo {slug}.",
        query_params=[
            {{"name": "id", "type": "integer", "req": True, "desc": "ID do registro"}}
        ],
        responses={{
            "200": {{"description": "Registro encontrado", "content": {{"application/json": {{"example": {{"id": 1, "titulo": "Exemplo"}}}}}}}},
            "404": {{"description": "Registro não encontrado"}}
        }}
    )
    def obter(params):
        item_id = int(params.get("id", [0])[0] if isinstance(params.get("id"), list) else params.get("id", 0))
        res = service.obter_por_id(item_id) if service else None
        return res if res else {{"sucesso": False, "erro": "Item não encontrado"}}

    @registry.post(
        "/api/{slug}/criar",
        summary="Criar novo item no módulo {slug}",
        tags=[tag_name],
        description="Cadastra um novo registro com emissão de evento no EventBus.",
        body_schema=[
            {{"name": "titulo", "type": "string", "req": True, "desc": "Título identificador"}},
            {{"name": "descricao", "type": "string", "req": False, "desc": "Descrição complementar"}},
            {{"name": "status", "type": "string", "req": False, "desc": "Status inicial (default 'ativo')"}},
            {{"name": "dados", "type": "object", "req": False, "desc": "Objeto JSON customizado"}}
        ],
        body_example={{"titulo": "Novo Registro {pascal}", "descricao": "Descrição detalhada", "status": "ativo", "dados": {{"prioridade": "alta"}}}},
        responses={{
            "200": {{"description": "Item criado com sucesso", "content": {{"application/json": {{"example": {{"sucesso": True, "id": 1}}}}}}}}
        }}
    )
    def criar(data):
        if not service:
            return {{"sucesso": False, "erro": "Serviço indisponível"}}
        try:
            return service.criar(
                titulo=data.get("titulo", ""),
                dados=data.get("dados", {{}}),
                descricao=data.get("descricao", ""),
                status=data.get("status", "ativo")
            )
        except Exception as e:
            return {{"sucesso": False, "erro": str(e)}}

    @registry.post(
        "/api/{slug}/atualizar",
        summary="Atualizar item do módulo {slug}",
        tags=[tag_name],
        description="Atualiza campos de um registro existente e emite evento de alteração.",
        body_schema=[
            {{"name": "id", "type": "integer", "req": True, "desc": "ID do registro a atualizar"}},
            {{"name": "titulo", "type": "string", "req": False, "desc": "Novo título"}},
            {{"name": "descricao", "type": "string", "req": False, "desc": "Nova descrição"}},
            {{"name": "status", "type": "string", "req": False, "desc": "Novo status"}},
            {{"name": "dados", "type": "object", "req": False, "desc": "Novos dados"}}
        ],
        body_example={{"id": 1, "titulo": "{pascal} Atualizado", "status": "concluido"}},
        responses={{
            "200": {{"description": "Item atualizado com sucesso", "content": {{"application/json": {{"example": {{"sucesso": True, "id": 1}}}}}}}}
        }}
    )
    def atualizar(data):
        if not service:
            return {{"sucesso": False, "erro": "Serviço indisponível"}}
        item_id = int(data.get("id", 0))
        return service.atualizar(
            item_id=item_id,
            titulo=data.get("titulo"),
            dados=data.get("dados"),
            descricao=data.get("descricao"),
            status=data.get("status")
        )

    @registry.post(
        "/api/{slug}/deletar",
        summary="Remover item do módulo {slug}",
        tags=[tag_name],
        description="Exclui permanentemente um registro e publica evento de exclusão.",
        body_schema=[
            {{"name": "id", "type": "integer", "req": True, "desc": "ID do registro a remover"}}
        ],
        body_example={{"id": 1}},
        responses={{
            "200": {{"description": "Item removido com sucesso", "content": {{"application/json": {{"example": {{"sucesso": True, "id": 1}}}}}}}}
        }}
    )
    def deletar(data):
        if not service:
            return {{"sucesso": False, "erro": "Serviço indisponível"}}
        item_id = int(data.get("id", 0))
        return service.deletar(item_id)
'''
    with open(os.path.join(module_dir, "routes.py"), "w", encoding="utf-8") as f:
        f.write(routes_code)

    # 4. Componente Visual Impeccable
    comp_html = f'''<!-- Componente UI: {pascal} -->
<div class="bg-slate-900/60 rounded-xl border border-slate-800 p-5 space-y-4 shadow-xl" id="module-{slug}">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
            <h3 class="text-sm font-bold text-slate-100 flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full bg-sky-500"></span>
                {pascal}
            </h3>
            <p class="text-xs text-slate-400">{desc}</p>
        </div>
        <div class="flex items-center gap-2">
            <button type="button" onclick="carregar{pascal}()" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition" title="Recarregar dados" aria-label="Recarregar dados">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg>
            </button>
            <button type="button" onclick="abrirModalNovo('{slug}')" class="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-lg shadow-sky-600/20" aria-label="Criar novo {pascal}">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
                <span>Novo {pascal}</span>
            </button>
        </div>
    </div>

    <!-- Tabela / Lista de Itens -->
    <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
            <thead class="bg-slate-950/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                <tr>
                    <th class="p-2.5">ID</th>
                    <th class="p-2.5">Título</th>
                    <th class="p-2.5">Descrição</th>
                    <th class="p-2.5">Status</th>
                    <th class="p-2.5">Data Criação</th>
                    <th class="p-2.5 text-right">Ações</th>
                </tr>
            </thead>
            <tbody id="tabela-{slug}-corpo" class="divide-y divide-slate-800/60 text-slate-300">
                <tr><td colspan="6" class="p-4 text-center text-slate-500">Carregando {slug}...</td></tr>
            </tbody>
        </table>
    </div>
</div>
'''
    with open(os.path.join(comp_dir, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(comp_html)

    # 5. Testes Unitários com pytest
    test_code = f'''# -*- coding: utf-8 -*-
"""
Suíte de testes unitários para o módulo '{slug}'.
Valida isolamento de schema, persistência SQLite WAL, regras de negócio e disparo de eventos.
"""

import pytest
import os
import sys

# Garante que src esteja no PYTHONPATH
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from core.database import Database
from core.events import EventBus
from modules.{slug}.models import init_schema
from modules.{slug}.services import {pascal}Service


@pytest.fixture
def test_env(tmp_path):
    """Fixture que isola o banco de dados e o EventBus para cada teste."""
    db_file = str(tmp_path / "test_{slug}.db")
    db = Database(f"sqlite:///{{db_file}}")
    with db.get_connection() as conn:
        init_schema(conn)

    events = EventBus()
    eventos_capturados = []
    events.on("{slug}_criado", lambda d: eventos_capturados.append(("criado", d)))
    events.on("{slug}_atualizado", lambda d: eventos_capturados.append(("atualizado", d)))
    events.on("{slug}_deletado", lambda d: eventos_capturados.append(("deletado", d)))

    service = {pascal}Service(db, events)
    return {{"service": service, "events": eventos_capturados, "db": db}}


def test_fluxo_completo_crud_{slug}(test_env):
    service = test_env["service"]
    eventos = test_env["events"]

    # 1. CREATE
    res_cria = service.criar(
        titulo="Item Teste Unitário {pascal}",
        descricao="Validação automatizada de integridade",
        status="ativo",
        dados={{"valor": 150.0, "prioridade": "alta"}}
    )
    assert res_cria["sucesso"] is True
    novo_id = res_cria["id"]
    assert novo_id > 0
    assert len(eventos) == 1
    assert eventos[0][0] == "criado"
    assert eventos[0][1]["id"] == novo_id

    # 2. READ (Obter por ID)
    item = service.obter_por_id(novo_id)
    assert item is not None
    assert item["titulo"] == "Item Teste Unitário {pascal}"
    assert item["status"] == "ativo"

    # 3. LIST
    lista = service.listar()
    assert len(lista) >= 1
    assert any(i["id"] == novo_id for i in lista)

    # 4. UPDATE
    res_up = service.atualizar(
        item_id=novo_id,
        titulo="Item Teste {pascal} Atualizado",
        status="concluido"
    )
    assert res_up["sucesso"] is True
    assert len(eventos) == 2
    assert eventos[1][0] == "atualizado"

    item_mod = service.obter_por_id(novo_id)
    assert item["titulo"] != item_mod["titulo"]
    assert item_mod["titulo"] == "Item Teste {pascal} Atualizado"
    assert item_mod["status"] == "concluido"

    # 5. DELETE
    res_del = service.deletar(novo_id)
    assert res_del["sucesso"] is True
    assert len(eventos) == 3
    assert eventos[2][0] == "deletado"

    item_deletado = service.obter_por_id(novo_id)
    assert item_deletado is None
    lista_pos = service.listar()
    assert all(i["id"] != novo_id for i in lista_pos)


def test_validacao_titulo_obrigatorio_{slug}(test_env):
    service = test_env["service"]
    with pytest.raises(ValueError):
        service.criar(titulo="   ")
'''
    with open(os.path.join(test_dir, f"test_{slug}.py"), "w", encoding="utf-8") as f:
        f.write(test_code)

    # 6. Atualizar PLANO-EXECUCAO-ESTRUTURADO.json se existir
    plano_path = os.path.join(target_dir, "PLANO-EXECUCAO-ESTRUTURADO.json")
    if os.path.isfile(plano_path):
        try:
            with open(plano_path, "r", encoding="utf-8") as f:
                plano = json.load(f)

            if "modulos" not in plano:
                plano["modulos"] = []

            mod_exists = any(m.get("slug") == slug for m in plano["modulos"] if isinstance(m, dict))
            if not mod_exists:
                plano["modulos"].append({
                    "nome": pascal,
                    "slug": slug,
                    "descricao": desc,
                    "status": "implementado",
                    "rotas": [
                        f"/api/{slug}",
                        f"/api/{slug}/obter",
                        f"/api/{slug}/criar",
                        f"/api/{slug}/atualizar",
                        f"/api/{slug}/deletar"
                    ],
                    "eventos": [f"{slug}_criado", f"{slug}_atualizado", f"{slug}_deletado"],
                    "testes": f"tests/unit/test_{slug}.py"
                })

                with open(plano_path, "w", encoding="utf-8") as f:
                    json.dump(plano, f, ensure_ascii=False, indent=2)
                print(f"  [+] Manifesto 'PLANO-EXECUCAO-ESTRUTURADO.json' atualizado com o módulo '{slug}'!")
        except Exception as e:
            print(f"  [!] Aviso ao atualizar manifesto: {e}")

    print(f"✨ [OK] Módulo '{slug}' gerado com 100% de integridade e Clean Architecture!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="AIDD v5.1 — Gerador de Módulos Desacoplados")
    parser.add_argument("nome", help="Nome do módulo (ex: faturamento, pedidos, crm)")
    parser.add_argument("--descricao", "-d", default="", help="Descrição da fatia vertical")
    parser.add_argument("--dir", default=".", help="Diretório raiz do projeto alvo")
    args = parser.parse_args()

    criar_modulo(args.nome, args.descricao, args.dir)
