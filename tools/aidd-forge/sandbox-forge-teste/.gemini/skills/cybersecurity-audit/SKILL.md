---
name: cybersecurity-audit
description: Varredura estatica cega contra OWASP Top 10 (SQL Injection, IDOR, XSS e demais categorias) sobre o codigo implementado.
---

# Cybersecurity Audit — Varredura Estatica OWASP Top 10

## Objetivo

Auditar estaticamente a fatia implementada contra as categorias do
OWASP Top 10, em modo cego (sem ver a intencao original do pedido) para
evitar vies de confirmacao.

## Categorias Verificadas

- **SQL Injection:** queries concatenadas com input do usuario em vez
  de parametros/prepared statements.
- **IDOR (Insecure Direct Object Reference):** endpoints que aceitam ID
  de recurso sem checar se o usuario autenticado tem permissao sobre
  aquele recurso.
- **XSS:** saida de dados nao sanitizados/nao escapados em contexto
  HTML/JS.
- **Auth quebrada:** endpoints sensiveis sem verificacao de sessao/token.
- **Exposicao de segredos:** chaves, tokens ou credenciais hardcoded no
  codigo ou em logs.
- **Deserializacao insegura, SSRF, configuracao incorreta de
  seguranca:** demais categorias do OWASP Top 10 vigente.

## Escopo Permitido

- Ler o codigo produzido em modo somente-leitura.
- Escrever `security_audit_report.md` listando cada achado com:
  arquivo, linha, categoria OWASP, severidade (critica/alta/media/baixa),
  e mitigacao sugerida.

## Escopo Proibido

- Nao corrigir o codigo diretamente: apenas reportar.
- Nao aprovar (`exit 0`) a fatia se houver vulnerabilidade critica ou
  alta sem mitigacao documentada.

## Gate de Saida

`exit 0` somente se `security_audit_report.md` existir e nenhum achado
critico/alto estiver marcado como nao mitigado.
