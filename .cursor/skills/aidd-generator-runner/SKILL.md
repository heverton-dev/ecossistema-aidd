---
name: aidd-generator-runner
description: Dispara a fábrica autônoma de software do aidd-generator através do pipeline de 8 fases.
---

# AIDD Generator Runner

Esta skill inicializa o pipeline de criação autônoma de software a partir de uma descrição em linguagem natural:
1. Pesquisa e Requisitos
2. Análise e Decomposição
3. Arquitetura e Design
4. Decisões Técnicas
5. Criação de Artefatos e Schemas (Draft 2020-12)
6. Documentação Completa
7. Autocrítica e Auditoria por Gates
8. Implementação Funcional com Testes Automatizados

## Como Usar
No chat do assistente:
```text
/generate <ideia>
```

Via CLI Python:
```bash
python ecossistema.py generate "<ideia>"
```
