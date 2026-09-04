import os, sys, re, json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[\s_-]+', '_', text)

def criar_modulo(nome_modulo, descricao=""):
    slug = slugify(nome_modulo)
    module_dir = os.path.join("src", "modules", slug)
    
    if os.path.exists(module_dir):
        print(f"[WARN] O modulo '{slug}' ja existe em: {module_dir}")
        return
        
    print(f"[AIDD] Gerando novo modulo desacoplado: '{slug}'...")
    os.makedirs(module_dir, exist_ok=True)
    open(os.path.join(module_dir, "__init__.py"), "w").close()
    
    # 1. models.py
    models_code = '''import sqlite3

def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS mod_''' + slug + ''' (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            dados_json TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_''' + slug + '''_ativo ON mod_''' + slug + '''(ativo);
    """)
    conn.commit()
'''
    with open(os.path.join(module_dir, "models.py"), "w", encoding="utf-8") as f:
        f.write(models_code)
        
    # 2. services.py
    services_code = '''import json
from core.database import Database
from core.events import EventBus

class ''' + slug.capitalize() + '''Service:
    def __init__(self, db: Database, events: EventBus = None):
        self.db = db
        self.events = events

    def listar(self, apenas_ativos: bool = True):
        with self.db.get_connection() as conn:
            query = "SELECT * FROM mod_''' + slug + '''"
            if apenas_ativos:
                query += " WHERE ativo = 1"
            query += " ORDER BY id DESC"
            rows = conn.execute(query).fetchall()
            return [dict(r) for r in rows]

    def criar(self, titulo: str, dados: dict = None):
        dados_dict = dados if dados is not None else {}
        with self.db.get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO mod_''' + slug + ''' (titulo, dados_json) VALUES (?, ?)",
                (titulo.strip(), json.dumps(dados_dict))
            )
            conn.commit()
            novo_id = cur.lastrowid
            if self.events:
                self.events.emit("''' + slug + '''_criado", {"id": novo_id, "titulo": titulo})
            return {"sucesso": True, "id": novo_id, "titulo": titulo}

    def deletar(self, item_id: int):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM mod_''' + slug + ''' WHERE id = ?", (item_id,))
            conn.commit()
            if self.events:
                self.events.emit("''' + slug + '''_deletado", {"id": item_id})
            return {"sucesso": True}
'''
    with open(os.path.join(module_dir, "services.py"), "w", encoding="utf-8") as f:
        f.write(services_code)

    # 3. routes.py
    routes_code = '''from core.openapi import RouteRegistry

registry = RouteRegistry()

def registrar_rotas(service):
    @registry.get("/api/''' + slug + '''", summary="Lista todos os itens do modulo ''' + slug + '''")
    def listar(params):
        return service.listar()

    @registry.post("/api/''' + slug + '''", summary="Cria um novo item no modulo ''' + slug + '''")
    def criar(data):
        return service.criar(data.get("titulo", ""), data.get("dados", {}))

    @registry.post("/api/''' + slug + '''/deletar", summary="Remove um item do modulo ''' + slug + '''")
    def deletar(data):
        return service.deletar(int(data.get("id", 0)))
'''
    with open(os.path.join(module_dir, "routes.py"), "w", encoding="utf-8") as f:
        f.write(routes_code)

    # 4. Componente Visual
    comp_dir = os.path.join("src", "static", "components")
    os.makedirs(comp_dir, exist_ok=True)
    comp_html = '''<div class="card module-card" id="module-''' + slug + '''">
    <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <h3 style="font-size: 1.2rem; font-weight: 700; color: #f8fafc;">''' + slug.capitalize() + '''</h3>
        <span class="card-tag" style="position: static;">Modulo Ativo</span>
    </div>
    <div class="card-body" id="''' + slug + '''-items-container">
        <p style="color: var(--text-muted); font-size: 0.9rem;">Carregando dados do modulo ''' + slug + '''...</p>
    </div>
    <div style="margin-top: 1rem; display: flex; gap: 0.5rem;">
        <input type="text" id="input-''' + slug + '''-novo" placeholder="Novo ''' + slug + '''..." style="flex: 1; padding: 0.6rem 1rem; border-radius: 8px; border: 1px solid var(--border-subtle); background: #060911; color: #fff;">
        <button class="btn btn-gold" onclick="adicionarItem''' + slug.capitalize() + '''()">Adicionar</button>
    </div>
</div>
'''
    with open(os.path.join(comp_dir, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(comp_html)

    # 5. Testes Unitários
    test_dir = os.path.join("tests", "unit")
    os.makedirs(test_dir, exist_ok=True)
    test_code = '''import pytest, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from core.database import Database
from core.events import EventBus
from modules.''' + slug + '''.services import ''' + slug.capitalize() + '''Service
from modules.''' + slug + '''.models import init_schema

def test_modulo_''' + slug + '''(tmp_path):
    db_file = str(tmp_path / "test_''' + slug + '''.db")
    db = Database(db_file)
    with db.get_connection() as conn:
        init_schema(conn)
        
    events = EventBus()
    eventos_recebidos = []
    events.on("''' + slug + '''_criado", lambda d: eventos_recebidos.append(d))

    service = ''' + slug.capitalize() + '''Service(db, events)
    
    # Criar
    res = service.criar("Item Teste ''' + slug.capitalize() + '''", {"valor": 100})
    assert res["sucesso"] is True
    assert len(eventos_recebidos) == 1
    
    # Listar
    itens = service.listar()
    assert len(itens) == 1
    assert itens[0]["titulo"] == "Item Teste ''' + slug.capitalize() + '''"
    
    # Deletar
    del_res = service.deletar(res["id"])
    assert del_res["sucesso"] is True
    assert len(service.listar()) == 0
'''
    with open(os.path.join(test_dir, f"test_{slug}.py"), "w", encoding="utf-8") as f:
        f.write(test_code)

    print(f"[OK] Modulo '{slug}' 100% gerado com rotas, regras, eventos, testes e UI Impeccable!")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python scripts/add_module.py <nome_do_modulo> [descricao]")
        sys.exit(1)
    criar_modulo(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
