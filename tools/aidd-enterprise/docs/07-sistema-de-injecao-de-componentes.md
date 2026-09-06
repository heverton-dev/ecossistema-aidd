# 07 — Sistema de Injeção Automática de Componentes

> **Projeto:** AIDD Master Enterprise
> **Status:** IMPLEMENTADO
> **Data:** 03/09/2026 (reescrito em 06/09/2026)

---

## 1. Objetivo

Sistema determinístico para **criar, sincronizar e remover componentes** (skills, MCPs, rules, specs, configs, hooks e agents) em todos os harnesses do ecossistema a partir de um único comando CLI — sem uso de LLM.

O Injetor Universal detecta a camada arquitetural alvo, materializa os arquivos físicos em todos os diretórios de harness, integra os pontos de referência globais (catálogo `CAPABILITIES.json`, âncoras em `AGENTS.md` e templates multi-harness) e, para o tipo `hook`, grava também a cópia canônica em `componentes/` no monorepo.

---

## 2. Tipos de Componente Suportados

O comando `inject` aceita **7 tipos** (confirmado via `python scripts/aidd.py inject --help`):

| Tipo | Exemplo de uso | Camada arquitetural |
| :--- | :--- | :--- |
| **skill** | Skill de análise de cibersegurança | `harness_multiplataforma` |
| **mcp** | Servidor MCP com ferramentas externas | `kernel_core` |
| **rule** | Regra Zero Trust | `governanca_regras` |
| **spec** | Especificação de novo domínio | `documentacao_oficial` |
| **config** | Configuração multi-arquivo de harness | `templates_scaffold` |
| **hook** | Hook de ciclo de vida (JSON/shell) | `harness_multiplataforma` |
| **agent** | Agente Security Analyst | `interface_orquestracao` |

Todos os 7 tipos seguem o mesmo pipeline de 4 etapas:

1. **Detecção** → identificar o tipo do componente e a camada alvo
2. **Materialização** → criar os arquivos nos diretórios corretos (com rollback automático)
3. **Sincronização** → atualizar `CAPABILITIES.json` e âncoras multi-harness
4. **Canônica** → para `hook`, gravar cópia em `componentes/<projeto>/hooks/` no monorepo

---

## 3. Flags do Comando `inject`

Confirmado via `python scripts/aidd.py inject --help`:

```
python scripts/aidd.py inject <tipo> <nome> [opções]

Posicionais:
  {skill,mcp,rule,spec,config,hook,agent}   Tipo do componente
  nome                                        Nome/slug (kebab-case)

Opções:
  --descricao, -d DESCRICAO     Descrição do componente
  --content-file CONTENT_FILE   Arquivo com o conteúdo completo
  --mcp-command MCP_COMMAND     [mcp] Comando executável do servidor MCP
  --mcp-args MCP_ARGS           [mcp] Argumentos separados por vírgula
  --mcp-env MCP_ENV             [mcp] Variáveis de ambiente (CHAVE=valor,...)
  --files-json FILES_JSON       [config] JSON {caminho: conteudo}
  --dry-run                     Simula sem escrever no filesystem
  --remover                     Remove um componente previamente injetado
  --dir DIR                     Diretório do projeto
```

### Exemplos

```bash
# Skill
python scripts/aidd.py inject skill ciberseguranca -d "Análise de vulnerabilidades"

# MCP externo
python scripts/aidd.py inject mcp audit-orchestrator --mcp-command python --mcp-args "server.py" -d "Orquestrador de auditoria"

# Rule
python scripts/aidd.py inject rule zero-trust -d "Regra de segurança zero trust"

# Hook
python scripts/aidd.py inject hook deploy-pre -d "Hook pré-deploy"

# Config multi-arquivo
python scripts/aidd.py inject config tsconfig --files-json configs/tsconfig.json

# Dry-run (simulação)
python scripts/aidd.py inject skill teste -d "Teste" --dry-run

# Remoção
python scripts/aidd.py inject skill ciberseguranca --remover
```

---

## 4. Arquitetura Compartilhada com aidd-master

O Injetor Universal é composto por 4 módulos em `src/core/`, compartilhados entre `aidd-master` e `aidd-enterprise`:

### 4.1 `profiles_registry.py` — Contrato e Matriz de Perfis

- Valida payloads contra `schema_injector_request.json` (JSON Schema Draft 2020-12).
- Mantém a **matriz de perfis** `PROFILES`: para cada `(projeto_alvo, tipo)`, define o `dest` (destino principal), `mirrors` (espelhos multi-harness), `anchors` (âncoras de governança), `registry` e `camada_alvo`.
- **Não escreve nada em disco** — apenas resolve caminhos absolutos de destino via `resolver_destinos()`.
- Tipos válidos: `("skill", "mcp", "rule", "spec", "config", "agent", "hook")` (constante `TIPOS_VALIDOS`).

### 4.2 `detector_camada.py` — Detector Híbrido de Camada

