# Fases de Execução: A Fábrica Autônoma do aidd-generator (Nota 10.0+)

> **Versão do Framework:** 2.1 (Pós-Elevação para Nota 10.0+ / Homologado)  
> **Para quem é este documento:** Engenheiros de software, arquitetos agênticos, líderes técnicos e pessoas de produto que desejam entender em detalhes o funcionamento da linha de montagem autônoma de software.

---

## 1. Visão Geral da Linha de Montagem

O **`aidd-generator`** opera como uma fábrica autônoma e determinística de software sob a metodologia AIDD (*AI-Driven Development*). A partir de uma única entrada em linguagem natural (ex: *"Crie um sistema de clínica com agendamento de consultas e prontuário eletrônico"*), o orquestrador dispara uma esteira de 8 fases especializadas com **Descarte Imediato de Contexto (Context-Purge Engine)** e **Carregamento Dinâmico de Módulos**.

```
                           ENTRADA DO USUÁRIO
                (/generate, linguagem natural ou painel web)
                                    │
                                    ▼
                         PRÉ-VOO & FLEET DISCOVERY
                (Detecção silenciosa de ferramentas e modelos)
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    │                                                               │
    ▼                                                               ▼
FASE 1: Pesquisador ──► FASE 2: Analisador ──► FASE 3: Designer ──► FASE 4: Planejador
 (Dossiê Estruturado)     (Entidades & Regras)   (Contratos & Schemas)   (Configurações & Tech)
                                                                            │
    ┌───────────────────────────────────────────────────────────────────────┘
    │
    ▼
FASE 5: Criador ──────► FASE 8: Implementador ──► FASE 6: Documentador ──► FASE 7: Auto-crítica
(Estrutura & Schemas)    (Código AST + Auto-Cura)    (Documentação Viva)     (Auditoria & Gates)
                                                                            │
                                                                            ▼
                                                                     GATES MECÂNICOS
                                                               (I3 Cross-Script + OWASP)
```

---

## 2. Passo a Passo Técnico das Fases

### Estação 0 — Auto-Descoberta de Frota & Pré-Voo (`Fleet Discovery`)
Antes de iniciar o pipeline, o sistema realiza inspeção sem gastar nenhum token de IA:
- **`detector.py`:** Detecta silenciosamente se o host possui `claude`, `codex`, `agy`, `cursor` ou `ollama`.
- **`orca_fleet.py`:** Gera dinamicamente `.orca/01_orca_inventory.json` e estabelece o fallback em cascata: se o usuário possui apenas 1 assistente de IA instalado, todas as fases operam nele com isolamento mecânico de worktrees sem emitir erro.
- **`preflight_llm.py`:** Valida a conectividade de IA antes do início da primeira fase, prevenindo falhas no meio do processo.

---

### Fase 1 — O Pesquisador (`01_pesquisador.py` / `phase_01_pesquisa/`)
- **Papel:** Analisa a ideia bruta do usuário e formula o escopo preliminar.
- **Mecânica:** 100% determinística em Python puro (Zero Token). Extrai termos técnicos, identifica domínio de negócio, regras de auditoria e atores do sistema.
- **Micro-ambiente:** `scripts/phases/phase_01_pesquisa/AGENTS.md` focado em isolamento e inspeção de sistema de arquivos (Filesystem MCP).

---

### Fase 2 — O Analisador de Domínio (`02_analisador.py` / `phase_02_analisador/`)
- **Papel:** Modelagem de domínio e levantamento de regras de negócio.
- **Cognição Isolada:** Instancia subagente efêmero com prompt limpo (< 1.000 tokens) sob a **Tríade Caveman Ultra** (Instrução em EN, CoT telegráfico em inglês caveman, Saída estrita em JSON/PT-BR).
- **Entregável:** `analise_phase2.json` mapeando entidades, atributos, invariantes e fluxos críticos.

---

