#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gates/test_regra10_check.py - Teste de execução determinística do hook regra10_check.py (ISSUE-0013).
Valida aprovação no formato obrigatório, status executivo curto de 1 linha,
e reprovação comprovada (bloqueio / exit 1) quando submetido a respostas prolixas,
com preâmbulos, narração de passos tomados ou jargão técnico não explicado.
"""

import json
import os
import subprocess
import sys
import uuid

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK_PATH = os.path.join(ROOT_DIR, "componentes", "compartilhado", "hooks", "regra10_check.py")
CLAUDE_HOOK_PATH = os.path.join(ROOT_DIR, ".claude", "hooks", "regra10_check.py")


def executar_hook(mensagem: str, strict: bool = False, hook_path: str = HOOK_PATH) -> subprocess.CompletedProcess:
    """Executa o script do hook via subprocess passando mensagem no formato JSON do Claude Stop hook."""
    uid = uuid.uuid4().hex
    payload = {
        "session_id": f"sess_{uid}",
        "prompt_id": f"prompt_{uid}",
        "last_assistant_message": mensagem,
    }
    cmd = [sys.executable, hook_path]
    if strict:
        cmd.append("--strict")

    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        cmd,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=10,
    )


def test_hook_failing_path_bloqueia_resposta_prolixa_com_preambulo_e_narracao():
    """
    Failing-path test (Lei #13):
    Executa o hook alimentando uma resposta prolixa com saudação, preâmbulo e narração de passos.
    Asserta que o hook efetivamente bloqueia a mensagem com decision 'block'.
    """
    resposta_prolixa = (
        "Olá! Com certeza, vou te ajudar com essa solicitação. Conforme você pediu, "
        "primeiro eu analisei todos os arquivos do repositório. Em seguida verifiquei o código "
        "e depois executei os testes manualmente para ver o que estava acontecendo. "
        "Você pode escolher entre a Opção A ou a Opção B para continuar."
    )
    res = executar_hook(resposta_prolixa)
    assert res.returncode == 0
    saida = json.loads(res.stdout)
    assert saida.get("decision") == "block", f"Esperado decision: block, obtido: {res.stdout}"
    assert "fora do padrão" in saida.get("reason", "")
    assert "Preâmbulo ou saudação proibida" in saida.get("reason", "")
    assert "Narração de processo" in saida.get("reason", "")


def test_hook_failing_path_strict_retorna_exit_1():
    """
    Valida que o hook quando executado com --strict em resposta prolixa retorna exit code 1.
    """
    resposta_prolixa = (
        "Bom dia! Entendido. Vou explicar o que aconteceu. "
        "Primeiro eu verifiquei as regras e depois li os logs completos do sistema. "
        "Temos duas opções disponíveis para implementar."
    )
    res = executar_hook(resposta_prolixa, strict=True)
    assert res.returncode == 1, f"Esperado exit 1 sob prolixidade com --strict, obtido {res.returncode}. Stdout: {res.stdout}"
    saida = json.loads(res.stdout)
    assert saida.get("decision") == "block"


def test_hook_bloqueia_resposta_extensa_sem_bullets():
    """
    Valida que respostas extensas (> 30 palavras) em bloco de parágrafo corrido
    sem marcadores de tópicos são bloqueadas por ausência de bullets.
    """
    resposta_bloco_corrido = (
        "A atualização dos componentes compartilhados foi finalizada no sistema. "
        "Todos os arquivos de configuração foram devidamente verificados e validados "
        "garantindo que as diretivas centrais de governança sejam cumpridas com rigor "
        "em conformidade com as diretrizes do ecossistema sem nenhuma pendência restante."
    )
    res = executar_hook(resposta_bloco_corrido)
    saida = json.loads(res.stdout)
    assert saida.get("decision") == "block"
    assert "Ausência de corpo estruturado em tópicos/bullets" in saida.get("reason", "")


def test_hook_bloqueia_jargao_tecnico_nao_explicado():
    """
    Valida que termos técnicos da lista (ex: payload, middleware) sem explicação
    são capturados e causam bloqueio.
    """
    resposta_com_jargao = (
        "Configuração concluída.\n\n"
        "- Atualizamos o middleware e o payload de requisição.\n"
        "- Ajustamos o endpoint de integração.\n\n"
        "Recomendação: validar em homologação."
    )
    res = executar_hook(resposta_com_jargao)
    saida = json.loads(res.stdout)
    assert saida.get("decision") == "block"
    assert "Termos técnicos sem explicação" in saida.get("reason", "")


def test_hook_aprova_resposta_conforme_shape_obrigatorio():
    """
    Valida que resposta no formato obrigatório (1 top sentence, bullets com fatos/números,
    bloco de sugestão isolado, sem jargões e sem preâmbulos) passa com sucesso.
    """
    resposta_conforme = (
        "Sincronização dos componentes multi-harness concluída com sucesso.\n\n"
        "- 8 pastas de hooks sincronizadas no repositório.\n"
        "- 14 testes automatizados executados com 100% de conformidade.\n"
        "- Redução de 45% no tempo de auditoria de conformidade.\n\n"
        "Recomendação: executar a auditoria completa antes do envio."
    )
    res = executar_hook(resposta_conforme)
    assert res.returncode == 0
    assert res.stdout.strip() == "", f"Esperado silêncio (aprovação), obtido: {res.stdout}"


def test_hook_aprova_status_executivo_curto_1_linha():
    """
    Valida que status executivo curto de 1 linha (per Law #4 Silent executor)
    passa de forma transparente sem acionar bloqueio.
    """
    status_curto = "3 arquivos modificados e testes passando com sucesso."
    res = executar_hook(status_curto)
    assert res.returncode == 0
    assert res.stdout.strip() == ""


def _resposta_com_n_bullets(n: int, prefixo: str = "Item numero") -> str:
    """Gera uma resposta em conformidade com o shape (cabecalho + bullets + sugestao),
    com N linhas de bullet, para variar o tamanho de forma previsivel e testavel."""
    linhas = [f"- {prefixo} {i}: dado medido e fato objetivo relatado nesta linha." for i in range(n)]
    corpo = "\n".join(linhas)
    return f"Sincronizacao concluida com sucesso.\n\n{corpo}\n\nRecomendacao: prosseguir."


def test_hook_bloqueia_resposta_normal_acima_do_teto_de_tokens():
    """
    Failing-path test (Lei #13): resposta em conformidade com o shape (sem
    jargao, sem preambulo, com bullets), mas longa o suficiente para
    ultrapassar o teto de 300 tokens de uma resposta normal (sem codigo/tabela).
    Deve bloquear citando o teto excedido, isolando esse motivo dos demais.
    """
    resposta_longa_normal = _resposta_com_n_bullets(60)
    res = executar_hook(resposta_longa_normal)
    saida = json.loads(res.stdout)
    assert saida.get("decision") == "block", f"Esperado bloqueio por teto, obtido: {res.stdout}"
    assert "Teto de tokens excedido" in saida.get("reason", "")
    assert "normal" in saida.get("reason", "")


def test_hook_aprova_resposta_normal_abaixo_do_teto_de_tokens():
    """
    False-positive check: mesma forma de resposta (shape correto), mas curta o
    suficiente para ficar abaixo do teto de 300 tokens. Nao deve bloquear.
    """
    resposta_curta_normal = _resposta_com_n_bullets(3)
    res = executar_hook(resposta_curta_normal)
    assert res.returncode == 0
    assert res.stdout.strip() == "", f"Esperado aprovacao, obtido: {res.stdout}"


def test_hook_bloqueia_resposta_tecnica_acima_do_teto_de_600():
    """
    Failing-path test (Lei #13): resposta com bloco de codigo cercado (marca
    a mensagem como 'tecnica', teto de 600), mas longa o suficiente para
    ultrapassar mesmo o teto maior. Deve bloquear citando o teto tecnico.
    """
    bloco_codigo = "```python\n" + "\n".join(f"linha_{i} = {i}" for i in range(250)) + "\n```"
    resposta_tecnica_longa = (
        "Implementacao concluida com sucesso.\n\n"
        f"{bloco_codigo}\n\n"
        "- Arquivo alterado conforme especificado.\n\n"
        "Recomendacao: revisar antes do commit."
    )
    res = executar_hook(resposta_tecnica_longa)
    saida = json.loads(res.stdout)
    assert saida.get("decision") == "block", f"Esperado bloqueio por teto tecnico, obtido: {res.stdout}"
    assert "Teto de tokens excedido" in saida.get("reason", "")
    assert "tecnica" in saida.get("reason", "")


def test_hook_aprova_resposta_tecnica_entre_300_e_600_tokens():
    """
    Prova que o teto tecnico (600) e realmente maior que o normal (300):
    uma resposta com bloco de codigo, medindo entre 300 e 600 tokens, deve
    APROVAR — a mesma quantidade de texto sem marcador tecnico reprovaria
    (ver test_hook_bloqueia_resposta_normal_acima_do_teto_de_tokens).
    """
    bloco_codigo = "```python\n" + "\n".join(f"x{i} = {i}" for i in range(90)) + "\n```"
    resposta_tecnica_media = (
        "Ajuste no script concluido.\n\n"
        f"{bloco_codigo}\n\n"
        "Recomendacao: rodar os testes."
    )
    res = executar_hook(resposta_tecnica_media)
    assert res.returncode == 0
    assert res.stdout.strip() == "", f"Esperado aprovacao (dentro do teto tecnico), obtido: {res.stdout}"


def test_hook_claude_sincronizado_comporta_se_identicamente():
    """
    Valida que a cópia em .claude/hooks/regra10_check.py possui o mesmo comportamento.
    """
    resposta_prolixa = "Olá! Vou explicar o que fiz: primeiro eu analisei e depois alterei."
    res = executar_hook(resposta_prolixa, hook_path=CLAUDE_HOOK_PATH)
    saida = json.loads(res.stdout)
    assert saida.get("decision") == "block"
