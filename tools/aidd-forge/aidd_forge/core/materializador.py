"""Motor de materializacao transacional do Injetor Universal.

Escreve o arquivo de destino do componente (e, quando o perfil exige,
atualiza o catalogo `registry.json` e a tabela ancorada no `AGENTS.md` do
alvo) dentro de uma transacao com buffer: todo o conteudo final e calculado
antes de qualquer escrita, e qualquer falha durante a sequencia de escritas
aciona rollback automatico dos arquivos ja gravados nesta transacao — nunca
deixando um arquivo orfao em disco por causa de uma interrupcao no meio do
caminho.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from aidd_forge.core.agents_md_anchor import render_component_table
from aidd_forge.core.injector_profiles import ComponentProfile, resolve_destination, resolve_profile

STUB_CONTEUDOS: frozenset[str] = frozenset({"", "pass", "todo", "..."})


class ConteudoStubError(ValueError):
    """Levantado quando `conteudo` e vazio ou um placeholder proibido."""


class DestinoExistenteError(FileExistsError):
    """Levantado quando o destino ja existe e `force=False`."""


class MaterializacaoError(RuntimeError):
    """Levantado quando uma escrita falha apos a transacao ja ter iniciado."""


@dataclass(frozen=True)
class InjectionRequest:
    """Requisicao ja validada de injecao de um componente."""

    tipo: str
    nome: str
    descricao: str
    conteudo: str


@dataclass
class MaterializationResult:
    """Resumo do que foi fisicamente gravado em disco por uma materializacao."""

    dest: Path
    created: list[Path] = field(default_factory=list)
    registry_updated: Path | None = None
    anchor_updated: Path | None = None


@dataclass
class _PlannedWrite:
    path: Path
    content: str
    existed_before: bool
    original_content: str | None


class Materializador:
    """Materializa um `InjectionRequest` dentro de `target_root` com rollback."""

    def __init__(self, target_root: Path):
        self.target_root = Path(target_root)

    def materializar(self, request: InjectionRequest, force: bool = False) -> MaterializationResult:
        if request.conteudo.strip().lower() in STUB_CONTEUDOS:
            raise ConteudoStubError(
                f"conteudo de '{request.nome}' ({request.tipo}) esta vazio ou e um placeholder proibido"
            )

        profile = resolve_profile(request.tipo)
        dest = resolve_destination(request.tipo, request.nome, self.target_root)

        if dest.exists() and not force:
            raise DestinoExistenteError(
                f"destino ja existe: {dest} (use force=True para sobrescrever)"
            )

        planned = [self._plan_dest_write(dest, request.conteudo)]
        registry_path = self._registry_path(profile)
        if registry_path is not None:
            planned.append(self._plan_registry_write(registry_path, request, dest))

        anchor_path = self._anchor_path(profile)
        if anchor_path is not None:
            planned.append(self._plan_anchor_write(anchor_path, request, dest))

        written: list[_PlannedWrite] = []
        try:
            for item in planned:
                self._write(item.path, item.content)
                written.append(item)
        except Exception as exc:
            self._rollback(written)
            raise MaterializacaoError(
                f"falha ao materializar '{request.nome}' ({request.tipo}); rollback aplicado: {exc}"
            ) from exc

        return MaterializationResult(
            dest=dest,
            created=[dest],
            registry_updated=registry_path,
            anchor_updated=anchor_path,
        )

    def _write(self, path: Path, content: str) -> None:
        """Ponto unico de escrita em disco (facilita simular falhas em testes)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _rollback(self, written: list[_PlannedWrite]) -> None:
        for item in reversed(written):
            if item.existed_before:
                item.path.write_text(item.original_content or "", encoding="utf-8")
            elif item.path.exists():
                item.path.unlink()

    def _plan_dest_write(self, dest: Path, conteudo: str) -> _PlannedWrite:
        existed = dest.exists()
        original = dest.read_text(encoding="utf-8") if existed else None
        return _PlannedWrite(path=dest, content=conteudo, existed_before=existed, original_content=original)

    def _registry_path(self, profile: ComponentProfile) -> Path | None:
        if profile.registry is None:
            return None
        return self.target_root / profile.registry

    def _plan_registry_write(
        self, registry_path: Path, request: InjectionRequest, dest: Path
    ) -> _PlannedWrite:
        existed = registry_path.exists()
        original = registry_path.read_text(encoding="utf-8") if existed else None
        entries: list[dict[str, str]] = json.loads(original) if original else []

        rel_dest = str(dest.relative_to(self.target_root)).replace("\\", "/")
        entries = [e for e in entries if e.get("nome") != request.nome]
        entries.append({"nome": request.nome, "descricao": request.descricao, "path": rel_dest})
        entries.sort(key=lambda e: e["nome"])

        content = json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
        return _PlannedWrite(
            path=registry_path, content=content, existed_before=existed, original_content=original
        )

    def _anchor_path(self, profile: ComponentProfile) -> Path | None:
        if profile.anchor is None:
            return None
        return self.target_root / profile.anchor

    def _plan_anchor_write(
        self, anchor_path: Path, request: InjectionRequest, dest: Path
    ) -> _PlannedWrite:
        existed = anchor_path.exists()
        original = anchor_path.read_text(encoding="utf-8") if existed else ""
        rel_dest = str(dest.relative_to(self.target_root)).replace("\\", "/")

        updated = render_component_table(
            original, tipo=request.tipo, nome=request.nome, descricao=request.descricao, caminho=rel_dest
        )
        return _PlannedWrite(
            path=anchor_path,
            content=updated,
            existed_before=existed,
            original_content=original if existed else None,
        )
