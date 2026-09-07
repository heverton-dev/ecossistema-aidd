# PROCESSO E DECISÕES — Validação Humana e Testes Reais em Sessões Isoladas

> **Origem:** Pedido do desenvolvedor em 06/09/2026 — "rodar os testes 1 em cada sessão para não haver contaminação de contexto, com relatório HIPER COMPLETO com todas as explicações e NOTAS, rodando frontend para ver funcionando e mexer na aplicação antes do aval final".
> **Propósito deste arquivo:** Registro canônico do processo de homologação empírica com o desenvolvedor no controle absoluto de cada teste.
> **Padrão:** Rigorosamente idêntico a `docs/planos/integracao-aidd-ops/00-PROCESSO-E-DECISOES.md`.

---

## 1. A Decisão

Executar a validação do Ecossistema AIDD em **6 sessões independentes e isoladas**, eliminando qualquer risco de saturação de contexto ou contaminação de memória entre ferramentas:

```text
Sessão Limpa ──► Executa no Disco Real (Desktop) ──► Sobe Aplicação/Frontend ──►
Desenvolvedor Analisa e Mexe ──► Contra-Análise Técnica ──► Comparativo Antes/Depois ──►
Aval do Usuário ──► Relatório Hiper Completo com Notas Sinceras (0-10) ──► PRÓXIMA SESSÃO
```

Nenhum teste roda em pasta temporária oculta. Tudo é criado em caminhos persistentes visíveis na Área de Trabalho para auditoria direta do usuário.

---

## 2. As 6 Sessões Isoladas

| Sessão | Bateria | Pasta Persistente no Disco | Foco da Inspeção & Interação | Documento |
|---|---|---|---|---|
| **1** | AIDD Forge | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-forge` | Governança, pre-commit hook e 7 gates instalados no projeto alvo | `01-teste-isolado-aidd-forge.md` |
| **2** | AIDD Generator | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-generator` | Software construído em 8 fases com frontend web rodando | `02-teste-isolado-aidd-generator.md` |
| **3** | AIDD Master | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-master` | Monólito modular com Swagger Studio interativo no browser | `03-teste-isolado-aidd-master.md` |
| **4** | AIDD Enterprise | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-enterprise` | Componentes injetados com selo de integridade SHA-256 e Zero-Trust | `04-teste-isolado-aidd-enterprise.md` |
| **5** | AIDD Ops | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-ops` | Sizing de VPS, Docker Compose, Preflight HTTP real e simulador de deploy | `05-teste-isolado-aidd-ops.md` |
| **6** | Integrado E2E | `C:\Users\trcnologia\Desktop\teste-integrado-ecossistema-aidd` | O ciclo de vida completo unificado das 5 ferramentas com frontend | `06-teste-integrado-ciclo-completo.md` |

---

## 3. Protocolo Mandatório para Cada Sessão ("Show & Run")

1. **Autonomia de Sessão:** Cada sessão é aberta em uma janela limpa do assistente, recebendo apenas o prompt autocontido daquele pacote.
2. **Execução Visual Obrigatória:** Se a ferramenta gerar interface ou API web, o assistente **DEVE** subir o servidor local e fornecer o link direto clicável (`http://localhost:...`).
3. **Aval Humano Obrigatório:** O assistente **NÃO PODE** redigir o relatório final nem considerar o pacote concluído antes de o usuário interagir e responder o que achou.
4. **Relatório Hiper Completo:** Contendo análise profunda, tabela comparativa de antes vs. depois (se houve ajustes) e notas sinceras de 0 a 10 (Usabilidade Leiga, Rigor de Engenharia, Fidelidade, UX/Frontend e Segurança).

---

## 4. Registro de Progresso

| Sessão | Status | Aval do Desenvolvedor | Documento |
|---|---|:---:|---|
| 1. AIDD Forge | ✅ Concluído & Aprovado | Aprovado | `01-teste-isolado-aidd-forge.md` |
| 2. AIDD Generator | ✅ Concluído & Aprovado | Aprovado | `02-teste-isolado-aidd-generator.md` |
| 3. AIDD Master | ✅ Concluído & Aprovado | Aprovado | `03-teste-isolado-aidd-master.md` |
| 4. AIDD Enterprise | ✅ Concluído & Aprovado | Aprovado | `04-teste-isolado-aidd-enterprise.md` |
| 5. AIDD Ops | ✅ Concluído & Aprovado | Aprovado | `05-teste-isolado-aidd-ops.md` |
| 6. Integrado E2E | ✅ Concluído & Homologado | Aprovado (Nota 9.56) | `06-teste-integrado-ciclo-completo.md` |

---
