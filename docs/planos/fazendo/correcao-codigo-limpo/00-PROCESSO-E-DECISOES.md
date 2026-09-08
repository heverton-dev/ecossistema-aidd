# PROCESSO E DECISOES — correcao-codigo-limpo

> **Origem:** Planejamento estruturado no monorepo ecossistema-aidd.
> **Proposito deste arquivo:** Registro unico do processo e governanca desta iniciativa.
> **Aviso de Governanca:** Todos os itens comecam como rascunhos. Nenhuma aprovacao ou decisao pode ser fabricada.

---

## 1. O que este esforco busca

- **Origem:** análise de qualidade de código (Clean Code) pedida pelo usuário em 2026-09-08, feita em duas rodadas via `.code-review-graph/graph.db` (contagem de definições por arquivo, tamanho de função e de classe, hash de arquivo) e varredura direta (`grep`/Python) por `except` genérico/sem tipo, linhas longas e proporção de comentário, cobrindo as 5 ferramentas de `tools/aidd-*` individualmente (não só o par aidd-enterprise/aidd-master). Esta iniciativa é **distinta** de `docs/planos/fazendo/correcao-arquitetura-limpa/` — aquela trata de relação/duplicação **entre** ferramentas e cópias (arquitetura); esta trata da qualidade de escrita **dentro** de cada arquivo/função/classe, em cada ferramenta, independente de haver ou não duplicação entre elas.
- **Objetivo Principal:** corrigir 8 achados concretos de qualidade de código, cobrindo as 5 ferramentas: uso excessivo de captura de erro genérica ou sem tipo (achado novo e o maior em volume: ~197 ocorrências de `except Exception` em aidd-enterprise/aidd-master, 65 em aidd-generator, 19 em aidd-ops, 7 em aidd-forge; 15 `except:` sem tipo em aidd-enterprise/aidd-master, 7 em aidd-generator, 0 em aidd-forge/aidd-ops), métodos/classes grandes demais (achado novo: 3 classes do aidd-generator com 894/718/659 linhas, com métodos internos de até 198 linhas), a função `run_all_checks` de 8 responsabilidades, um import duplicado, um comentário usado como divisor de seção, nomenclatura PT-BR/inglês sem convenção combinada, e um registro final consolidado — não é uma reescrita nem uma reestruturação de pastas, não mexe em duplicação entre ferramentas (isso é escopo da iniciativa `correcao-arquitetura-limpa`).
- **Limites de Escopo:** não inclui decisões não aprovadas por humano; não inclui unificar/consolidar código entre `tools/aidd-*` (acoplamento de runtime é proibido — regra fixa da iniciativa de arquitetura); não inclui reescrever nenhuma ferramenta do zero; não inclui trocar formatador/linter automático de todo o monorepo (fora de escopo, seria uma decisão de tooling separada).

## 2. Processo Adotado

Diagnostico rapido → Definicao de Pronto checavel → Prompt de Execucao autocontido (PT-BR + EN-US) → Auditoria por reproducao real → Registro do veredito.

## 3. Onde vive o conteudo tecnico

| # | Item | Documento |
|---|---|---|
| 1 | Trocar except Exception generico por excecoes especificas nas 5 ferramentas | `01-trocar-except-exception-generico-por-excecoes-especificas-nas-5-ferramentas.md` |
| 2 | Eliminar except sem tipo (bare except) em aidd-enterprise, aidd-master e aidd-generator | `02-eliminar-except-sem-tipo-bare-except-em-aidd-enterprise-aidd-master-e-aidd-generator.md` |
| 3 | Dividir metodos com mais de 100 linhas nas classes grandes do aidd-generator e aidd-ops | `03-dividir-metodos-com-mais-de-100-linhas-nas-classes-grandes-do-aidd-generator-e-aidd-ops.md` |
| 4 | Dividir run_all_checks (G_SEGURANCA.py) em funcoes menores por camada de responsabilidade | `04-dividir-run-all-checks-g-segurancapy-em-funcoes-menores-por-camada-de-responsabilidade.md` |
| 5 | Remover import duplicado (import subprocess repetido) em G_SEGURANCA.py | `05-remover-import-duplicado-import-subprocess-repetido-em-g-segurancapy.md` |
| 6 | Substituir comentarios-divisorios de secao por decomposicao real em funcao onde o mesmo padrao se repete | `06-substituir-comentarios-divisorios-de-secao-por-decomposicao-real-em-funcao-onde-o-mesmo-padrao-se-repete.md` |
| 7 | Definir e documentar convencao unica de nomenclatura PT-BR e ingles entre as ferramentas | `07-definir-e-documentar-convencao-unica-de-nomenclatura-pt-br-e-ingles-entre-as-ferramentas.md` |
| 8 | Registrar ranking de limpeza por ferramenta atualizado com todas as metricas (sem acao corretiva) | `08-registrar-ranking-de-limpeza-por-ferramenta-atualizado-com-todas-as-metricas-sem-acao-corretiva.md` |

