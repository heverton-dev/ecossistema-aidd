"""
Script de Simulação em Tempo Real para Demonstração Visual do Quadro Kanban.
Percorre as etapas do pipeline auditoria-4f com intervalos controlados.
"""

import sys
import time
from pathlib import Path

# Garantir importação do módulo de estado
sys.path.insert(0, str(Path(__file__).parent))
from estado_execucao import Execucao

def main():
    print("[SIMULADOR] Iniciando demonstracao em tempo real...")
    
    with Execucao.abrir(
        pipeline="auditoria-4f",
        chave="DEMO-AO-VIVO",
        titulo="Auditoria 4F: Teste de Transição em Tempo Real",
        comando="python scripts/orquestrador_4f.py --demo"
    ) as ex:
        print("[1/6] Etapa: Fila -> Inspetor (fase-1)")
        ex.etapa("fase-1", "executando")
        time.sleep(4)

        print("[2/6] Etapa: Arquiteto (fase-2)")
        ex.etapa("fase-1", "concluido")
        ex.etapa("fase-2", "executando")
        time.sleep(4)

        print("[3/6] Etapa: Construtor (fase-3)")
        ex.etapa("fase-2", "concluido")
        ex.etapa("fase-3", "executando")
        time.sleep(4)

        print("[4/6] Etapa: Inspetor de Retorno (fase-4)")
        ex.etapa("fase-3", "concluido")
        ex.etapa("fase-4", "executando")
        time.sleep(4)

        print("[5/6] Etapa: Quality Gate Final (gate-final)")
        ex.etapa("fase-4", "concluido")
        ex.etapa("gate-final", "executando")
        time.sleep(3)

        print("[6/6] Etapa: Barreira de Aprovação Humana (aprovacao)")
        ex.etapa("gate-final", "concluido")
        ex.etapa("aprovacao", "executando")
        ex.pedir_humano(
            motivo="Auditoria aprovada 100%. Confirmação de merge solicitada ao operador humano.",
            comando="python ecossistema.py aprovar-join --ticket AUDIT-4F-DEMO"
        )
        print("[AGUARDANDO] Pausa de 25 segundos na Barreira Humana para teste de clique...")
        time.sleep(25)

        print("[FIM] Concluindo simulacao com sucesso!")
        ex.etapa("aprovacao", "concluido")

    print("[SIMULADOR] Concluido com sucesso. Card arquivado na coluna Concluido!")

if __name__ == "__main__":
    main()
