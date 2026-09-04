# AGENTS.md — Fase 04: Audit Security

## Objetivo

Auditar **cegamente** a fatia implementada contra o OWASP Top 10. "Cega"
significa: o auditor não vê a intenção original do pedido, apenas o
código final — evita viés de confirmação.

## Escopo Permitido

- Ler o código produzido em `phase_03_implementation/` em modo
  somente-leitura.
- Escrever `audit_report.md` nesta pasta listando vulnerabilidades
  encontradas, mapeadas para a categoria OWASP correspondente.

## Escopo Proibido

- Não corrigir o código diretamente: apenas reportar.
- Não usar nenhum MCP com permissão de escrita fora desta pasta.
- Não aprovar (`exit 0`) a fatia se houver vulnerabilidade crítica
  (injeção, segredo exposto, auth quebrada) sem mitigação documentada.

## Gate de Saída

`exit 0` somente se `audit_report.md` existir e nenhuma vulnerabilidade
crítica estiver marcada como não mitigada.
