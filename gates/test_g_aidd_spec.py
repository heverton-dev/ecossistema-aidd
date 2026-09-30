# -*- coding: utf-8 -*-
"""
Teste de Quality Gate Determinístico de Especificação Técnica (Ticket 7 / Lei #13).
Comprova que G_aidd_spec.py aprova especificações íntegras (exit 0) e morde (exit 1) diante de:
1. Ausência de qualquer uma das 5 seções canônicas obrigatórias.
2. Critérios de aceitação subjetivos sem verificação mecânica.
3. Arquivo inexistente ou sem conteúdo.
"""

import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "gates" / "G_aidd_spec.py"


def executar_gate(arquivo_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GATE), "--arquivo", str(arquivo_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT)
    )


SPEC_CANONICA_VALIDA = """
# Especificação Técnica: Módulo de Autenticação

## 1. Context & Explicit Non-Goals
- O objetivo é implementar login via JWT.
- Non-goals: login social e autenticação biométrica estão fora de escopo.

## 2. Contracts & Typed Interfaces
```typescript
interface LoginRequest {
  email: string;
  hash: string;
}
```

## 3. Invariants & Business Rules
1. Tokens JWT expiram obrigatoriamente após 3600 segundos.
2. Senhas devem conter no mínimo 8 caracteres.

## 4. Binary Acceptance Criteria
- Endpoint `/auth/login` retorna status 200 quando credenciais são válidas.
- Endpoint `/auth/login` retorna status 401 quando senha for incorreta.
- Execução de `pytest tests/test_auth.py` finaliza com exit code 0.

## 5. Failure & Degradation Modes
- Em caso de falha no banco, retorna status 503 com chave obrigatória `error`.
"""


def test_gate_spec_aprova_spec_integra(tmp_path):
    arq = tmp_path / "spec_valida.md"
    arq.write_text(SPEC_CANONICA_VALIDA, encoding="utf-8")

    res = executar_gate(arq)
    assert res.returncode == 0
    assert "APROVADO" in res.stdout


def test_gate_spec_morde_se_faltar_secao_obrigatoria(tmp_path):
    # Sem a seção 5 (Failure & Degradation Modes)
    conteudo_sem_secao_5 = """
# Especificação Incompleta
## 1. Context & Explicit Non-Goals
- Escopo definido.
## 2. Contracts & Typed Interfaces
- Interface definida.
## 3. Invariants & Business Rules
1. Invariante 1.
## 4. Binary Acceptance Criteria
- Retorna exit code 0.
"""
    arq = tmp_path / "spec_incompleta.md"
    arq.write_text(conteudo_sem_secao_5, encoding="utf-8")

    res = executar_gate(arq)
    assert res.returncode == 1
    assert "Seção obrigatória ausente" in res.stdout


def test_gate_spec_morde_se_criterio_for_subjetivo(tmp_path):
    conteudo_subjetivo = """
# Especificação com Critério Subjetivo
## 1. Context & Explicit Non-Goals
- Escopo.
## 2. Contracts & Typed Interfaces
- Interfaces.
## 3. Invariants & Business Rules
1. Invariante 1.
## 4. Binary Acceptance Criteria
- O sistema deve ser rápido e a interface bonita.
## 5. Failure & Degradation Modes
- Falha tratada.
"""
    arq = tmp_path / "spec_subjetiva.md"
    arq.write_text(conteudo_subjetivo, encoding="utf-8")

    res = executar_gate(arq)
    assert res.returncode == 1
    assert "Critério subjetivo rejeitado" in res.stdout or "Critério não verificável mecanicamente" in res.stdout


def test_gate_spec_morde_se_arquivo_inexistente(tmp_path):
    arq = tmp_path / "inexistente.md"
    res = executar_gate(arq)
    assert res.returncode == 1
    assert "não existe" in res.stdout
