# Item — maquina-estados-pipeline-generator-e-resume

> **Escopo:** Implementar máquina de estados formal e retomada inteligente (--resume) no pipeline do aidd-generator, com validação jsonschema estrita na leitura inter-fases.
> **Status:** [PARCIAL — parte ja implementada, ver auditoria abaixo]
> **Auditoria por reproducao real (11-09-2026):** PARCIAL. .aidd/cache/_pipeline_state.json e gravado por pipeline_completo.py. Faltam a flag --resume (nao existe nos scripts do generator) e a validacao das entradas de cache por jsonschema.

---

## Contexto já investigado

- executar_pipeline é uma função linear sem máquina de estados [PIPE-1/3/4]. Falha na fase 7 força reexecutar fases 1-6 queimando tokens. Cache truncado gera crash cru.

## Definição de Pronto

1. Criar estado estruturado versionado `.aidd/cache/_pipeline_state.json` gravado atomicamente.
2. Implementar flag `--resume` que pula fases com status COMPLETO e artefatos válidos.
3. Validar entradas de cache com jsonschema na fronteira de leitura de cada fase.
4. Tratar JSON corrompido com `_falhar` estruturado e orientativo.

## Critério de saída

- Pipeline retoma a partir da fase falha sem gastar tokens nas fases anteriores. Teste com cache corrompido falha de forma limpa.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execução (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Você vai implementar o Item: maquina-estados-pipeline-generator-e-resume.
Siga rigorosamente a Definição de Pronto acima:
1. Criar estado estruturado versionado `.aidd/cache/_pipeline_state.json` gravado atomicamente.
2. Implementar flag `--resume` que pula fases com status COMPLETO e artefatos válidos.
3. Validar entradas de cache com jsonschema na fronteira de leitura de cada fase.
4. Tratar JSON corrompido com `_falhar` estruturado e orientativo.
Garanta exit 0 nos testes e gates pertinentes.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item: maquina-estados-pipeline-generator-e-resume.
Strictly follow the Definition of Done above:
1. Criar estado estruturado versionado `.aidd/cache/_pipeline_state.json` gravado atomicamente.
2. Implementar flag `--resume` que pula fases com status COMPLETO e artefatos válidos.
3. Validar entradas de cache com jsonschema na fronteira de leitura de cada fase.
4. Tratar JSON corrompido com `_falhar` estruturado e orientativo.
Ensure exit code 0 across relevant tests and gates.
```
