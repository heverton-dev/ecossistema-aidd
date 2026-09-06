# ♻️ Ciclo de Vida Efêmero dos Worktrees (Mesas Descartáveis)

> **Local Canônico:** `docs/features/orquestracao-orca-ade/06-ciclo-de-vida-ephemeral-worktrees.md`  
> **Status:** Regra Arquitetural Inegociável  
> **Data:** 06/09/2026  
> **Idioma Oficial:** Português do Brasil (PT-BR)  

---

## 1. Princípio Fundamental: Worktrees São Efêmeros

**Corretíssimo.** No ORCA ADE, uma Git Worktree é tratada como uma **mesa cirúrgica estéril**:
- Ela é montada para um procedimento pontual.
- Durante o procedimento, ela é totalmente isolada da árvore principal.
- Após o procedimento, se a auditoria comprovar **100% de conformidade (exit 0)**, o resultado é incorporado (*merge*) e a mesa é **imediatamente destruída e purgada do disco**.

> **Regra de Ouro AIDD:**  
> *Nenhuma pasta de worktree deve permanecer viva no sistema após a conclusão bem-sucedida da sua respectiva fase.*

---

## 2. As 5 Fases do Ciclo de Vida

```mermaid
flowchart TD
    Nascer["1. NASCIMENTO (Spawning)<br>• git worktree add ../wt-frente -b orca/frente<br>• Estado: WORKTREE_ACTIVE"]
    Exec["2. OPERAÇÃO (Execution)<br>• Agente executor (agy) atua isolado<br>• Estado: RUNNING"]
    Auditar["3. AUDITORIA (Quality Gate)<br>• Gate mecânico verifica exit 0 e testes 100%<br>• Estado: AUDITING"]
    
    Decisao{"Aprovado 100%?"}
    
    Merge["4. INCORPORAÇÃO (Atomic Merge)<br>• git merge --no-ff orca/frente<br>• Estado: MERGED"]
    Morte["5. PURGA / DESCARTE (Destruction)<br>• git worktree remove ../wt-frente --force<br>• git branch -D orca/frente<br>• Estado: PURGED"]
    
    Quarentena["QUARANTINE / RETRY<br>• Worktree retida para diagnóstico<br>• Se retry esgotar: Rollback e Purga"]

    Nascer --> Exec --> Auditar --> Decisao
    Decisao -->|Sim (exit 0)| Merge --> Morte
    Decisao -->|Não (exit 1)| Quarentena
```

---

## 3. Comandos Mecânicos do Ciclo

### Fase 1: Criação da Mesa Efêmera
```powershell
git worktree add ../wt-teste-master -b orca/teste-master
```

### Fase 2: Execução Isolada
O agente opera exclusivamente dentro do caminho `../wt-teste-master/`, sem gerar lock nem conflitos no repositório raiz.

### Fase 3 & 4: Auditoria e Incorporação Atômica
Somente executado se o gate mecânico der `exit 0`:
```powershell
# Realizado pelo orquestrador no repositório raiz
git merge --no-ff orca/teste-master -m "orca(master): aprovado 100% por gate deterministico"
```

### Fase 5: Purga Mecânica Completa (Limpeza Imediata)
```powershell
# 1. Desconectar e deletar fisicamente a pasta da worktree
git worktree remove ../wt-teste-master --force

# 2. Deletar a branch temporária efêmera
git branch -D orca/teste-master

# 3. Limpar metadados órfãos no git
git worktree prune
```

---

## 4. Garantia em Código: O Bloco `try / finally` do `worktree_engine.py`

Para garantir que nenhuma worktree fique esquecida mesmo em caso de erro não tratado em Python, o `worktree_engine.py` implementa um context manager com garantia de encerramento:

```python
class EphemeralWorktree:
    def __init__(self, frente_id: str, branch_name: str):
        self.frente_id = frente_id
        self.path = Path(f"../wt-{frente_id}").resolve()
        self.branch = branch_name

    def __enter__(self):
        # 1. Cria worktree
        subprocess.run(["git", "worktree", "add", str(self.path), "-b", self.branch], check=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Se aprovado (sem exceção e gate 100%), o merge já foi feito
        # Bloco finally: purga incondicional se marcado para descarte
        if self.should_purge():
            subprocess.run(["git", "worktree", "remove", str(self.path), "--force"], check=False)
            subprocess.run(["git", "branch", "-D", self.branch], check=False)
            subprocess.run(["git", "worktree", "prune"], check=False)
```

---

## 5. Tratamento de Falhas: O que Acontece se o Gate Reprovar?

1. **Tentativa de Correção (Self-Healing):** O orquestrador despacha uma instrução pontual de correção para o agente na mesma mesa (até um limite máximo, ex.: 3 tentativas).
2. **Quarentena Notificada:** Se a falha persistir, a worktree **não é mergeada** (a branch principal permanece 100% limpa e estável). O `memory.md` registra o erro exato e a branch fica retida com a tag `quarantine/`.
3. **Comando de Abort / Purga Manual:** O desenvolvedor pode rodar:
   ```powershell
   python ecossistema.py orchestrate <plano> --abort-frente 02-master
   ```
   Isso descarta a mesa com falha, remove a pasta do disco e restaura a branch principal ao estado original intacto.