### Fase 3 — O Designer de Contratos (`03_designer.py` / `phase_03_designer/`)
- **Papel:** Especificação formal de engenharia e contratos de dados.
- **Orquestração Especializada:** Divide o trabalho em subagentes efêmeros concorrentes:
  1. *Arquiteto de Camadas:* Estrutura modular e limites de contexto.
  2. *Engenheiro de Scripts:* Interfaces públicas e assinaturas.
  3. *Especialista em Dados:* Schemas JSON rígidos padrão Draft 2020-12.
  4. *Especialista em Tokens:* Otimização de contexto para execução econômica.
  5. *Especialista em Gates:* Definição dos critérios de aceitação mecânicos.
- **Entregável:** `design_aidd_phase3.json`.

---

### Fase 4 — O Planejador Técnico (`04_decisor.py` / `phase_04_planejador/`)
- **Papel:** Resolução de dependências, arquitetura de persistência e stack.
- **Operação:** Seleciona banco de dados (SQLite WAL de alta performance), bibliotecas, estrutura de testes e isolamento de módulos. Opera em modo automático ou interativo conforme preferência do usuário.
- **Entregável:** `config_global_local_phase4.json`.

---

### Fase 5 — O Criador de Estrutura (`05_criador.py` / `phase_05_criador/`)
- **Papel:** Materialização da fundação do projeto no disco físico.
- **Mecânica:** Python determinístico de alta velocidade (Zero Tokens). Cria a árvore completa de pastas, escreve os contratos JSON Schema, configurações de ambiente, linters e templates de teste.

---

### Fase 8 — O Implementador Funcional com Auto-Cura (`08_implementador.py` / `phase_08_implementador/`)
- **Papel:** Geração do código-fonte real e executável do sistema.
- **Decomposição em Micro-Tasks AST:** O código não é gerado como um bloco monolítico. A AST (*Abstract Syntax Tree*) decompõe cada script em funções individuais.
- **Result Monad Obrigatório:** Todas as funções de serviço utilizam `Result[T, E]`, garantindo tratamento robusto de erros e eliminação de exceções 500 não tratadas.
- **Auto-Cura Post-Mortem 5-Porquês:**
  1. O orquestrador executa o `pytest` localmente após a geração.
  2. Se houver falha, o `PostMortemAnalyzer` isola o traceback, diagnostica a causa raiz via método 5-Porquês e regenera cirurgicamente apenas a função defeituosa em sandbox isolada.
  3. A sessão do subagente é destruída imediatamente após a compilação AST válida.

---

### Fase 6 — O Documentador Vivo (`06_documentador.py` / `phase_06_documentador/`)
- **Papel:** Geração da documentação viva do projeto construído.
- **Mecânica:** Roda após a Fase 8, garantindo que a documentação reflita o código real implementado e testado, e não apenas o design teórico. Gera manuais de API, diagramas Mermaid e guias de uso.

---

### Fase 7 — A Auto-Crítica & Auditoria Final (`07_analisador.py` / `phase_07_auto_critica/`)
- **Papel:** Auditoria factual e cálculo do score final de qualidade (0 a 100).
- **Verificações:** Inspeciona integridade de arquivos, conformidade de contratos, ausência de stubs ou mocks em produção e conformidade arquitetural.

---

## 3. Gates Mecânicos de Homologação Final

Após o término das 8 fases, o runner `scripts/verificar_gates.py` dispara as validações de barreira final com veredito binário (`exit 0` = aprovado / `exit 1` = bloqueado):

1. **`G_BLOQUEAR_SEGREDOS`:** Bloqueia credenciais, chaves de API e tokens expostos.
2. **`G_INTEGRACAO_CROSS_SCRIPT` (Gate I3):** Validação estática de ponta a ponta que assegura que todos os módulos gerados conversam perfeitamente entre si, checando imports mútuos, compatibilidade de schemas e tipagem.
3. **`G_CYBERSECURITY_OWASP`:** Varredura estática profunda contra injeções SQL, bypass de autenticação, IDOR, deserialização insegura e configurações permissivas.
