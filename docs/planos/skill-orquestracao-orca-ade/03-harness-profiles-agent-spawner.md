# Item 3 — `harness_profiles.json` (corrigido) + `agent_spawner.py` (compilação de comando, sem disparo real)

> **Escopo:** o catálogo declarativo de perfis de harness (arquivo `.orca/harness_profiles.json`) e o compilador que monta a linha de comando final a partir do perfil + prompt fatiado — **sem executar o comando de verdade**. Este item prova que o comando compilado está correto por inspeção de string, nunca por invocação real.
> **Não faz parte deste item:** disparar de fato `agy`/`mimo`/`claude`/`opencode` com um prompt real — isso é o Item 6, com aprovação separada.
> **Custo de LLM:** zero (o módulo só monta uma string de comando, nunca a executa neste item).

---

## Contexto já investigado

- Manual (`MANUAL-UNIFICADO-ORQUESTRACAO-ORCA-ADE.md` §5, §9): perfis de harness declarados em `.orca/harness_profiles.json`, compilados em `[Binário] + [Flags do Perfil] + [Flag do Prompt] + [Prompt Fatiado]` por `agent_spawner.py`.
- **Verificação real feita antes deste documento** (custo zero — só leitura do `--help` estático dos 4 binários já instalados nesta máquina, nenhuma chamada de LLM): o exemplo de `harness_profiles.json` do manual está **errado** para 2 dos 4 harnesses. Tabela de correção (ver também `00-PROCESSO-E-DECISOES.md` §2):

  | Harness | Binário | Flag de auto-aprovação real | `prompt_flag` real | Mecanismo de prompt |
  |---|---|---|---|---|
  | `antigravity` | `agy` | `--dangerously-skip-permissions` | **não confirmado** | `--print`/`-p`/`--prompt` são **flags booleanas** (ativam modo não-interativo) — não recebem valor. O texto do prompt provavelmente é um argumento posicional final, mas isso não foi confirmado por execução real (custaria uma chamada de LLM) |
  | `mimo` | `mimo` | `--dangerously-skip-permissions` (alias `--yolo`) | `--prompt <texto>` | Flag de nível raiz, aceita valor string diretamente — confirmado no `--help` |
  | `claude` | `claude` | `--dangerously-skip-permissions` | `-p`/`--print` (booleano) | Boolean ativa modo `print`; o texto do prompt é um **argumento posicional** (`claude [options] [command] [prompt]`), não o valor do flag `-p` |
  | `opencode` | `opencode` | `--auto` | `--prompt <texto>` | Igual ao `mimo` (mesmo binário-base) — flag de nível raiz, aceita valor string |

  **O manual original tinha `"prompt_flag": "-p"` para `mimo` e `opencode`** — nos dois, `-p` significa `--password` (autenticação básica do servidor local), não o prompt. Se implementado como o manual original descreve, o texto da tarefa seria enviado como senha de servidor — bug funcional real. Este item corrige isso.

## Definição de Pronto

3.1. `componentes/compartilhado/skills/orca-plan-orchestrator/.orca/harness_profiles.json.example` (ou caminho equivalente de exemplo/schema): schema JSON com os 4 perfis usando os valores **corrigidos** da tabela acima. Para `agy` e `claude`, o schema deve modelar explicitamente que o prompt é um **argumento posicional**, não o valor de uma flag (ex.: um campo `prompt_mode: "positional"` vs `prompt_mode: "flag_value"` com o nome do flag), para o `agent_spawner.py` saber montar o comando de forma diferente conforme o harness.

3.2. `componentes/compartilhado/skills/orca-plan-orchestrator/scripts/agent_spawner.py`: função `compilar_comando(perfil, prompt_fatiado)` que retorna a lista de argumentos (`list[str]`, nunca uma string concatenada manualmente — evita bugs de escaping) pronta para passar a `subprocess.run`, respeitando `prompt_mode` de cada harness (positional vs flag_value). A função **nunca chama `subprocess.run` de verdade neste item** — só monta e retorna a lista de argumentos.

