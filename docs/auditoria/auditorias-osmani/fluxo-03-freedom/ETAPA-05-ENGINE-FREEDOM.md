# Relatório de Auditoria de Micropipeline — ETAPA 05: ENGINE (AIDD-FREEDOM)

> **Fluxo:** 03 (AIDD-FREEDOM)  
> **Micropipeline Auditado:** `aidd-freedom` (`ecossistema.py freedom-motor scan|migrate`)  
> **Localização na Máquina:** `modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom/`  
> **Data:** 2026-10-21  
> **Status da Etapa:** **AUDITADA — 2 BUGS CORRIGIDOS / MITIGADOS NA MÁQUINA**  

---

## 1. Escopo e Propósito do Motor Freedom

O `aidd-freedom` é a ferramenta de soberania tecnológica responsável por erradicar o vendor lock-in de plataformas Low-Code (Lovable, Supabase Cloud, v0, Bolt, Firebase). Suas responsabilidades são:
1. Varrer a pasta de export/origem identificando dependências proprietárias (`LovableScanner`).
2. Extrair esquemas de banco de dados (`supabase/migrations/`) e sintetizar o DDL soberano em PostgreSQL (`init-db.sql`).
3. Emular papéis e RLS (Row Level Security) nativamente via PostgREST local e SQLite WAL.
4. Substituir chamadas ao SDK Supabase por chamadas REST locais limpas com tipagem TypeScript.

---

## 2. Inconsistências Fatuais Detectadas e Analisadas

### [ERRO #004] Bloqueio do Scanner por Ausência da Pasta `origem`
- **Sintoma:** O scanner abortou com:
  ```
  [ERRO] package.json nao encontrado em: ...\app\origem
  ```
- **Causa Raiz na Máquina:** `LovableScanner.__init__()` exige estritamente um `package.json` na pasta de origem. Quando o fluxo é acionado a partir de uma spec do zero (sem export prévio de Lovable), a máquina deve oferecer modo "Soberania do Zero" ou avisar preventivamente a exigência da pasta de export.
- **Impacto:** O fluxo 03 travou na Etapa 5 exigindo estruturação manual da pasta `origem`.

### [ERRO #005] Coletor de Testes do Pytest Rejeita Colchetes em Caminhos Absolutos
- **Sintoma:** Ao validar a fatia gerada via `_rodar_testes_fatia()`, o pytest abortou com:
  ```
  ERROR: path cannot contain [] parametrization: ...\[TESTE]ecossistema-aidd\...
  RC: 4
  ```
- **Causa Raiz na Máquina:** `modulos/02-triade-motores/fluxo-03-freedom/core/aidd-freedom/aidd_freedom/cli.py` passava o caminho absoluto da fatia diretamente no comando do `pytest`. O pytest interpreta colchetes no caminho como parâmetros de teste de fixture (`test[param]`).
- **Resolução / Ticket:** `TCK-ENG-01` — Uso mandatória de caminho relativo (`os.path.relpath(fatia_dir, projeto)`) e injeção de `-o testpaths=<rel_fatia>`.

---

## 3. Avaliação de Desacoplamento Factual (Lei #6)

* **Supabase Erradicado:** 0 ocorrências de `@supabase/supabase-js` em `src/` e `frontend/`.
* **Banco Local Ativo:** `suite.db` operacional em modo WAL com 14 testes passando e DDL em `init-db.sql` configurado para PostgreSQL 16.

---

## 4. Veredito

* **Classificação:** **APROVADO APÓS CORREÇÃO (Soberania alcançada com persistência local).**
