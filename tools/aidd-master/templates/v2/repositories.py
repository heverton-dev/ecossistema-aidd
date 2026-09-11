# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD v5.1 Enterprise — Camada de Infraestrutura: Repositorios das Verticais
=============================================================================
Concentra o acesso a banco (SQL) das fatias verticais de negocio do monolito
de demonstracao (Pronto-Socorro/Triagem, PEP & Prescricoes, Centro Cirurgico,
Farmacia, Faturamento TISS/TUSS e Auditoria) que antes vivia inline em
server.py. server.py (camada de interface/rotas) passa a chamar apenas estes
repositorios — nenhuma chamada .execute()/.executemany() ou import sqlite3
direto fora desta camada.
"""


class TriagemRepository:
    def __init__(self, db):
        self.db = db

    def listar(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM triagens ORDER BY tempo_espera_max_min ASC, criado_em ASC").fetchall()
            return [dict(r) for r in rows]

    def obter(self, tid):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM triagens WHERE id = ?", (tid,)).fetchone()
            return dict(row) if row else None

    def criar(self, protocolo, paciente_nome, idade, sinais_vitais, queixa_principal, classificacao, sla_min):
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO triagens (protocolo, paciente_nome, idade, sinais_vitais, queixa_principal, classificacao, tempo_espera_max_min, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'aguardando')
            """, (protocolo, paciente_nome, idade, sinais_vitais, queixa_principal, classificacao, sla_min))
            conn.commit()

    def atualizar(self, tid, sinais_vitais, status, classificacao):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE triagens SET sinais_vitais = ?, status = ?, classificacao = ? WHERE id = ?",
                (sinais_vitais, status, classificacao, tid)
            )
            conn.commit()

    def remover(self, tid):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM triagens WHERE id = ?", (tid,))
            conn.commit()

    def alocar_leito(self, tid, leito):
        with self.db.get_connection() as conn:
            conn.execute("UPDATE triagens SET leito_alocado = ?, status = 'em_atendimento' WHERE id = ?", (leito, tid))
            conn.commit()

    def alocar_leito_por_protocolo(self, protocolo, leito):
        with self.db.get_connection() as conn:
            conn.execute("UPDATE triagens SET leito_alocado = ?, status = 'em_atendimento' WHERE protocolo = ?", (leito, protocolo))
            conn.commit()


class PepRepository:
    def __init__(self, db):
        self.db = db

    def listar_prontuarios(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM prontuarios ORDER BY atualizado_em DESC").fetchall()
            return [dict(r) for r in rows]

    def obter_prontuario(self, pid):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM prontuarios WHERE id = ?", (pid,)).fetchone()
            return dict(row) if row else None

    def criar_prontuario(self, numero_prontuario, paciente_nome, medico_responsavel, crm, diagnostico_cid10, evolucao_clinica, alergias):
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO prontuarios (numero_prontuario, paciente_nome, medico_responsavel, crm, diagnostico_cid10, evolucao_clinica, alergias, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'ativo')
            """, (numero_prontuario, paciente_nome, medico_responsavel, crm, diagnostico_cid10, evolucao_clinica, alergias))
            conn.commit()

    def atualizar_prontuario(self, pid, evolucao_clinica, diagnostico_cid10):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE prontuarios SET evolucao_clinica = ?, diagnostico_cid10 = ?, atualizado_em = CURRENT_TIMESTAMP WHERE id = ?",
                (evolucao_clinica, diagnostico_cid10, pid)
            )
            conn.commit()

    def remover_prontuario(self, pid):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM prontuarios WHERE id = ?", (pid,))
            conn.commit()

    def listar_prescricoes(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM prescricoes ORDER BY criado_em DESC").fetchall()
            return [dict(r) for r in rows]

    def obter_paciente_nome(self, pid):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT paciente_nome FROM prontuarios WHERE id = ?", (pid,)).fetchone()
            return row["paciente_nome"] if row else None

    def criar_prescricao(self, prontuario_id, paciente_nome, medicamento, dosagem, frequencia, via_administracao):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prescricoes (prontuario_id, paciente_nome, medicamento, dosagem, frequencia, via_administracao, status)
                VALUES (?, ?, ?, ?, ?, ?, 'pendente')
            """, (prontuario_id, paciente_nome, medicamento, dosagem, frequencia, via_administracao))
            conn.commit()
            return cursor.lastrowid

    def atualizar_status_prescricao(self, pid, status):
        with self.db.get_connection() as conn:
            conn.execute("UPDATE prescricoes SET status = ? WHERE id = ?", (status, pid))
            conn.commit()


