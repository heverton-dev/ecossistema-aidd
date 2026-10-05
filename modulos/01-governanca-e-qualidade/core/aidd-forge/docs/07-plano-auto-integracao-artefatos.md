# 07 — Plano de Auto-Integração de Artefatos

> **Objetivo:** Sistema de auto-integração onde o framework detecta, injeta e integra automaticamente novos artefatos (skills, MCPs, rules, specs, configs, roteiros) na camada correta do projeto.

---

## Visão Geral

Quando alguém adiciona uma nova skill, MCP, rule, spec, config ou roteiro, o framework deve:

1. **Detectar automaticamente** a camada/categoria do artefato
2. **Injetar fisicamente** os arquivos na estrutura correta
3. **Integrar estruturalmente** ao projeto (registros, índices, globals)
4. **Atualizar todas as referências** cruzadas (AGENTS.md, SKILL.md, indexadores, etc.)

Isso vale para **todos** os tipos de artefatos: skills, MCPs, rules, specs, configs, roteiros.

---

## Fase 1 — Mapeamento

**Status:** Pendente

**Objetivo:** Entender a árvore de diretórios atual e catalogar onde vivem cada tipo de artefato.

**Entregáveis:**
- Levantamento completo da árvore de diretórios
- Catálogo de camadas: `core/`, `tutoriais/`, `extension/`, `landing/`, etc.
- Identificação dos arquivos-âncora que precisam ser atualizados (ex: `AGENTS.md`, `available_skills`, etc.)
- Mapa de dependências cruzadas entre artefatos

**Ações:**
- [ ] Mapear diretório `aidd_forge/`
- [ ] Mapear diretório `~/.agents/skills/`
- [ ] Mapear diretório `~/.config/opencode/skills/`
- [ ] Identificar padrões de naming por tipo
- [ ] Listar arquivos-âncora (AGENTS.md, SKILL.md, indexes)

---

## Fase 2 — Motor de Classificação

**Status:** Pendente

**Objetivo:** Criar um classificador que recebe um artefato + metadados e retorna a camada de destino.

**Entrada:**
- Artefato (código/template)
- Metadados: nome, tipo, descrição, dependências

**Saída:**
- `tipo`: skill | mcp | rule | spec | config | roteiro
- `camada`: core | tutoriais | extension | landing | custom
- `destino`: path exato onde o artefato deve ser criado
- `referencias`: lista de arquivos-âncora que precisam ser atualizados

**Ações:**
- [ ] Definir taxonomia de tipos
- [ ] Definir regras de classificação por tipo
- [ ] Implementar motor de classificação (Python)
- [ ] Criar schema de metadados de entrada
- [ ] Testar com cenários reais

---

## Fase 3 — Engine de Injeção

**Status:** Pendente

**Objetivo:** Copiar, registrar e atualizar referências de forma transacional.

**Fluxo:**
1. Criar artefato no destino (template por tipo)
2. Registrar no índice do tipo (ex: `available_skills` no AGENTS.md)
3. Atualizar referências cruzadas (outros arquivos-âncora)
4. Validação pós-injeção: existe? path correto? index atualizado?

**Ações:**
- [ ] Criar template de cada tipo de artefato
- [ ] Implementar rotina de cópia com validação
- [ ] Implementar rotina de registro em índices
- [ ] Implementar rotina de atualização de referências
- [ ] Implementar rollback em caso de falha
- [ ] Criar validador pós-injeção

---

## Fase 4 — Interface (CLI / Linguagem Natural)

**Status:** Pendente

**Objetivo:** Interface amigável para o usuário adicionar artefatos.

**Opções:**
- CLI: `/add-skill nome --tipo=cybersecurity --camada=extension`
- Linguagem Natural: *"adicione uma skill de análise de segurança cibernética"*
- Formulário interativo com perguntas guiadas

**Ações:**
- [ ] Definir interface de comando
- [ ] Implementar parser de linguagem natural (se aplicável)
- [ ] Criar fluxo interutivo de coleta de metadados
- [ ] Integrar com motor de classificação (Fase 2)
- [ ] Integrar com engine de injeção (Fase 3)
- [ ] Testar fluxo end-to-end

---

## Diagrama de Fluxo

```
┌─────────────┐
│   Usuário   │
│  adiciona   │
│  artefato   │
└──────┬──────┘
       │
       ▼
┌──────────────┐
│  Classificador│  ← detecta tipo + camada
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Injetor     │  ← cria arquivo + registra + atualiza refs
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Validador   │  ← confirma integração OK
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Confirma    │  → artefato integrado ao projeto
└──────────────┘
```

---

## Tipos de Artefatos Suportados

| Tipo | Exemplo | Camada padrão |
|------|---------|---------------|
| Skill | cybersecurity-analyzer | extension |
| MCP | notion-server | extension |
| Rule | no-stubs | core |
| Spec | api-contract | core |
| Config | brand-configurator | custom |
| Roteiro | deploy-vps | tutoriais |

---

## Notas

- Este plano NÃO substitui a estrutura existente — complementa
- Prioridade: skills e MCPs primeiro, depois rules e specs
- Validação sempre por observação (nunca por asserção)
- Rollback obrigatório em caso de falha parcial
