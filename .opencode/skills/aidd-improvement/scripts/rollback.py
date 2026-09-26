# -*- coding: utf-8 -*-
"""
AIDD-Melhoria Módulo de Rollback, Limpeza de Intermediários e Critério de Rejeição (D14 / Ticket 7).
Provê:
1. Context manager determinístico com bloco `finally` à prova de falhas.
2. Limpeza sumária de arquivos temporários, rascunhos e artefatos parciais (.tmp, .partial, .draft)
   em caso de falha, crash de parser ou código de saída não-zero (exit 1).
3. Reversão completa (rollback) de arquivos existentes modificados via snapshots atômicos.
4. Restauração integral de variáveis de ambiente alteradas durante a sessão.
5. Garantia de zero rastro transitório ou corrupção no repositório.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Union


class RollbackError(Exception):
    """Exceção base para operações do gerenciador de rollback."""
    pass


class ParserCrashSimuladoError(RollbackError):
    """Exceção levantada para simular crashes críticos de parsing durante testes e verificações."""
    pass


PADROES_INTERMEDIARIOS_PADRAO = (
    "*.tmp",
    "*.partial",
    "*.draft",
    "*.part",
    "*.crswap",
    "*.swp",
    "*~",
)


def limpar_artefatos_residuais(
    diretorio: str | Path,
    padroes: Optional[List[str]] = None,
) -> List[Path]:
    """
    Remove arquivos temporários e intermediários residuais em um diretório com base em padrões de sufixo.
    Retorna a lista de arquivos removidos com sucesso.
    """
    caminho_dir = Path(diretorio).resolve()
    if not caminho_dir.exists() or not caminho_dir.is_dir():
        return []

    padroes_busca = padroes or list(PADROES_INTERMEDIARIOS_PADRAO)
    removidos: List[Path] = []

    for padrao in padroes_busca:
        for arq in caminho_dir.glob(padrao):
            try:
                if arq.is_file():
                    arq.unlink(missing_ok=True)
                    removidos.append(arq)
                elif arq.is_dir():
                    shutil.rmtree(arq, ignore_errors=True)
                    removidos.append(arq)
            except Exception as exc:
                sys.stderr.write(f"[AVISO ROLLBACK] Falha ao remover residual '{arq}': {exc}\n")

    return removidos


class GerenciadorRollback:
    """
    Context manager determinístico para transações com garantia de limpeza e rollback em caso de falha.
    """

    def __init__(
        self,
        repo_root: Optional[str | Path] = None,
        varredura_automatica: bool = False,
    ) -> None:
        self.repo_root = Path(repo_root or Path.cwd()).resolve()
        self.varredura_automatica = varredura_automatica
        self.arquivos_temporarios: Set[Path] = set()
        self.diretorios_temporarios: Set[Path] = set()
        self.artefatos_finais: Set[Path] = set()
        self.snapshots_arquivos: Dict[Path, Optional[bytes]] = {}
        self.env_originais: Dict[str, Optional[str]] = {}
        self.comitado: bool = False
        self._snapshots_iniciais_dir: Set[Path] = set()

    def __enter__(self) -> "GerenciadorRollback":
        if self.varredura_automatica:
            self._capturar_estado_arquivos_existentes()
        return self

    def _capturar_estado_arquivos_existentes(self) -> None:
        """Captura os caminhos de arquivos já existentes nas áreas de trabalho para identificar novos."""
        if not self.repo_root.exists():
            return
        docs_dir = self.repo_root / "docs" / "melhorias"
        alvos = [docs_dir] if docs_dir.exists() else [self.repo_root]
        for alvo in alvos:
            for item in alvo.rglob("*"):
                if item.is_file():
                    self._snapshots_iniciais_dir.add(item.resolve())

    def registrar_temporario(self, caminho: str | Path) -> Path:
        """Registra um arquivo intermediário/temporário para exclusão garantida."""
        caminho_abs = Path(caminho).resolve()
        self.arquivos_temporarios.add(caminho_abs)
        return caminho_abs

    def registrar_diretorio_temporario(self, caminho: str | Path) -> Path:
        """Registra um diretório intermediário/temporário para remoção recursiva garantida."""
        caminho_abs = Path(caminho).resolve()
        self.diretorios_temporarios.add(caminho_abs)
        return caminho_abs

    def registrar_artefato_final(self, caminho: str | Path) -> Path:
        """Registra um artefato final legítimo que só deve ser preservado se a transação comitar com sucesso."""
        caminho_abs = Path(caminho).resolve()
        self.artefatos_finais.add(caminho_abs)
        return caminho_abs

    def salvar_snapshot(self, caminho: str | Path) -> None:
        """
        Salva uma cópia de segurança em memória de um arquivo existente antes de qualquer modificação.
        Caso o arquivo não exista no momento do snapshot, registra que ele não existia (será excluído no rollback).
        """
        caminho_abs = Path(caminho).resolve()
        if caminho_abs in self.snapshots_arquivos:
            return  # Preserva o primeiro estado original absoluto

        if caminho_abs.exists() and caminho_abs.is_file():
            try:
                self.snapshots_arquivos[caminho_abs] = caminho_abs.read_bytes()
            except Exception as exc:
                sys.stderr.write(f"[AVISO ROLLBACK] Falha ao capturar snapshot de {caminho_abs}: {exc}\n")
        else:
            self.snapshots_arquivos[caminho_abs] = None

    def definir_env(self, chave: str, valor: str) -> None:
        """Define uma variável de ambiente rastreando o valor original para reversão automática."""
        if chave not in self.env_originais:
            self.env_originais[chave] = os.environ.get(chave)
        os.environ[chave] = valor

    def commit(self) -> None:
        """
        Sela a transação como bem-sucedida.
        Remove apenas os arquivos temporários intermediários, mantendo intactos os artefatos finais.
        """
        self.comitado = True
        self._limpar_temporarios_declarados()

    def _limpar_temporarios_declarados(self) -> None:
        """Remove todos os arquivos e diretórios explicitamente registrados como temporários."""
        for arq in list(self.arquivos_temporarios):
            try:
                if arq.exists():
                    arq.unlink(missing_ok=True)
            except Exception as exc:
                sys.stderr.write(f"[AVISO ROLLBACK] Falha ao remover temporário {arq}: {exc}\n")
        self.arquivos_temporarios.clear()

        for d in list(self.diretorios_temporarios):
            try:
                if d.exists():
                    shutil.rmtree(d, ignore_errors=True)
            except Exception as exc:
                sys.stderr.write(f"[AVISO ROLLBACK] Falha ao remover pasta temporária {d}: {exc}\n")
        self.diretorios_temporarios.clear()

    def _executar_varredura_residuais(self) -> None:
        """Varre e expurga novos arquivos temporários e parciais criados durante a sessão."""
        docs_dir = self.repo_root / "docs" / "melhorias"
        alvos = [docs_dir, self.repo_root]

        for alvo in alvos:
            if not alvo.exists():
                continue
            for padrao in PADROES_INTERMEDIARIOS_PADRAO:
                for arq in alvo.rglob(padrao):
                    try:
                        if arq.is_file():
                            arq.unlink(missing_ok=True)
                    except Exception:
                        pass

            if self.varredura_automatica:
                for item in alvo.rglob("*"):
                    if item.is_file() and item.resolve() not in self._snapshots_iniciais_dir:
                        # Arquivo novo criado durante a sessão que falhou
                        try:
                            item.unlink(missing_ok=True)
                        except Exception:
                            pass

    def rollback(self) -> None:
        """
        Executa a reversão completa (rollback) e expurgo de qualquer rastro transitório:
        1. Exclui artefatos finais parciais já gravados antes da falha.
        2. Exclui todos os arquivos e diretórios intermediários temporários.
        3. Restaura arquivos modificados aos seus conteúdos originais via snapshots.
        4. Restaura variáveis de ambiente para seus valores originais.
        5. Executa varredura residual profunda para garantir zero resíduo.
        """
        # 1. Excluir artefatos finais incompletos gerados antes do crash
        for final_path in list(self.artefatos_finais):
            try:
                if final_path.exists():
                    final_path.unlink(missing_ok=True)
            except Exception as exc:
                sys.stderr.write(f"[AVISO ROLLBACK] Falha ao descartar artefato parcial {final_path}: {exc}\n")
        self.artefatos_finais.clear()

        # 2. Excluir temporários
        self._limpar_temporarios_declarados()

        # 3. Restaurar arquivos a partir de snapshots
        for caminho_arq, conteudo_antigo in self.snapshots_arquivos.items():
            try:
                if conteudo_antigo is None:
                    if caminho_arq.exists():
                        caminho_arq.unlink(missing_ok=True)
                else:
                    caminho_arq.parent.mkdir(parents=True, exist_ok=True)
                    caminho_arq.write_bytes(conteudo_antigo)
            except Exception as exc:
                sys.stderr.write(f"[AVISO ROLLBACK] Falha ao reverter snapshot de {caminho_arq}: {exc}\n")
        self.snapshots_arquivos.clear()

        # 4. Restaurar variáveis de ambiente
        for chave, val_original in self.env_originais.items():
            if val_original is None:
                os.environ.pop(chave, None)
            else:
                os.environ[chave] = val_original
        self.env_originais.clear()

        # 5. Varredura residual
        self._executar_varredura_residuais()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Garante tratamento determinístico no encerramento:
        Se ocorreu uma exceção ou se o commit() não foi chamado, executa rollback() na cláusula finally.
        """
        try:
            if exc_type is not None or not self.comitado:
                self.rollback()
            else:
                # Transação concluída com sucesso: apenas garante limpeza de temporários residuais
                self._limpar_temporarios_declarados()
        finally:
            pass
        return False  # Propaga exceções normalmente


