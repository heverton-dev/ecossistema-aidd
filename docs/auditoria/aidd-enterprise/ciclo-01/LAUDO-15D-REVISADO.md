# Laudo de Auditoria Arquitetural (Lens 15-D) — aidd-enterprise

> **Ciclo:** 01 | **Fase:** 4 (Inspetor / Retorno) | **Alvo:** `.agents/skills/aidd-enterprise/`
> **Base de evidência:** leitura integral dos 8 arquivos-fonte + execução empírica de sondas (injeção, adulteração de hash, gate, pipeline, rollback, telemetria) + execução da suíte de testes.
> **Veredito global:** **REPROVADO** — a camada 15-D é ortogonal ao comportamento real da ferramenta.

---

## 1. Identificação da Ferramenta

- **Nome da Ferramenta:** `aidd-enterprise`
- **Descrição Breve:** injeção transacional de componentes mission-critical (skill, rule, mcp, spec, config, hook, agent) com validação estrita por JSON Schema, integridade SHA-256 e reversão automática.
- **Comando de Gatilho:** `python ecossistema.py enterprise inject <tipo> <nome>` (slash: `/enterprise <tipo> <nome>`).

### 1.1 Inventário do alvo auditado

| Arquivo | Linhas | Papel declarado |
|---|---|---|
| `SKILL.md` | 22 | Contrato de descoberta do harness |
| `scripts/cli.py` | 223 | Entrypoint (D4) |
| `scripts/injetor.py` | 214 | Motor de injeção + SHA-256 (D8) |
| `scripts/orquestrador.py` | 241 | Pipeline de 5 estágios (D10) |
| `scripts/rollback.py` | 283 | Transação e reversão (D14) |
| `scripts/fallback.py` | 200 | Retry e backoff (D11) |
| `scripts/observabilidade.py` | 196 | Telemetria (D12) |
| `scripts/isolamento.py` | 101 | Guard de escrita (D3) |

Total: **1.480 linhas**. Dependências externas: `jsonschema` (opcional, degrada para exit 1).

### 1.2 Achado transversal que contamina toda a matriz (ACHADO-00)

Varredura de todos os consumidores dos módulos locais em todo o repositório:

```
grep -rn "aidd-enterprise/scripts/(injetor|orquestrador|rollback|fallback|observabilidade|isolamento)"
```

**Resultado: nenhuma chamada de produção.** As únicas ocorrências são (a) cópias espelhadas do mesmo `cli.py` distribuídas nos harnesses e (b) as strings de `COMPONENTES_PADRAO` (`cli.py:29-38`), usadas **exclusivamente para calcular SHA-256 de arquivo** no handoff — nunca como `import` ou invocação. Os únicos carregadores reais são os testes, via `importlib.util.spec_from_file_location` (`tests/test_enterprise_rollback.py:27`).

O entrypoint documentado executa outra máquina entirely:

```
python ecossistema.py enterprise inject skill X
  └─> ecossistema.py:217 cmd_enterprise()
        └─> tools/aidd-enterprise/scripts/aidd.py   (pacote Click, 19 subcomandos)
              └─> application/commands/inject.py     (injetor do pacote tools)
```

Consequência: **`injetor.py`, `orquestrador.py`, `rollback.py`, `fallback.py`, `observabilidade.py` e `isolamento.py` somam 1.235 linhas (83% do alvo) que nenhum usuário jamais executa.** Elas existem para satisfazer o checklist do DoD e são exercitadas apenas pelos testes escritos para elas. Isso viola a Lei #5 (Zero Stubs) e contamina D3, D10, D11, D12 e D15.

---

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem

#### D1. Contratos e Regras

**Status: IMPLEMENTADO (com ressalvas).**

- **SKILL.md** declara frontmatter canônico `name` + `description` no formato "Use when" e fixa o critério de término (`Done when: exit 0 with no hash divergence`, `SKILL.md:22`).
- **Contrato de dados primário:** `tools/aidd-enterprise/scripts/injector/schema/component_manifest.schema.json` — JSON Schema Draft 2020-12, com `required: [type, name]`, `enum` fechado de 7 tipos, `name` com pattern `^[a-z][a-z0-9-]*$`, `mcp.additionalProperties: false` e 7 blocos `allOf` `if/then` que Tornam a carga útil obrigatória por tipo.
- **Contrato de interface:** `argparse` com `choices=TIPOS_COMPONENTES` (`cli.py:26,91`) — a duplicação da enum entre código e schema é o único ponto de divergência possível; hoje coincidem.
- **Diretivas de domínio:** `tools/aidd-enterprise/AGENTS.md` (§2 Invariantes Enterprise) e as 13 Leis do `AGENTS.md` raiz.

