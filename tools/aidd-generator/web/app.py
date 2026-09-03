#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor Web Local Flask
web/app.py — aidd-project-generator
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify

from web.config_manager import (
    obter_configuracao,
    salvar_configuracao,
    testar_chave_llm
)
from web.pipeline_runner import runner_global
from web.status_parser import analisar_status_pasta_projeto

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(Path(__file__).resolve().parent / 'templates'),
    static_folder=str(Path(__file__).resolve().parent / 'static')
)


def sanitizar_nome_pasta(texto: str) -> str:
    """Converte a ideia do usuário em um nome de pasta limpo e amigável."""
    if not texto:
        return "novo-projeto-aidd"
    # Pega as primeiras 4 palavras
    palavras = re.findall(r'[a-zA-Z0-9áéíóúÁÉÍÓÚâêîôûÂÊÎÔÛãõÃÕçÇ]+', texto.lower())
    nome_base = "-".join(palavras[:4]) if palavras else "novo-projeto-aidd"
    # Remove acentos
    tabela_acentos = str.maketrans('áéíóúâêîôûãõç', 'aeiouaeiouaoc')
    nome_limpo = nome_base.translate(tabela_acentos)
    nome_limpo = re.sub(r'[^a-z0-9_-]', '', nome_limpo)
    return f"projeto-{nome_limpo}" if not nome_limpo.startswith('projeto-') else nome_limpo


@app.route('/')
def index():
    """Renderiza a página principal do aplicativo."""
    return render_template('index.html')


@app.route('/api/config', methods=['GET'])
def api_obter_config():
    """Retorna o estado da configuração atual."""
    config = obter_configuracao()
    return jsonify({
        'sucesso': True,
        'config': config
    })


@app.route('/api/config', methods=['POST'])
def api_salvar_config():
    """Salva a configuração do provedor no arquivo .env."""
    dados = request.get_json() or {}
    provedor_id = dados.get('provedor_id', '').strip()
    chave = dados.get('chave', '').strip()
    modelo = dados.get('modelo')
    base_url = dados.get('base_url')
    timeout = int(dados.get('timeout', 120))

    if not provedor_id:
        return jsonify({'sucesso': False, 'mensagem': 'Provedor não informado.'}), 400

    sucesso, msg = salvar_configuracao(
        provedor_id=provedor_id,
        chave=chave,
        modelo=modelo,
        base_url=base_url,
        timeout_segundos=timeout
    )

    status_code = 200 if sucesso else 400
    return jsonify({
        'sucesso': sucesso,
        'mensagem': msg,
        'config': obter_configuracao()
    }), status_code


@app.route('/api/test-key', methods=['POST'])
def api_testar_chave():
    """Realiza teste de conectividade e validação da chave de IA."""
    dados = request.get_json() or {}
    provedor_id = dados.get('provedor_id', '').strip()
    chave = dados.get('chave', '').strip()
    modelo = dados.get('modelo')
    base_url = dados.get('base_url')

    if not provedor_id:
        return jsonify({'sucesso': False, 'mensagem': 'Selecione um provedor para testar.'}), 400

    # Se a chave não foi enviada na requisição, tenta usar a já salva no .env
    if not chave:
        config_atual = obter_configuracao()
        vars_env = os.environ
        # Descobre a env key
        prov = next((p for p in config_atual['provedores_disponiveis'] if p['id'] == provedor_id), None)
        if prov:
            chave = vars_env.get(prov['env_key'], '')

    if not chave:
        return jsonify({'sucesso': False, 'mensagem': 'Por favor, informe a chave de API para testar.'}), 400

    sucesso, msg, detalhes = testar_chave_llm(
        provedor_id=provedor_id,
        chave=chave,
        modelo=modelo,
        base_url=base_url
    )

    return jsonify({
        'sucesso': sucesso,
        'mensagem': msg,
        'detalhes': detalhes
    })


@app.route('/api/suggest-folder', methods=['GET'])
def api_sugerir_pasta():
    """Sugere um caminho de pasta padrão para o novo projeto."""
    ideia = request.args.get('ideia', '').strip()
    nome_pasta = sanitizar_nome_pasta(ideia)
    caminho_sugerido = str(Path('..') / nome_pasta)
    caminho_absoluto = str((ROOT_DIR.parent / nome_pasta).resolve())

    return jsonify({
        'sucesso': True,
        'sugestao_relativa': caminho_sugerido,
        'sugestao_absoluta': caminho_absoluto,
        'nome_pasta': nome_pasta
    })


@app.route('/api/pipeline/start', methods=['POST'])
def api_iniciar_pipeline():
    """Inicia a execução do pipeline em background após verificação preventiva de configuração."""
    # 1. Verificação preventiva obrigatória de configuração de IA
    config = obter_configuracao()
    if not config['esta_configurado']:
        return jsonify({
            'sucesso': False,
            'bloqueado_por_configuracao': True,
            'mensagem': 'Você ainda não configurou uma chave de IA. Vá em Configurações para definir a chave antes de gerar o projeto.'
        }), 400

    dados = request.get_json() or {}
    ideia = dados.get('ideia', '').strip()
    pasta = dados.get('pasta_projeto', '').strip()
    implementar_codigo = bool(dados.get('implementar_codigo', False))

    if not ideia:
        return jsonify({'sucesso': False, 'mensagem': 'O campo "O que você quer construir?" é obrigatório.'}), 400

    if not pasta:
        # Usar sugestão padrão
        nome_pasta = sanitizar_nome_pasta(ideia)
        pasta = str((ROOT_DIR.parent / nome_pasta).resolve())

    resultado = runner_global.iniciar_pipeline(
        ideia=ideia,
        pasta_projeto=pasta,
        implementar_codigo=implementar_codigo
    )

    status_code = 200 if resultado['sucesso'] else 400
    return jsonify(resultado), status_code


