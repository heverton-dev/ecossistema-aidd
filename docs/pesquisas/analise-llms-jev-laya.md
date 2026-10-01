# Análise Técnica & Sem Marketing: Modelos de Decisão Jev e Laya

> **Data da Investigação:** 01/10/2026  
> **Escopo:** Avaliação dos modelos Jev (TypeSafe AI) e Laya (Convai Innovations), seu hype, arquitetura, aplicações reais e conformidade com o ecossistema AIDD.

---

## 1. O que são estes modelos e por que o HYPE?

### O que são na prática
**Jev** e **Laya** não são LLMs generativos tradicionais (como Claude, GPT-4 ou Gemini) que "escrevem" texto token por token. Eles pertencem à categoria chamada **"System One Decision Models"** (Modelos de Decisão Não-Autorregressivos):

1. **Jev (TypeSafe AI):** Serviço proprietário fechado, disponibilizado via API gerenciada, focado em tomadas de decisão ultra-rápidas em nuvem.
2. **Laya (Convai Innovations / Nandakishor M):** Família open-source (licença Apache 2.0), baseada em um encoder **ModernBERT-large (421M parâmetros)**, projetada para rodar localmente (CPU/GPU/Apple Silicon/ONNX) mantendo compatibilidade de protocolo com a API do Jev.

### Mecanismo de Funcionamento
Em vez do loop autorregressivo tradicional (onde o modelo cospe palavras sequencialmente e torce para que o JSON saia no formato correto), esses modelos recebem um **estado** (texto, log, payload JSON) e uma **pergunta tipada**, resolvendo a classificação em **um único forward pass** (inferência direta do encoder, tipicamente de 30ms a 40ms):
- **Choice:** Seleciona 1 rótulo entre uma lista finita predefinida.
- **Score:** Retorna uma pontuação calibrada em escala ordenada (ex: 1 a 5).
- **Noul (Booleano):** Retorna uma probabilidade estrita/calibrada para uma afirmação afirmativa/negativa (Sim/Não).

### A Razão do Hype
O hype decorre de uma dor real da indústria de IA:
- **Desperdício de recursos:** Gastar modelos de 70B+ ou APIs caras (como GPT-4o ou Claude 3.5 Sonnet) pagando centenas de tokens para fazer tarefas idiotas de roteamento como "classifique se este chamado é urgente (Sim/Não)" ou "escolha a categoria A, B ou C".
- **Latência e fragilidade de parsing:** Um LLM generativo demora de 500ms a 3s para gerar texto, pode alucinar ou cuspir JSON quebrado com markdown indesejado. Jev e Laya resolvem isso em ~30ms retornando diretamente um vetor de probabilidade calibrado.

---

## 2. Para que servem estes modelos?

Eles servem exclusivamente como **roteadores semânticos de alta velocidade e baixo custo**:

- **Triagem e Roteamento de Tickets:** Direcionar mensagens de suporte para departamentos específicos.
- **Guards e Moderação Semântica:** Identificar spam, toxicidade ou tentativas de jailbreak antes de invocar um modelo pesado.
- **Circuit Breakers / Escalação:** Avaliar incerteza e decidir se uma tarefa vai para automação ou se requer intervenção humana.
- **Classificação de Intenção em Gateways:** Identificar qual ferramenta ou subagente deve ser acionado a partir de uma frase de usuário informal.

---

## 3. Estes modelos são utilizáveis em projetos do dia a dia como o ecossistema-aidd?

### Resposta Direta
**Parcialmente e apenas em pontos marginais específicos.** Eles **NÃO** servem para as atividades centrais do ecossistema (código, refatoração, gates ou documentação).

### Quadro Comparativo no Contexto AIDD