**Ressalvas:**
- O schema canônico vive **fora** do diretório da skill (`tools/`), enquanto a skill é o componente distribuído. Um harness que instale apenas a skill fica sem contrato.
- `cli.py:7-8` e `AGENTS.md` do pacote **prometem "nunca exit 2"**, mas a delegação herda o `sys.exit` do pacote Click (`cli.py:80`), que emite exit 2 em erro deparsing. Promessa não honrada.

#### D2. Input e Gatilhos

**Status: IMPLEMENTADO (documentação parcial).**

- **Gatilho primário:** `inject <tipo> <nome>` + flags `--descricao/-d`, `--content-file`, `--dir`, `--dry-run`, `--remover` (`cli.py:90-97`).
- **Gatilho secundário:** `audit [path] [--report] [--json]` (`cli.py:99-102`), reescrito para o argv do pacote em `montar_argv_delegacao` (`cli.py:107-116`).
- **Gatilho não documentado:** `handoff emit|verify` (`cli.py:176-200`), interceptado **antes** do argparse principal (`cli.py:206-207`). Não aparece no `SKILL.md` nem no `--help` do argparse, que é montado depois do desvio.
- **Payload do injetor estrito:** manifest JSON em arquivo, referenciado por `--payload` (`injetor.py:182`).

**Ressalvas:**
- `SKILL.md` documenta **1 de 3** subcomandos. `handoff` é invocável por um usuário que nunca obou no contrato de descoberta.
- `inject` e o subcomando `inject` do pacote têm **conjuntos de flags divergentes**: a skill oferece `--content-file/--dir/--dry-run/--remover`; o pacote Click adiciona `--mcp-command/--mcp-args/--mcp-env/--files-json` e não oferece `--dry-run` com a mesma semântica. O `montar_argv_delegacao` só normaliza o ramo `audit`; o ramo `inject` repassa `argv` cru (`cli.py:116`),LOGO validação e delegated parser podem divergir silenciosamente.
- Estado exigido: raiz do repositório detectável por `ecossistema.py` (`cli.py:41-47`, `injetor.py:42-48`, `observabilidade.py:45-51`). Sem ele, exit 1.

#### D3. Raio de Impacto e Isolamento

**Status: IMPLEMENTADO no módulo, NÃO APLICADO no caminho real (gravidade ALTA).**

`isolamento.py` é um guard de allowlist de escrita, com suporte a worktree efêmera, e foi provado por sonda:

| Sonda | Esperado | Observado | Exit |
|---|---|---|---|
| `injetor.py --destino` fora do `repo_root` | 1 | `injecao bloqueada: destino '.../ent_probe/out' fora do repo_root '.../Fase_4_Inspetor_Retorno'` | **1** |
| `injetor.py --destino` confinado | 0 | `copiado: .../probe-skill/probe-skill.md` | **0** |

A validação trata corretamente traversal (`resolve()` + `relative_to`), recusa a própria raiz do repositório (`isolamento.py:58-62`) e aceita worktree efêmera quando `worktree_dir` é informado.

**Defeitos:**
1. **Guard órfão.** A injeção real (via `cmd_enterprise`) materializou 5 diretórios de harness — `.claude/`, `.agent/`, `.mimocode/`, `.gemini/`, `.skills/` — no diretório alvo, **sem passar por `validar_caminho_escrita`**. O raio de impacto efetivo da ferramenta é o projeto inteiro do usuário, sem allowlist.
2. **Lógica de confinamento duplicada.** `injetor.py:120-131` reimplementa seu próprio `_destino_confinado` em vez de reutilizar `isolamento.py`. Duas implementações do mesmo invariante divergem por construção: `injetor.py` não tem o conceito de worktree efêmera e `isolamento.py` não conhece manifestos. Um conserto em uma não corrige a outra.
3. **`worktree_dir` nunca é exercido em produção.** `orquestrador.py` e `rollback.py` passam `worktree_dir=None` em todas as chamadas (`orquestrador.py:122,132,162`; `rollback.py:87`). O DoD 1 promete "suporte a execução isolada dentro de Git Worktree efêmera": o parâmetro existe, o caminho de código existe, nenhum consumidor existe.

#### D4. Componentes e Fractalidade

**Status: IMPLEMENTADO (boa estrutura, má integração).**

