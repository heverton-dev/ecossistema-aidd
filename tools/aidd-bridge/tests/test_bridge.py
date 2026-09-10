# -*- coding: utf-8 -*-
import os
import json
import tempfile
import pytest
from aidd_bridge.scanner import LovableScanner
from aidd_bridge.data_bridge import DataBridge
from aidd_bridge.devops import DevOpsPackager
from aidd_bridge.unifier import MultiAppUnifier

@pytest.fixture
def mock_lovable_project(tmp_path):
    proj = tmp_path / "mock-app"
    proj.mkdir()
    
    # package.json
    pkg = {
        "name": "mock-lovable",
        "version": "1.0.0",
        "dependencies": {"react": "^18.2.0", "@supabase/supabase-js": "^2.39.0"}
    }
    (proj / "package.json").write_text(json.dumps(pkg), encoding="utf-8")

    # src/App.tsx com rotas
    src = proj / "src"
    src.mkdir()
    (src / "App.tsx").write_text("""
    import { Route, Routes } from "react-router-dom";
    export default function App() {
        return (
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
        );
    }
    """, encoding="utf-8")

    # migrations
    mig = proj / "supabase" / "migrations"
    mig.mkdir(parents=True)
    (mig / "20260101_init.sql").write_text("""
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "supabase_vault";
    CREATE TABLE users (id UUID PRIMARY KEY, name TEXT);
    ALTER PUBLICATION supabase_realtime ADD TABLE users;
    """, encoding="utf-8")

    return str(proj)

def test_scanner(mock_lovable_project):
    scanner = LovableScanner(mock_lovable_project)
    manifest = scanner.scan()
    assert manifest["package_info"]["name"] == "mock-lovable"
    assert len(manifest["routes"]) == 2
    assert manifest["database"]["has_supabase"] is True
    assert len(manifest["database"]["migrations"]) == 1

def test_data_bridge(mock_lovable_project):
    scanner = LovableScanner(mock_lovable_project)
    manifest = scanner.scan()
    bridge = DataBridge(manifest["database"]["migrations"])
    sql = bridge.generate_consolidated_init_sql()
    assert "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" in sql
    assert "-- [AIDD-BRIDGE REMOVED PROPRIETARY CLOUD HOOK]" in sql
    assert "ALTER PUBLICATION supabase_realtime" in sql

def test_devops_packager(tmp_path):
    packager = DevOpsPackager(str(tmp_path), domain="app.meusite.com")
    files = packager.export_all()
    assert "Dockerfile" in files
    assert "docker-compose.yml" in files
    assert "Caddyfile" in files
    assert os.path.exists(files["docker-compose.yml"])
    
    compose_content = open(files["docker-compose.yml"], encoding="utf-8").read()
    assert "postgrest" in compose_content
    assert "postgres:16-alpine" in compose_content

def test_unifier(mock_lovable_project, tmp_path):
    out = tmp_path / "unified-app"
    unifier = MultiAppUnifier([mock_lovable_project], str(out))
    res = unifier.merge()
    assert res["status"] == "success"
    assert os.path.exists(out / "package.json")
    assert os.path.exists(out / "src" / "AppMasterRouter.tsx")