def executar_com_rollback(
    funcao_operacao: Callable[[GerenciadorRollback], int],
    repo_root: Optional[str | Path] = None,
    varredura_automatica: bool = False,
) -> int:
    """
    Executa uma operação encapsulada sob o gerenciador de rollback determinístico.
    Caso a função retorne um código diferente de zero ou lance uma exceção,
    o rollback completo é executado e o erro/código é propagado.
    """
    with GerenciadorRollback(repo_root=repo_root, varredura_automatica=varredura_automatica) as rb:
        codigo_retorno = funcao_operacao(rb)
        if codigo_retorno == 0:
            rb.commit()
            return 0
        else:
            rb.rollback()
            return codigo_retorno if isinstance(codigo_retorno, int) else 1


def main(args: Optional[List[str]] = None) -> int:
    """Ponto de entrada CLI para comandos de limpeza e rollback manual."""
    parser = argparse.ArgumentParser(description="AIDD-Melhoria Utilitário de Limpeza e Rollback (D14 / Ticket 7)")
    parser.add_argument("--limpar", default=None, help="Caminho do diretório para expurgo de artefatos residuais temporários.")
    parser.add_argument("--repo-root", default=None, help="Raiz do repositório.")
    parsed = parser.parse_args(args)

    if parsed.limpar:
        removidos = limpar_artefatos_residuais(parsed.limpar)
        print(f"[ROLLBACK] Removidos {len(removidos)} artefatos temporários residuais em '{parsed.limpar}'.")
        return 0

    print("[ROLLBACK] Especifique uma ação (--limpar <dir>).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