Sete módulos Python locais com fronteiras claras, carregamento dinâmico de módulo irmão por `importlib.util.spec_from_file_location` com cache em `sys.modules` (`orquestrador.py:37-46`, `rollback.py:30-39`) e **aliases separados por consumidor** (`aidd_enterprise_isolamento_orquestrador` vs `aidd_enterprise_isolamento_rollback`) para evitar colisão de estado — decisão correta.

Fractalidade externa: espelhamento em 8 harnesses (`.agents`, `.claude`, `.cursor`, `.gemini`, `.mimocode`, `.opencode`, `.skills`) a partir da fonte única `componentes/compartilhado/skills/aidd-enterprise/`.

**Ressalvas:**
- O grafo de dependência é um **relacionamento de arquivos, não de módulos**: nenhum deles é importável por nome (`scripts/` não é pacote, não há `__init__.py`). Isso é o que forçou o `spec_from_file_location` e o que torna a composicao frágil.
- Nenhum MCP server, hook ou micro-skill é recrutado internamente. O componente de mais alto risco do ecossistema (escrita em massa multi-harness) não engata nenhum hook de pré-commit ou gate de filesystem.
- Fractelidade **declarada mas não consumida**: `COMPONENTES_PADRAO` (`cli.py:29-38`) é a lista que define o que o handoff assina — mas nenhum desses componentes participa da injeção.

---

### Fase 2: O Chão de Fábrica (Workflow Agêntico)

#### D5. Visão e Escopo

**Status: IMPLEMENTADO (com tensão entre promessa e prática).**

Transformação central pretendida: transformar um componente **não confiável** (artefato de terceiros, baixado, editado à mão) em um componente **certificado** (schema-validado, hash-comprovado, registrado e auditável) dentro de todos os harnesses, de forma transacional.

O escopo declarado no `SKILL.md:8-12` — validação estrita, integridade criptográfica, snapshot/rollback, 7 tipos — está coerente com o código.

A tensão: a pipeline de certificação descrita em `SKILL.md` (linhas 9-11) é executada pelo `injetor.py` local, mas o comando documentado executa a pipeline **do pacote `tools/`**, que é outra implementação. Duas implementações do mesmo conceito, uma não testada pela suíte desta skill.

#### Estágio 1 — `prevalidacao`

- **D6. O que o Estágio Faz:** verifica se a pasta de trabalho existe e é diretório (`orquestrador.py:107-108`).
- **D7. O que o Estágio Recebe:** `pasta: PathLike` já resolvido em `executar_pipeline` (`orquestrador.py:182`).
- **D8. O que o Estágio Processa:** motor puro, zero LLM. Correto.
- **D9. O que o Estágio Entrega:** `return 0/1`; nenhum artefato. Consistente com a natureza de um portão.

#### Estágio 2 — `snapshot`

- **D6. O que o Estágio Faz:** grava `ORQUESTRADOR-SNAPSHOT.json` atraves do guard de isolamento (`orquestrador.py:110-123`).
- **D7. O que o Estágio Recebe:** `pasta`.
- **D8. O que o Estágio Processa:** motor puro. Sem LLM.
- **D9. O que o Estágio Entrega:** **FAILED: Not implemented.** O snapshot **não captura estado de conteúdo**. O payload gravado é um descritor da própria pipeline:
  ```json
  {"estagios": ["prevalidacao","snapshot","injecao","verificacao","handoff"],
   "origem": "<pasta>", "snapshot_de": "prevalidacao"}
  ```
  É metadado do roteiro, não o estado anterior dos arquivos. O snapshot real de conteúdo pré-injeção existe — mas em `rollback.py:66-77` (`_capturar_snapshot`), módulo que **nunca é chamado por este estágio**. O DoD 4 e o DoD 8 dependem deste artefato.

#### Estágio 3 — `injecao`

- **D6. O que o Estágio Faz:** grava um arquivo de texto constante `ORQUESTRADOR-MARCADOR.txt` contendo a literal `"injecao-concluida\n"` (`orquestrador.py:125-133`).
- **D7. O que o Estágio Recebe:** `pasta`.
- **D8. O que o Estágio Processa:** **FAILED: Not implemented.** O handler **não executa injeção alguma**. Não chama `injetor_componente()`, não valida manifest, não calcula SHA-256, não materializa componente. O corpo inteiro do estágio é uma escrita literal. É um stub que retorna 0 — o pior tipo de stub: **verde no gate, vazio na realidade**. Viola a Lei #5.
- **D9. O que o Estágio Entrega:** um arquivo-marcador que não representa nenhum componente injetado.

