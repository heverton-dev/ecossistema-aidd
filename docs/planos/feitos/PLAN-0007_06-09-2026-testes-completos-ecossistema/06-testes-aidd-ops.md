# Bateria 6 — Testes End-to-End da Ferramenta AIDD-Ops

> **Status:** ✅ [CONCLUÍDO E HOMOLOGADO EM 06/09/2026 — 7/7 APROVADO]  
> **Ferramenta/Escopo:** `tools/aidd-ops` (5ª ferramenta oficial do ecossistema) + roteamento raiz `python ecossistema.py ops ...`.  
> **Artefatos de saída:** `docs/testes/testes/06_aidd_ops.py`, `docs/testes/prompts/06_aidd_ops.txt` e `docs/testes/relatorios/06_aidd_ops.md`.

---

## 1. Contexto Investigado

A ferramenta `aidd-ops` foi integrada como a 5ª ferramenta oficial do monorepo ecossistema-aidd. Seu núcleo foi validado em 9 pacotes com 56 testes unitários herméticos e 2 Quality Gates específicos (`G_OPS_MVP.py` e `G_OPS_SSH.py`), além do gate de infraestrutura `G_INFRA_COMPOSE.py`.

A superfície de interface que um desenvolvedor ou operador utiliza diretamente na CLI e nos harnesses compreende:
1. **Intake, Curadoria e Sizing (Fases 1 a 3):**
   - `python ecossistema.py ops plan "<briefing do nicho>"` gerando o plano de infraestrutura estruturado em JSON com conformidade estrita aos schemas.
2. **Runner SSH Remoto Seguro (Fase 4):**
   - `python ecossistema.py ops bootstrap <host> --dry-run` demonstrando a execução determinística da lista fechada de 5 comandos de hardening/docker sem injeção shell.
3. **MCPs de Borda Cloudflare e Docker (Fases 5 e 8):**
   - Servidores MCP em `tools/aidd-ops/mcps/` respondendo via JSON-RPC/stdio a chamadas de listagem e inspeção sem bibliotecas de terceiros desnecessárias (stdlib).
4. **Validação de Topologias Docker Compose (Fases 7 e 8):**
   - Quality Gate `gates/G_INFRA_COMPOSE.py` auditando a integridade estática dos composes, colisão de portas e cobertura de variáveis em `.env.example`.
5. **Pre-flight E2E (Fase 9):**
   - `python ecossistema.py ops preflight <ambiente>` executando a bateria determinística de 4 checagens (healthz, SSL, DNS e webhook).
6. **Orquestrador de Deploy E2E (Fases 1 a 10 encadeadas):**
   - `python ecossistema.py ops deploy <ambiente> --dry-run` executando o fluxo completo com Result monad, fail-fast e verificação do plano de rollback.

---

## 2. Definição de Pronto (DoD)

Para declarar esta bateria concluída e aprovada, o script `docs/testes/testes/06_aidd_ops.py` deve executar em ambiente isolado (diretório temporário para saídas de planos) e comprovar:

1. **Roteamento Raiz via `ecossistema.py ops`:**
   - Execução de `python ecossistema.py ops --help` retornando exit code 0 e listando os subcomandos oficiais (`plan`, `bootstrap`, `preflight`, `deploy`).
2. **Geração de Plano de Nicho (Intake -> Curadoria -> Sizing):**
   - Execução de `python ecossistema.py ops plan "Clínica médica com agendamento online e prontuário"` gerando artefato JSON válido conforme `schema_sizing_output.json`.
3. **Execução de Bootstrap SSH em modo seguro `--dry-run`:**
   - Execução de `python ecossistema.py ops bootstrap 192.0.2.1 --user root --dry-run` retornando exit code 0 e listando os 5 passos planejados sem tentar abrir socket real.
4. **Inspeção de Contêineres e DNS via MCPs:**
   - Execução do servidor `docker-mcp` listando ferramentas disponíveis (`docker_compose_config`, `docker_ps`).
   - Execução do servidor `cloudflare-mcp` listando ferramentas (`consultar_dns`, `create_dns_record`).
5. **Auditoria Estática de Compose via Quality Gate:**
   - Execução direta de `python gates/G_INFRA_COMPOSE.py` retornando exit code 0 para todos os 7 composes de templates canônicos.
6. **Bateria de Preflight Hermética:**
   - Execução de `python ecossistema.py ops preflight staging` contra servidor de teste local hermético retornando Result.ok com status 200.
7. **Deploy E2E Dry-Run com Rollback Seguro:**
   - Execução de `python ecossistema.py ops deploy staging --dry-run` simulando as 10 fases encadeadas e confirmando geração do relatório final de entrega.
8. **Relatório Formal Consolidado:**
   - Geração de `docs/testes/relatorios/06_aidd_ops.md` contendo tempos de execução, saídas reais e veredito técnico.

---

## 3. Prompt de Execução

> Copie e cole o bloco abaixo para o agente executor rodar a bateria determinística de ponta a ponta.

```
Você é o executor técnico responsável por rodar a BATERIA 6 — TESTES END-TO-END DA FERRAMENTA AIDD-OPS, seguindo as regras fixas de "docs/planos/testes-completos-ecossistema/00-PROCESSO-E-DECISOES.md".

SEU OBJETIVO:
1. Criar o script de teste determinístico em "docs/testes/testes/06_aidd_ops.py".
2. Salvar os briefings e payloads de teste em "docs/testes/prompts/06_aidd_ops.txt".
3. Executar o script de teste de verdade, capturando todos os tempos, saídas brutas e exit codes reais.
4. Gerar o relatório consolidado em "docs/testes/relatorios/06_aidd_ops.md" com o veredito técnico.

REGRAS INEGOCIÁVEIS:
- Nunca use mock falso onde um servidor HTTP local real pode ser instanciado em 127.0.0.1 (use http.server.HTTPServer hermético).
- Toda execução de rede externa deve rodar em modo seguro (--dry-run), respeitando o teto de custo e segurança sem tentar conexão remota sem credenciais explícitas.
- Nunca faça commit ou push automático.
- Capture saídas e tempos reais. Exit codes diferentes de 0 devem ser documentados com honestidade técnica estrita.
```

---

## 4. Prompt de Execução — English version

```
You are the technical executor responsible for running BATTERY 6 — END-TO-END TESTS FOR AIDD-OPS, following the fixed rules in "docs/planos/testes-completos-ecossistema/00-PROCESSO-E-DECISOES.md".

YOUR OBJECTIVE:
1. Create the deterministic test script in "docs/testes/testes/06_aidd_ops.py".
2. Save test briefings and payloads in "docs/testes/prompts/06_aidd_ops.txt".
3. Execute the test script for real, capturing all real execution times, raw outputs, and exit codes.
4. Generate the consolidated report in "docs/testes/relatorios/06_aidd_ops.md" with the technical verdict.

NON-NEGOTIABLE RULES:
- Never use fake mocks where a real local HTTP server can be spun up on 127.0.0.1 (use hermetic http.server.HTTPServer).
- All external network operations must run in safe mode (--dry-run), respecting security boundaries without attempting remote connections without explicit credentials.
- Never execute automatic git commit or push.
- Capture real outputs and durations. Any exit code other than 0 must be documented with strict technical honesty.
```
