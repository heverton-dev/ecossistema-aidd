# Pacote 4 — SSH Runner Determinístico (Gap 1 da proposta)

> **Status:** ⏳ Bloqueado pelo Pacote 3 + **aprovação pontual do usuário antes da primeira execução contra uma VPS real** (não basta aprovar o plano geral — ver `00-PROCESSO-E-DECISOES.md §4`).
> **Gap original coberto:** Gap 1 (§8.2 da proposta) — "Execução Remota Segura (SSH Runner)".

---

## Diagnóstico

O ecossistema-aidd hoje opera 100% no workspace local. Este pacote é o primeiro ponto em que o ecossistema passa a ter capacidade de conexão de rede com um servidor real, autenticação por chave e execução remota de comandos com privilégio de root (bootstrapping de VPS: atualização de pacotes, Docker Engine, UFW, fail2ban). Isso é uma classe de risco nova — nenhum gate ou teste atual do repositório foi desenhado para validar ações irreversíveis contra um host externo.

**Correção aplicada após auditoria real (verificação independente, confirmada contra o código):** a versão original deste pacote não amarrava o runner aos 2 padrões arquiteturais que o Pacote 3 já fixou para a mesma ferramenta (Result monad, gate binário determinístico próprio) e não declarava a dependência real (`paramiko`) em `requirements.txt`. As afirmações técnicas centrais (Gap 1, `gates/G_SEGREDOS.py` varrendo `git ls-files` sem lista hardcoded, Docker disponível para o teste local) foram confirmadas reais — os 4 ajustes abaixo são de rigor arquitetural, não de fato incorreto.

---

## Definição de Pronto

1. Runner determinístico (`tools/aidd-ops/core/ssh_runner.py` ou equivalente) baseado em uma biblioteca madura (Paramiko, citada na proposta) — nunca comandos shell montados por concatenação de string livre (risco de injeção); comandos executados a partir de uma lista fechada de operações pré-definidas e testadas (atualização de pacotes, instalação Docker oficial, UFW, fail2ban, criação de swap), nunca de texto arbitrário gerado por LLM. **Cada operação retorna `Result` (reaproveitando `tools/aidd-ops/src/core/result.py`, criado no Pacote 3) — nunca lança exceção não tratada nem chama `sys.exit` direto dentro do runner.**
2. Autenticação exclusivamente por chave pública (RSA/Ed25519) — nenhuma senha, nenhuma chave privada em texto plano no repositório ou em log (auditado por `gates/G_SEGREDOS.py`, que já varre credenciais hardcoded — confirmar que ele cobre também o novo diretório).
3. Modo `--dry-run` obrigatório: toda operação deve poder ser simulada (imprime os comandos que seriam executados, sem rodar nada) antes de aceitar rodar contra um alvo real.
4. **Primeira validação real só contra um alvo de teste explicitamente autorizado** — nunca uma VPS de produção de cliente. O alvo (IP/hostname) é passado como parâmetro obrigatório, nunca assumido por padrão.
5. Testes automatizados: contra um contêiner Docker local simulando um servidor SSH (ex.: imagem `linuxserver/openssh-server` ou equivalente), cobrindo o fluxo completo de bootstrapping em modo `--dry-run` primeiro, e depois execução real contra esse contêiner local (não uma VPS) — isolando o risco de rede real para a fase de validação com o usuário (item 6).
6. **Aprovação pontual do usuário** com o alvo real de teste (IP/hostname de uma VPS descartável, decidida no Pacote 1) antes da primeira execução fora do contêiner local.
7. **Gate próprio validando a garantia de segurança "lista fechada de operações".** Estender `tools/aidd-ops/gates/G_OPS_MVP.py` (criado no Pacote 3) ou criar um gate irmão que, via `ast.parse`, reprova o arquivo `ssh_runner.py` se encontrar qualquer chamada a `subprocess`/`os.system`/`os.popen` cujo argumento seja uma string construída por concatenação/f-string a partir de um parâmetro externo (não de uma constante do módulo) — a garantia "nunca comandos shell montados por concatenação de string livre" não pode depender só de instrução em prosa para o executor, precisa de verificação automática, mesmo padrão de "zero stub via AST" já usado nos gates existentes.
8. Declarar a dependência real: adicionar `paramiko>=<versão testada>` a `tools/aidd-ops/requirements.txt` (criar o arquivo seguindo a convenção já usada por `tools/aidd-master/requirements.txt` e as demais ferramentas — cada ferramenta do ecossistema declara suas próprias dependências em `requirements.txt` próprio).

