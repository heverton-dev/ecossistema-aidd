from pathlib import Path

arquivo = Path("modulos/02-triade-motores/fluxo-01-pure/core/aidd-pure/scripts/phases/08_implementador.py")
linhas = arquivo.read_text(encoding="utf-8").splitlines(keepends=True)

# Procurar linha com 'if "validador" in mod:'
idx_inicio = -1
for i, l in enumerate(linhas):
    if 'if "validador" in mod:' in l:
        idx_inicio = i
        break

idx_fim = -1
for i in range(idx_inicio, len(linhas)):
    if 'if not linhas_chamadas:' in l or 'conteudo_teste = (' in linhas[i]:
        idx_fim = i
        break

print(f"Bloco encontrado entre linhas {idx_inicio} e {idx_fim}")

novo_bloco = """            if "validador" in mod and "validar_payload" in codigo:
                linhas_import.append(f"from {mod} import validar_payload")
                linhas_chamadas.append("    assert validar_payload({'id': 'e2e-1', 'nome': 'Teste'}) is True")
            elif "servico" in mod and "ServicoDominio" in codigo:
                linhas_import.append(f"from {mod} import ServicoDominio")
                linhas_chamadas.append("    servico = ServicoDominio()")
                linhas_chamadas.append("    assert servico.executar({'id': 'e2e-1', 'acao': 'ok'})['sucesso'] is True")
            elif ("persistencia" in mod or "sqlite" in mod) and "RepositorioSQLite" in codigo:
                caminho_rel = script.get('caminho_relativo', '')
                if caminho_rel.startswith(('infrastructure/', 'infrastructure\\\\')):
                    linhas_import.append(
                        f"try:\\n"
                        f"    from infrastructure.{mod} import RepositorioSQLite\\n"
                        f"except ImportError:\\n"
                        f"    from {mod} import RepositorioSQLite"
                    )
                else:
                    linhas_import.append(
                        f"try:\\n"
                        f"    from {mod} import RepositorioSQLite\\n"
                        f"except ImportError:\\n"
                        f"    from infrastructure.{mod} import RepositorioSQLite"
                    )
                linhas_chamadas.append("    repo = RepositorioSQLite(':memory:')")
                linhas_chamadas.append("    assert repo.salvar('e2e-1', 'conteudo') is True")
                linhas_chamadas.append("    assert repo.buscar('e2e-1') == 'conteudo'")
            elif "quarteto" in mod and "obter_openapi_spec" in codigo:
                linhas_import.append(f"from {mod} import obter_openapi_spec")
                linhas_chamadas.append("    assert obter_openapi_spec()['openapi'] == '3.1.0'")
            else:
                simbolo = self._extrair_simbolo_publico(codigo)
                caminho_rel = script.get('caminho_relativo', '')
                prefixo = "infrastructure." if caminho_rel.startswith(('infrastructure/', 'infrastructure\\\\')) else ""
                if simbolo:
                    linhas_import.append(f"try:\\n    from {prefixo}{mod} import {simbolo}\\nexcept ImportError:\\n    from {mod} import {simbolo}")
                    linhas_chamadas.append(f"    assert {simbolo} is not None")
                else:
                    linhas_import.append(f"import {mod} as _mod_{mod}")
                    linhas_chamadas.append(f"    assert _mod_{mod} is not None")
"""

linhas[idx_inicio:idx_fim] = [novo_bloco + "\n"]
arquivo.write_text("".join(linhas), encoding="utf-8")
print("[OK] Bloco substituído com sucesso!")