| Função no Ecossistema | Aplicabilidade de Jev / Laya | Status no AIDD |
| :--- | :--- | :--- |
| **Geração de Código & Refatoração** | Impossível (modelos não geram texto/código) | ❌ Inaplicável |
| **Execução de Quality Gates (Lei #2)** | Proibido (portões devem ser determinísticos) | ❌ Não Conforme (Viola Lei #1 e #2) |
| **TDD / Suíte de Testes (Lei #5)** | Inaplicável | ❌ Inaplicável |
| **Geração de Documentação / SDD / BDD** | Impossível (não geram prosa) | ❌ Inaplicável |
| **Triagem Semântica no Intake (Pré-Plano)** | Viável (classificar intenção vaga de usuário) | ⚠️ Opcional / Marginal |
| **Roteador de Comandos no CLI** | Viável, mas redundante com regex/CLI parser | ⚠️ Dispensável |

---

## 4. Se utilizáveis, como de fato utilizar no ecossistema-aidd?

Caso fosse adotado, o único modelo admissível sob a **Lei #6 (Agnostic Supremacy - Zero Vendor Lock-in)** seria o **Laya** (código aberto, Apache 2.0, executável local via ONNX ou PyTorch sem dependência de nuvem de terceiros). O **Jev** seria vetado por ser SaaS proprietário.

### Cenário Concreto de Uso: Router Semântico no Pré-Intake
No `tools/aidd-planner` ou no ponto de entrada interativo do CLI:
1. O usuário digita uma intenção livre em linguagem natural sem usar slash commands (ex: *"preciso subir meu protótipo do lovable mas tirando o banco deles"*).
2. O Laya roda localmente em CPU/ONNX em ~30ms avaliando a pergunta do tipo `Choice`:
   - Categorias: `["fluxo_pure", "fluxo_open", "fluxo_freedom", "outro"]`
   - O Laya retorna `fluxo_freedom` com probabilidade calibrada de `0.94`.
3. Se probabilidade > 0.85, o sistema sugere/encaminha automaticamente para o `aidd-freedom`.
4. Se probabilidade < 0.85, o sistema aciona o `aidd-grill` para desambiguação socrática.

---

## 5. Se não utilizáveis, qual o motivo e explicação da não conformidade?

A incompatibilidade com o núcleo do ecossistema decorre diretamente das **Leis Invioláveis do AIDD**:

### A. Violação da Lei #1: Determinismo First
> *"Use deterministic scripts, AST, regex, or JSON Schema. Never use LLM for mechanical tasks."*
- Decisões estruturais e validações no ecossistema são resolvidas por analisadores sintáticos determinísticos (AST, regex compilado, JSON Schema formal e CLI parsers tipados).
- Substituir regras determinísticas por inferência probabilística (mesmo calibrada como no Laya) insere estocasticidade desnecessária onde código puro Python (exit 0 / exit 1) é instantâneo e 100% reproduzível.

### B. Incompatibilidade com os Quality Gates (Lei #2 e Lei #13)
- Quality Gates exigem garantia matemática binária e determinística (`G_*.py`). Um modelo de classificação probabilístico não pode atuar como portão de qualidade, pois não garante determinismo absoluto em bordas sutis.

### C. Natureza Não-Generativa
- O ecossistema gera arquiteturas, testes, contratos de OpenAPI, stubs VSA, compose files e documentação viva. Como Jev e Laya têm output limitado a rótulos discretos e probabilidades, eles não produzem software.

### D. Risco de Lock-in (especificamente sobre o Jev)
- O Jev viola frontalmente a **Lei #6 (Agnostic Supremacy)**: amarra o desenvolvedor a uma API externa proprietária (TypeSafe AI) para decisões que podem ser feitas via código puro ou via modelos abertos locais.

---

## 6. Conclusão Executiva

O surgimento de modelos como Jev e Laya reflete a maturidade do mercado ao reconhecer que **usar LLMs generativos de grande porte para classificação e roteamento binário é um desperdício crasso de computação e dinheiro**.

No entanto, no **Ecossistema AIDD**, o papel que esses modelos exercem em startups comuns já é resolvido de forma superior pelo **Determinismo da Lei #1**: regex rigorosos, esquemas JSON, AST e scripts determinísticos. Apenas o **Laya**, em modo offline/ONNX, possui valor pragmático como classificador semântico auxiliar para triagem de linguagem natural informal antes do intake, sem nunca interferir no motor de engenharia, nos testes ou nos Quality Gates.