#### Estágio 4 — `verificacao`

- **D6. O que o Estágio Faz:** confere a existência de snapshot e marcador, compara o marcador com a literal esperada e valida que `estagios` no snapshot é a tupla canônica (`orquestrador.py:135-146`).
- **D7. O que o Estágio Recebe:** arquivos em disco.
- **D8. O que o Estágio Processa:** motor puro, leitura de JSON com `try/except ValueError` → return 1.
- **D9. O que o Estágio Entrega:** `0/1`.
- **Ressalva:** a verificação é **circular** — ela valida que o marcador que o estágio anterior escreveu contém a string que o próprio código de verificação espera. Não há verificação de integridade de componente, que era o propósito declarado do estágio. `verify` retorna 0 mesmo com o motor de injeção inteiramente ausente.

#### Estágio 5 — `handoff`

- **D6. O que o Estágio Faz:** grava `HANDOFF-ENTERPRISE.json` via guard de isolamento, com guarda de pré-condição de existência de marcador e snapshot (`orquestrador.py:148-163`).
- **D7. O que o Estágio Recebe:** `pasta`.
- **D8. O que o Estágio Processa:** motor puro.
- **D9. O que o Estágio Entrega:** `{"versao":1,"estagios":[...],"status":"pronto"}` — **sem SHA-256 de componente algum**. Compare com o handoff real de `cli.py:119-139`, que assina cada componente. O handoff do orquestrador atesta que a pipeline rodou, não que algo foi certificado.

#### D10. Orquestração e Topologia

**Status: FAILED: Not implemented no caminho executado (gravidade CRÍTICA).**

*O que existe:* uma topologia sequencial estrita e determinística, comprovadamente funcional quando invocada diretamente:

```
python .agents/skills/aidd-enterprise/scripts/orquestrador.py <pasta>
  → [aidd-enterprise] pipeline concluido: prevalidacao, snapshot, injecao, verificacao, handoff
  → exit 0; artefatos: ORQUESTRADOR-ESTADO.json, ORQUESTRADOR-SNAPSHOT.json,
                        ORQUESTRADOR-MARCADOR.txt, HANDOFF-ENTERPRISE.json
re-execução → "[aidd-enterprise] pipeline ja concluido." → exit 0 (idempotente)
```

*O transporte:* estado persistido em `ORQUESTRADOR-ESTADO.json` com escrita atômica (`tmp` + `os.replace`, `orquestrador.py:96-101`), validado estritamente por `validar_estado` (versão, campos desconhecidos, ordem de estágios,=status coerente) e retomável a partir de `ESTAGIOS[len(concluidos):]` (`orquestrador.py:208`). Um estado corrompido aborta com exit 1 (`orquestrador.py:193-195`) e a violação de ordem — "prevalidacao pulada" — é detectada explicitamente (`orquestrador.py:72-73`). Essa parte é trabalho sério e de boa qualidade.

*Por que FAILED:*
1. **Órfão total.** `cli.py` referencia `orquestrador.py` apenas como string em `COMPONENTES_PADRAO` (linha 33). `main()` (`cli.py:203-219`) roteia para `executar_script_local` → `tools/aidd-enterprise/scripts/aidd.py`. O subcomando `orquestrador` não existe em nenhum dispatcher. Nenhum usuário chega a esta topologia pelo comando documentado.
2. **A topologia é um casulo.** Mesmo quando executada manualmente, ela não toca os módulos que de fato importam: `injetor.py`, `rollback.py`, `fallback.py`, `observabilidade.py`. Os cinco estágios descrevem um roteiro de fiction operational.
3. **Handoff divergente.** `cli.py:28` usa `handoff-enterprise.json`; `orquestrador.py:25` usa `HANDOFF-ENTERPRISE.json`. Dois nomes para o mesmo conceito, em um filesystem Windows case-insensitive onde colidem, e em Linux onde se fragmentam. O DoD 9 nomeia o primeiro; a topologia produz o segundo. Não há consumidor de nenhum dos dois no caminho real.

---

### Fase 3: Resiliência e Economia (Engenharia Operacional)

#### D11. Tratamento de Exceções e Fallback

**Status: FAILED: Not implemented no caminho executado (gravidade ALTA).**

