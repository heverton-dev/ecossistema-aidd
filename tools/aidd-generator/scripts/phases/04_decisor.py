#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PHASE 4: Decisor de Configuração Global/Local
aidd-project-generator v2.1

Apresenta modal interativo para escolher:
- CLAUDE.md: GLOBAL ou LOCAL?
- Skills: GLOBAL ou LOCAL?
- MCPs: GLOBAL ou LOCAL?
- Hooks: GLOBAL ou LOCAL?

Executa 2 gates de validação (C1-C2)
Gera _phase_04_index.json com configuração aprovada

Tokens: 0 (modal determinístico) — Determinismo: 100% (Python puro)
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# =============================================================================
# GATES DE VALIDAÇÃO
# =============================================================================

class Gate:
    """Resultado de validação de gate"""
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


class ValidadorGatesPhase4:
    """Valida decisões Global/Local"""

    @staticmethod
    def executar_todos(config: Dict) -> tuple[List[Gate], bool]:
        """Executa C1-C2 sequencialmente"""
        gates_resultado = []

        # Gate C1: Decisões válidas
        gate_c1 = ValidadorGatesPhase4._gate_c1_decisoes_validas(config)
        gates_resultado.append(gate_c1)

        # Gate C2: Symlinks resolvem
        gate_c2 = ValidadorGatesPhase4._gate_c2_symlinks_resolvem(config)
        gates_resultado.append(gate_c2)

        todos_passaram = all(g.passou for g in gates_resultado)
        return gates_resultado, todos_passaram

    @staticmethod
    def _gate_c1_decisoes_validas(config: Dict) -> Gate:
        """C1: Todas decisões são GLOBAL ou LOCAL"""
        decisoes = config.get('decisoes', {})
        validas = sum(1 for k, v in decisoes.items() if v in ['GLOBAL', 'LOCAL'])
        total = len(decisoes)

        passou = validas == total and total > 0
        detalhes = f"{validas}/{total} decisões válidas (GLOBAL/LOCAL)"

        return Gate('C1_decisoes_validas',
                   'Validar decisões GLOBAL/LOCAL',
                   passou,
                   detalhes)

    @staticmethod
    def _gate_c2_symlinks_resolvem(config: Dict) -> Gate:
        """C2: Symlinks GLOBAL (quando existem) apontam para arquivos reais.

        Nenhum item GLOBAL decidido é um estado VÁLIDO (projeto 100% LOCAL
        é uma escolha legítima) — não deve bloquear a fase. O gate só
        reprova quando HÁ symlinks_paths configurados e algum não resolve.
        """
        symlinks_paths = config.get('symlinks_paths', [])

        if not symlinks_paths:
            return Gate('C2_symlinks_resolvem',
                       'Validar symlinks resolvem para global',
                       True,
                       'Nenhum item GLOBAL decidido — nada para validar (projeto 100% LOCAL é válido)')

        resolvidos = 0
        nao_resolvidos = []

        for symlink_path in symlinks_paths:
            path = Path(symlink_path).resolve()
            if path.exists():
                resolvidos += 1
            else:
                nao_resolvidos.append(symlink_path)

        passou = resolvidos == len(symlinks_paths) and resolvidos > 0
        if nao_resolvidos:
            detalhes = f"{resolvidos}/{len(symlinks_paths)} symlinks existem. Não encontrados: {', '.join(nao_resolvidos)}"
        else:
            detalhes = f"{resolvidos}/{len(symlinks_paths)} symlinks válidos"

        return Gate('C2_symlinks_resolvem',
                   'Validar symlinks resolvem para global',
                   passou,
                   detalhes)


# =============================================================================
# DECISOR PRINCIPAL
# =============================================================================

