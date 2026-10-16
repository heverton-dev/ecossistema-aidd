# -*- coding: utf-8 -*-
"""
Achados da auditoria do motor aidd-freedom (TDD, RED -> GREEN):

1. Rotas TanStack file-based em formato plano (`posts.$postId.tsx`), pathless
   (`_auth.login.tsx`), splat (`files.$.tsx`), grupos `(grp)/` e arquivos
   ignorados (`-helper.tsx`, `routeTree.gen.ts`) eram convertidos em caminhos errados.
2. `funcao` do contrato C3 (`renderizar_<x>`) saia com hifen e extensao
   (ex.: `renderizar_posts-postid-tsx`), nao um identificador valido, e colidia
   entre rotas homonimas em pastas distintas.
3. FrontendLiberator copiava `.env.production`, `.env.staging` e `.env.*.local`
   do projeto de origem (segredos reais) para a saida liberada.
4. FrontendLiberator copiava builds de frameworks SSR (`.output`, `.vinxi`).
"""

import keyword
import os
import sys
from pathlib import Path

FREEDOM_DIR = Path(__file__).resolve().parent.parent
if str(FREEDOM_DIR) not in sys.path:
    sys.path.insert(0, str(FREEDOM_DIR))

from aidd_freedom.cli import _funcoes_unicas_c3  # noqa: E402
from aidd_freedom.frontend_liberator import FrontendLiberator  # noqa: E402
from aidd_freedom.scanner import LovableScanner  # noqa: E402


def _projeto_tanstack(tmp_path: Path, arquivos) -> Path:
    rotas = tmp_path / "src" / "routes"
    for nome in arquivos:
        alvo = rotas / nome
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text("export const Route = {};\n", encoding="utf-8")
    (tmp_path / "package.json").write_text('{"name": "app"}', encoding="utf-8")
    return tmp_path


def _paths(projeto: Path):
    return {r["path"] for r in LovableScanner(str(projeto)).scan()["routes"]}


def test_rota_plana_com_parametro_vira_segmentos(tmp_path):
    p = _projeto_tanstack(tmp_path, ["__root.tsx", "index.tsx", "posts.index.tsx", "posts.$postId.tsx"])
    assert _paths(p) == {"/", "/posts", "/posts/:postId"}


def test_rota_pathless_nao_entra_no_caminho(tmp_path):
    p = _projeto_tanstack(tmp_path, ["_auth.login.tsx", "_auth.tsx"])
    assert _paths(p) == {"/login", "/"}


def test_splat_e_grupo(tmp_path):
    p = _projeto_tanstack(tmp_path, ["files.$.tsx", "(grp)/about.tsx"])
    assert _paths(p) == {"/files/*", "/about"}


def test_arquivos_ignorados_nao_viram_rota_nem_pagina(tmp_path):
    p = _projeto_tanstack(tmp_path, ["index.tsx", "-helper.tsx"])
    (p / "src" / "routeTree.gen.ts").write_text("x", encoding="utf-8")
    manifest = LovableScanner(str(p)).scan()
    assert {r["path"] for r in manifest["routes"]} == {"/"}
    assert not any("-helper" in pg or "routeTree.gen" in pg for pg in manifest["pages"])


def test_funcao_c3_e_identificador_valido_e_unico():
    rotas = [
        {"path": "/posts/:postId", "component": "posts.$postId.tsx",
         "source_file": "posts.$postId.tsx", "type": "tanstack-file-route"},
        {"path": "/a", "component": "index.tsx", "source_file": "a/index.tsx",
         "type": "tanstack-file-route"},
        {"path": "/b", "component": "index.tsx", "source_file": "b/index.tsx",
         "type": "tanstack-file-route"},
        {"path": "/x", "component": "Home", "source_file": "App.tsx", "type": "react-router"},
    ]
    funcoes = _funcoes_unicas_c3(rotas, "dom")
    assert len(set(funcoes)) == len(rotas)
    for nome in funcoes:
        assert nome.isidentifier() and not keyword.iskeyword(nome), nome
        assert nome.startswith("renderizar_")
        assert "tsx" not in nome


def _origem_com_envs(tmp_path: Path, nomes) -> Path:
    origem = tmp_path / "origem"
    origem.mkdir()
    for nome in nomes:
        (origem / nome).write_text("CHAVE=segredo-real\n", encoding="utf-8")
    return origem


def test_liberator_nao_copia_nenhum_env_real(tmp_path):
    envs = [".env", ".env.production", ".env.staging", ".env.development.local",
            ".env.production.local", ".env.local"]
    origem = _origem_com_envs(tmp_path, envs + [".env.example"])
    destino = tmp_path / "destino"
    FrontendLiberator(str(origem), str(destino)).copy_and_liberate()
    copiados = {f for f in os.listdir(destino)}
    assert ".env.example" in copiados
    assert not (copiados & set(envs)), copiados & set(envs)


def test_liberator_ignora_builds_ssr(tmp_path):
    origem = _origem_com_envs(tmp_path, [])
    for d in (".output", ".vinxi", ".wrangler"):
        (origem / d).mkdir()
        (origem / d / "bundle.js").write_text("x", encoding="utf-8")
    (origem / "src.ts").write_text("export {}", encoding="utf-8")
    destino = tmp_path / "destino"
    FrontendLiberator(str(origem), str(destino)).copy_and_liberate()
    assert sorted(os.listdir(destino)) == ["src.ts"]