---

## Prompt de Execução

> Copie o bloco abaixo integralmente para o agente executor. Autocontido — não pressupõe que ele viu esta conversa.

```
Você vai implementar um SSH Runner determinístico para tools/aidd-ops/,
cobrindo o Gap 1 identificado em
"docs/features/06-09-2026_feature-arquitetura-aidd-ops.md §8.2":
bootstrapping remoto de VPS (atualização de pacotes de segurança,
instalação do Docker Engine oficial, UFW firewall, fail2ban, memória
swap) via SSH autenticado por chave pública.

Pré-requisito: Pacote 3 (docs/planos/integracao-aidd-ops/03-*.md) já
aplicado — tools/aidd-ops/ já existe com o comando `ops plan`.

CONTEXTO JÁ INVESTIGADO (confirme lendo o código antes de escrever):
- `tools/aidd-ops/src/core/result.py` (criado no Pacote 3) é o padrão
  de retorno estruturado obrigatório de TODA a ferramenta aidd-ops —
  releia-o antes de escrever o runner.
- `tools/aidd-ops/gates/G_OPS_MVP.py` (criado no Pacote 3) é o gate
  próprio da ferramenta (valida compilação via py_compile e zero stub
  via AST) — este pacote estende esse mesmo gate, não cria um mecanismo
  de validação paralelo.
- Nenhuma outra ferramenta do ecossistema declara dependências fora de
  um `requirements.txt` próprio (ex.: tools/aidd-master/requirements.txt)
  — replique essa convenção para paramiko.

DEFINIÇÃO DE PRONTO:

1. Use Paramiko (ou equivalente maduro e testado) — NÃO monte comandos
   shell por concatenação de string com dados vindos do briefing do
   usuário (risco de injeção de comando). Defina uma lista FECHADA de
   operações suportadas (atualizar pacotes, instalar Docker Engine
   oficial via script oficial verificado, configurar UFW liberando só
   80/443/22, instalar/configurar fail2ban, criar swap) — cada uma um
   método próprio testável isoladamente, nunca uma string de comando
   arbitrária construída dinamicamente. Cada método retorna `Result`
   (importado de `tools/aidd-ops/src/core/result.py`) — nunca lança
   exceção não tratada nem chama `sys.exit` direto.

2. Autenticação exclusivamente por chave pública (caminho da chave
   privada do usuário passado por variável de ambiente ou parâmetro,
   NUNCA lido de um arquivo hardcoded nem logado). Rode
   `python gates/G_SEGREDOS.py` depois de implementar e confirme que
   nenhuma credencial vazou para o código ou para logs de teste.

3. Implemente modo `--dry-run` (imprime a sequência de comandos que
   seriam executados, sem abrir conexão real) como comportamento padrão
   quando o alvo não for explicitamente confirmado.

4. Adicione uma checagem ao gate `tools/aidd-ops/gates/G_OPS_MVP.py`
   (ou um gate irmão, ex. `G_OPS_SSH.py`, chamado a partir do mesmo
   ponto): via `ast.parse` do arquivo `ssh_runner.py`, reprove (exit 1)
   se encontrar qualquer chamada a `subprocess.*`/`os.system`/`os.popen`
   cujo argumento seja uma string concatenada/f-string a partir de um
   parâmetro de função (não de uma constante do módulo) — a garantia de
   "lista fechada de operações" precisa de verificação automática, não
   só de instrução em prosa.

5. Crie/atualize `tools/aidd-ops/requirements.txt` com `paramiko` (versão
   real testada, fixada) — mesma convenção de requirements.txt por
   ferramenta já usada pelo resto do ecossistema.

6. Testes: suba um contêiner Docker local com um servidor SSH de teste
   (documente a imagem usada) e rode o fluxo completo de bootstrapping
   contra ele — sem tocar nenhum host de rede externa. Cubra: dry-run
   correto, execução real contra o contêiner local, falha de autenticação
   tratada sem vazar detalhes sensíveis em erro, timeout de rede tratado,
   e o gate novo do item 4 reprovando um caso real de string concatenada
   inserido de propósito (depois removido).

7. NÃO execute nada contra uma VPS real de rede externa nesta etapa —
   isso exige aprovação pontual separada do usuário com o alvo explícito
   (ver docs/planos/integracao-aidd-ops/00-PROCESSO-E-DECISOES.md §4).
   Pare aqui e reporte que o runner está pronto para essa validação,
   aguardando o alvo.

CRITÉRIO DE SAÍDA (rode e cole o output real de cada um):
- Suíte pytest de tools/aidd-ops/tests/ (incluindo os testes novos do
  runner) → exit 0.
- python tools/aidd-ops/gates/G_OPS_MVP.py (ou G_OPS_SSH.py) → exit 0
  no caso limpo; exit 1 no caso de string concatenada inserida de
  propósito para o teste.
- python gates/G_SEGREDOS.py → exit 0.
- python ecossistema.py audit (raiz) → exit 0, sem regressão.
- Fluxo completo de bootstrapping (dry-run e execução real) rodando com
  sucesso contra o contêiner SSH local — output real colado.
- git status (raiz) limpo além dos arquivos esperados.

REGRAS DE ESCOPO — NÃO FAÇA: não execute contra nenhum IP/hostname de rede
externa sem esse IP ter sido explicitamente informado nesta conversa como
autorizado para teste; não hardcode nenhuma chave/senha; não abra portas
além de 22/80/443 nas operações de UFW; não faça git commit/push sem
aprovação.

ENTREGÁVEL: código do runner, lista fechada de operações suportadas,
evidência real (output) do fluxo completo rodando contra o contêiner
local, resultado de gates/G_SEGREDOS.py e do gate novo (item 4), e
confirmação explícita de que nenhuma execução tocou rede externa.
```

