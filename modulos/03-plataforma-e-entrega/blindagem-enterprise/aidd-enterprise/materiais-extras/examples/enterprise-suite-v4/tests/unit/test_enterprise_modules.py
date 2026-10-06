import pytest

def test_leads_crm_scoring(db_conn):
    rows = db_conn.execute("SELECT nome, score, status FROM leads ORDER BY score DESC").fetchall()
    assert len(rows) >= 4
    top = dict(rows[0])
    assert top["score"] >= 90
    assert top["status"] in ["qualificado", "ganho"]

def test_lancamentos_erp_dre(db_conn):
    receitas = db_conn.execute("SELECT SUM(valor) FROM lancamentos WHERE tipo = 'receita'").fetchone()[0] or 0
    despesas = db_conn.execute("SELECT SUM(valor) FROM lancamentos WHERE tipo = 'despesa'").fetchone()[0] or 0
    assert receitas > 0
    assert despesas > 0
    assert receitas > despesas

def test_tickets_helpdesk_sla(db_conn):
    tickets = db_conn.execute("SELECT protocolo, prioridade, sla_limite_horas FROM tickets").fetchall()
    assert len(tickets) >= 3
    for t in tickets:
        t_dict = dict(t)
        assert t_dict["prioridade"] in ["P1", "P2", "P3"]
        assert t_dict["sla_limite_horas"] > 0

def test_cursos_e_produtos_catalogo(db_conn):
    cursos = db_conn.execute("SELECT COUNT(*) FROM cursos").fetchone()[0]
    produtos = db_conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    assert cursos >= 2
    assert produtos >= 3
