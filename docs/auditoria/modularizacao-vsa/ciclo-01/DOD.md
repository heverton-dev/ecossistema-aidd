# Definição de Pronto (Definition of Done - DoD) — modularizacao-vsa

> Critérios determinísticos de conformidade arquitetural baseados no framework Lens 15-D e na Especificação Canônica de Modularização VSA + Monólito Modular.

---

## Critérios Obrigatórios de Aceite

1. **DoD 1: Estruturação dos 4 Domínios Canônicos (D1, D3, D5)**
   - O ecossistema deve possuir a pasta raiz `modulos/` particionada estritamente em:
     - `01-governanca-e-qualidade/`
     - `02-triade-motores/` (com submódulos `fluxo-01-pure/`, `fluxo-02-open/`, `fluxo-03-freedom/`)
     - `03-plataforma-e-entrega/`
     - `04-nucleo-compartilhado/`
   - Nenhuma nova ferramenta de domínio pode residir solta em `tools/`.

2. **DoD 2: Anatomia Granular e Regra Fractal (D4, D6, D9)**
   - Cada módulo e submódulo deve adotar o contrato das **12 camadas atômicas padronizadas** sob a regra de *Sparse Scaffolding* (pastas só existem se contiverem arquivos reais):
     `core/`, `scripts/`, `skills/`, `mcps/`, `hooks/`, `gates/`, `tests/`, `contracts/`, `templates/`, `prompts/`, `specs/`, `docs/`.
   - Cada fatia deve conter obrigatoriamente seus documentos de contexto: `README.md` (< 500 tokens) e `AGENTS.md` (< 400 tokens).

3. **DoD 3: Fachada Fina e Lazy Loading CLI (D2, D8)**
   - O arquivo raiz `ecossistema.py` deve atuar exclusivamente como **Thin Facade**, realizando roteamento dinâmico via `importlib` sob demanda sem carregar dependências pesadas no boot.
   - O tempo de inicialização do CLI deve ser inferior a 50ms para qualquer comando.

4. **DoD 4: Portão de Fronteira Estrita via AST (D13, D14)**
   - Implementação do quality gate determinístico `gates/G_MODULO_FRONTEIRA.py` (ou `modulos/01-governanca-e-qualidade/gates/G_MODULO_FRONTEIRA.py`).
   - O portão deve analisar a AST do Python e reprovar (`exit 1`) caso ocorram importações de submódulos privados sem passar pela interface pública oficial (`interface.py` ou `__all__`). Deve provar que morde (Lei #13).

5. **DoD 5: Grafos Federados no codebase-memory-mcp (D4, D12)**
   - Registro de subgrafos independentes por domínio no `codebase-memory-mcp`: `aidd-nucleo`, `modulo-governanca`, `triade-fluxo-pure`, `triade-fluxo-open`, `triade-fluxo-freedom`, `modulo-plataforma-ops`.
   - Blast radius médio por consulta `trace_path` em módulo isolado inferior a 15 nós.

6. **DoD 6: Poda de Inchaço e Escopo de Skills (D12)**
   - Desativação do carregamento estático global de skills irrelevantes (médicas/bioinformáticas, office pesado) do perfil padrão de engenharia.
   - Cada módulo declara estritamente suas skills nativas para os harnesses via `components sync`.

7. **DoD 7: Retrocompatibilidade e Aliases Transparentes (D11, D14)**
   - Manutenção de proxies/redirecionadores nos caminhos legados (`tools/`, `gates/`) emitindo warnings amigáveis sem quebrar comandos existentes.
   - Zero regressão nos 54 macro-gates existentes (`python ecossistema.py audit` com exit 0).

8. **DoD 8: Output Consolidado e Handoff Formal (D15)**
   - Emissão do `LAUDO-15D-INICIAL.md`, `PLANO-EVOLUCAO.md` com tickets atômicos executáveis em worktrees, relatório de entrega do construtor e `LAUDO-15D-REVISADO.md` aprovado pelo `G_auditoria_15D.py` com EXIT 0.