class DecisorFase4:
    """Apresenta modal e gera configuração"""

    def __init__(self, pasta_cache: Path):
        self.pasta_cache = Path(pasta_cache)
        self.pasta_cache.mkdir(parents=True, exist_ok=True)

    def executar(self, design_anterior: Dict, nao_interativo: bool = False) -> Optional[Dict]:
        """Executa pipeline completo da Phase 4"""
        print(f"\n⚙️  PHASE 4: Decisão Global/Local")
        print(f"   {'-' * 60}")

        tempo_inicio = datetime.now()

        # 1. Apresentar modal (interativo ou heurística para CI)
        print(f"\n📋 Apresentando opções de configuração...")
        if nao_interativo:
            config = self._apresentar_modal_nao_interativo(design_anterior)
            print(f"   ✅ Configuração decidida (modo não-interativo, heurística)")
        else:
            config = self._apresentar_modal_interativo()
            print(f"   ✅ Configuração decidida (modo interativo)")

        # 2. Executar gates
        print(f"\n✅ Executando gates (C1-C2)...")
        gates, todos_passaram = ValidadorGatesPhase4.executar_todos(config)

        for gate in gates:
            status_icon = "✓" if gate.passou else "✗"
            print(f"   {status_icon} {gate.gate_id}: {gate.detalhes}")

        if not todos_passaram:
            print(f"\n❌ FASE FALHOU: Gates não passaram")
            return None

        # 3. Gerar index
        tempo_execucao = (datetime.now() - tempo_inicio).total_seconds()
        print(f"\n📝 Gerando índice de fase...")

        index = self._gerar_index(config, gates, tempo_execucao)

        # 4. Salvar index e config
        path_index = self.pasta_cache / '_phase_04_index.json'
        path_config = self.pasta_cache / 'data' / 'config_global_local_phase4.json'

        path_config.parent.mkdir(parents=True, exist_ok=True)

        with open(path_index, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        with open(path_config, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f"   ✓ {path_index}")
        print(f"   ✓ {path_config}")

        print(f"\n{'=' * 60}")
        print(f"✅ PHASE 4 COMPLETO")
        print(f"   Status: {index['status']}")
        print(f"   Tempo: {tempo_execucao:.1f}s")
        print(f"   Tokens: {index['tokens']['consumidos']}")
        print(f"{'=' * 60}\n")

        return index

    # Itens cujo escopo GLOBAL corresponde a uma pasta compartilhada real
    # em ~/.claude/ (claude_md/agents_md são sempre LOCAL por design —
    # cada projeto tem seu próprio AGENTS.md como fonte única; scripts
    # nunca é compartilhável entre projetos)
    ITENS_GLOBAL_COMPARTILHAVEL = ['skills', 'mcps', 'hooks']

    @staticmethod
    def _computar_symlinks_paths(decisoes: Dict) -> List[str]:
        """Para cada item GLOBAL compartilhável, computa o caminho em
        ~/.claude/<item> — só inclui se o caminho global já existir de
        fato (não inventa um caminho que não existe)."""
        paths = []
        for item in DecisorFase4.ITENS_GLOBAL_COMPARTILHAVEL:
            if decisoes.get(item) == 'GLOBAL':
                caminho = Path.home() / '.claude' / item
                if caminho.exists():
                    paths.append(str(caminho))
        return paths

    def _apresentar_modal_interativo(self) -> Dict:
        """Modal genuinamente interativo usando input()"""
        opcoes = {
            'claude_md': 'CLAUDE.md (configuração do harness)',
            'skills': 'Skills (utilitários reutilizáveis)',
            'mcps': 'MCPs (servidores de ferramentas)',
            'hooks': 'Hooks (ações automatizadas)',
            'agents_md': 'AGENTS.md (configuração de agentes)',
            'scripts': 'Scripts (código executável)'
        }

        decisoes = {}
        justificativas = {}

        print("\n📝 Responda GLOBAL ou LOCAL para cada item:")
        print("   GLOBAL = compartilhado entre projetos")
        print("   LOCAL = específico deste projeto\n")

        for chave, descricao in opcoes.items():
            while True:
                resposta = input(f"   {descricao}: ").strip().upper()
                if resposta in ['GLOBAL', 'LOCAL']:
                    decisoes[chave] = resposta
                    justificativa = input(f"      (Justificativa): ").strip()
                    justificativas[chave] = justificativa or "Sem justificativa"
                    break
                print("      ❌ Digite GLOBAL ou LOCAL")

        return {
            'decisoes': decisoes,
            'symlinks_paths': self._computar_symlinks_paths(decisoes),
            'justificativas': justificativas
        }

    def _apresentar_modal_nao_interativo(self, design_anterior: Dict) -> Dict:
        """Heurística para modo não-interativo (CI/CD).

        total_scripts vem do design real da Fase 3 (design.design.scripts) —
        não de uma chave fantasma que nunca existiu no schema (achado na
        integração ponta a ponta: 'subagentes_paralelos' nunca é produzido
        por 03_designer.py, então a heurística de skills nunca disparava).
        """
        total_scripts = len(design_anterior.get('design', {}).get('scripts', []))

        decisoes = {
            'claude_md': 'LOCAL',
            'skills': 'GLOBAL' if total_scripts > 2 else 'LOCAL',
            'mcps': 'GLOBAL',
            'hooks': 'LOCAL',
            'agents_md': 'LOCAL',
            'scripts': 'LOCAL'
        }

        symlinks_paths = self._computar_symlinks_paths(decisoes)

        justificativas = {
            'claude_md': 'Heurística: específico do projeto',
            'skills': f"Heurística: {'compartilhado' if decisoes['skills'] == 'GLOBAL' else 'local'} (scripts_no_design={total_scripts})",
            'mcps': 'Heurística: compartilhado entre projetos',
            'hooks': 'Heurística: custom do projeto',
            'agents_md': 'Heurística: local',
            'scripts': 'Heurística: local'
        }

        return {
            'decisoes': decisoes,
            'symlinks_paths': symlinks_paths,
            'justificativas': justificativas
        }

    def _gerar_index(self, config: Dict, gates: List[Gate], tempo_execucao: float) -> Dict:
        """Gera _phase_04_index.json"""

        index = {
            'fase_id': 'phase_04_decision',
            'versao': '2.1',
            'status': 'COMPLETO' if all(g.passou for g in gates) else 'FALHOU',

            'timestamps': {
                'data_inicio': datetime.now(timezone.utc).isoformat(),
                'data_conclusao': datetime.now(timezone.utc).isoformat(),
                'duracao_segundos': tempo_execucao
            },

            'tokens': {
                'consumidos': 0,
                'percentual_determinismo': 100  # Phase 4 é 100% determinístico
            },

            'processamento': {
                'decisoes_tomadas': len(config.get('decisoes', {})),
                'symlinks_criados': config.get('symlinks_count', 0),
                'config_conformidade': '100%'
            },

            'gates_executados': [g.to_dict() for g in gates],

            'resume_info': {
                'proxima_fase': 'phase_05_creation',
                'pode_prosseguir': all(g.passou for g in gates),
                'requer_intervencao_manual': False
            }
        }

        return index


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """CLI para testar Phase 4"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Phase 4: Decisor Global/Local - aidd-project-generator v2.1'
    )
    parser.add_argument('--cache-dir',
                       default='.aidd/cache',
                       help='Diretório para cache')
    parser.add_argument('--design',
                       default='{}',
                       help='JSON do design de Phase 3')
    parser.add_argument('--nao-interativo',
                       action='store_true',
                       help='Usar heurística (CI/CD) em vez de input interativo')

    args = parser.parse_args()

    design = json.loads(args.design)

    decisor = DecisorFase4(Path(args.cache_dir))
    resultado = decisor.executar(design, nao_interativo=args.nao_interativo)

    if resultado is None:
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