O módulo `fallback.py` é a peça mais bem desenhada do alvo: classificação de falha transitória por `errno` com o caso Win32 `EBUSY=32` tratado explicitamente (`fallback.py:33`, ausente do módulo POSIX `errno`), detecção por substring de lock (`"index.lock"`), backoff exponencial determinístico `base * fator**(tentativa-1)` injetável, e captura `graceful` que nunca propaga traceback.

Prova empírica:

```
op() falha com PermissionError 2x, acerta na 3a
  → com_retry retornou 'ok'; tentativas=3; backoff observado=[0.1, 0.2]  ✓ determinístico
op() sempre falha com PermissionError
  → executar_com_fallback → exit 1
  → ENTERPRISE-DIAGNOSTICO.json gravado atomicamente (tmp + os.replace)  ✓
  → stderr: "falha capturada (ResilienciaEsgotadaError): [Errno 13] lock permanente -> ..."
```

*Por que FAILED:* nenhum consumidor. `grep` confirma que `fallback.py` não é importado por nenhum módulo de produção da skill nem por `cli.py`. A injeção real, no pacote `tools/`, tem sua própria política de erro, desconhecida desta auditoria. A resiliência testada não é a resiliência do produto.

*Observação adicional:* `com_retry` captura `BaseException` (`fallback.py:89`) e re-raise não-transientes apenas no caminho do `for`; um `KeyboardInterrupt` durante `esperar()` escapa — comportamento correto, mas vale registro.

#### D12. Observabilidade e Frugalidade

**Status: FAILED: Not implemented no caminho executado (gravidade ALTA).**

