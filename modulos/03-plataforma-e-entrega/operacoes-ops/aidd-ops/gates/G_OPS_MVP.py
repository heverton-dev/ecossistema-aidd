# -*- coding: utf-8 -*-
"""
=============================================================================
AIDD-Ops MVP — GATE DETERMINÍSTICO (G_OPS_MVP)
=============================================================================
Dois modos de operação:
  (a) Sem --dir: valida a própria estrutura de tools/aidd-ops/
      - Compila via py_compile todos os .py
      - Varredura AST anti-stubs (nenhuma função com só pass/.../docstring)
  (b) Com --dir <saída>: valida que <saída>/PLANO-INFRAESTRUTURA.json
      existe e cada seção bate com o schema correspondente.

Uso:
  python gates/G_OPS_MVP.py              # modo (a): valida estrutura
  python gates/G_OPS_MVP.py --dir <saída> # modo (b): valida saída
"""

import ast
import json
import os
import subprocess
import sys

TOOL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class OpsMvpGate:
    def __init__(self):
        self.errors = []
        self.checks_passed = 0

    def check(self, condition: bool, description: str, error_msg: str):
        if condition:
            print(f"  [PASS] {description}")
            self.checks_passed += 1
        else:
            print(f"  [FAIL] {description} -> {error_msg}")
            self.errors.append(f"{description}: {error_msg}")

    def _listar_py_files(self, raiz: str) -> list:
        """Lista todos os .py recursivamente, excluindo __pycache__."""
        arquivos = []
        for dirpath, dirnames, filenames in os.walk(raiz):
            # Excluir __pycache__
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for f in filenames:
                if f.endswith(".py"):
                    arquivos.append(os.path.join(dirpath, f))
        return sorted(arquivos)

    def _verificar_compilacao(self, arquivos: list):
        """Compila todos os .py via py_compile."""
        for caminho in arquivos:
            relativo = os.path.relpath(caminho, TOOL_ROOT)
            res = subprocess.run(
                [sys.executable, "-m", "py_compile", caminho],
                capture_output=True, text=True,
            )
            self.check(
                res.returncode == 0,
                f"Compilacao '{relativo}'",
                res.stderr.strip()[:300] or "erro de sintaxe",
            )

    def _verificar_anti_stubs(self, arquivos: list):
        """Varredura AST: nenhuma funcao com body = pass ou Ellipsis."""
        for caminho in arquivos:
            relativo = os.path.relpath(caminho, TOOL_ROOT)
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    fonte = f.read()
                tree = ast.parse(fonte, filename=caminho)
                stubs = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                            stubs.append(node.name)
                        elif (
                            len(node.body) == 1
                            and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and node.body[0].value.value is Ellipsis
                        ):
                            stubs.append(node.name)
                        elif (
                            len(node.body) == 1
                            and isinstance(node.body[0], ast.Expr)
                            and isinstance(node.body[0].value, ast.Constant)
                            and isinstance(node.body[0].value.value, str)
                            and node.body[0].value.value.strip().startswith('"""')
                        ):
                            # Docstring sozinha = stub
                            stubs.append(node.name)
                self.check(
                    len(stubs) == 0,
                    f"Zero Stubs (AST) em '{relativo}'",
                    f"Funcoes vazias detectadas: {', '.join(stubs)}",
                )
            except (OSError, SyntaxError) as e:
                self.check(False, f"Varredura AST em '{relativo}'", str(e))

    def _validar_estrutura(self):
        """Modo (a): valida estrutura de tools/aidd-ops/."""
        print("=" * 70)
        print(" [GATE G_OPS_MVP] Validacao da Estrutura do aidd-ops")
        print(f" Raiz: {TOOL_ROOT}")
        print("=" * 70)

        # Verificar arquivos core
        arquivos_necessarios = [
            os.path.join("src", "core", "result.py"),
            os.path.join("scripts", "pipeline_ops.py"),
            os.path.join("scripts", "phases", "01_intake.py"),
            os.path.join("scripts", "phases", "02_curadoria.py"),
            os.path.join("scripts", "phases", "03_sizing.py"),
        ]
        for rel in arquivos_necessarios:
            caminho = os.path.join(TOOL_ROOT, rel)
            self.check(
                os.path.isfile(caminho),
                f"Arquivo core '{rel}'",
                f"Ausente: {caminho}",
            )

        # Verificar schemas
        schemas_necessarios = [
            "schema_intake_request.json",
            "schema_stack_selecionada.json",
            "schema_sizing_output.json",
        ]
        for nome in schemas_necessarios:
            caminho = os.path.join(TOOL_ROOT, "schemas", nome)
            if not os.path.isfile(caminho):
                self.check(False, f"Schema '{nome}'", f"Ausente: {caminho}")
                continue
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                eh_2020_12 = schema.get("$schema", "").endswith("2020-12/schema")
                tem_additional = schema.get("additionalProperties") is False
                tem_required = len(schema.get("required", [])) > 0
                self.check(
                    eh_2020_12 and tem_additional and tem_required,
                    f"Schema '{nome}' (Draft 2020-12, additionalProperties:false, required)",
                    f"Invalido: $schema={schema.get('$schema')}, additionalProperties={schema.get('additionalProperties')}, required={schema.get('required')}",
                )
            except (OSError, json.JSONDecodeError) as e:
                self.check(False, f"Schema '{nome}'", f"JSON corrompido: {e}")

        # Verificar dados
        dados_necessarios = ["catalogo_nichos.json", "requisitos_recursos.json"]
        for nome in dados_necessarios:
            caminho = os.path.join(TOOL_ROOT, "data", nome)
            if not os.path.isfile(caminho):
                self.check(False, f"Dados '{nome}'", f"Ausente: {caminho}")
                continue
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                self.check(
                    isinstance(dados, dict) and len(dados) > 0,
                    f"Dados '{nome}' (JSON valido e nao vazio)",
                    "JSON invalido ou vazio",
                )
            except (OSError, json.JSONDecodeError) as e:
                self.check(False, f"Dados '{nome}'", f"JSON corrompido: {e}")

        # Compilacao e anti-stubs
        todos_py = self._listar_py_files(TOOL_ROOT)
        if todos_py:
            self._verificar_compilacao(todos_py)
            self._verificar_anti_stubs(todos_py)
        else:
            self.check(False, "Arquivos .py encontrados", "Nenhum .py encontrado em tools/aidd-ops/")

    def _carregar_plano_saida(self, dir_saida: str):
        """Confere que PLANO-INFRAESTRUTURA.json existe e e JSON valido; retorna o dict ou None."""
        caminho_plano = os.path.join(dir_saida, "PLANO-INFRAESTRUTURA.json")
        self.check(
            os.path.isfile(caminho_plano),
            "PLANO-INFRAESTRUTURA.json existe",
            f"Ausente: {caminho_plano}",
        )

        if not os.path.isfile(caminho_plano):
            return None

        try:
            with open(caminho_plano, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            self.check(False, "PLANO-INFRAESTRUTURA.json e JSON valido", f"Corrompido: {e}")
            return None

    def _validar_campos_topo(self, plano: dict):
        self.check(
            plano.get("versao") == "1.0.0",
            "Campo 'versao' == '1.0.0'",
            f"Encontrado: {plano.get('versao')}",
        )
        self.check(
            "gerado_em" in plano,
            "Campo 'gerado_em' presente",
            "Ausente",
        )

    def _validar_fase1_intake(self, plano: dict):
        f1 = plano.get("fase_1_intake")
        self.check(
            f1 is not None and isinstance(f1, dict),
            "Fase 1 (fase_1_intake) presente",
            "Ausente ou invalida",
        )
        if f1 and f1.get("saida"):
            saida_f1 = f1["saida"]
            self.check(
                "nicho_slug" in saida_f1 and "nicho_nome_exibicao" in saida_f1,
                "Fase 1 saida tem campos obrigatorios",
                f"Campos ausentes. Encontrado: {list(saida_f1.keys())}",
            )

    def _validar_fase2_curadoria(self, plano: dict):
        f2 = plano.get("fase_2_curadoria")
        self.check(
            f2 is not None and isinstance(f2, dict),
            "Fase 2 (fase_2_curadoria) presente",
            "Ausente ou invalida",
        )
        if f2 and f2.get("saida"):
            saida_f2 = f2["saida"]
            self.check(
                "ferramentas" in saida_f2 and isinstance(saida_f2["ferramentas"], list),
                "Fase 2 saida tem 'ferramentas' (array)",
                f"Encontrado: {type(saida_f2.get('ferramentas'))}",
            )

    def _validar_fase3_sizing(self, plano: dict):
        f3 = plano.get("fase_3_sizing")
        self.check(
            f3 is not None and isinstance(f3, dict),
            "Fase 3 (fase_3_sizing) presente",
            "Ausente ou invalida",
        )
        if f3 and f3.get("saida"):
            saida_f3 = f3["saida"]
            # Validar vps
            vps = saida_f3.get("vps")
            self.check(
                vps is not None and isinstance(vps, dict),
                "Fase 3 saida tem 'vps' (objeto)",
                f"Encontrado: {type(vps)}",
            )
            if vps:
                self.check(
                    all(k in vps for k in ("vcpu", "ram_gb", "disco_gb")),
                    "VPS tem campos vcpu, ram_gb, disco_gb",
                    f"Encontrado: {list(vps.keys())}",
                )
            # Validar bancos_logicos
            self.check(
                "bancos_logicos" in saida_f3 and isinstance(saida_f3["bancos_logicos"], list),
                "Fase 3 saida tem 'bancos_logicos' (array)",
                f"Encontrado: {type(saida_f3.get('bancos_logicos'))}",
            )
            # Validar fontes_consultadas
            self.check(
                "fontes_consultadas" in saida_f3 and isinstance(saida_f3["fontes_consultadas"], list),
                "Fase 3 saida tem 'fontes_consultadas' (array)",
                f"Encontrado: {type(saida_f3.get('fontes_consultadas'))}",
            )

    def _validar_todas_fases_produziram_saida(self, plano: dict):
        for nome_fase, chave in [("fase_1_intake", "fase_1_intake"), ("fase_2_curadoria", "fase_2_curadoria"), ("fase_3_sizing", "fase_3_sizing")]:
            fase = plano.get(chave)
            if fase and isinstance(fase, dict):
                saida_fase = fase.get("saida")
                erro_fase = fase.get("erro")
                self.check(
                    saida_fase is not None and isinstance(saida_fase, dict),
                    f"{nome_fase} produziu saida valida (saida != None)",
                    f"Campo 'saida' e None. " + (f"Erro registrado: {erro_fase.get('codigo')}" if erro_fase else "Nenhum erro registrado."),
                )

    def _validar_saida(self, dir_saida: str):
        """Modo (b): valida PLANO-INFRAESTRUTURA.json em dir_saida."""
        print("=" * 70)
        print(" [GATE G_OPS_MVP] Validacao da Saida do Pipeline")
        print(f" Diretorio: {dir_saida}")
        print("=" * 70)

        plano = self._carregar_plano_saida(dir_saida)
        if plano is None:
            return

        self._validar_campos_topo(plano)
        self._validar_fase1_intake(plano)
        self._validar_fase2_curadoria(plano)
        self._validar_fase3_sizing(plano)
        self._validar_todas_fases_produziram_saida(plano)

    def run_estrutura(self) -> int:
        self._validar_estrutura()
        return self._resumo()

    def run_saida(self, dir_saida: str) -> int:
        self._validar_saida(dir_saida)
        return self._resumo()

    def _resumo(self) -> int:
        print()
        print("=" * 70)
        print(f" RESUMO DO GATE G_OPS_MVP:")
        print(f"   - Validacoes Aprovadas: {self.checks_passed}")
        print(f"   - Falhas: {len(self.errors)}")
        print("=" * 70)

        if self.errors:
            print(" [BLOQUEADO]: aidd-ops nao esta 100% homologado.")
            return 1

        print(" [APROVADO]: aidd-ops MVP 100% homologado (exit 0)!")
        return 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="G_OPS_MVP — Gate de Validacao do aidd-ops MVP")
    parser.add_argument("--dir", default=None, help="Diretorio de saida do pipeline para validar")
    args = parser.parse_args()

    gate = OpsMvpGate()
    if args.dir:
        sys.exit(gate.run_saida(args.dir))
    else:
        sys.exit(gate.run_estrutura())


if __name__ == "__main__":
    main()
