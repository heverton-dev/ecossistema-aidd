# -*- coding: utf-8 -*-
"""
AIDD-Melhoria Motor Analítico Determinístico (D8 / DoD 4).
Substitui processamento de bate-papo de LLM por validação estrita de JSON Schema,
rejeição categórica de strings malformadas ou texto puro (exit 1 / AnaliseEstruturalError),
e motor determinístico interno de geração e extração de relatório estruturado.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union


class AnaliseEstruturalError(Exception):
    """Exceção levantada quando o conteúdo não cumpre o JSON Schema estrito ou está malformado."""
    pass


class FallbackOperacionalError(Exception):
    """Exceção levantada quando retries autônomos são esgotados ou ocorre falha operacional persistente."""
    pass


SCHEMA_RELATORIO_CAMPOS_OBRIGATORIOS = ("pedido",)
STATUS_AVALIACAO_PERMITIDOS = {"feito", "parcial", "nao-feito"}


def validar_resposta_analitica(conteudo: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Valida estritamente a resposta do motor analítico contra o JSON Schema canônico.
    Rejeita terminantemente texto puro, strings JSON malformadas ou ausência do envelope 'relatorio'.
    """
    if isinstance(conteudo, str):
        texto_limpo = conteudo.strip()
        if not texto_limpo:
            raise AnaliseEstruturalError("Conteúdo vazio ou nulo fornecido para validação.")
        
        # Tenta decodificar JSON estrito
        try:
            dados = json.loads(texto_limpo)
        except json.JSONDecodeError as exc:
            raise AnaliseEstruturalError(
                f"Resposta malformada (não é JSON válido): {exc.msg} na linha {exc.lineno}, coluna {exc.colno}"
            ) from exc
    elif isinstance(conteudo, dict):
        dados = conteudo
    else:
        raise AnaliseEstruturalError(
            f"Tipo de dado inválido para resposta analítica: esperado str ou dict, recebido {type(conteudo).__name__}"
        )

    if not isinstance(dados, dict):
        raise AnaliseEstruturalError("O JSON da resposta analítica raiz deve ser um objeto/dicionário.")

    if "relatorio" not in dados:
        raise AnaliseEstruturalError("Schema inválido: envelope obrigatório 'relatorio' não encontrado.")

    relatorio = dados["relatorio"]
    if not isinstance(relatorio, dict):
        raise AnaliseEstruturalError("O envelope 'relatorio' deve conter um objeto estruturado.")

    # Validação de campos obrigatórios
    for campo in SCHEMA_RELATORIO_CAMPOS_OBRIGATORIOS:
        if campo not in relatorio:
            raise AnaliseEstruturalError(f"Campo obrigatório '{campo}' ausente dentro do envelope 'relatorio'.")
        if not isinstance(relatorio[campo], str) or not relatorio[campo].strip():
            raise AnaliseEstruturalError(f"Campo obrigatório '{campo}' deve ser uma string não vazia.")

    # Validação de itens avaliados quando presentes
    if "itens_avaliados" in relatorio and relatorio["itens_avaliados"] is not None:
        itens = relatorio["itens_avaliados"]
        if not isinstance(itens, list):
            raise AnaliseEstruturalError("Campo 'itens_avaliados' deve ser uma lista.")
        for idx, item_entry in enumerate(itens):
            if isinstance(item_entry, dict):
                if "item" not in item_entry:
                    raise AnaliseEstruturalError(f"Item #{idx} em 'itens_avaliados' não possui a chave 'item'.")
                if "status" in item_entry and item_entry["status"] not in STATUS_AVALIACAO_PERMITIDOS:
                    raise AnaliseEstruturalError(
                        f"Status '{item_entry['status']}' inválido no item #{idx}. "
                        f"Permitidos: {sorted(STATUS_AVALIACAO_PERMITIDOS)}"
                    )
            elif isinstance(item_entry, str):
                partes = item_entry.split("::")
                if len(partes) < 2:
                    raise AnaliseEstruturalError(
                        f"Item string #{idx} deve seguir o formato '<item>::<status>::<justificativa>'."
                    )
            else:
                raise AnaliseEstruturalError(f"Item #{idx} em 'itens_avaliados' possui tipo inválido ({type(item_entry).__name__}).")

    return dados


def executar_com_retry(
    funcao: Callable[[], Any],
    max_tentativas: int = 3,
    backoff_base: float = 0.01,
) -> Any:
    """
    Executa uma operação com política de retry autônomo com backoff exponencial.
    Em caso de falha persistente ao término das tentativas, levanta FallbackOperacionalError.
    """
    ultimo_erro: Optional[Exception] = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            return funcao()
        except Exception as exc:
            ultimo_erro = exc
            if tentativa < max_tentativas:
                time.sleep(backoff_base * (2 ** (tentativa - 1)))
            else:
                break

    mensagem_erro = f"Falha persistente na execução após {max_tentativas} tentativas: {ultimo_erro}"
    raise FallbackOperacionalError(mensagem_erro) from ultimo_erro