3.3. Teste real: para os 4 perfis corrigidos, confirmar por asserção que a lista de argumentos compilada bate exatamente com o esperado (ex.: para `mimo`, `["mimo", "--yolo", "--pure", "--model", "<modelo>", "--prompt", "<texto>"]`; para `claude`, `["claude", "--dangerously-skip-permissions", "--chrome", "--model", "<modelo>", "-p", "<texto>"]` com o texto como último elemento posicional, não como valor de uma flag nomeada).

3.4. **Verificação adicional de baixo custo (ainda zero LLM), recomendada mas não obrigatória:** para `agy` e `claude`, tentar confirmar o mecanismo de posicional lendo mais fundo a documentação/`--help` de subcomandos relacionados (ex.: `agy help`, `claude --help` completo) antes de assumir — documentar no relatório final se a dúvida foi resolvida ou continua em aberto para o Item 6.

## Critério de saída

- `harness_profiles.json` de exemplo com os 4 perfis corrigidos, sem o erro `-p`=senha do manual original.
- `agent_spawner.py` com teste real confirmando a lista de argumentos exata para os 4 perfis, exit 0.
- Nenhum binário real (`agy`, `mimo`, `claude`, `opencode`) invocado com um prompt de verdade neste item — só `--help`/inspeção estática, se necessário para a verificação opcional de 3.4.
- `git status` da raiz limpo ao final, exceto os arquivos novos deste item.

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai criar um catálogo declarativo de perfis de harness e um
compilador de linha de comando para um motor de orquestração
multi-agente, no monorepo ecossistema-aidd (raiz em
C:\Users\trcnologia\Desktop\ecossistema-aidd). Você NÃO vai executar
nenhum agente de LLM real neste item - só montar e validar a lista de
argumentos de comando por inspeção de string.

CONTEXTO JÁ INVESTIGADO - ACHADO CRÍTICO (leia com atenção, um manual
de referência tinha um erro real aqui):
Os 4 binários abaixo já estão instalados nesta máquina. O --help real
de cada um foi lido (sem gastar chamada de LLM - é só o binário
imprimindo sua própria ajuda estática) e produziu esta tabela, que você
deve usar como fonte da verdade (NÃO use os valores do manual original
em docs/features/orquestracao-orca-ade/MANUAL-UNIFICADO-ORQUESTRACAO-ORCA-ADE.md
§5 sem primeiro confirmar - aquele exemplo tem pelo menos 2 erros já
identificados):

| Harness     | Binário   | Flag de auto-aprovação        | prompt_flag real     | Mecanismo do prompt |
|-------------|-----------|--------------------------------|-----------------------|----------------------|
| antigravity | agy       | --dangerously-skip-permissions | NAO CONFIRMADO        | --print/-p/--prompt sao BOOLEANOS (ativam modo nao-interativo), nao recebem valor. O texto do prompt provavelmente e um argumento posicional final - nao confirmado por execucao real |
| mimo        | mimo      | --dangerously-skip-permissions (alias --yolo) | --prompt <texto> | Flag de nivel raiz, aceita valor string diretamente |
| claude      | claude    | --dangerously-skip-permissions | -p/--print (booleano) | Boolean ativa modo print; o texto do prompt e um ARGUMENTO POSICIONAL (uso: claude [options] [command] [prompt]), nao o valor do flag -p |
| opencode    | opencode  | --auto                         | --prompt <texto>      | Igual ao mimo (mesmo binario-base) - flag de nivel raiz, aceita valor string |

Confirme você mesmo rodando "agy --help", "mimo --help", "claude --help",
"opencode --help" (e "mimo run --help" / "opencode run --help" se
quiser aprofundar) antes de codificar - não invente nem presuma
comportamento além do que o --help real mostrar. Se conseguir
confirmar com certeza o mecanismo do prompt de agy/claude (positional
vs outra forma), documente como resolvido; se não, documente como "em
aberto, resolver no Item 6 com aprovação de teste real".

