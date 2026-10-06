# Estrutura do Manifesto `PLANO-EXECUCAO-ESTRUTURADO.json` — AIDD Master Pack

> **Tag/Versão documentada:** `v5.1.0`
> **Fonte primária:** Instâncias reais do arquivo `PLANO-EXECUCAO-ESTRUTURADO.json` presentes na própria tag, dentro de `examples/*/PLANO-EXECUCAO-ESTRUTURADO.json` (ex.: `examples/catalogo-digital-v3/`, `examples/catalogo-digital-whatsapp/`, `examples/plataforma-de-membros/`, `examples/plataforma-modular-assinaturas/`).
> **Escopo:** Descrição factual dos campos observados nesses manifestos reais, tal como gerados/consumidos pela CLI `scripts/aidd.py` (funções `cmd_plan`/`cmd_apply`) nesta tag.

---

## 1. O que é este arquivo

O `PLANO-EXECUCAO-ESTRUTURADO.json` é o **manifesto de estado do plano de execução** de um projeto gerado pelo AIDD. Ele é criado na Fase 1.5 do ciclo de vida (Spec Gate), antes de qualquer geração de código, e depois é atualizado conforme cada fase do plano avança — funcionando como um rastro auditável ("saga do próprio processo de geração") de tudo que foi planejado versus tudo que já foi concluído e validado por gates.

Cada projeto gerado pela v5.1.0 recebe seu próprio manifesto na raiz do projeto.

## 2. Estrutura de campos (schema observado)

```json
{
  "projeto": {
    "nome": "string",
    "descricao": "string",
    "arquitetura": "string",
    "zero_api_key_mode": true,
    "status": "string"
  },
  "fases": [
    {
      "id": "string",
      "nome": "string",
      "status": "string",
      "mesa_orca": "string",
      "expected_outputs": ["string", "..."],
      "gates_validados": ["string", "..."]
    }
  ]
}
```

### 2.1. Bloco `projeto`

| Campo | Tipo | Descrição | Exemplo observado |
| :--- | :--- | :--- | :--- |
| `nome` | string | Nome interno/slug do projeto gerado. | `"catalogo-digital-e"`, `"plataforma-de-cursos"` |
| `descricao` | string | Descrição de negócio em linguagem natural do que o projeto faz. | `"Catalogo Digital e Loja com Checkout WhatsApp e Painel Admin"` |
| `arquitetura` | string | Identificador do estilo arquitetural aplicado. | `"AIDD 4 Camadas"` (constante observada em todos os manifestos analisados) |
| `zero_api_key_mode` | boolean | Indica se o projeto foi composto em modo "zero API key" (sem dependência de chaves de serviços pagos externos como pré-requisito de funcionamento). | `true` em todos os exemplos analisados |
| `status` | string | Estado geral do projeto no ciclo do plano. | Valores observados: `"INICIALIZADO"` (plano criado, nada executado ainda) e `"CONCLUIDO_COM_SUCESSO"` (todas as fases concluídas e validadas) |

### 2.2. Bloco `fases` (array)

Cada projeto observado possui exatamente 3 fases padrão, correspondentes às etapas mecânicas do ciclo de vida (ver `ciclo-de-vida.md`):

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | string | Identificador estável da fase. Valores observados: `"fase-01-analise"`, `"fase-02-implementacao"`, `"fase-03-validacao"`. |
| `nome` | string | Nome legível da fase. |
| `status` | string | Estado da fase individual. Valores observados: `"PENDENTE"` (ainda não executada) e `"CONCLUIDO"` (executada e validada). |
| `mesa_orca` | string | Identificador da "mesa" de trabalho/agente responsável por essa fase dentro do fluxo de orquestração. Valores observados: `"mesa-analise"`, `"mesa-dev"`, `"mesa-qa"`. |
| `expected_outputs` | array de string | Lista de caminhos/artefatos que a fase deve produzir para ser considerada concluída. |
| `gates_validados` | array de string | Presente apenas quando a fase já foi concluída — lista os Quality Gates que aprovaram aquela fase (ex.: `"G_SEGREDOS"`, `"G_QUALIDADE"`, `"G_HARNESS_COMPAT"`). Em fases ainda `"PENDENTE"`, este campo pode estar ausente. |

### 2.3. As 3 fases padrão e seus outputs esperados

