# 📜 Protocolo Norteador de Validação Humana e Testes Reais do Ecossistema AIDD

> **Status:** ATIVO & VIGENTE  
> **Data:** 06/09/2026  
> **Princípio Fundamental:** *"Trust, but verify"* — Nenhuma entrega é aceita apenas por relatório do agente; o desenvolvedor humano inspeciona no disco real, interage visualmente com a aplicação (frontend rodando), avalia e dá o aval explícito antes de avançar.

---

## 1. O Ciclo Interativo Obrigatório (Passo a Passo)

Para **CADA FERRAMENTA (Frente Isolada)** e para o **PROJETO PILOTO (Frente Integrada)**, o fluxo seguirá rigorosamente as 6 etapas abaixo:

```text
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 1. EXECUÇÃO  │ ──► │ 2. SHOW &    │ ──► │ 3. ANÁLISE   │
│ REAL NO      │     │    RUN       │     │    DO        │
│ DISCO        │     │ (Frontend On)│     │ DESENVOLVEDOR│
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
┌──────────────┐     ┌──────────────┐            │
│ 6. RELATÓRIO │ ◄── │ 5. COMPARATIV│ ◄──────────┘
│ COM NOTAS    │     │    ANTES vs  │     ┌──────────────┐
│ SINCERAS     │     │    DEPOIS    │ ◄── │ 4. CONTRA-   │
└──────────────┘     └──────────────┘     │    ANÁLISE   │
                                          │    DO AGENTE │
                                          └──────────────┘
```

1. **Execução Real no Disco:**
   - O agente cria e roda a ferramenta no diretório permanente indicado na Área de Trabalho (`C:\Users\trcnologia\Desktop\...`).
   - Nada de pastas temporárias ocultas.
2. **Demonstração & Execução do Frontend (*Show & Run*):**
   - O agente lista os arquivos gerados e coloca o servidor/aplicação para rodar em porta local (ex.: `http://localhost:3000` ou `http://localhost:8000`).
   - O desenvolvedor abre no navegador, clica, mexe e testa a interface e a API com as próprias mãos.
3. **Análise do Desenvolvedor Humano:**
   - O desenvolvedor aponta pontos fortes, falhas, bugs visuais, lentidões ou comportamentos inesperados.
4. **Contra-Análise e Conclusões Técnicas do Agente:**
   - O agente analisa as observações do usuário, investiga a causa raiz e aponta se o problema é de regras, modelo ou arquitetura.
5. **Resultado Comparativo (Antes vs. Depois):**
   - Se houver ajustes, o agente aplica as correções e apresenta a tabela comparativa explícita de melhoria.
6. **Relatório Hiper Completo com Notas Sinceras:**
   - Após o aval definitivo do usuário, gera-se o relatório com notas honestas (0 a 10) para: Facilidade de Uso, Robustez, Fidelidade ao Prompt, Velocidade e Acabamento Visual.

---

## 2. Mapa das Pastas Permanentes de Teste

| # | Bateria / Frente | Pasta Permanente no Disco | O que você irá inspecionar e rodar |
|---|---|---|---|
| **1** | **AIDD Forge (Isolado)** | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-forge` | Governança criada, pre-commit hook e 7 gates locais funcionando. |
| **2** | **AIDD Generator (Isolado)** | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-generator` | Aplicação completa gerada com frontend para rodar no navegador. |
| **3** | **AIDD Master (Isolado)** | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-master` | Monólito modular com Swagger Studio interativo no browser. |
| **4** | **AIDD Enterprise (Isolado)** | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-enterprise` | Componentes injetados certificados com hashes SHA-256 reais. |
| **5** | **AIDD Ops (Isolado)** | `C:\Users\trcnologia\Desktop\teste-isolado-aidd-ops` | Planos de infra, Compose, preflight E2E e simulador de deploy. |
| **6** | **Ecossistema Integrado** | `C:\Users\trcnologia\Desktop\teste-integrado-ecossistema-aidd` | O ciclo de vida completo: Ideia -> Forge -> Master -> Enterprise -> Ops. |

---

## 3. Critérios de Avaliação das Notas (0 a 10)

Cada relatório conterá o boletim com justificativas transparentes:
- **Usabilidade Leiga (0-10):** Um usuário sem conhecimento técnico consegue usar via chat sem travar?
- **Rigor de Engenharia / PhD (0-10):** A arquitetura é limpa, tipada, modular e sem gambiarras?
- **Fidelidade da Geração (0-10):** O código cumpre exatamente o que foi solicitado sem alucinações?
- **Acabamento do Frontend / UX (0-10):** A interface é agradável, responsiva e funcional?
- **Autonomia & Segurança (0-10):** Passou nos gates sem violar segredos ou regras de governança?

---

## 4. Regra de Execução de Frontend

Sempre que um teste envolver telas ou APIs interativas:
- O agente **DEVE iniciar o servidor local** (FastAPI, Vite, Next.js, HTML/HTTP estático).
- O agente **DEVE fornecer o link direto clicável** (ex: [http://localhost:8000/docs](http://localhost:8000/docs)).
- O agente **NÃO PODE considerar a etapa concluída** antes de o desenvolvedor confirmar que abriu, mexeu e aprovou o funcionamento visual.