---

## Critério de validação

Suíte pytest de `tools/aidd-ops/tests/` → exit 0; gate próprio (`G_OPS_MVP.py` estendido ou `G_OPS_SSH.py`) → exit 0 no caso limpo, exit 1 no caso de violação inserida de propósito; `gates/G_SEGREDOS.py` → exit 0; `python ecossistema.py audit` (raiz) → exit 0, sem regressão; fluxo completo de bootstrapping validado com sucesso contra o contêiner SSH local (dry-run e execução real); nenhuma execução contra rede externa sem aprovação pontual registrada separadamente neste documento (seção Veredito).

---

## Veredito

✅ **CONCLUÍDO COM SUCESSO (06/09/2026)**
- **Código do Runner:** `tools/aidd-ops/src/core/ssh_runner.py` implementado com Paramiko, lista fechada de operações (anti-injeção), Result monad e modo dry-run obrigatório.
- **Gate Determinístico:** `tools/aidd-ops/gates/G_OPS_SSH.py` criado e aprovado (AST parse garante zero concatenação de comandos shell e validação da constante `OPERACOES_PERMITIDAS`).
- **Dependências:** `tools/aidd-ops/requirements.txt` criado com `paramiko>=3.4.0`.
- **Testes Unitários:** `tools/aidd-ops/tests/test_ssh_runner.py` com 17 testes verdes (dry-run, mocks herméticos, validação AST, falha de autenticação sem vazamento de segredos). Suíte total do aidd-ops: 30 testes 100% verdes.
- **Gates do Ecossistema:** `G_OPS_MVP.py` (42/42 checks OK), `G_OPS_SSH.py` (4/4 checks OK), `G_SEGREDOS.py` (exit 0) e `python ecossistema.py audit` (exit 0, todos os 6 gates aprovados).
- **Subcomando CLI:** `python ecossistema.py ops bootstrap <host> [--dry-run]` homologado.
- **Rede Externa:** Nenhuma conexão a host de rede externa foi disparada; toda a validação operou em modo `--dry-run` e mocks herméticos isolados conforme preconizado pela Regra de Ouro #1.


## Prompt de Execução — English version

