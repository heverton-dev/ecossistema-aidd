# O que Acontece nos Bastidores quando Alguém Executa o AIDD Forge

> **Versão documentada:** 1.0.0 (Homologada com Nota 10.0+)  
> **Para quem é este documento:** Pessoas de produto, líderes técnicos, arquitetos e desenvolvedores que desejam compreender a mecânica exata de transformação que o AIDD Forge aplica em qualquer repositório de software.

---

## Em uma frase

O **`AIDD Forge`** é o **motor autônomo de blindagem e governança agêntica**: você executa um único comando (`/forge`, `setup.bat` ou linguagem natural) em qualquer projeto e, em menos de um segundo, ele inspeciona o host, descobre quais agentes de IA estão instalados, constrói uma esteira de micro-ambientes isolados por fase, injeta 6 skills de engenharia, instala 7 quality gates mecânicos e aplica o protocolo rígido de economia extrema de tokens (Tríade Caveman Ultra).

---

## A Linha de Montagem: Passo a Passo dos Bastidores

### Estação 0 — "A Deteção Silenciosa do Host" (`detector.py`)
Antes de tocar em qualquer arquivo do projeto, o Forge realiza um diagnóstico silencioso da máquina:
- Identifica o Sistema Operacional (Windows, Linux ou macOS).
- Realiza uma varredura silenciosa no PATH à procura de ferramentas de IA instaladas: Claude Code, Codex, Antigravity (AGY), Cursor IDE e Ollama.
- Verifica a presença do orquestrador ORCA ADE.
- **Diferencial:** Nunca quebra caso alguma ferramenta não exista. Constrói um inventário factual contendo apenas o que realmente está presente.

---

### Estação 1 — "A Ponte de Roteamento Universal" (`orca_bridge.py`)
Com a frota do host mapeada:
- Compila o `01_orca_inventory.json` e o `02_routing_rules.json`.
- Aplica **fallback em cascata**: se o usuário possui múltiplos agentes, delega papéis específicos (Arquiteto para Claude, Backend para Codex, etc.). Se possuir apenas um agente (ex: Antigravity), roteia todos os workers para ele operando em branches/worktrees isoladas, garantindo zero erro por falta de ferramentas.

---

### Estação 2 — "O Cerco de Fases Granulares" (`phase_fencer.py`)
Para impedir que regras monolíticas contaminem o raciocínio das IAs, o Forge divide o fluxo em micro-ambientes isolados em `.aidd/pipeline/`:
1. **`phase_00_bootstrap`**: diagnóstico do ambiente, hardware e git.
2. **`phase_01_requirements`**: escopo, personas e regras funcionais (apenas Filesystem MCP).
3. **`phase_02_architecture`**: contratos de dados e schemas JSON Draft 2020-12 (apenas Schemas MCP).
4. **`phase_03_implementation`**: desenvolvimento guiado a testes, Result Monad e Zero Stubs (apenas Database MCP).
5. **`phase_04_audit_security`**: verificação estática de cibersegurança e conformidade OWASP Top 10.
- **Diferencial:** Cada micro-fase possui seu próprio `AGENTS.md` cirúrgico (~380 tokens) e seu `mcp_config.json` exclusivo.

---

### Estação 3 — "A Injeção do Pacote Físico de 6 Skills" (`templates/skills/`)
O Forge instala na pasta canônica universal `.agent/skills/` os 6 pacotes de habilidades especializadas com symlinks automáticos:
- **`caveman-ultra`**: protocolo severo de economia de tokens.
- **`orca-orchestration`**: governança multi-agente e decision gates.
- **`impeccable-ui`**: design system Tailwind, modais WCAG 2.1 e ausência de emojis amadores.
- **`open-code-review`**: análise de acoplamento e grafo de Clean Architecture.
- **`post-mortem`**: investigação de incidentes pela técnica dos 5-Porquês.
- **`cybersecurity-audit`**: análise estática contra SQLi, IDOR e vulnerabilidades de entrada.

---

### Estação 4 — "A Blindagem Mecânica dos 7 Quality Gates" (`templates/gates/`)
O Forge deposita e ativa os 7 scripts determinísticos que barram commits que violem a integridade do código:
1. `G_BLOQUEAR_SEGREDOS.py`: Impede vazamento de chaves AWS, tokens e credenciais.
2. `G_ESTRUTURA_AST.py`: Valida sintaxe de 100% dos arquivos Python via árvore sintática abstrata.
3. `G_HARNESS_COMPAT.py`: Garante que `.agent`, `.claude` e `.cursor` permaneçam sincronizados.
4. `G_CONTRACTS.py`: Exige schemas JSON Draft 2020-12 válidos.
5. `G_TESTES_REAIS.py`: Executa a suíte de pytest e impõe política Zero Fail.
6. `G_CYBERSECURITY_OWASP.py`: Bloqueia chamadas perigosas (`eval`, `shell=True`, concatenação crua de SQL).
7. `G_PERFORMANCE.py`: Valida SLAs de latência para evitar degradação de endpoints.
- Instala o hook `.git/hooks/pre-commit` com bloqueio binário (`exit 0` / `exit 1`).

---

### Estação 5 — "A Interface Humana Zero Fricção" (`slash_router.py`)
Para o usuário final, nada é complexo:
- Mapeia os comandos `/forge` e `/aidd-init` para `.cursor/rules/`, `.claude/commands/` e `.agent/commands/`.
- Injeta no `AGENTS.md` o roteador de intenções em linguagem natural: se o usuário pedir *"prepare o ambiente"*, o agente sabe exatamente o que executar.
- Disponibiliza `setup.bat` e `setup.sh` para execução com 1 clique direto no explorador de arquivos.
