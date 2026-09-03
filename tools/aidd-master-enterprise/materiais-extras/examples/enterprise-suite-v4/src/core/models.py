import sqlite3

def init_all_schemas(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        );

        -- CRM: LEADS COM FULL-CRUD E SCORING
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            telefone TEXT NOT NULL,
            empresa TEXT,
            score INTEGER DEFAULT 50,
            status TEXT DEFAULT 'novo',
            valor_estimado REAL DEFAULT 0,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- ERP: LANÇAMENTOS E DRE
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            valor REAL NOT NULL,
            data_vencimento DATE NOT NULL,
            status TEXT DEFAULT 'pendente',
            entidade_nome TEXT DEFAULT 'Geral',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- HELPDESK: TICKETS E SLA
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protocolo TEXT UNIQUE NOT NULL,
            assunto TEXT NOT NULL,
            descricao TEXT NOT NULL,
            cliente_nome TEXT NOT NULL,
            cliente_email TEXT NOT NULL,
            prioridade TEXT DEFAULT 'P3',
            status TEXT DEFAULT 'aberto',
            sla_limite_horas INTEGER DEFAULT 24,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- MEMBROS: CURSOS E ASSINATURAS
        CREATE TABLE IF NOT EXISTS cursos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria TEXT NOT NULL,
            thumbnail TEXT NOT NULL,
            total_aulas INTEGER DEFAULT 12
        );

        CREATE TABLE IF NOT EXISTS assinaturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_nome TEXT NOT NULL,
            usuario_email TEXT NOT NULL,
            plano TEXT NOT NULL,
            metodo TEXT NOT NULL,
            valor REAL NOT NULL,
            status TEXT DEFAULT 'ativa',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- CATÁLOGO: PRODUTOS E PEDIDOS
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            preco REAL NOT NULL,
            categoria TEXT NOT NULL,
            descricao TEXT NOT NULL,
            estoque INTEGER DEFAULT 50
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nome TEXT NOT NULL,
            cliente_telefone TEXT NOT NULL,
            total REAL NOT NULL,
            itens_json TEXT NOT NULL,
            status TEXT DEFAULT 'pendente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    if conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0] == 0:
        conn.executescript("""
            INSERT INTO leads (nome, email, telefone, empresa, score, status, valor_estimado) VALUES
            ('Dr. Carlos Eduardo Mendes', 'carlos@techcorp.com.br', '5511988887777', 'TechCorp Brasil', 95, 'qualificado', 28500.0),
            ('Dra. Helena Castro', 'helena@biomed.med.br', '5541999991111', 'BioMed Lab', 98, 'ganho', 75000.0),
            ('Mariana Silveira', 'mariana@inovare.com', '5511977776666', 'Inovare Soluções', 80, 'proposta', 15000.0),
            ('Bruno Figueiredo', 'bruno@logtech.com', '5519981112222', 'LogTech Express', 65, 'novo', 9800.0);

            INSERT INTO lancamentos (descricao, tipo, categoria, valor, data_vencimento, status, entidade_nome) VALUES
            ('Contrato Fechado: BioMed Lab', 'receita', 'Contratos CRM', 75000.0, '2026-09-15', 'pago', 'BioMed Lab'),
            ('Infraestrutura Cloud Hetzner', 'despesa', 'Servidores', 1250.0, '2026-09-05', 'pago', 'Hetzner Online'),
            ('Licenciamento APIs OpenAI', 'despesa', 'Inteligência Artificial', 3400.0, '2026-09-10', 'pendente', 'OpenAI Inc'),
            ('Consultoria Arquitetura AIDD', 'receita', 'Serviços', 18500.0, '2026-09-20', 'pendente', 'TechCorp Brasil');

            INSERT INTO tickets (protocolo, assunto, descricao, cliente_nome, cliente_email, prioridade, status, sla_limite_horas) VALUES
            ('TICK-A92B1C', 'Configuração de Webhook n8n', 'Suporte à esteira de automação comercial.', 'Rafael Souza', 'rafael@empresa.com', 'P1', 'aberto', 2),
            ('TICK-F83C2D', 'Dúvida na Conciliação Fiscal', 'Como emitir relatório DRE consolidado.', 'Mariana Lima', 'mariana@inovare.com', 'P2', 'em_andamento', 4),
            ('TICK-D71A4E', 'Atualização de Cadastro', 'Solicitação de troca de e-mail corporativo.', 'Bruno Alves', 'bruno@logtech.com', 'P3', 'resolvido', 24);

            INSERT INTO cursos (titulo, descricao, categoria, thumbnail, total_aulas) VALUES
            ('Formação Engenharia Agêntica & AIDD', 'Domine arquitetura modular, Vertical Slices e economia extrema de tokens.', 'Arquitetura', 'https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600&auto=format&fit=crop&q=60', 24),
            ('Microsserviços de Alta Performance com Python', 'Construção de APIs assíncronas com SQLite WAL, OpenAPI e Webhooks.', 'Backend', 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&auto=format&fit=crop&q=60', 18);

            INSERT INTO produtos (nome, preco, categoria, descricao, estoque) VALUES
            ('Licença AIDD Enterprise v5.1', 4990.00, 'Software', 'Acesso completo ao Monólito Modular com 5 fatias de negócio.', 100),
            ('Kit de Automação n8n Pro', 1290.00, 'Templates', 'Workflows prontos de CRM, ERP e Helpdesk para n8n.', 250),
            ('Mentoria de Arquitetura de Software', 3500.00, 'Serviços', 'Acompanhamento direto para implementação em larga escala.', 10);
        """)
        conn.commit()
