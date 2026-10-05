"""Engine de subagentes efemeros com descarte imediato de contexto.

Ciclo de vida cirurgico: Spawn -> Execucao -> Verificacao (AST) -> Purge.
O subagente real (Claude/Codex/etc) e injetado via `spawn_fn` para manter
este modulo desacoplado do harness e testavel sem chamadas de rede.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Generic, TypeVar

T = TypeVar("T")

# Callable que recebe o prompt enxuto e devolve o codigo-fonte gerado pelo subagente.
SpawnFn = Callable[[str], str]

# ~4 chars por token (heuristica BPE conservadora) para o limite de ~1000 tokens.
MAX_PROMPT_CHARS = 4000


@dataclass(frozen=True)
class Result(Generic[T]):
    """Result Monad: sucesso carrega `value`, falha carrega `error` (nunca os dois)."""

    value: T | None
    error: str | None

    @property
    def is_ok(self) -> bool:
        return self.error is None

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        return cls(value=value, error=None)

    @classmethod
    def fail(cls, error: str) -> "Result[T]":
        return cls(value=None, error=error)


class SubagentPurger:
    """Instancia um subagente efemero, valida o artefato e destroi a sessao."""

    def __init__(self, spawn_fn: SpawnFn, max_prompt_chars: int = MAX_PROMPT_CHARS):
        self._spawn_fn = spawn_fn
        self._max_prompt_chars = max_prompt_chars
        self._session_active = False

    @property
    def session_active(self) -> bool:
        """True somente durante a janela de execucao do subagente."""
        return self._session_active

    def run(self, prompt: str, output_path: Path) -> Result[Path]:
        """Executa o ciclo completo e retorna o Result do caminho salvo."""
        if len(prompt) > self._max_prompt_chars:
            return Result.fail(
                f"prompt excede o limite de {self._max_prompt_chars} chars (~1000 tokens)"
            )

        self._session_active = True
        try:
            artifact_source = self._spawn_fn(prompt)
        except Exception as exc:  # noqa: BLE001 - qualquer falha do harness vira Result.fail
            self._purge()
            return Result.fail(f"falha ao executar subagente: {exc}")

        try:
            ast.parse(artifact_source)
        except SyntaxError as exc:
            self._purge()
            return Result.fail(f"artefato invalido (AST): {exc}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(artifact_source, encoding="utf-8")

        self._purge()
        return Result.ok(output_path)

    def _purge(self) -> None:
        """Descarta imediatamente a sessao/contexto do subagente."""
        self._session_active = False
