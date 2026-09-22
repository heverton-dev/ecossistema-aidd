# Metodologia e Protocolo Canônico de Auditoria Bit a Bit do Ecossistema AIDD

> **Status:** Ativo e Canônico  
> **Localização das Fichas:** `docs/auditoria/`  
> **Manifesto Dinâmico de Handoff:** `docs/auditoria/manifesto_auditoria.json`

---

## 1. Objetivo e Filosofia (Do Micro ao Macro)

A auditoria bit a bit inspeciona cada ferramenta, micro-ferramenta e fluxo do ecossistema AIDD em nível atômico. Nenhum fluxo macro é executado ou validado sem que cada engrenagem micro esteja funcionalmente provada com 100% de conformidade, zero stubs e portões que mordem.

---

## 2. As 11 Dimensões de Análise por Ferramenta

Cada ficha técnica de auditoria deve dissecar obrigatoriamente:

1. **INPUT (Recebe):** CLI arguments, flags, variáveis de ambiente, schemas JSON e arquivos consumidos.
2. **PROCESSAMENTO (Cria / Executa):** Classes internas, algoritmos de cálculo, manipulação AST/regex e fluxos determinísticos.
3. **OUTPUT (Entrega):** Arquivos gerados, diretórios criados, saídas formatadas (JSON, Markdown, HTML) e códigos de saída (`exit 0` / `exit 1`).
4. **CONFIGS (Botões Reconfigurados):** Flags CLI, configurações de templates e perfis customizáveis.
5. **GATES (Guardas de Qualidade):** Quality gates executados e testes que provam a rejeição de violações (*o portão morde*).
6. **SCRIPTS DETERMINÍSTICOS (0 LLM):** Métodos e rotinas 100% mecânicas sem inteligência não-determinística.
7. **HOOKS (Campainhas de Alerta):** Interceptadores git, scripts de checagem prévia e gatilhos de segurança.
8. **AGENTS (Pessoas / Personas):** Subagentes acionados, tempos de vida e regras de isolamento de contexto.
9. **SKILLS (Tarefas Únicas):** Habilidades operacionais vinculadas à ferramenta.
10. **MCPS (Telefones para Fora):** Ferramentas de contexto Model Context Protocol consumidas ou expostas.
11. **RULES (Bilhetes / AGENTS.md):** Diretrizes canônicas, invariantes arquiteturais e regras de execução locais.

---

## 3. Ciclo de Vida da Ficha de Auditoria (3 Sessões Obrigatórias)

Cada arquivo em `docs/auditoria/<nome-da-ferramenta>-YYYY-MM-DD.md` é estruturado em três seções dinâmicas:

### Sessão I: Estado Atual (Diagnóstico Pré-Implementação)
- Data da auditoria e versão do módulo.
- Matriz das 11 dimensões preenchida minuciosamente.
- Cobertura de testes unitários reais e resultado dos quality gates.
- Inventário de falhas, desvios da Lei #1 à #13 e gargalos encontrados.

### Sessão II: Plano de Correção e Tickets de Melhoria
- Lista atômica de tickets de correção (Tracer Bullets) no padrão TDD Red-Green.
- Definição precisa do arquivo alvo, teste que irá quebrar e código de correção.
- Fluxo de execução automatizada das correções.

### Sessão III: Estado Pós-Implementação (Validação e Certificação)
- Relatório de reexecução dos testes e quality gates após as correções.
- Novo estado consolidado das 11 dimensões da ferramenta.
- Handoff registrado com status `CONCLUIDO` no `manifesto_auditoria.json`.

---

## 4. Ordem Topológica da Auditoria

1. **Camada 0: Micro-Fundação & Governança:** `aidd-forge`, `aidd-planner`.
2. **Camada 1: Motores Especializados (Tríade):** `aidd-generator` (Fluxo 01), `aidd-factory` (Fluxo 02), `aidd-bridge` (Fluxo 03).
3. **Camada 2: Meso-Camada & Convergência:** `aidd-master` (Monólito Modular VSA), `vsa_join_barrier.py`, `dispatch_pipeline.py`.
4. **Camada 3: Resiliência & Produção:** `aidd-enterprise`, `aidd-ops`.
