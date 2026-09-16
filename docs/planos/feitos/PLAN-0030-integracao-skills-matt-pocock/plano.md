# PLAN-0030: Integração Agnóstica das Skills de Engenharia de Matt Pocock

> **Status:** Concluído  
> **Tipo:** Evolução Arquitetural & Skills de Engenharia  
> **Harnesses:** Universal (Claude, Cursor, Gemini, OpenCode, Codex, Kiro, Qoder)  
> **Relatório de Referência:** `docs/reports/analise-integracao-skills-matt-pocock.md`

---

## 1. Contexto & Motivação

O ecossistema AIDD opera com rigorosas Leis Invioláveis de determinismo, tolerância zero a stubs e testes executáveis reais. Para prevenir o *"vibe coding"* e o retrabalho durante a fase de concepção e especificação de tarefas, integramos o protocolo de engenharia procedimental baseado nas skills de Matt Pocock (`mattpocock/skills`), adaptando-o para ser **100% agnóstico de linguagem** (suporte nativo a Python, Go, Rust, Java, TypeScript) e aderente à **Extrema Economia de Tokens** (< 2000 tokens por skill).

---

## 2. Objetivos Principais

1. **Protocolo Socrático Pré-Código:** Implementar `/aidd-grill` e `/aidd-grill-docs` para forçar o alinhamento de premissas e invariantes antes de qualquer edição de código.
2. **Decomposição Determinística:** Implementar `/aidd-spec` e `/aidd-tickets` gerando especificações formais e fatias verticais atômicas (*tracer bullets*).
3. **Ciclo de TDD Poliglota & Zero Stubs:** Implementar `/aidd-tdd` com contratos prévios de tipagem e asserções reais (Pytest, Vitest, Go test, Cargo test).
4. **Triage Científica de Falhas:** Implementar `/aidd-diagnose` acoplado ao MCP `code-review-graph`.
5. **Preservação de Contexto:** Implementar `/aidd-handoff` serializando o estado da sessão diretamente na pasta `secoes/`.
6. **Distribuição Universal:** Distribuir as skills para todos os harnesses através de `componentes/compartilhado/skills/`.

---

## 3. Fases de Execução

### Fase 1: Criação das Skills Agnósticas Compartilhadas com Namespace AIDD
- `componentes/compartilhado/skills/aidd-grill/SKILL.md`
- `componentes/compartilhado/skills/aidd-grill-docs/SKILL.md`
- `componentes/compartilhado/skills/aidd-spec/SKILL.md`
- `componentes/compartilhado/skills/aidd-tickets/SKILL.md`
- `componentes/compartilhado/skills/aidd-tdd/SKILL.md`
- `componentes/compartilhado/skills/aidd-diagnose/SKILL.md`
- `componentes/compartilhado/skills/aidd-handoff/SKILL.md`

### Fase 2: Sincronização e Distribuição nos Harnesses
- Atualizar `.agents/skills/` com os links e diretórios das novas skills.
- Garantir presença nos harnesses mapeados pelo ecossistema.

### Fase 3: Vinculação com Ferramentas Especializadas (`tools/aidd-*`)
- `tools/aidd-forge`: Vinculação de bootstrap e questionamento inicial.
- `tools/aidd-generator`: Vinculação nas Fases 1 (Spec) e 2 (Decomposição).
- `tools/aidd-master`: Acoplamento de Vertical Slices ao `aidd-tickets` e `aidd-tdd`.
- `tools/aidd-enterprise`: Exigência de `aidd-tdd` antes de hash SHA-256.
- `tools/aidd-ops`: Adoção do `aidd-diagnose` para infra/containers.

### Fase 4: Quality Gate e Validação
- Executar `python ecossistema.py audit` garantindo saída 0.
- Atualizar índice de planos via `python scripts/atualizar_index_planos.py`.

---

## 4. Critérios de Aceite Binários

- [x] Todas as 7 skills criadas com frontmatter válido e instruções em Compact English denso (Padrão Core / Tokenomics).
- [x] Nenhuma menção ou dependência rígida de TypeScript/Node exclusiva em skills de uso geral.
- [x] Conformidade de tokens (< 2000 tokens por arquivo SKILL.md).
- [x] `python ecossistema.py components verify --tipo skill` retorna exit 0 com integridade SHA-256 em todos os harnesses.
- [x] `python ecossistema.py audit` retorna exit 0.
