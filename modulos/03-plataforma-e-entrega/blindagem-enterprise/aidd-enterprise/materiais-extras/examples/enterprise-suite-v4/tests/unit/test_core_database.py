from core.database import Database
from core.models import init_all_schemas


def test_get_connection_applies_expected_pragmas(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'pragma.db'}")
    with db.get_connection() as conn:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_init_all_schemas_creates_expected_tables(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'schema.db'}")
    with db.get_connection() as conn:
        init_all_schemas(conn)
        tabelas = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    esperadas = {
        "veiculos", "entregas", "estoque_wms", "fretes_financeiro",
        "incidentes_sla", "logs_auditoria", "configuracoes",
        "webhooks", "webhook_logs",
    }
    assert esperadas.issubset(tabelas)


def test_init_all_schemas_seeds_initial_data_once(tmp_path):
    db = Database(f"sqlite:///{tmp_path / 'seed.db'}")
    with db.get_connection() as conn:
        init_all_schemas(conn)
        total_veiculos = conn.execute("SELECT COUNT(*) FROM veiculos").fetchone()[0]
        total_estoque = conn.execute("SELECT COUNT(*) FROM estoque_wms").fetchone()[0]
        total_entregas = conn.execute("SELECT COUNT(*) FROM entregas").fetchone()[0]
        total_fretes = conn.execute("SELECT COUNT(*) FROM fretes_financeiro").fetchone()[0]

        # Rodar de novo não deve duplicar os seeds (guarda por COUNT(*) == 0)
        init_all_schemas(conn)
        total_veiculos_2 = conn.execute("SELECT COUNT(*) FROM veiculos").fetchone()[0]

    assert total_veiculos == 3
    assert total_estoque == 3
    assert total_entregas == 2
    assert total_fretes == 3
    assert total_veiculos_2 == total_veiculos
