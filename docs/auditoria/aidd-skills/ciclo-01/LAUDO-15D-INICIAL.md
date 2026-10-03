# Laudo de Auditoria 15-D: aidd-skills (Lens 15-D)

Auditoria técnica da meta-skill `aidd-skills` e da convenção de habilidades confrontada com o documento analítico `O que é uma Skill em AIDD.md` (benchmark de excelência percentil 99).

---

## 1. Identificação da Ferramenta
- **Nome da Ferramenta:** `aidd-skills`
- **Descrição Breve:** Meta-skill responsável por criar, melhorar e avaliar skills no ecossistema, orientada pela convenção `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md` e distribuída agnosticamente via `ecossistema.py components sync`.
- **Comando de Gatilho:** Gatilhos contextuais "criar skill", "nova skill", "melhorar skill", "skill-creator" ou invocação via `python ecossistema.py components sync --tipo skill`.

---

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem
- **D1. Contratos e Regras:**
  - Regida por `docs/protocolos/CONVENCAO-AUTORIA-SKILLS.md` (Seção 5: frontmatter universal, corpo em inglês conciso, teto de 450 linhas, scripts em `scripts/`, referências em `references/`).
  - Submetida aos Quality Gates `gates/G_SKILL_FORMATO.py` e `gates/G_SKILL_ROT.py`.
  - **Lacuna frente ao documento de referência:** Falta exigência formal explícita das seções `Negative Guardrails` (anti-patterns) e `Checklist de Fechamento` (stopping criteria) dentro da convenção e nos gates.
- **D2. Input e Gatilhos:**
  - Recebe intenção do usuário ou instrução de refatoração de skill existente.
  - Verifica catálogo de peças `docs/auditoria/mapa-pecas/catalogo-pecas.json`.
- **D3. Raio de Impacto e Isolamento:**
  - Fonte única estrita em `componentes/compartilhado/skills/<nome>/` (ou `componentes/<ferramenta>/skills/<nome>/`).
  - Nunca escreve direto em `.agents/`, `.claude/`, `.opencode/`.
  - Distribuição executada por script determinístico `ecossistema.py components sync`.
- **D4. Componentes e Fractalidade:**
  - Recruta `aidd-agent-writing` para redação técnica enxuta.
  - Recruta `aidd-dependencies` quando envolve skills de terceiros.
  - Utiliza os gates determinísticos `G_SKILL_ROT` e `G_SKILL_FORMATO`.

### Fase 2: O Chão de Fábrica (Workflow Agêntico)
- **D5. Visão e Escopo:**
  - Transformar requisitos operacionais ou regras de engenharia em um manual executável agêntico, com scripts determinísticos e zero perda de contexto.
- **[Estágio 1 - Busca e Unicidade] D6. O que o Estágio Faz:** Busca no catálogo por nomes e descrições semelhantes para evitar duplicidade.
- **[Estágio 1 - Busca e Unicidade] D7. O que o Estágio Recebe:** Nome proposto e escopo da nova skill.
- **[Estágio 1 - Busca e Unicidade] D8. O que o Estágio Processa:** Consulta `catalogo-pecas.json` e termos vizinhos.
- **[Estágio 1 - Busca e Unicidade] D9. O que o Estágio Entrega:** Veredito de novidade ("criar nova" vs "evoluir existente").
- **[Estágio 2 - Especificação de Testes] D6. O que o Estágio Faz:** Define 3 cenários comportamentais onde o agente erra sem a skill.
- **[Estágio 2 - Especificação de Testes] D7. O que o Estágio Recebe:** Casos de uso e falhas típicas de modelo comum.
- **[Estágio 2 - Especificação de Testes] D8. O que o Estágio Processa:** Análise de vulnerabilidade comportamental e baseline sem a skill.
- **[Estágio 2 - Especificação de Testes] D9. O que o Estágio Entrega:** Suíte de validação comportamental (testes em `tests/`).
- **[Estágio 3 - Escrita e Scaffolding] D6. O que o Estágio Faz:** Gera a estrutura `SKILL.md`, `scripts/`, `references/` e templates.
- **[Estágio 3 - Escrita e Scaffolding] D7. O que o Estágio Recebe:** Padrões da convenção e especificações técnicas.
- **[Estágio 3 - Escrita e Scaffolding] D8. O que o Estágio Processa:** Síntese em inglês técnico conciso respeitando teto de linhas e regras sintáticas.
- **[Estágio 3 - Escrita e Scaffolding] D9. O que o Estágio Entrega:** Arquivos físicos criados na pasta canônica `componentes/compartilhado/skills/<nome>/`.
- **D10. Orquestração e Topologia:**
  - O fluxo transita sequencialmente: Busca no Catálogo -> Baseline de Testes -> Redação do Manifesto -> Execução de Scripts -> Validação em Gates -> Sincronização Multi-harness.

### Fase 3: Resiliência e Economia (Engenharia Operacional)
- **D11. Tratamento de Exceções e Fallback:**
  - Se o gate `G_SKILL_FORMATO` ou `G_SKILL_ROT` falhar, o artefato não é propagado.
  - Rollback garantido pelo isolamento: edições feitas apenas na fonte única, mantendo harnesses sincronizados somente após validação.
  - **Lacuna apontada pelo documento externo:** O `SKILL.md` gerado necessita de seção obrigatória de `Failure Modes` (recuperação graciosa de erros em tempo de execução pelo subagente).
- **D12. Observabilidade e Frugalidade:**
  - Frugalidade máxima: frontmatter otimizado para carregamento dinâmico (on-demand injection).
  - Teto rígido de 450 linhas (meta de 150) garante que a leitura da skill consuma menos de 2.000 tokens de contexto.

### Fase 4: O Inspetor e a Expedição (Validação)
- **D13. Quality Gates (Portões):**
  - `python gates/G_SKILL_FORMATO.py`: Valida sintaxe YAML, regex do nome, `Use when`, tamanho e ausência de falsos runners.
  - `python gates/G_SKILL_ROT.py`: Assegura 100% de resolução física de arquivos referenciados em disco.
  - `python ecossistema.py components verify --tipo skill`: Comprova integridade e integridade hash entre harnesses.
- **D14. Critério de Rejeição (Rollback):**
  - Exit 1 em qualquer dos gates impede commit e distribuição.
  - Proibição de skills com nomes duplicados ou violação da Lei #4 (idioma em inglês no manual da máquina).
- **D15. Output Consolidado e Handoff:**
  - Skill sincronizada em todos os harnesses suportados (`.claude/`, `.agents/`, `.opencode/`, etc.).
  - Registro atualizado no catálogo de peças e manifesto de dependências quando aplicável.

---

## 3. Matriz de Avaliação da Execução
- [x] A ferramenta isolou seu raio de impacto corretamente?
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff?