DEFINIÇÃO DE PRONTO:
1. Criar um arquivo de exemplo/schema
   componentes/compartilhado/skills/orca-plan-orchestrator/.orca/harness_profiles.json.example
   com os 4 perfis usando os valores CORRIGIDOS da tabela acima. Para
   agy e claude, modele explicitamente que o prompt e um argumento
   POSICIONAL (nao o valor de uma flag) - por exemplo, um campo
   "prompt_mode": "positional" versus "prompt_mode": "flag_value" com
   o nome do flag, para o compilador de comando saber montar de forma
   diferente conforme o harness.

2. Criar componentes/compartilhado/skills/orca-plan-orchestrator/scripts/agent_spawner.py
   com uma funcao compilar_comando(perfil, prompt_fatiado) que retorna
   uma LISTA de argumentos (list[str], nunca uma string concatenada
   manualmente - evita bugs de escaping), pronta para ser passada a
   subprocess.run, respeitando o prompt_mode de cada harness. Esta
   funcao NUNCA deve chamar subprocess.run de verdade neste item - so
   monta e retorna a lista.

3. Escrever um teste real que, para os 4 perfis corrigidos, confirme
   por asserção que a lista de argumentos compilada bate exatamente
   com o esperado. Exemplos de formato esperado (ajuste conforme sua
   confirmação real do --help):
   - mimo: ["mimo", "--yolo", "--pure", "--model", "<modelo>", "--prompt", "<texto>"]
   - opencode: ["opencode", "--auto", "--pure", "--model", "<modelo>", "--prompt", "<texto>"]
   - claude: ["claude", "--dangerously-skip-permissions", "--chrome", "--model", "<modelo>", "-p", "<texto>"]
     (com <texto> como ULTIMO elemento posicional, nao como valor de
     uma flag nomeada)
   - agy: monte conforme sua melhor confirmação real do --help; se o
     mecanismo do prompt continuar incerto, documente isso claramente
     no relatório final em vez de adivinhar.

Execute o teste de verdade agora e cite a lista de argumentos exata
compilada para cada um dos 4 perfis no relatório final.

CRITÉRIO DE SAÍDA:
- harness_profiles.json.example com os 4 perfis corrigidos, sem o erro
  de -p=senha do manual original.
- agent_spawner.py com teste real confirmando a lista de argumentos
  exata para os 4 perfis, exit 0.
- Nenhum binário real (agy, mimo, claude, opencode) invocado com um
  prompt de verdade neste item - somente --help/inspeção estática, se
  necessário.
- git status da raiz limpo ao final, exceto os arquivos novos deste
  item.

REGRAS DE ESCOPO - NÃO FAÇA:
- Não invoque nenhum dos 4 binários com um prompt real (nada que
  dispare uma chamada de LLM de verdade) - isso é um item futuro
  separado, com aprovação explícita à parte.
- Não presuma o mecanismo do prompt de agy/claude além do que o --help
  real confirmar - documente incerteza explicitamente em vez de
  inventar.
- Não faça git commit nem git push.

ENTREGÁVEL: caminho do harness_profiles.json.example, caminho do
agent_spawner.py, saída real do teste com a lista de argumentos exata
para os 4 perfis, e uma nota explícita confirmando se o mecanismo de
prompt de agy/claude ficou 100% confirmado ou permanece em aberto.
```

## Prompt de Execução — English version

> Copy the block below in full to the executor agent. Self-contained.

```
You are going to create a declarative harness-profile catalog and a
command-line compiler for a multi-agent orchestration engine, in the
ecossistema-aidd monorepo (root at
C:\Users\trcnologia\Desktop\ecossistema-aidd). You will NOT execute any
real LLM agent in this item - only assemble and validate the command
argument list by string inspection.

ALREADY-INVESTIGATED CONTEXT - CRITICAL FINDING (read carefully, a
reference manual had a real error here):
The 4 binaries below are already installed on this machine. The real
--help of each was read (at zero LLM cost - it is just the binary
printing its own static help text) and produced this table, which you
must use as source of truth (do NOT use the values from the original
manual at
docs/features/orquestracao-orca-ade/MANUAL-UNIFICADO-ORQUESTRACAO-ORCA-ADE.md
section 5 without first confirming - that example has at least 2
already-identified errors):

