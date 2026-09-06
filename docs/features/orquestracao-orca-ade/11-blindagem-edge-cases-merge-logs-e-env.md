# 🛡️ Blindagem de Casos de Borda: Conflitos de Merge, Preservação de Logs e Variáveis de Ambiente

> **Local Canônico:** `docs/features/orquestracao-orca-ade/11-blindagem-edge-cases-merge-logs-e-env.md`  
> **Status:** Especificação de Blindagem e Casos de Borda  
> **Data:** 06/09/2026  
> **Idioma Oficial:** Português do Brasil (PT-BR)  

---

## 1. Prevenção e Resolução de Conflitos de Git Merge

### 1.1. O Risco
Quando múltiplas worktrees operam em paralelo, se duas frentes alterarem o mesmo arquivo central (ex.: `AGENTS.md`, tabelas de capacidades ou dependências compartilhadas), o `git merge` gerará conflito.

### 1.2. A Solução Arquitetural
1. **Fatiamento com Princípio de Segregação (Boundary Isolation):**  
   Cada plano/frente define no cabeçalho quais caminhos de arquivo ela tem permissão de tocar. Modificações em arquivos centrais fora da sua fronteira são proibidas pelo Quality Gate.
2. **Merge Serializado com Lock Atômico (`MergeQueue`):**  
   Mesmo que 3 agentes terminem no mesmo segundo, o orquestrador enfileira os merges:
   - Faz o merge da Frente A na `main`.
   - Se a Frente B tocar em arquivos adjacentes, o orquestrador executa um `git merge --no-commit` ou rebase rápido. Se for em arquivos estritamente segregados, o merge é limpo e automático (`exit 0`).

---

## 2. Preservação de Logs Pós-Purga (Auditoria Forense)

### 2.1. O Risco
Ao aplicar a regra de destruição total da worktree efêmera (`git worktree remove --force`), todos os arquivos gerados dentro dela (inclusive `exec.log`, traços de teste e relatórios json) seriam destruídos, impedindo auditorias futuras.

### 2.2. A Solução Arquitetural
O **Post-Hook** executa a rotina de arquivamento antes de liberar a destruição:
1. Copia `../wt-<frente>/exec.log` para `.orca/logs/<timestamp>-<frente_id>.log` na raiz do projeto.
2. Copia relatórios de cobertura e telemetria para `.orca/reports/<frente_id>.json`.
3. Apenas após a cópia confirmada, emite o sinal de purge para o `worktree_engine.py`.
- **Resultado:** O disco e o Git ficam 100% limpos de branches e pastas temporárias, enquanto a memória forense do projeto permanece preservada e auditável.

---

## 3. Propagação Segura de Variáveis de Ambiente e Segredos (`.env`)

### 3.1. O Risco
Por padrão, `git worktree add` cria a mesa respeitando o `.gitignore`. Isso significa que arquivos `.env` ou credenciais locais não são copiados, o que causaria falha imediata em testes que dependem de chaves de API ou configurações de ambiente.

### 3.2. A Solução Arquitetural
O **Pre-Hook** executa o protocolo seguro de injeção de ambiente:
1. Identifica se existem arquivos `.env` ou `.env.local` na raiz do repositório.
2. Copia temporariamente esses arquivos para a raiz da worktree.
3. Adiciona esses caminhos explicitamente ao `.git/info/exclude` da worktree.
4. **Garantia de Segurança:** O agente pode consumir as variáveis necessárias para os testes, mas é **mecanicamente impossível** commitar ou vazar segredos acidentalmente para o histórico do Git.