| Fase | `id` | `mesa_orca` | `expected_outputs` |
| :--- | :--- | :--- | :--- |
| Análise e Modelagem de Contratos | `fase-01-analise` | `mesa-analise` | `docs/ARQUITETURA.md` |
| Implementação do Core Determinístico | `fase-02-implementacao` | `mesa-dev` | `src/main.py` |
| Auditoria de Gates e Testes Finais | `fase-03-validacao` | `mesa-qa` | `tests/` |

## 3. Exemplo real completo (estado inicial — plano recém-criado)

Extraído de `examples/catalogo-digital-v3/PLANO-EXECUCAO-ESTRUTURADO.json` na tag `v5.1.0`:

```json
{
  "projeto": {
    "nome": "catalogo-digital-e",
    "descricao": "Catalogo Digital e Loja com Checkout WhatsApp e Painel Admin",
    "arquitetura": "AIDD 4 Camadas",
    "zero_api_key_mode": true,
    "status": "INICIALIZADO"
  },
  "fases": [
    {
      "id": "fase-01-analise",
      "nome": "Analise e Modelagem de Contratos",
      "status": "PENDENTE",
      "mesa_orca": "mesa-analise",
      "expected_outputs": ["docs/ARQUITETURA.md"]
    },
    {
      "id": "fase-02-implementacao",
      "nome": "Implementacao do Core Determinístico",
      "status": "PENDENTE",
      "mesa_orca": "mesa-dev",
      "expected_outputs": ["src/main.py"]
    },
    {
      "id": "fase-03-validacao",
      "nome": "Auditoria de Gates e Testes Finais",
      "status": "PENDENTE",
      "mesa_orca": "mesa-qa",
      "expected_outputs": ["tests/"]
    }
  ]
}
```

## 4. Exemplo real completo (estado final — plano concluído com sucesso)

Extraído de `examples/plataforma-de-membros/PLANO-EXECUCAO-ESTRUTURADO.json` na tag `v5.1.0`, mostrando o campo `gates_validados` preenchido em cada fase concluída:

```json
{
  "projeto": {
    "nome": "plataforma-de-cursos",
    "descricao": "Plataforma de Cursos e Area de Membros com Checkout",
    "arquitetura": "AIDD 4 Camadas",
    "zero_api_key_mode": true,
    "status": "CONCLUIDO_COM_SUCESSO"
  },
  "fases": [
    {
      "id": "fase-01-analise",
      "nome": "Analise e Modelagem de Contratos",
      "status": "CONCLUIDO",
      "mesa_orca": "mesa-analise",
      "expected_outputs": ["docs/ARQUITETURA.md"],
      "gates_validados": ["G_SEGREDOS", "G_QUALIDADE", "G_HARNESS_COMPAT"]
    },
    {
      "id": "fase-02-implementacao",
      "nome": "Implementacao do Core Determinístico",
      "status": "CONCLUIDO",
      "mesa_orca": "mesa-dev",
      "expected_outputs": ["src/main.py"],
      "gates_validados": ["G_SEGREDOS", "G_QUALIDADE", "G_HARNESS_COMPAT"]
    },
    {
      "id": "fase-03-validacao",
      "nome": "Auditoria de Gates e Testes Finais",
      "status": "CONCLUIDO",
      "mesa_orca": "mesa-qa",
      "expected_outputs": ["tests/"],
      "gates_validados": ["G_SEGREDOS", "G_QUALIDADE", "G_HARNESS_COMPAT"]
    }
  ]
}
```

## 5. Como o manifesto se conecta à CLI

- `python scripts/aidd.py plan "<prompt>"` — cria o manifesto inicial (`status: "INICIALIZADO"`, todas as fases `"PENDENTE"`), junto com `SPEC-ARQUITETURA.md`.
- `python scripts/aidd.py apply --dir <pasta>` — lê o manifesto, executa cada fase pendente na ordem, dispara os gates correspondentes e atualiza `status` de cada fase para `"CONCLUIDO"` (populando `gates_validados`), até que o `status` do bloco `projeto` avance para `"CONCLUIDO_COM_SUCESSO"`.
- `python scripts/aidd.py status` — inspeciona o manifesto e reporta a integridade/progresso atual do projeto sem re-executar nada.

Este manifesto é, portanto, a fonte única de verdade sobre "o que já foi feito e validado" em um projeto composto pela v5.1.0, permitindo retomar ou auditar o processo de geração a qualquer momento.