| Harness     | Binary    | Real auto-approve flag         | Real prompt_flag       | Prompt mechanism |
|-------------|-----------|----------------------------------|--------------------------|--------------------|
| antigravity | agy       | --dangerously-skip-permissions | NOT CONFIRMED           | --print/-p/--prompt are BOOLEAN flags (enable non-interactive mode), they take no value. The prompt text is likely a trailing positional argument - not confirmed by a real invocation |
| mimo        | mimo      | --dangerously-skip-permissions (alias --yolo) | --prompt <text> | Root-level flag, takes a string value directly |
| claude      | claude    | --dangerously-skip-permissions | -p/--print (boolean)    | Boolean enables print mode; the prompt text is a POSITIONAL ARGUMENT (usage: claude [options] [command] [prompt]), not the value of the -p flag |
| opencode    | opencode  | --auto                          | --prompt <text>         | Same as mimo (same underlying binary) - root-level flag, takes a string value |

Confirm this yourself by running "agy --help", "mimo --help",
"claude --help", "opencode --help" (and "mimo run --help" /
"opencode run --help" if you want to dig deeper) before coding - do
not invent or assume behavior beyond what the real --help shows. If you
can confirm with certainty the prompt mechanism for agy/claude
(positional vs another form), document it as resolved; if not, document
it as "open, to be resolved in Item 6 with real-test approval".

DEFINITION OF DONE:
1. Create an example/schema file
   componentes/compartilhado/skills/orca-plan-orchestrator/.orca/harness_profiles.json.example
   with the 4 profiles using the CORRECTED values from the table
   above. For agy and claude, explicitly model that the prompt is a
   POSITIONAL argument (not a flag value) - for example, a field
   "prompt_mode": "positional" versus "prompt_mode": "flag_value" with
   the flag name, so the command compiler knows to assemble things
   differently per harness.

2. Create componentes/compartilhado/skills/orca-plan-orchestrator/scripts/agent_spawner.py
   with a function compilar_comando(profile, sliced_prompt) that
   returns a LIST of arguments (list[str], never a manually
   concatenated string - avoids escaping bugs), ready to be passed to
   subprocess.run, respecting each harness's prompt_mode. This function
   must NEVER actually call subprocess.run in this item - it only
   assembles and returns the list.

3. Write a real test that, for the 4 corrected profiles, asserts the
   compiled argument list matches exactly what is expected. Example
   expected shapes (adjust per your real --help confirmation):
   - mimo: ["mimo", "--yolo", "--pure", "--model", "<model>", "--prompt", "<text>"]
   - opencode: ["opencode", "--auto", "--pure", "--model", "<model>", "--prompt", "<text>"]
   - claude: ["claude", "--dangerously-skip-permissions", "--chrome", "--model", "<model>", "-p", "<text>"]
     (with <text> as the LAST positional element, not as a named
     flag's value)
   - agy: assemble per your best real --help confirmation; if the
     prompt mechanism remains uncertain, document this clearly in the
     final report instead of guessing.

Run the test for real now and cite the exact compiled argument list for
each of the 4 profiles in the final report.

EXIT CRITERIA:
- harness_profiles.json.example with the 4 corrected profiles, without
  the original manual's -p=password error.
- agent_spawner.py with a real test confirming the exact argument list
  for the 4 profiles, exit 0.
- No real binary (agy, mimo, claude, opencode) invoked with a real
  prompt in this item - only --help/static inspection, if needed.
- Root git status clean at the end, except the new files of this item.

SCOPE RULES - DO NOT:
- Do not invoke any of the 4 binaries with a real prompt (anything that
  triggers a real LLM call) - that is a future separate item, with
  explicit approval of its own.
- Do not assume the agy/claude prompt mechanism beyond what the real
  --help confirms - document uncertainty explicitly instead of
  inventing.
- Do not git commit or git push.

DELIVERABLE: path of harness_profiles.json.example, path of
agent_spawner.py, real test output with the exact argument list for the
4 profiles, and an explicit note confirming whether the agy/claude
prompt mechanism was 100% confirmed or remains open.
```