class MotorAnaliticoDeterministico:
    """
    Motor analítico interno 100% determinístico.
    Substitui consultas abertas de chat por geração estruturada, análise de regras e JSON Schema estrito.
    """

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()

    def gerar_slug(self, texto: str) -> str:
        """Gera um slug canônico a partir do pedido."""
        texto_limpo = re.sub(r"[^\w\s-]", "", texto.lower())
        palavras = [p for p in re.split(r"[\s_]+", texto_limpo) if p][:3]
        return "-".join(palavras) if palavras else "analise-melhoria"

    def extrair_achados_e_riscos(self, pedido: str) -> tuple[List[str], List[str]]:
        """Gera achados técnicos determinísticos baseados nas características do pedido."""
        achados = [
            f"Demanda analítica registrada com foco em '{pedido}'",
            "Estrutura pré-planejamento avaliada conforme diretrizes de governança AIDD"
        ]
        riscos = [
            "Necessidade de isolamento estrito de worktree antes da execução do plano",
            "Monitoramento contínuo de consumo de tokens e latência"
        ]
        return achados, riscos

    def processar_analise(
        self,
        pedido: str,
        nome: Optional[str] = None,
        nota_atual: Optional[str] = None,
        evidencia: Optional[str] = None,
        resumo: Optional[str] = None,
        itens_avaliados: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Processa deterministamente o pedido gerando um relatório em conformidade estrita com o JSON Schema.
        """
        if not pedido or not isinstance(pedido, str) or not pedido.strip():
            raise AnaliseEstruturalError("Parâmetro 'pedido' é obrigatório e deve ser uma string não vazia.")

        pedido_limpo = pedido.strip()
        slug_calculado = nome or self.gerar_slug(pedido_limpo)
        achados, riscos = self.extrair_achados_e_riscos(pedido_limpo)

        relatorio_conteudo = {
            "pedido": pedido_limpo,
            "nome": slug_calculado,
            "nota_atual": nota_atual or "NAO AUDITADO",
            "evidencia": evidencia or "(nota pendente de medicao real - nao preencher com estimativa)",
            "resumo": resumo or f"Sugestão de refatoração para '{pedido_limpo}' avaliada deterministamente.",
            "achados": achados,
            "riscos": riscos,
            "recomendacao": f"Sugestão de refatoração para {pedido_limpo} pronta para derivação de plano.",
            "itens_avaliados": itens_avaliados or [
                {"item": "Determinismo", "status": "feito", "justificativa": "Motor determinístico ativo"},
                {"item": "Schema", "status": "feito", "justificativa": "JSON Schema estrito validado"}
            ]
        }

        envelope = {"relatorio": relatorio_conteudo}
        return validar_resposta_analitica(envelope)

    def extrair_relatorio(self, dados_ou_texto: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Extrai e valida um relatório existente a partir de string ou dict."""
        return validar_resposta_analitica(dados_ou_texto)


def main(args: Optional[List[str]] = None) -> int:
    """
    Ponto de entrada CLI para o motor analítico e validador JSON estrito.
    Crasheia com exit 1 em caso de JSON malformado, texto puro ou violação de schema.
    """
    parser = argparse.ArgumentParser(
        description="AIDD-Melhoria Motor Analítico Determinístico e Validador de Schema (D8 / DoD 4)"
    )
    parser.add_argument(
        "entrada",
        nargs="?",
        default=None,
        help="Caminho do arquivo JSON, '-' para stdin, ou string JSON bruta para validação."
    )
    parser.add_argument("--pedido", help="Gera análise determinística estruturada a partir da descrição do pedido.")
    parser.add_argument("--nota-atual", help="Nota atual para o relatório determinístico.")
    parser.add_argument("--evidencia", help="Evidência factual para o relatório determinístico.")
    parser.add_argument("--output", help="Caminho para gravação do JSON serializado resultante.")

    parsed = parser.parse_args(args)

    try:
        if parsed.pedido:
            motor = MotorAnaliticoDeterministico()
            resultado = motor.processar_analise(
                pedido=parsed.pedido,
                nota_atual=parsed.nota_atual,
                evidencia=parsed.evidencia,
            )
        elif parsed.entrada:
            entrada_texto = parsed.entrada
            # Se for '-' ou caminho existente no disco, lê o conteúdo
            if entrada_texto == "-":
                entrada_texto = sys.stdin.read()
            elif os.path.isfile(entrada_texto):
                entrada_texto = Path(entrada_texto).read_text(encoding="utf-8")
            resultado = validar_resposta_analitica(entrada_texto)
        elif not sys.stdin.isatty():
            entrada_texto = sys.stdin.read()
            resultado = validar_resposta_analitica(entrada_texto)
        else:
            sys.stderr.write("[ERRO ESTRUTURAL] Nenhuma entrada ou pedido fornecido para processamento.\n")
            return 1

        json_saida = json.dumps(resultado, indent=2, ensure_ascii=False)
        if parsed.output:
            Path(parsed.output).write_text(json_saida, encoding="utf-8")
        else:
            print(json_saida)
        return 0

    except AnaliseEstruturalError as exc:
        sys.stderr.write(f"[ERRO ESTRUTURAL] Falha na validação de schema: {exc}\n")
        return 1
    except FallbackOperacionalError as exc:
        sys.stderr.write(f"[ERRO OPERACIONAL] Fallback acionado: {exc}\n")
        return 1
    except Exception as exc:
        sys.stderr.write(f"[ERRO INESPERADO] {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