@app.route('/api/pipeline/status', methods=['GET'])
def api_status_pipeline():
    """Retorna o status consolidado da execução atual (polling a cada 2s)."""
    status = runner_global.obter_status()
    return jsonify({
        'sucesso': True,
        'status': status
    })


@app.route('/api/pipeline/cancel', methods=['POST'])
def api_cancelar_pipeline():
    """Cancela o pipeline em execução."""
    resultado = runner_global.cancelar_pipeline()
    return jsonify(resultado)


@app.route('/api/open-folder', methods=['POST'])
def api_abrir_pasta():
    """Abre a pasta gerada no Explorador de Arquivos do Windows."""
    dados = request.get_json() or {}
    caminho_str = dados.get('caminho', '').strip()

    if not caminho_str:
        # Tentar usar a pasta do último pipeline executado
        status = runner_global.obter_status()
        caminho_str = status.get('pasta_projeto', '')

    if not caminho_str:
        return jsonify({'sucesso': False, 'mensagem': 'Caminho de pasta não especificado.'}), 400

    caminho = Path(caminho_str).resolve()
    if not caminho.exists():
        return jsonify({'sucesso': False, 'mensagem': f"A pasta '{caminho}' não existe no disco."}), 404

    try:
        if sys.platform == 'win32':
            os.startfile(str(caminho))
        else:
            # Fallback para outros sistemas operacionais
            subprocess.Popen(['xdg-open' if sys.platform.startswith('linux') else 'open', str(caminho)])

        return jsonify({
            'sucesso': True,
            'mensagem': f"Pasta aberta com sucesso: {caminho}"
        })
    except Exception as e:
        # Fallback via explorer no Windows
        try:
            subprocess.Popen(['explorer', str(caminho)])
            return jsonify({
                'sucesso': True,
                'mensagem': f"Pasta aberta com sucesso via Explorer: {caminho}"
            })
        except Exception as e2:
            return jsonify({
                'sucesso': False,
                'mensagem': f"Erro ao abrir pasta: {e2}"
            }), 500


@app.route('/api/projeto/status', methods=['GET'])
def api_status_projeto_arbitrario():
    """Retorna o status de qualquer pasta de projeto AIDD (não só a do runner)."""
    pasta = request.args.get('pasta', '').strip()

    if not pasta:
        # Fallback: usar pasta do runner_global se houver
        status_runner = runner_global.obter_status()
        pasta = status_runner.get('pasta_projeto', '')

    if not pasta:
        return jsonify({'sucesso': False, 'mensagem': 'Nenhuma pasta informada e nenhum pipeline em execução.'}), 400

    pasta_path = Path(pasta)
    if not pasta_path.exists():
        return jsonify({'sucesso': False, 'mensagem': f'Pasta não encontrada: {pasta}'}), 404

    try:
        dados = analisar_status_pasta_projeto(pasta_path)
        return jsonify({'sucesso': True, 'status': dados})
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao analisar pasta: {str(e)}'}), 500


@app.route('/api/workspace/status', methods=['GET'])
def api_status_workspace():
    """Retorna o progresso do desenvolvimento da ferramenta (PLANO-EXECUCAO-ESTRUTURADO.json)."""
    plano_path = ROOT_DIR / 'PLANO-EXECUCAO-ESTRUTURADO.json'

    if not plano_path.exists():
        return jsonify({'sucesso': False, 'mensagem': 'PLANO-EXECUCAO-ESTRUTURADO.json não encontrado'}), 404

    try:
        import json
        conteudo = plano_path.read_text(encoding='utf-8')
        plano = json.loads(conteudo)

        metadata = plano.get('metadata', {})
        etapas = plano.get('etapas', [])

        # Contar status
        total_etapas = len(etapas)
        completas = sum(1 for e in etapas if 'COMPLETO' in (e.get('status', '')).upper())
        pendentes = sum(1 for e in etapas if 'PENDENTE' in (e.get('status', '')).upper())
        parciais = sum(1 for e in etapas if 'PARCIALMENTE' in (e.get('status', '')).upper())

        etapas_simplificadas = []
        for e in etapas:
            etapas_simplificadas.append({
                'id': e.get('id', ''),
                'nome': e.get('nome', ''),
                'status': e.get('status', ''),
                'data_conclusao': e.get('data_conclusao', ''),
                'commit': e.get('commit', '')
            })

        return jsonify({
            'sucesso': True,
            'workspace': {
                'objetivo_geral': metadata.get('objetivo_geral', ''),
                'ultima_atualizacao': metadata.get('ultima_atualizacao', ''),
                'total_etapas': total_etapas,
                'etapas_completas': completas,
                'etapas_pendentes': pendentes,
                'etapas_parciais': parciais,
                'progresso_percentual': int((completas / total_etapas) * 100) if total_etapas > 0 else 0,
                'etapas': etapas_simplificadas
            }
        })
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro ao ler plano: {str(e)}'}), 500


def criar_app() -> Flask:
    """Fábrica de aplicação Flask para testes e inicialização."""
    return app


if __name__ == '__main__':
    porta = int(os.environ.get('PORT', 5000))
    print(f"============================================================")
    print(f"🚀 AIDD Project Generator — Interface Web Local")
    print(f"🌐 Acesse no seu navegador: http://localhost:{porta}")
    print(f"============================================================")
    app.run(host='127.0.0.1', port=porta, debug=False)
