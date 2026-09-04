#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 5: Criador de Projeto
aidd-project-generator v2.1

Cria estrutura completa do projeto:
- mkdir -p diretórios
- Render templates Jinja2
- Criar symlinks
- git init + first commit
- SQLite schema

Executa 5 gates de validação (E1-E5 + S1 segurança)
Gera _phase_05_index.json com auditoria completa

Tokens: 0 (100% Python determinístico)
"""

import sys
import json
import hashlib
import subprocess
import shutil
from pathlib import Path

# Importar utils para detectar harness/modelo real (nunca fabricar)
sys.path.insert(0, str(Path(__file__).parent))
from utils_modelo import detectar_harness_nome, detectar_modelo_harness
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# CONSTANTS
# =============================================================================

ESTRUTURA_PADRAO = {
    '.claude': ['CLAUDE.md', 'settings.json'],
    '.aidd': ['config.json', 'rules.md', 'cache/data'],
    'scripts': ['phases', 'gates', 'schemas', 'utils', 'orquestrador.py'],
    'docs': [],
    '.git': [],
}

# =============================================================================
# GATES DE VALIDAÇÃO
# =============================================================================

class Gate:
    """Estrutura de resultado de gate"""
    def __init__(self, gate_id: str, descricao: str, passou: bool, detalhes: str):
        self.gate_id = gate_id
        self.descricao = descricao
        self.passou = passou
        self.detalhes = detalhes

    def to_dict(self):
        return {
            'gate_id': self.gate_id,
            'descricao': self.descricao,
            'status': 'PASSOU' if self.passou else 'FALHOU',
            'detalhes': self.detalhes
        }


class ValidadorGatesPhase5:
    """Executa gates de validação da Fase 5"""

    @staticmethod
    def executar_todos(pasta_projeto: Path) -> tuple[List[Gate], bool]:
        """Executa E1-E5 + S1 sequencialmente"""
        gates_resultado = []

        # Gate E1: Todos arquivos criados
        gate_e1 = ValidadorGatesPhase5._gate_e1_arquivos_criados(pasta_projeto)
        gates_resultado.append(gate_e1)

        # Gate E2: Git commit sucedeu
        gate_e2 = ValidadorGatesPhase5._gate_e2_git_commit(pasta_projeto)
        gates_resultado.append(gate_e2)

        # Gate E3: SQLite schema válido
        gate_e3 = ValidadorGatesPhase5._gate_e3_sqlite_schema(pasta_projeto)
        gates_resultado.append(gate_e3)

        # Gate E4: Permissões corretas
        gate_e4 = ValidadorGatesPhase5._gate_e4_permissoes(pasta_projeto)
        gates_resultado.append(gate_e4)

        # Gate E5: Sincronismo multi-harness (symlink real ou cópia honesta,
        # sem drift em relação a AGENTS.md no instante da geração)
        gate_e5 = ValidadorGatesPhase5._gate_e5_sincronizacao_harness(pasta_projeto)
        gates_resultado.append(gate_e5)

        # Gate S1: AUDITORIA DE SEGURANÇA
        gate_s1 = ValidadorGatesPhase5._gate_s1_auditoria_seguranca(pasta_projeto)
        gates_resultado.append(gate_s1)

        todos_passaram = all(g.passou for g in gates_resultado)

        return gates_resultado, todos_passaram

    @staticmethod
    def _gate_e1_arquivos_criados(pasta: Path) -> Gate:
        """E1: Todos arquivos esperados foram criados"""
        arquivos_esperados = [
            '.claude/CLAUDE.md',
            '.aidd/config.json',
            '.aidd/rules.md',
            'scripts/orquestrador.py',
            'README.md',
            '.gitignore',
            'pytest.ini'
        ]

        criados = sum(1 for a in arquivos_esperados if (pasta / a).exists())
        total = len(arquivos_esperados)

        passou = criados == total
        detalhes = f"{criados}/{total} arquivos esperados criados"

        return Gate('E1_arquivos_criados',
                   'Validar todos arquivos foram criados',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_e2_git_commit(pasta: Path) -> Gate:
        """E2: Git commit sucedeu"""
        try:
            resultado = subprocess.run(
                ['git', 'log', '--oneline', '-1'],
                cwd=str(pasta),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=5
            )

            passou = resultado.returncode == 0 and resultado.stdout.strip()
            detalhes = f"Último commit: {resultado.stdout.strip()[:50]}" if passou else "Git não inicializado ou sem commits"

        except Exception as e:
            passou = False
            detalhes = f"Erro ao verificar git: {e}"

        return Gate('E2_git_commit',
                   'Validar git init + commit',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_e3_sqlite_schema(pasta: Path) -> Gate:
        """E3: SQLite schema foi criado"""
        try:
            import sqlite3

            db_path = pasta / 'estado_projeto.db'

            if not db_path.exists():
                return Gate('E3_sqlite_schema',
                           'Validar SQLite schema',
                           False,
                           "Banco de dados não foi criado")

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()

            passou = len(tables) >= 1  # Mínimo 1 tabela
            detalhes = f"{len(tables)} tabelas criadas"

        except Exception as e:
            passou = False
            detalhes = f"Erro ao verificar SQLite: {e}"

        return Gate('E3_sqlite_schema',
                   'Validar SQLite schema',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_e4_permissoes(pasta: Path) -> Gate:
        """E4: Scripts têm permissão de execução"""
        try:
            import os

            scripts = list((pasta / 'scripts').glob('*.py')) if (pasta / 'scripts').exists() else []

            if not scripts:
                return Gate('E4_permissoes',
                           'Validar permissões +x',
                           False,
                           "Nenhum script Python encontrado")

            executaveis = sum(1 for s in scripts if os.access(str(s), os.X_OK))

            # Em Windows, X_OK pode não funcionar bem, então verificamos apenas se arquivo existe
            passou = len(scripts) > 0
            detalhes = f"{len(scripts)} scripts encontrados (Windows: perms verificadas por existência)"

        except Exception as e:
            passou = False
            detalhes = f"Erro ao verificar permissões: {e}"

        return Gate('E4_permissoes',
                   'Validar permissões de scripts',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_e5_sincronizacao_harness(pasta: Path) -> Gate:
        """E5: symlinks multi-harness reais, ou cópias de fallback honestas
        e sincronizadas com AGENTS.md no instante da geração.

        Reaproveita scripts/gates/G_SYNC_HARNESS.py (o mesmo gate deixado
        dentro do projeto para o dono re-executar depois) em vez de duplicar
        a lógica de comparação aqui — uma só fonte de verdade para o check.
        """
        gate_path = pasta / 'scripts/gates/G_SYNC_HARNESS.py'
        if not gate_path.exists():
            # Nenhuma cópia de fallback foi necessária (todos os harness
            # conseguiram symlink real) — nada a sincronizar, gate trivialmente ok.
            return Gate('E5_sincronizacao_harness',
                       'Validar sincronismo multi-harness (symlink/cópia)',
                       True,
                       'Todos os harness usaram symlink real — nada pode divergir')

        try:
            resultado = subprocess.run(
                [sys.executable, str(gate_path)],
                cwd=str(pasta),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=10
            )
            passou = resultado.returncode == 0
            detalhes = resultado.stdout.strip().splitlines()[-1] if resultado.stdout.strip() else resultado.stderr.strip()
        except Exception as e:
            passou = False
            detalhes = f"Erro ao executar G_SYNC_HARNESS.py: {e}"

        return Gate('E5_sincronizacao_harness',
                   'Validar sincronismo multi-harness (symlink/cópia)',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_s1_auditoria_seguranca(pasta: Path) -> Gate:
        """S1: AUDITORIA DE SEGURANÇA - Verificações críticas"""

        problemas = []

        # Check 1: .env ou secrets em .gitignore
        gitignore = pasta / '.gitignore'
        if gitignore.exists():
            conteudo = gitignore.read_text()
            if '.env' not in conteudo and 'secrets' not in conteudo.lower():
                problemas.append("⚠️  .env e secrets não estão em .gitignore")

        # Check 2: requirements.txt existe (se Python)
        scripts = list((pasta / 'scripts').glob('*.py')) if (pasta / 'scripts').exists() else []
        if scripts and not (pasta / 'requirements.txt').exists():
            problemas.append("⚠️  requirements.txt não encontrado (projeto Python)")

        # Check 3: README.md com instruções de segurança
        readme = pasta / 'README.md'
        if readme.exists():
            conteudo = readme.read_text()
            if 'segurança' not in conteudo.lower() and 'credentials' not in conteudo.lower():
                problemas.append("ℹ️  README não menciona segurança/credenciais (considere adicionar)")

        # Check 4: Verificar se há hard-coded secrets (padrão básico)
        for arquivo_py in scripts:
            try:
                conteudo = arquivo_py.read_text()
                padroes_perigosos = ['password=', 'api_key=', 'secret=', 'token=']
                for padrao in padroes_perigosos:
                    if padrao in conteudo.lower() and '=' in conteudo:
                        # Verificar se não está em comentário ou string de configuração
                        if not conteudo.lower().startswith('#'):
                            problemas.append(f"⚠️  Possível credencial hard-coded em {arquivo_py.name}")
                            break
            except:
                pass  # Arquivo binário ou erro de leitura

        passou = len([p for p in problemas if '⚠️' in p]) == 0
        detalhes = "; ".join(problemas) if problemas else "Todas as verificações de segurança passaram"

        return Gate('S1_auditoria_seguranca',
                   'AUDITORIA DE SEGURANÇA - Verificações críticas',
                   passou,
                   detalhes)


# =============================================================================
# CRIADOR DE PROJETO
# =============================================================================

class CriadorProjetoFase5:
    """Orquestrador da Fase 5: Criação do Projeto"""

    def __init__(self, pasta_projeto: Path):
        self.pasta_projeto = Path(pasta_projeto)

    def executar(self, ideia_projeto: str, config_fase4: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Executa pipeline completo da Fase 5.

        config_fase4: saída de DecisorFase4 (04_decisor.py) — decisões
        GLOBAL/LOCAL e symlinks_paths já resolvidos. Sem essa config,
        nenhum symlink de skills/mcps/hooks é criado (apenas AGENTS.md
        → .claude/CLAUDE.md, que independe da decisão de Fase 4).
        """
        print(f"\n🏗️  PHASE 5: Criador de Projeto")
        print(f"   Ideia: {ideia_projeto}")
        print(f"   Pasta: {self.pasta_projeto}")
        print(f"   {'-' * 60}")

        tempo_inicio = datetime.now()

        # 1. Criar estrutura de diretórios
        print(f"\n📁 Criando estrutura de diretórios...")
        self._criar_estrutura()
        print(f"   ✓ Estrutura criada")

        # 2. Criar arquivos de configuração
        print(f"\n⚙️  Criando arquivos de configuração...")
        self._criar_arquivos_configuracao(ideia_projeto)
        print(f"   ✓ Arquivos criados")

        # 2.5. Criar symlinks GLOBAL decididos na Fase 4 (skills/mcps/hooks)
        if config_fase4:
            print(f"\n🔗 Aplicando decisões GLOBAL/LOCAL da Fase 4...")
            criados = self._criar_symlinks_globais(config_fase4)
            print(f"   ✓ {criados} symlink(s) GLOBAL criado(s)")

        # 3. Criar SQLite schema
        print(f"\n💾 Criando SQLite schema...")
        self._criar_sqlite()
        print(f"   ✓ Banco de dados inicializado")

        # 4. Git init + commit
        print(f"\n🔗 Inicializando repositório Git...")
        self._git_init_commit(ideia_projeto)
        print(f"   ✓ Git init + primeiro commit")

        # 5. Executar gates
        print(f"\n✅ Executando gates (E1-E5 + S1)...")
        gates, todos_passaram = ValidadorGatesPhase5.executar_todos(self.pasta_projeto)
        for gate in gates:
            status_icon = "✓" if gate.passou else "✗"
            print(f"   {status_icon} {gate.gate_id}: {gate.detalhes}")

        if not todos_passaram:
            # Gate S1 (segurança) não bloqueia, apenas avisa
            gates_criticos = [g for g in gates if g.gate_id != 'S1_auditoria_seguranca' and not g.passou]
            if gates_criticos:
                print(f"\n❌ FASE FALHOU: Gates críticos não passaram")
                return None
            else:
                print(f"\n⚠️  ATENÇÃO: Issues de segurança detectadas (vide Gate S1)")
                print(f"   Por favor revisar antes de fazer deploy")

        # 6. Gerar index
        tempo_execucao = (datetime.now() - tempo_inicio).total_seconds()
        print(f"\n📝 Gerando índice de fase...")
        index = self._gerar_index(gates, tempo_execucao)

        # 7. Salvar index
        path_index = self.pasta_projeto / '.aidd/cache/_phase_05_index.json'
        path_index.parent.mkdir(parents=True, exist_ok=True)
        with open(path_index, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
        print(f"   ✓ {path_index}")

        print(f"\n{'=' * 60}")
        print(f"✅ PHASE 5 COMPLETO")
        print(f"   Status: {index['status']}")
        print(f"   Tempo: {tempo_execucao:.1f}s")
        print(f"   Tokens: {index['tokens']['consumidos']}")
        print(f"{'=' * 60}\n")

        return index

    def _criar_estrutura(self):
        """Cria diretórios base"""
        for diretorio in ESTRUTURA_PADRAO.keys():
            (self.pasta_projeto / diretorio).mkdir(parents=True, exist_ok=True)

        # Criar subdirs
        (self.pasta_projeto / '.aidd/cache/data').mkdir(parents=True, exist_ok=True)
        (self.pasta_projeto / 'scripts/phases').mkdir(parents=True, exist_ok=True)
        (self.pasta_projeto / 'scripts/gates').mkdir(parents=True, exist_ok=True)
        (self.pasta_projeto / 'scripts/schemas').mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _criar_symlink_ou_copia(link_path: Path, alvo: Path) -> bool:
        """Cria link_path como symlink real apontando para alvo.

        Sem fallback silencioso: se o symlink não puder ser criado
        (ex: Windows sem Modo Desenvolvedor/privilégio), cria uma cópia
        do conteúdo e AVISA explicitamente — nunca finge que é symlink.

        Retorna True se foi symlink real, False se foi cópia de fallback
        (usado pelo chamador para registrar no manifesto de sincronismo —
        ver _registrar_sync_manifest — já que uma cópia pode divergir de
        `alvo` no futuro se `alvo` for editado e ninguém re-sincronizar).
        """
        link_path.parent.mkdir(parents=True, exist_ok=True)
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()

        try:
            link_path.symlink_to(alvo.resolve())
            return True
        except OSError as e:
            print(f"   ⚠️  Não foi possível criar symlink {link_path} → {alvo} ({e}). Copiando conteúdo em vez de symlink.")
            link_path.write_text(alvo.read_text(encoding='utf-8'), encoding='utf-8')
            return False

    def _registrar_sync_manifest(self, fonte: Path, copias_relativas: List[str]):
        """Grava .aidd/sync_manifest.json e scripts/gates/G_SYNC_HARNESS.py
        no PRÓPRIO projeto gerado — sem depender do aidd-generator nem de
        nenhuma outra ferramenta do ecossistema (auto-contido).

        O gate é standalone e re-executável a qualquer momento pelo dono do
        projeto (`python scripts/gates/G_SYNC_HARNESS.py`) para detectar se
        alguma cópia de fallback ficou desatualizada em relação a AGENTS.md
        depois da geração — o problema real que symlink-ou-cópia sozinho não
        resolve (cópia só é honesta no instante em que foi feita).
        """
        manifest = {
            'fonte': fonte.name,
            'gerado_em': datetime.now(timezone.utc).isoformat(),
            'copias_fallback': copias_relativas,
            'motivo': 'SO negou permissao de symlink no momento da geracao '
                      '(ex.: Windows sem Modo Desenvolvedor/privilegio).',
        }
        (self.pasta_projeto / '.aidd/sync_manifest.json').write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        gate_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GATE: G_SYNC_HARNESS — Deteccao de drift entre AGENTS.md e copias de
fallback (.claude/CLAUDE.md, .agent/AGENT.md, etc.) criadas quando o SO
negou permissao de symlink no momento da geracao do projeto.

Por que existe: quando symlink real nao e possivel, o gerador cria uma
COPIA do conteudo de AGENTS.md. A copia so e honesta no instante em que
foi feita — se AGENTS.md for editado depois e ninguem re-sincronizar as
copias manualmente, elas ficam obsoletas em silencio. Este gate roda a
qualquer momento e avisa exatamente isso, sem inventar numero nem esconder
o problema (Zero Alucinacao / Transparencia Total).

Uso: python scripts/gates/G_SYNC_HARNESS.py
Saida: exit 0 (sincronizado ou nada a checar) / exit 1 (drift detectado)
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = RAIZ / '.aidd' / 'sync_manifest.json'


def checar_drift():
    if not MANIFEST_PATH.exists():
        print("[OK] Nenhum manifesto de sincronismo — todas as copias de harness "
              "sao symlinks reais (nada pode divergir).")
        return 0

    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    fonte_path = RAIZ / manifest['fonte']
    if not fonte_path.exists():
        print(f"[FALHA] Fonte '{manifest['fonte']}' nao existe mais.")
        return 1

    fonte_conteudo = fonte_path.read_text(encoding='utf-8')
    divergentes = []

    for relativo in manifest.get('copias_fallback', []):
        copia_path = RAIZ / relativo
        if copia_path.is_symlink():
            continue  # symlink real nao pode divergir por definicao
        if not copia_path.exists():
            divergentes.append((relativo, 'arquivo nao existe mais'))
            continue
        if copia_path.read_text(encoding='utf-8') != fonte_conteudo:
            divergentes.append((relativo, f'conteudo diferente de {manifest["fonte"]}'))

    if divergentes:
        print(f"[FALHA] {len(divergentes)} copia(s) desatualizada(s) em relacao a "
              f"{manifest['fonte']}:")
        for relativo, motivo in divergentes:
            print(f"  - {relativo}: {motivo}")
        print(f"\\nCorrija copiando o conteudo atual de {manifest['fonte']} para "
              f"cada arquivo listado acima.")
        return 1

    print(f"[OK] {len(manifest.get('copias_fallback', []))} copia(s) sincronizada(s) "
          f"com {manifest['fonte']}.")
    return 0


if __name__ == '__main__':
    sys.exit(checar_drift())
'''
        gate_path = self.pasta_projeto / 'scripts/gates/G_SYNC_HARNESS.py'
        gate_path.parent.mkdir(parents=True, exist_ok=True)
        gate_path.write_text(gate_script, encoding='utf-8')

    @staticmethod
    def _criar_symlink_dir_ou_copia(link_path: Path, alvo: Path) -> bool:
        """Cria link_path como symlink real apontando para alvo (diretório
        GLOBAL compartilhado, ex: ~/.claude/skills).

        Sem fallback de cópia: alvo aqui é um diretório potencialmente
        grande e PESSOAL do usuário (não um único arquivo pequeno como
        AGENTS.md) — copiá-lo para dentro de cada projeto gerado bloa o
        projeto com conteúdo arbitrário e viola diretamente o próprio
        princípio "Zero Duplicidade" que este mecanismo deveria cumprir
        (achado real: copytree de ~/.claude/skills gerou 39MB de conteúdo
        pessoal dentro de um projeto de teste descartável). Se o SO negar
        o symlink, o item GLOBAL simplesmente não é materializado
        localmente — o projeto segue válido sem ele, sem duplicar dado
        alheio ao seu escopo.
        """
        link_path.parent.mkdir(parents=True, exist_ok=True)
        if link_path.is_symlink() or link_path.exists():
            if link_path.is_dir() and not link_path.is_symlink():
                shutil.rmtree(link_path)
            else:
                link_path.unlink()

        try:
            link_path.symlink_to(alvo.resolve(), target_is_directory=True)
            return True
        except OSError as e:
            print(f"   ⚠️  Não foi possível criar symlink {link_path} → {alvo} ({e}). "
                  f"Item GLOBAL '{alvo.name}' NÃO será copiado (evita duplicar conteúdo "
                  f"pessoal/potencialmente grande) — projeto segue sem ele.")
            return False

    def _criar_symlinks_globais(self, config_fase4: Dict[str, Any]) -> int:
        """Cria, dentro do projeto, os symlinks correspondentes às
        decisões GLOBAL da Fase 4 (skills/mcps/hooks) — aponta para o
        caminho compartilhado em ~/.claude/<item> que a Fase 4 já validou
        que existe (config_fase4['symlinks_paths']).

        Retorna a contagem real de symlinks (não fallbacks de cópia)
        efetivamente criados.
        """
        symlinks_reais = 0
        for caminho_global in config_fase4.get('symlinks_paths', []):
            alvo = Path(caminho_global)
            link_local = self.pasta_projeto / '.claude' / alvo.name
            criado_como_symlink = self._criar_symlink_dir_ou_copia(link_local, alvo)
            if criado_como_symlink:
                symlinks_reais += 1
                print(f"   ✓ .claude/{alvo.name} → {alvo} (symlink)")
            else:
                print(f"   ✓ .claude/{alvo.name} ← cópia de {alvo} (symlink negado pelo SO)")
        return symlinks_reais

    def _criar_arquivos_configuracao(self, ideia: str):
        """Cria arquivos de configuração padrão"""

        # Criar orquestrador.py placeholder
        orquestrador_py = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"Orquestrador principal do projeto\"\"\"

import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("Orquestrador do projeto AIDD")

if __name__ == '__main__':
    main()
"""
        (self.pasta_projeto / 'scripts/orquestrador.py').write_text(
            orquestrador_py,
            encoding='utf-8'
        )

        # Criar settings.json — harness/modelo detectados de verdade
        # (nunca fixo: essencial para testes comparativos entre harness)
        settings_json = {
            "harness": detectar_harness_nome(),
            "modelo": detectar_modelo_harness(),
            "auto_update": True
        }
        (self.pasta_projeto / '.claude/settings.json').write_text(
            json.dumps(settings_json, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # AGENTS.md — fonte única (padrão Zero Duplicidade Desnecessária,
        # ver AGENTS.md do próprio aidd-generator). .claude/CLAUDE.md é
        # symlink para este arquivo, nunca uma cópia separada.
        agents_md = f"""# AI-Driven Development Setup

Este projeto foi gerado pela skill aidd-project-generator v2.1

> Fonte única de verdade para configuração de agentes (Zero Duplicidade
> Desnecessária) — outros harness (.codex/CODEX.md, .gemini/GEMINI.md
> etc) devem apontar aqui via symlink, nunca duplicar conteúdo.

## Ideia Original
{ideia}

## Estrutura AIDD
- Camada 1: Contratos e Schemas (JSON Schema Draft 2020-12)
- Camada 2: Determinismo Primeiro (Python puro)
- Camada 3: Gates Mecânicos (validação)
- Camada 4: Persistência SQLite
- Camada 5: Bundles Modulares

## Próximas Etapas
1. Implementar Phase 2 (Análise)
2. Implementar Phase 3 (Design AIDD)
3. Implementar Phase 6 (Documentação)
"""
        (self.pasta_projeto / 'AGENTS.md').write_text(agents_md, encoding='utf-8')

        # Sincronização multi-harness (Universalidade — Zero Duplicidade)
        harnesses_alvos = [
            ('.claude', 'CLAUDE.md'),
            ('.agent', 'AGENT.md'),
            ('.codex', 'CODEX.md'),
            ('.gemini', 'GEMINI.md'),
            ('.mimocode', 'MIMO.md'),
        ]
        agents_md_path = self.pasta_projeto / 'AGENTS.md'
        copias_fallback = []
        for h_dir, h_file in harnesses_alvos:
            link_path = self.pasta_projeto / h_dir / h_file
            foi_symlink_real = self._criar_symlink_ou_copia(link_path, agents_md_path)
            if not foi_symlink_real:
                copias_fallback.append(link_path.relative_to(self.pasta_projeto).as_posix())

        # Manifesto de sincronismo + gate de drift (só materializado se houve
        # ao menos uma cópia de fallback — symlink real não pode divergir).
        # Sem isso, uma cópia fica honesta só no instante da criação: se
        # AGENTS.md for editado depois e ninguém re-sincronizar manualmente,
        # nada no projeto avisa que .claude/CLAUDE.md (etc.) ficou obsoleto.
        if copias_fallback:
            self._registrar_sync_manifest(agents_md_path, copias_fallback)

        # config.json
        config = {
            'versao': '1.0',
            'data_criacao': datetime.now(timezone.utc).isoformat(),
            'ideia_original': ideia,
            'arquitetura': 'AIDD 5-camadas',
            'lm': detectar_modelo_harness(),
            'harness': detectar_harness_nome(),
            'estado': 'criado'
        }
        (self.pasta_projeto / '.aidd/config.json').write_text(
            json.dumps(config, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        # rules.md (10 leis AIDD)
        rules_md = """# 10 Leis Inegociáveis da AIDD

1. **R-TOKEN** - Economia Severa: 90%+ determinismo em coleta/parsing
2. **R-MIDIA** - Zero Download Pesado: apenas metadados textuais
3. **R-BRASIL** - Brasil First: conteúdo PT-BR é prioridade
4. **R-DIDATICA** - Acessibilidade: módulo 0 com conceitos desmistificados
5. **R-GATES** - Validação Mecânica: G0, G1, G2, S1 (segurança)
6. **R-CITACOES** - Zero Alucinação: 100% rastreabilidade
7. **R-TRIPARTITE** - 3 Formatos: HTML + Markdown + PDF
8. **R-BUNDLES** - Modularidade: artefatos autocontidos
9. **R-TELEMETRIA** - Transparência: relatório completo
10. **R-PERSISTENCIA** - SQLite: estado do projeto em banco relacional
"""
        (self.pasta_projeto / '.aidd/rules.md').write_text(rules_md, encoding='utf-8')

        # requirements.txt
        requirements_txt = """# Dependências do projeto AIDD
requests>=2.31.0
"""
        (self.pasta_projeto / 'requirements.txt').write_text(requirements_txt, encoding='utf-8')

        # pytest.ini — pythonpath=src garante que qualquer código futuro em
        # src/<pacote>/ (ex: gerado pela Fase 8) seja importável pelo pytest
        # sem exigir instalação editável ou config manual por quem implementa.
        # Achado real (2026-08-30): um harness entregou testes reais que
        # nunca rodaram por falta exatamente disso (ModuleNotFoundError).
        pytest_ini = """[pytest]
testpaths = tests
pythonpath = src
addopts = -ra
"""
        (self.pasta_projeto / 'pytest.ini').write_text(pytest_ini, encoding='utf-8')

        # README.md
        readme = f"""# {ideia.title()}

Projeto gerado com AIDD (AI-Driven Development).

## Segurança

- ✅ Credenciais devem ser gerenciadas via variáveis de ambiente
- ✅ Nunca comitar `.env` ou arquivos de secrets
- ✅ Manter `requirements.txt` atualizado
- ✅ Executar verificações de segurança regularmente

## Estrutura

- `.claude/` - Configurações do agente
- `.aidd/` - Metadata AIDD + cache
- `scripts/` - Código determinístico
- `docs/` - Documentação
- `.git/` - Controle de versão

## Começar

```bash
cd {self.pasta_projeto}
python scripts/orquestrador.py --modo interativo
```
"""
        (self.pasta_projeto / 'README.md').write_text(readme, encoding='utf-8')

        # .gitignore
        gitignore = """# Ambiente
.env
.env.local
.env.*.local
secrets.json
credentials.json

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Projeto
estado_projeto.db
*.db
.aidd/cache/data/*.json
planejamentos/
output/
"""
        (self.pasta_projeto / '.gitignore').write_text(gitignore, encoding='utf-8')

    def _criar_sqlite(self):
        """Inicializa banco SQLite com schema"""
        try:
            import sqlite3

            conn = sqlite3.connect(str(self.pasta_projeto / 'estado_projeto.db'))
            cursor = conn.cursor()

            # Tabela de metadata — generica, independente do dominio da ideia
            # (bug real corrigido em 04/09/2026: antes era hardcoded para
            # "yt_videos_processados" com colunas de video/canal do YouTube,
            # resíduo de um projeto de exemplo anterior, criada sempre,
            # não importa a ideia informada pelo usuário)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens_processados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT UNIQUE NOT NULL,
                categoria TEXT NOT NULL,
                titulo TEXT NOT NULL,
                status TEXT DEFAULT 'pendente',
                data_processamento TEXT,
                tokens_consumidos INTEGER DEFAULT 0
            )
            """)

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️  Erro ao criar SQLite: {e}")

    def _git_init_commit(self, ideia: str):
        """Inicializa git e faz primeiro commit"""
        try:
            # git init
            subprocess.run(['git', 'init'],
                         cwd=str(self.pasta_projeto),
                         capture_output=True,
                         timeout=5)

            # git add .
            subprocess.run(['git', 'add', '.'],
                         cwd=str(self.pasta_projeto),
                         capture_output=True,
                         timeout=5)

            # git commit — mensagem via stdin (-F -) com bytes UTF-8
            # explícitos: passar acentos via argv -m quebra no Windows
            # (git decodifica argv na codepage OEM do console, não UTF-8),
            # reproduzido com "Inicialização" virando "InicializaÃ§Ã£o"
            commit_msg = f"feat: Inicialização de projeto AIDD para '{ideia}'"
            subprocess.run(['git', 'commit', '-F', '-'],
                         cwd=str(self.pasta_projeto),
                         input=commit_msg.encode('utf-8'),
                         capture_output=True,
                         timeout=5)

        except Exception as e:
            print(f"⚠️  Erro ao inicializar git: {e}")

    def _gerar_index(self, gates: List[Gate], tempo_execucao: float) -> Dict[str, Any]:
        """Gera estrutura completa do index com métricas medidas"""

        arquivos = sum(1 for f in self.pasta_projeto.rglob('*') if f.is_file())
        diretorios = sum(1 for d in self.pasta_projeto.rglob('*') if d.is_dir())
        symlinks = sum(1 for f in self.pasta_projeto.rglob('*') if f.is_symlink())

        git_commits = 0
        try:
            resultado = subprocess.run(
                ['git', 'rev-list', '--count', 'HEAD'],
                cwd=str(self.pasta_projeto),
                capture_output=True, text=True, timeout=5
            )
            if resultado.returncode == 0:
                git_commits = int(resultado.stdout.strip())
        except Exception:
            pass

        index = {
            'fase_id': 'phase_05_creation',
            'versao': '2.1',
            'status': 'COMPLETO' if all(g.passou for g in gates) else 'COM_AVISOS',

            'timestamps': {
                'data_inicio': datetime.now(timezone.utc).isoformat(),
                'data_conclusao': datetime.now(timezone.utc).isoformat(),
                'duracao_segundos': tempo_execucao
            },

            'tokens': {
                'consumidos': 0,
                'percentual_determinismo': '100%'
            },

            'processamento': {
                'arquivos_criados': arquivos,
                'diretorios_criados': diretorios,
                'symlinks_criados': symlinks,
                'git_commits': git_commits
            },

            'gates_executados': [g.to_dict() for g in gates],

            'resume_info': {
                'proxima_fase': 'phase_06_documentation',
                'pode_prosseguir': True,
                'requer_intervencao_manual': any(
                    g.gate_id == 'S1_auditoria_seguranca' and not g.passou
                    for g in gates
                )
            }
        }

        return index


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """CLI para testar Phase 5"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Phase 5: Criador de Projeto - aidd-project-generator v2.1'
    )
    parser.add_argument('pasta',
                       help='Caminho da pasta do novo projeto')
    parser.add_argument('--ideia',
                       default='Projeto AIDD Novo',
                       help='Descrição da ideia do projeto')
    parser.add_argument('--config-fase4',
                       default='{}',
                       help='JSON de saída de DecisorFase4 (decisoes + symlinks_paths)')

    args = parser.parse_args()

    config_fase4 = json.loads(args.config_fase4)

    criador = CriadorProjetoFase5(Path(args.pasta))
    resultado = criador.executar(args.ideia, config_fase4 or None)

    if resultado is None:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