- Converte pedidos em linguagem natural PT-BR (ex: *"crie uma skill de cibersegurança"*) em `InjectorRequest` completo.
- **Heurística determinística por palavra-chave** (`_PALAVRAS_CHAVE`): para cada tipo, uma tupla de termos PT-BR/EN.
- Se a heurística identifica exatamente 1 candidato, retorna o tipo; caso contrário, retorna `Result.fail` com código `TIPO_AMBIGUO` — **nunca usa LLM para adivinhar**.
- Extrai `nome` (slug kebab-case) e `descricao` a partir do texto livre.

### 4.3 `materializador.py` — Motor de Materialização Transacional

- Escreve o artefato principal + espelhos multi-harness em buffer atômico.
- **Rollback automático**: se qualquer escrita falhar, o estado prévio exato de cada destino é restaurado via `_executar_rollback()` (snapshot completo de bytes antes da escrita).
- Rotas especiais:
  - **config** com `--files-json`: mapa arbitrário `{caminho: conteudo}` com validação de path traversal.
  - **mcp** com `--mcp-command`: registra no `mcp.json` do projeto alvo.
- Função `remover_componente()`: remove arquivos registrados em `CAPABILITIES.json`, limpa diretórios vazios e atualiza o catálogo.

### 4.4 `sincronizador_harness.py` — Sincronizador Multi-Harness

- Pós-materialização, executa integração global:
  1. **Registry**: atualiza `CAPABILITIES.json` com hash SHA-256 de cada arquivo criado.
  2. **Âncoras**: para `rule`, insere/upserta tabela de componentes em `AGENTS.md` + templates multi-harness (entre marcadores idempotentes `AIDD_INJECTOR`).
  3. **Intent Router**: para `agent`, registra novo padrão de intenção PT-BR em `src/core/intent_router.py`.
- `verificar_sincronizacao()`: verifica integridade comparando hashes SHA-256 registrados com o conteúdo real em disco.

---

## 5. Capacidades Entregues pela Unificação

As 5 capacidades confirmadas na implementação real:

### 5.1 Detecção de Drift via SHA-256

O `sincronizador_harness.py` calcula o hash SHA-256 de cada arquivo materializado e o registra em `CAPABILITIES.json` (campo `arquivos_hashes`). A função `verificar_sincronizacao()` compara esses hashes com o conteúdo real em disco, reportando divergências.

### 5.2 Remoção de Componentes (`--remover`)

O flag `--remover` aciona `remover_componente()` em `materializador.py`, que:
- Localiza o componente em `CAPABILITIES.json`
- Remove todos os arquivos listados em `arquivos_hashes` + o destino canônico (para `hook`)
- Limpa diretórios vazios subindo até o `root_dir`
- Atualiza o catálogo removendo a entrada

### 5.3 Rollback com Snapshot Completo

Antes de escrever qualquer arquivo, o materializador salva o conteúdo binário prévio de cada destino (snapshot). Se a escrita falhar no meio da operação, `_executar_rollback()` restaura cada arquivo ao estado exato anterior e remove diretórios vazios criados pela operação.

### 5.4 Modo Dry-Run (`--dry-run`)

O flag `--dry-run` percorre todo o pipeline (resolução de destinos, validação) mas retorna os caminhos que seriam escritos **sem alterar o filesystem**. Útil para validação prévia de injeções complexas.

### 5.5 Configuração Multi-Arquivo (`--files-json`)

O flag `--files-json` aceita o caminho de um JSON com mapa `{caminho_relativo: conteudo}`. Cada caminho é validado contra path traversal antes da materialização. Permite configurar múltiplos arquivos em uma única operação de injeção.

---

## 6. Pipeline de Execução (Fluxo Interno)

O fluxo real executado por `cmd_inject()` → `run_inject()`:

```
cmd_inject(args)
  ├── Se --remover: materializador.remover_componente() → sair
  └── Senão:
       1. Monta payload {tipo, nome, descricao, alvo_projeto, ...}
       2. profiles_registry.resolver_destinos() → calcula caminhos absolutos
       3. materializador.materializar() → escreve arquivos (rollback se falhar)
       4. sincronizador_harness.sincronizar() → atualiza registry + âncoras
```

Para injeção por linguagem natural PT-BR, o `IntentRouter` (`intent_router.py`) também pode acionar `run_inject()` diretamente via `_tentar_injecao_por_linguagem_natural()`.

---

## 7. Critérios de Aceite

A entrega é validada quando:

1. **Detecção correta**: `profiles_registry.resolver_destinos()` resolve os caminhos de todos os 7 tipos.
2. **Materialização completa**: `materializador.materializar()` cria todos os arquivos (principal + espelhos).
3. **Rollback funcional**: falha de escrita I/O reverte o estado com `_executar_rollback()`.
4. **Sincronização multi-harness**: `sincronizador_harness.sincronizar()` atualiza `CAPABILITIES.json` e âncoras.
5. **Remoção limpa**: `--remover` remove arquivos + catálogo + diretórios vazios.
6. **Dry-run seguro**: `--dry-run` não altera o filesystem.
7. **Gate `G_INJECT`**: validação determinística retorna exit 0 (em `scripts/gates/G_INJECT.py`).
