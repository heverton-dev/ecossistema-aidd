# PROCESSO E DECISÕES — Skill Geradora de Planos de Auditoria/Evolução/Testes

> **Origem:** pedido do usuário, 06/09/2026 — formalizar em uma skill (vivendo em `componentes/`) o processo manual já usado 3 vezes neste monorepo para gerar pastas de plano com um padrão estrutural comum: `docs/planos/evolucao-notas-auditoria/`, `docs/planos/refinamento-notas-auditoria/`, `docs/planos/testes-completos-ecossistema/`.
> **Propósito deste arquivo:** registro único do *processo*, igual ao das 3 iniciativas anteriores — o conteúdo técnico do item vive em documento próprio (ver §3). Esta própria pasta serve, adicionalmente, como um 4º exemplo real do padrão para o agente executor consultar.

---

## 1. O que este esforço busca (para não virar promessa vazia)

A skill **não substitui julgamento humano** — ela só reduz o trabalho manual de redigitar a estrutura/convenções repetitivas (pastas, nomenclatura de arquivo, seções internas, checagem de cercas de código) que hoje eu faço à mão toda vez que uma nova iniciativa de plano começa. As decisões que sempre exigiram uma pessoa real — quais itens entram, qual opção escolher entre alternativas, quando um item está de fato aprovado ou concluído — continuam exigindo uma pessoa real depois que a skill existir. Isso é regra fixa, não uma aspiração (ver §4).

## 2. Mesmo processo das iniciativas anteriores

Diagnóstico rápido do que precisa ser formalizado → Definição de Pronto travada → um único Prompt de Execução autocontido (PT-BR + EN-US), pronto para copiar e colar num agente executor → eu audito por reprodução real (nunca confio no relatório do executor) → registro do veredito.

## 3. Onde vive o conteúdo técnico

| # | Item | Documento |
|---|---|---|
| 1 | Criar a skill compartilhada `planos-auditoria-runner` (nome sugerido) em `componentes/compartilhado/skills/` | `01-criar-skill-planos-auditoria-runner.md` |

## 4. Regras fixas que valem para este item (e para a skill que ele produz)

1. **A skill nunca decide ou aprova sozinha.** Ela gera estrutura e rascunhos, sempre marcados explicitamente como "aguardando aprovação" — nunca como aprovados/concluídos por conta própria. Regra motivada por um incidente real já registrado em memória (`feedback-fork-nao-pode-decidir-nem-fabricar-aprovacao`): um fork de levantamento já fabricou uma "decisão do usuário" que nunca aconteceu.
2. **A skill nunca envia o Prompt de Execução a um agente executor sozinha, nem faz commit/push.** Essas ações continuam humanas (ou seguem o protocolo já registrado de auditoria pós-teste, que também é acionado por sinal explícito do usuário, nunca pela skill).
3. **Teste real da skill nunca escreve em `docs/planos/` de verdade.** Qualquer geração de exemplo para validar a skill acontece em diretório temporário isolado.
4. **Checagem de cercas de código aninhadas obrigatória** em qualquer Prompt de Execução que a skill gerar (contagem de marcadores ``` — pares isolados, nunca aninhados) — regra reincidente 2x antes desta iniciativa, agora vira parte do próprio protocolo da skill.
5. **Sem git commit/push** feito pela skill em nenhuma circunstância.

## 5. Registro de progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Criar skill `planos-auditoria-runner` | ⏳ Prompt gerado, aguardando execução | `01-criar-skill-planos-auditoria-runner.md` |

Esta tabela é atualizada para ✅ Concluído só depois que a auditoria por reprodução real confirmar o resultado.