`observabilidade.py` implementa telemetria estrita com schema de campos exatos (`set(metrica.keys()) != set(_CAMPOS_METRICA)` rejeita chave extra **ou** faltante, `observabilidade.py:75-76`), validação de SHA-256 por regex `^[0-9a-f]{64}$`, não-negatividade numérica com rejeição de `bool` (via `isinstance(valor, bool)`), context manager que **exige** emissão antes do sucesso, e log JSONL em `secoes/ENTERPRISE-TELEMETRIA.jsonl` (Lei #3).

Prova empírica:

```
with execucao('probe-injecao') → emitir() → 1 linha JSONL em secoes/            ✓
with execucao('sem-emissao')   → MetricaAusenteError levantado no __exit__    ✓ (morde)
```

*Por que FAILED:* a execução real do orquestrador **não gerou nenhum log**:

```
python orquestrador.py <pasta>   → exit 0, 4 artefatos
find <pasta> -name "*TELEMETRIA*"  → (vazio)
```

Nenhuma execução de produção da ferramenta emite telemetria. O `MetricaAusenteError` — a defesa que tornaria a ausência impossível — só existe dentro de um contexto que ninguém abre. A Token Economy (Lei #4) não tem lastro mensurável: não há medição de custo, contagem de tokens, tamanho de saída nem tempo por fase. O `duracao_s` existe no schema mas nada o alimenta em produção.

---

### Fase 4: O Inspetor e a Expedição (Validação)

#### D13. Quality Gates (Portões)

**Status: IMPLEMENTADO (o dimension mais sólido do alvo).**

`gates/G_aidd_enterprise.py` (162 linhas) valida em quatro camadas: JSON legível, conformidade com o JSON Schema canônico (com `Draft202012Validator` degradando para violação explícita se a biblioteca faltar, linha 66-67), SHA-256 declarado vs. calculado sobre a carga útil, e — o mais forte — **SHA-256 do arquivo materializado vs. declarado**, com confinamento por `relative_to` (linhas 104-120). Esta última camada é a que detecta **adulteração pós-injeção**, exatamente a ameaça mission-critical.

**Prova de que o portão morde (Lei #13), executada nesta auditoria:**

| Cenário | Saída | Exit |
|---|---|---|
| Manifest conforme | `[SUCESSO] Quality Gate G_aidd_enterprise APROVADO. EXIT 0` | **0** |
| Componente adulterado em disco | `[VIOLAÇÃO] componente adulterado: SHA-256 do arquivo 9c989d17... difere do declarado 9d7b9574...` → `REPROVADO. EXIT 1` | **1** |

Cobertura de teste: `tests/test_gate_aidd_enterprise.py` com 10 casos, incluindo o caminho de reprovação.

**Ressalvas:**
- O gate **não é invocado pelo fluxo da skill**. Roda apenas quando alguém o chama explicitamente com `--manifest`. Não há hook de pre-commit nem amarração ao `enterprise inject`. A certificação é um opt-in manual.
- Duplicação de `calcular_sha256` e `carga_integridade` entre `injetor.py:85-104` e o gate (`G_aidd_enterprise.py:43-61`) — mesma semântica, duas cópias.

#### D14. Critério de Rejeição (Rollback)

**Status: IMPLEMENTADO COM DEFEITO FUNCIONAL (gravidade ALTA).**

**Mecânica de rejeição (correta e provada).** Exit 1 é emitido em: manifest fora do schema, hash divergente, destino fora do `repo_root`, carga útil ausente (`injetor.py:104,114,127`), pacote local ausente (`cli.py:69`), falha de estágio, estado corrompido, exceção não tratada. A suíte confirma 110 testes verdes.

**Transação e reversão (provada).** Snapshot do estado prévio distinguindo conteúdo de ausência (`rollback.py:66-77`), journal persistido atomicamente, `__exit__` disparando `desfazer()` em exceção, remoção de diretórios vazios criados pela transação, e recuperação de crash abrupto:

```
falha no meio da injeção   → exit 1, 'existente.md' restaurado a 'CONTEUDO ORIGINAL\n',
                            workspace_limpo = True, resíduos = []
crash abrupto (journal órfão) → recuperar() → 4 itens tratados,
                            'existente.md' restaurado, 'crasheado.txt' removido,
                            workspace_limpo = True
```

**DEFEITO — escrita em subdiretório novo falha.** `TransacaoEnterprise.escriturar()` não consegue criar o diretório intermediário:

| Cenário | Resultado |
|---|---|
| T1: `tx.escriturar('raiz.md', ...)` | OK |
| T2: `tx.escriturar('sub/novo.md', ...)` | **`FileNotFoundError [Errno 2]`** |
| T3: `tx.escriturar('existente/a.md', ...)` com `existente/` pré-criado | OK |

Causa raiz em `rollback.py:92-98`:
```python
pai = destino.parent
while pai != self.raiz and not pai.exists():
    self._dirs.append(pai)
    pai = pai.parent          # <-- sai com pai == self.raiz
pai.mkdir(parents=True, exist_ok=True)   # <-- cria a raiz, que JÁ existe
destino.write_text(conteudo, encoding="utf-8")  # <-- pai intermediário nunca criado
```
O laço consome a variável `pai` subindo até a raiz, de modo que o `mkdir` seguinte é aplicado ao caminho errado.

**Impacto — direto sobre o DoD 8:** "descartando artefatos parciais". Um componente do tipo `config` é injetado por `injetor.py:152-158` com caminhos relativos aninhados (`files: {"a/b/c.json": ...}`). Se essa escrita ocorrer sob transação, a reversão não consegue cobrir o artefato parcial — que é precisamente o cenário que o rollback existe para conter. A falha é *fail-safe* (exit 1, workspace limpo), mas a feature está quebrada.

**Cobertura cega:** os 9 usos de `escriturar()` em `tests/test_enterprise_rollback.py` escrevem **apenas na raiz ou em diretórios preexistentes**. Nenhum teste cobre subdiretório novo — exatamente o caminho defeituoso. A suíte verde mascara o bug.

#### D15. Output Consolidado e Handoff

**Status: IMPLEMENTADO (com contradição de contrato).**

O handoff de `cli.py:119-146` é o melhor artefato do alvo: manifesto versionado (`versao: "1.0"`), consumidor declarado (`aidd-ops`), timestamp UTC, e SHA-256 + tamanho de cada componente. O modo `verify` (`cli.py:149-173`) recalcula e compara, exit 1 em handoff ausente, ilegível, malformado, componente inexistente ou hash divergente — com mensagens direcionadas a stderr. É um handoff realmente verificável.

**Contradições:**
1. **Artefato nunca emitido pela injeção.** Após `enterprise inject skill auth-probe` (exit 0, 5 arquivos materializados), **não existia** `handoff-enterprise.json` nem `HANDOFF-ENTERPRISE.json` no alvo. O handoff só é produzido pelo subcomando `handoff emit`, não documentado.
2. **Dois nomes, um conceito.** `handoff-enterprise.json` (`cli.py:28`) vs `HANDOFF-ENTERPRISE.json` (`orquestrador.py:25`).
3. **Conteúdo divergente.** O handoff de `cli.py` assina 8 componentes com SHA-256 real; o do orquestrador assina zero componentes.
4. **Consumidor não verificado.** `"consumidor": "aidd-ops"` (`cli.py:136`) é uma string declarada; não há como `aidd-ops` é ligado a este schema.

---

## 3. Matriz de Avaliação da Execução

- [ ] **A ferramenta isolou seu raio de impacto corretamente?** — **NÃO.** O guard `isolamento.py` é provado correto por sonda, mas órfão: a injeção real escreveu em 5 diretórios de harness sem passar por ele. Agrava com a duplicação de lógica em `injetor.py:120-131` e com `worktree_dir` nunca exercido.
- [ ] **O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas?** — **NÃO.** Totalmente determinístico e livre de LLM (veredito positivo isolado), mas as fases não executam trabalho: o estágio `injecao` escreve a literal `"injecao-concluida"` e retorna 0, e o `snapshot` grava o roteiro em vez do conteúdo. Green gate sobre motor vazio.
- [ ] **O output final passou em todos os Quality Gates e emitiu o Handoff?** — **PARCIAL.** O gate próprio existe e morde de verdade (exit 0 / exit 1 comprovados, com teste de adulteração), mas não é invocado pelo fluxo. O handoff não é emitido pela injeção econtradiz o DoD 9 em nome, assinatura e conteúdo.

### 3.1 Consolidação de Vereditos

| Dimensão | Veredito | Gravidade |
|---|---|---|
| D1. Contratos e Regras | IMPLEMENTADO | MÉDIA |
| D2. Input e Gatilhos | IMPLEMENTADO (parcial) | MÉDIA |
| D3. Raio de Impacto e Isolamento | IMPLEMENTADO / NÃO APLICADO | **ALTA** |
| D4. Componentes e Fractalidade | IMPLEMENTADO | BAIXA |
| D5. Visão e Escopo | IMPLEMENTADO | BAIXA |
| D6–D7 (estágios) | IMPLEMENTADO | BAIXA |
| **D8 (estágio `injecao`)** | **FAILED: Not implemented** | **CRÍTICA** |
| D8 (estágio `prevalidacao`/`snapshot`/`verificacao`/`handoff`) | IMPLEMENTADO | MÉDIA |
| D9 (estágios individuais) | IMPLEMENTADO (ver ressalva D9 `snapshot`) | BAIXA |
| **D9 (estágio `snapshot`)** | **FAILED: Not implemented** | **ALTA** |
| **D10. Orquestração e Topologia** | **FAILED: Not implemented** | **CRÍTICA** |
| **D11. Tratamento de Exceções e Fallback** | **FAILED: Not implemented** | **ALTA** |
| **D12. Observabilidade e Frugalidade** | **FAILED: Not implemented** | **ALTA** |
| D13. Quality Gates (Portões) | IMPLEMENTADO | MÉDIA |
| D14. Critério de Rejeição (Rollback) | IMPLEMENTADO COM DEFEITO | **ALTA** |
| D15. Output Consolidado e Handoff | IMPLEMENTADO (contradição de contrato) | **ALTA** |

**Dimensões marcadas `FAILED: Not implemented`: 5** — D8 (estágio `injecao`), D9 (estágio `snapshot`), D10, D11, D12.

### 3.2 Princípio Reitor do Veredito

O alvo **não é um buraco**: a engenharia é real, os testes são verdes (110/110), o gate morde sob adulteração, o rollback restaura conteúdo e limpa o workspace, o retry tem backoff determinístico, a telemetria tem schema estrito. O problema é outro, e é um só:

> **83% do código auditado (1.235 de 1.480 linhas) nunca é executado por nenhum usuário.** A CLI delega 100% da execução para `tools/aidd-enterprise/scripts/aidd.py`, uma segunda implementação da mesma ideia, não coberta por esta suíte. Os 110 testes verdes medem módulos que o produto não usa — e por isso o stub do estágio `injecao`, o snapshot sem conteúdo e a telemetria ausente atravessam a auditoria sem-barulho.

A suíte verde, longe de ser atestado de qualidade, é aqui o **vetor de ocultação**: ela transforma código morto em evidência de conformidade, e é o que permitiu que 5 dimensões fossem declaradas satisfas DoD enquanto não existiam no caminho real.

### 3.3 Recomendações (ordenadas por leverage)

1. **D10 / D3 / D11 / D12 — Amarrar os módulos ao caminho executado.** Fazer `cli.py` invocar `orquestrador.executar_pipeline()` e eliminar a delegação ao pacote `tools/`, **ou** remover os 6 módulos órfãos e migrar a DoD para o que o pacote `tools/` realmente faz. A terceira opção — manter os dois — é a que produziu este laudo. Decidir é obrigatório; a ambiguidade atual é a causa raiz.
2. **D14 — Corrigir `rollback.py:92-98`.** Preservar o pai original antes do laço (`pai_alvo = destino.parent`) e criar os diretórios com `destino.parent.mkdir(parents=True, exist_ok=True)`. Adicionar teste para subdiretório novo — os 9 testes atuais cobrem apenas raiz e diretórios preexistentes.
3. **D8/D9 — Substituir os stubs do orquestrador.** `injecao()` deve chamar `injetor_componente()`; `snapshot()` deve delegar a `TransacaoEnterprise._capturar_snapshot`. Enquanto o estágio `injecao` escrever uma string literal, a dimensão está ausente por definição.
4. **D12 — Tornar a telemetria obrigatória no caminho real.** Envolver a execução de `inject` em `observabilidade.execucao()`; sem isso, o `MetricaAusenteError` é inerte e a Lei #4 não tem lastro.
5. **D13 — Invocar o gate no fluxo.** Amarcar `gates/G_aidd_enterprise.py` à conclusão de `enterprise inject` (ou a um hook de pre-commit), para que a certificação deixe de ser opt-in.
6. **D15 — Unificar o handoff.** Eleger um nome, um schema e um produtor; reconciliar com o `consumidor: aidd-ops` e com o DoD 9.
7. **D1 — Unificar a enum dos 7 tipos** entre `argparse`, JSON Schema e `AGENTS.md` em uma fonte única, e corrigir a promessa de "nunca exit 2" (`cli.py:7-8`).

---

## 4. Anexo — Evidência Brutal da Auditoria

### 4.1 Ambiente

```
Alvo:      .agents/skills/aidd-enterprise/   (8 arquivos, 1.480 linhas)
Gate:      docs/auditoria/aidd-enterprise/G_auditoria_15D.py
Suíte:     tests/test_enterprise_*.py + tests/test_gate_aidd_enterprise.py
```

### 4.2 Suíte de Testes

```
collected 110 items
test_enterprise_cli ............ 12
test_enterprise_fallback ........ 11
test_enterprise_handoff ......... 8
test_enterprise_injetor ......... 22
test_enterprise_isolamento ...... 8
test_enterprise_observabilidade . 15
test_enterprise_orquestrador .... 13
test_enterprise_rollback ....... 11
test_gate_aidd_enterprise ....... 10
============================ 110 passed in 4.66s =============================
```

### 4.3 Sondas Executadas

| # | Sonda | Resultado |
|---|---|---|
| S1 | `cli.py inject skill auth-probe --dir <tmp>` | exit 0, 5 arquivos em 5 harnesses, sem telemetria, sem handoff |
| S2 | `injetor.py --destino` fora do `repo_root` | exit 1, bloqueio correto |
| S3 | `injetor.py --destino` confinado | exit 0, cópia efetuada |
| S4 | `injetor.py` com manifest adulterado | exit 1, `SHA-256 divergente` |
| S5 | `G_aidd_enterprise.py` manifest conforme | exit 0 |
| S6 | `G_aidd_enterprise.py` componente adulterado | exit 1, `componente adulterado` |
| S7 | `orquestrador.py <pasta>` | exit 0, 4 artefatos, 0 linhas de telemetria |
| S8 | `orquestrador.py <pasta>` (re-execução) | exit 0, idempotente |
| S9 | `executar_com_rollback` com falha no meio | exit 1, conteúdo restaurado, `workspace_limpo=True` |
| S10 | `recuperar()` após crash abrupto | 4 itens, restaurado + expurgado, `workspace_limpo=True` |
| S11 | `escriturar('sub/novo.md')` — subdiretório novo | **`FileNotFoundError` (DEFEITO)** |
| S12 | `com_retry` com falha transitória ×2 | sucesso, 3 tentativas, backoff `[0.1, 0.2]` |
| S13 | `executar_com_fallback` esgotado | exit 1, `ENTERPRISE-DIAGNOSTICO.json` gravado |
| S14 | `execucao()` com `emitir()` | 1 linha JSONL |
| S15 | `execucao()` sem `emitir()` | `MetricaAusenteError` (guarda morde) |
| S16 | `grep` de consumidores de produção dos 6 módulos | **nenhum** |

### 4.4 Higiene da Auditoria

Todas as sondas foram executadas em diretório temporário e removidas. `git status --porcelain` retorna vazio — nenhuma árvore de trabalho foi contaminada por esta auditoria. Nenhum `git commit`, `git push` ou `git reset` foi executado.