class CirurgicoRepository:
    def __init__(self, db):
        self.db = db

    def listar(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM cirurgias ORDER BY data_hora_cirurgia ASC").fetchall()
            return [dict(r) for r in rows]

    def obter(self, cid):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM cirurgias WHERE id = ?", (cid,)).fetchone()
            return dict(row) if row else None

    def criar(self, codigo_agendamento, paciente_nome, procedimento, sala_bloco, cirurgiao_principal, anestesista, tipo_anestesia, data_hora_cirurgia, necessita_opme):
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO cirurgias (codigo_agendamento, paciente_nome, procedimento, sala_bloco, cirurgiao_principal, anestesista, tipo_anestesia, data_hora_cirurgia, status, necessita_opme)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'agendada', ?)
            """, (codigo_agendamento, paciente_nome, procedimento, sala_bloco, cirurgiao_principal, anestesista, tipo_anestesia, data_hora_cirurgia, necessita_opme))
            conn.commit()

    def atualizar(self, cid, sala_bloco, status):
        with self.db.get_connection() as conn:
            conn.execute("UPDATE cirurgias SET sala_bloco = ?, status = ? WHERE id = ?", (sala_bloco, status, cid))
            conn.commit()

    def cancelar(self, cid):
        with self.db.get_connection() as conn:
            conn.execute("UPDATE cirurgias SET status = 'cancelada' WHERE id = ?", (cid,))
            conn.commit()

    def atualizar_status(self, cid, status):
        with self.db.get_connection() as conn:
            conn.execute("UPDATE cirurgias SET status = ? WHERE id = ?", (status, cid))
            conn.commit()


class FarmaciaRepository:
    def __init__(self, db):
        self.db = db

    def listar_estoque(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM farmacia_estoque ORDER BY status_estoque DESC, medicamento ASC").fetchall()
            return [dict(r) for r in rows]

    def criar_item(self, codigo_item, medicamento, lote, categoria, quantidade_disponivel, quantidade_minima, temperatura_armazenamento, validade, status_estoque):
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO farmacia_estoque (codigo_item, medicamento, lote, categoria, quantidade_disponivel, quantidade_minima, temperatura_armazenamento, validade, status_estoque)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (codigo_item, medicamento, lote, categoria, quantidade_disponivel, quantidade_minima, temperatura_armazenamento, validade, status_estoque))
            conn.commit()

    def obter_quantidade_minima(self, iid):
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT quantidade_minima FROM farmacia_estoque WHERE id = ?", (iid,)).fetchone()
            return row["quantidade_minima"] if row else None

    def atualizar_saldo(self, iid, quantidade_disponivel, status_estoque):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE farmacia_estoque SET quantidade_disponivel = ?, status_estoque = ? WHERE id = ?",
                (quantidade_disponivel, status_estoque, iid)
            )
            conn.commit()

    def remover_item(self, iid):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM farmacia_estoque WHERE id = ?", (iid,))
            conn.commit()

    def listar_dispensacoes(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM dispensacoes ORDER BY data_dispensacao DESC").fetchall()
            return [dict(r) for r in rows]


class FaturamentoRepository:
    def __init__(self, db):
        self.db = db

    def listar_guias(self):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM faturamento_guias ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def criar_guia(self, numero_guia, paciente_nome, convenio, codigo_tuss, descricao_procedimento, valor_total):
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO faturamento_guias (numero_guia, paciente_nome, convenio, codigo_tuss, descricao_procedimento, valor_total, status_guia)
                VALUES (?, ?, ?, ?, ?, ?, 'gerada')
            """, (numero_guia, paciente_nome, convenio, codigo_tuss, descricao_procedimento, valor_total))
            conn.commit()

    def criar_guia_cirurgia(self, numero_guia, paciente_nome, descricao_procedimento, valor_total):
        with self.db.get_connection() as conn:
            conn.execute("""
                INSERT INTO faturamento_guias (numero_guia, paciente_nome, convenio, codigo_tuss, descricao_procedimento, valor_total, status_guia)
                VALUES (?, ?, 'Bradesco Saúde / Cirúrgico', '31003443', ?, ?, 'gerada')
            """, (numero_guia, paciente_nome, descricao_procedimento, valor_total))
            conn.commit()

    def atualizar_status(self, gid, status_guia):
        with self.db.get_connection() as conn:
            liq = "datetime('now')" if status_guia == "liquidada" else "NULL"
            conn.execute(f"UPDATE faturamento_guias SET status_guia = ?, data_liquidacao = {liq} WHERE id = ?", (status_guia, gid))
            conn.commit()

    def remover_guia(self, gid):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM faturamento_guias WHERE id = ?", (gid,))
            conn.commit()

    def dre(self):
        with self.db.get_connection() as conn:
            total = conn.execute("SELECT COALESCE(SUM(valor_total), 0) FROM faturamento_guias").fetchone()[0]
            liquidado = conn.execute("SELECT COALESCE(SUM(valor_total), 0) FROM faturamento_guias WHERE status_guia = 'liquidada'").fetchone()[0]
            return total, liquidado


class AuditoriaRepository:
    def __init__(self, db):
        self.db = db

    def registrar(self, evento, modulo, payload_json):
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO logs_auditoria (evento, modulo, payload_json) VALUES (?, ?, ?)",
                (evento, modulo, payload_json)
            )
            conn.commit()

    def listar(self, limite=50):
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM logs_auditoria ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
            return [dict(r) for r in rows]
