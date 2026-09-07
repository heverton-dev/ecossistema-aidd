# Item 2 — Registro do direcionamento correto e 2 novas Regras de Ouro (checklist anti-NIH, zero linguagem de marketing)

> **Escopo:** Entra: adicionar 2 Regras de Ouro novas ao `AGENTS.md` (checklist anti-NIH antes de escrever mecanismo novo; zero linguagem de marketing em mensagem de saída de ferramenta) e um gate/checklist que as torne verificáveis, não só texto. Não entra: reescrever as 7 Regras de Ouro existentes.
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (decisão de governança, mesmo nível das outras Regras de Ouro)

---

## Contexto ja investigado

- A Regra de Ouro #1 atual ("Determinismo Primeiro / Zero Token Fallacy") já apontava na direção certa, mas foi lida como "escreva seu próprio script determinístico" em vez de "não gaste esforço — seu ou de agente — reinventando o que já está resolvido". O levantamento NIH (`docs/features/oportunidades-reaproveitamento-oss-nih.md`) documenta 26 casos onde essa leitura errada gerou reinvenção de ferramenta madura.
- O achado "gate de segurança rotulado blindagem militar/homologado pra produção global" (item 7 do plano tático) é sintoma de uma causa mais ampla: nada no `AGENTS.md` hoje proíbe linguagem de marketing em mensagem de saída de ferramenta.
- Guia de referência já escrito e salvo fora do repo (não é fonte canônica do monorepo, é referência pessoal): `C:\Users\trcnologia\Desktop\CONSTRUA-SO-O-QUE-NINGUEM-CONSTRUIU.md` — o checklist de 5 perguntas e a tabela de ferramentas padrão de lá servem de base pra formalizar a regra aqui dentro do `AGENTS.md`.

## Definicao de Pronto

1. `AGENTS.md` §2 ganha uma 8ª Regra de Ouro: "Anti-NIH — antes de escrever mecanismo novo com mais de ~30-50 linhas pra um problema genérico (scaffolding, parsing, scanner, fila, dashboard, hardening), documentar por escrito por que nenhuma ferramenta OSS madura resolve."
2. `AGENTS.md` ganha uma 9ª Regra de Ouro: "Honestidade de Rótulo — nenhuma mensagem de saída de gate/CLI pode usar linguagem que sugira certificação/segurança maior do que a cobertura real testada (proibido: 'blindagem militar', 'homologado para produção global', 'nota A+' sem rubrica auditável por trás)."
3. Pelo menos 1 gate (pode reaproveitar/estender `G_ECOSSISTEMA_INTEGRIDADE.py` ou ser novo) faz uma checagem mecânica simples da regra 2 — ex.: grep de lista de termos proibidos nas mensagens de `print()`/`raise()` dos scripts de `gates/` e `scripts/gates/` de cada ferramenta, falhando se encontrar.
4. Reproduzir: inserir temporariamente um termo proibido numa mensagem de gate, rodar a checagem, confirmar que ela pega — depois reverter.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 2: Registro do direcionamento correto e 2 novas Regras de Ouro (checklist anti-NIH, zero linguagem de marketing).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 2: Registro do direcionamento correto e 2 novas Regras de Ouro (checklist anti-NIH, zero linguagem de marketing).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