## 4. Regras Fixas

1. **A skill/agente nunca decide ou aprova sozinho.** Rascunhos aguardam aprovacao explicita de pessoa real.
2. **Sem disparos autonomos:** Prompts de execucao nao devem ser enviados a subagentes sem consentimento.
3. **Sem commit/push automatico:** Commits dependem de aprovacao do usuario.
4. **Isolamento:** Testes devem ocorrer sem poluir arquivos de producao.

## 5. Registro de Progresso

| # | Item | Status | Documento |
|---|---|---|---|
| 1 | Trocar except Exception generico por excecoes especificas nas 5 ferramentas | ⏳ Aprovado, aguardando execucao (item grande, execucao em fatias) | `01-trocar-except-exception-generico-por-excecoes-especificas-nas-5-ferramentas.md` |
| 2 | Eliminar except sem tipo (bare except) em aidd-enterprise, aidd-master e aidd-generator | ✅ Concluido (auditado por reproducao real em 2026-09-08) | `02-eliminar-except-sem-tipo-bare-except-em-aidd-enterprise-aidd-master-e-aidd-generator.md` |
| 3 | Dividir metodos com mais de 100 linhas nas classes grandes do aidd-generator e aidd-ops | ⏳ Aprovado, aguardando execucao | `03-dividir-metodos-com-mais-de-100-linhas-nas-classes-grandes-do-aidd-generator-e-aidd-ops.md` |
| 4 | Dividir run_all_checks (G_SEGURANCA.py) em funcoes menores por camada de responsabilidade | ✅ Concluido (auditado por reproducao real em 2026-09-08 — saida e exit code identicos antes/depois, nas 4 copias) | `04-dividir-run-all-checks-g-segurancapy-em-funcoes-menores-por-camada-de-responsabilidade.md` |
| 5 | Remover import duplicado (import subprocess repetido) em G_SEGURANCA.py | ✅ Concluido (auditado por reproducao real em 2026-09-08) | `05-remover-import-duplicado-import-subprocess-repetido-em-g-segurancapy.md` |
| 6 | Substituir comentarios-divisorios de secao por decomposicao real em funcao onde o mesmo padrao se repete | ✅ Concluido (censo real confirma zero ocorrencias remanescentes, 2026-09-08) | `06-substituir-comentarios-divisorios-de-secao-por-decomposicao-real-em-funcao-onde-o-mesmo-padrao-se-repete.md` |
| 7 | Definir e documentar convencao unica de nomenclatura PT-BR e ingles entre as ferramentas | ✅ Aprovado pelo usuario em 2026-09-08 — aguardando decisao especifica (qual convencao) antes de documentar | `07-definir-e-documentar-convencao-unica-de-nomenclatura-pt-br-e-ingles-entre-as-ferramentas.md` |
| 8 | Registrar ranking de limpeza por ferramenta atualizado com todas as metricas (sem acao corretiva) | ✅ Aprovado pelo usuario em 2026-09-08 — aguardando implementacao | `08-registrar-ranking-de-limpeza-por-ferramenta-atualizado-com-todas-as-metricas-sem-acao-corretiva.md` |

Esta tabela so e atualizada para Concluido apos auditoria por reproducao real. "Aprovado" (2026-09-08) significa autorizacao para iniciar implementacao — nao significa que a implementacao ja foi feita ou auditada.