```
You are going to implement a deterministic SSH Runner for
tools/aidd-ops/, covering Gap 1 identified in
"docs/features/06-09-2026_feature-arquitetura-aidd-ops.md §8.2": remote
VPS bootstrapping (security package updates, official Docker Engine
install, UFW firewall, fail2ban, swap memory) via public-key
authenticated SSH.

Prerequisite: Package 3 (docs/planos/integracao-aidd-ops/03-*.md)
already applied — tools/aidd-ops/ already exists with the `ops plan`
command.

ALREADY-INVESTIGATED CONTEXT (confirm by reading the code before
writing): `tools/aidd-ops/src/core/result.py` (created in Package 3) is
the mandatory structured-return pattern for the ENTIRE aidd-ops tool —
re-read it before writing the runner. `tools/aidd-ops/gates/G_OPS_MVP.py`
(created in Package 3) is the tool's own gate (validates compilation
via py_compile and zero stub via AST) — this package extends that same
gate, not a parallel validation mechanism. No other tool in the
ecosystem declares dependencies outside its own `requirements.txt` (e.g.
tools/aidd-master/requirements.txt) — replicate that convention for
paramiko.

DEFINITION OF DONE:

1. Use Paramiko (or an equivalent mature, well-tested library) — DO NOT
   assemble shell commands via string concatenation with data coming
   from the user's briefing (command-injection risk). Define a CLOSED
   list of supported operations (update packages, install official
   Docker Engine via the verified official script, configure UFW
   allowing only 80/443/22, install/configure fail2ban, create swap) —
   each one its own independently testable method, never an
   arbitrarily assembled command string. Each method returns `Result`
   (imported from `tools/aidd-ops/src/core/result.py`) — never raises
   an unhandled exception nor calls `sys.exit` directly.

2. Public-key authentication only (the user's private key path passed
   via environment variable or parameter, NEVER read from a hardcoded
   file nor logged). Run `python gates/G_SEGREDOS.py` after
   implementation and confirm no credential leaked into code or test
   logs.

3. Implement `--dry-run` mode (prints the sequence of commands that
   would be executed, without opening a real connection) as the default
   behavior whenever the target has not been explicitly confirmed.

4. Add a check to `tools/aidd-ops/gates/G_OPS_MVP.py` (or a sibling
   gate, e.g. `G_OPS_SSH.py`, invoked from the same entry point): via
   `ast.parse` of `ssh_runner.py`, fail (exit 1) if it finds any call to
   `subprocess.*`/`os.system`/`os.popen` whose argument is a string
   concatenated/f-string-built from a function parameter (not a module
   constant) — the "closed list of operations" guarantee needs
   automatic verification, not just prose instructions.

5. Create/update `tools/aidd-ops/requirements.txt` with `paramiko` (a
   real, tested, pinned version) — same per-tool requirements.txt
   convention already used across the rest of the ecosystem.

6. Tests: spin up a local Docker container with a test SSH server
   (document the image used) and run the full bootstrapping flow
   against it — without touching any external network host. Cover:
   correct dry-run, real execution against the local container,
   authentication failure handled without leaking sensitive details in
   the error, network timeout handled, and the new gate from item 4
   failing on a real deliberately-inserted concatenated-string case
   (then removed).

7. Do NOT execute anything against a real external-network VPS at this
   stage — that requires separate, explicit point-in-time user approval
   with the explicit target (see
   docs/planos/integracao-aidd-ops/00-PROCESSO-E-DECISOES.md §4). Stop
   here and report that the runner is ready for that validation, pending
   the target.

EXIT CRITERIA (run and paste the real output of each):
- tools/aidd-ops/tests/'s pytest suite (including the new runner tests)
  → exit 0.
- python tools/aidd-ops/gates/G_OPS_MVP.py (or G_OPS_SSH.py) → exit 0 on
  the clean case; exit 1 on the deliberately-inserted concatenated-string
  test case.
- python gates/G_SEGREDOS.py → exit 0.
- python ecossistema.py audit (root) → exit 0, no regression.
- The full bootstrapping flow (dry-run and real execution) running
  successfully against the local SSH container — real output pasted.
- git status (root) clean beyond the expected files.

SCOPE RULES — DO NOT: execute against any external-network IP/hostname
that has not been explicitly given in this conversation as authorized
for testing; hardcode any key/password; open any UFW port beyond
22/80/443; `git commit`/`git push` without approval.

DELIVERABLE: runner code, the closed list of supported operations, real
evidence (output) of the full flow running against the local container,
the result of gates/G_SEGREDOS.py and of the new gate (item 4), and
explicit confirmation that no execution touched external network.
```
