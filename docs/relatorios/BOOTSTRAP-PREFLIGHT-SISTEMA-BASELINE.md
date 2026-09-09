# AUDITORIA: BOOTSTRAP DE AMBIENTE, PRÉ-REQUISITOS E PREFLIGHT DE SISTEMA

> **Data:** 2026-09-09
> **Status:** ✅ PLANO FORMALIZADO — `docs/planos/a-fazer/06-bootstrap-ambiente-e-preflight-host/`
> **Tags:** #plano-gerado #bootstrap #preflight #devex #dependencias-sistema #node #docker #git
> **Escopo:** Análise de detecção, diagnóstico e auto-instalação assistida de dependências de nível de sistema operacional (Python, Node.js, Git, Docker, Hadolint) para desenvolvedores e usuários finais.
> **Método:** varredura de todos os pontos de spawn de binários (`shutil.which`, `subprocess.run`, `Popen`) em `ecossistema.py`, `scripts/gestor_dependencias.py`, `gates/`, e as 5 tools; rastreio do comportamento real em máquina virgem.

──────

## 1. Host Prerequisites Inventory (matriz obrigatório × opcional por comando)

| Binário | Obrigatório para | Opcional para | Detectado hoje? |
|:--|:--|:--|:--|
| **Python ≥ 3.10** | tudo (é o interpretador da CLI) | — | ⚠️ implícito: o usuário já tem Python para rodar `ecossistema.py`, mas **nenhuma checagem de versão mínima** |
| **Git ≥ 2.30** | `bootstrap` (hooks), todos os gates de descoberta de arquivos (`git ls-files`), worktrees | — | 🟡 spawn direto sem preflight (`gestor_dependencias.py:343-350`) |
| **click, python-dotenv** (pacotes pip) | **import no topo do `ecossistema.py`** (`:17,24`) | — | 🔴 sem self-diagnóstico: crash de ImportError cru |
| **Node.js / npx** | `dependencia bootstrap` (skill `impeccable`), MCPs npm | runtime gerado (se stack web) | 🔴 nunca verificado antes do spawn |
| **Docker / docker compose** | ops `cofre up`, compose audit (`G_INFRA_COMPOSE` fallback), aidd-master suite | — | 🟡 `G_INFRA_COMPOSE:55` checa `shutil.which("docker")`; ops `cofre` detecta na falha (`cofre_credenciais.py:428`) |
| **sops** | ops `cofre decrypt/up` | — | 🟡 erro estruturado com instrução de install (`cofre_credenciais.py:250,332`) — o melhor padrão do repo |
| **ansible-playbook** | ops deploy/hardening | — | 🟡 `shutil.which` + `Result.fail` com mensagem clara (`ssh_runner.py:194-197`) |
| **hadolint** | gate `G_HADOLINT` | — | 🟢 busca PATH + diretórios comuns Win/Linux (`G_HADOLINT.py:38-61`) — porém ver §2 |
| **checkov** | gate `G_INFRA_COMPOSE` | — | 🟢 triple-check: PATH, `checkov.cmd` (Windows shim) e `find_spec` (`G_INFRA_COMPOSE.py:46-50`) — melhor detector do repo |
| **bash** | `G_INFRA_COMPOSE` (`bash -n` nos scripts) | — | 🟡 `shutil.which("bash")` — em Windows sem Git-Bash no PATH, etapa é pulada silenciosamente |
| **ssh/paramiko** | ops deploy pre-voo | — | 🟢 paramiko opcional com erro claro (`ssh_runner.py:38-40`) |
| **LLM harness** (claude/codex/ade) | `/generate` fases 2-4,6-8 | — | 🟡 `preflight_llm.verificar_llm_pronto` verifica credencial/modelo — bom, mas só para o generator |

**Conclusão da matriz:** a detecção existe em **pontos isolados** (checkov/sops/ansible/hadolint têm `shutil.which` + mensagem boa), mas não há **um ponto único** que diga ao usuário o que falta *antes* de cada comando rodar — cada comando descobre por si, tarde.

## 2. Current Crash Failure Modes (máquina virgem, cenários reais)

- **[BP-1] 🔴 `python ecossistema.py` em Python sem `pip install -r requirements.txt` = ImportError cru.** `ecossistema.py:17` (`import click`) e `:24` (`from dotenv import load_dotenv`) rodam no import do módulo — antes de qualquer código da CLI. Máquina virgem: `ModuleNotFoundError: No module named 'click'` com traceback, zero orientação. Não existe verificação de `.venv`, de versão de Python, nem fallback que sugira `pip install -r requirements.txt`.
- **[BP-2] 🔴 `dependencia bootstrap` sem Node.js: falha opaca em shell.** `gestor_dependencias.py:113` usa `subprocess.run(cfg["instalar"], shell=True)` no Windows (necessário para shims `.cmd`) — sem `npx` no PATH, o `cmd.exe` responde `'npx' is not recognized...` **no stdout bruto do shell**, exit code ≠ 0 vira `{"falhas": ["impeccable (exit N)"]}` sem dizer *por quê* (não menciona "instale Node.js LTS"). No POSIX (`:115`, `shlex.split` sem shell), ausência de `npx` lança `FileNotFoundError` **não tratado** — traceback cru, o relatório de bootstrap inteiro se perde (skills já instaladas não são reportadas).
- **[BP-3] 🔴 Gates de binário externo param o commit sem rota de saída:** `G_HADOLINT` falha (exit 1) com "hadolint não instalado" (docstring `:24`) — correto em *política* (nunca mascarar gate vermelho), mas a mensagem não diz como instalar nem oferece o caminho assistido; `git ls-files` dentro do mesmo gate já tem try/except genérico (`:80-99` — engole qualquer erro de git, inclusive ausência do binário, e cai no walk — comportamento bom por acidente, não por política declarada).
- **[BP-4] 🟡 `/generate` sem LLM configurado:** coberto — `preflight_llm` falha antes de gastar tokens com mensagem de configuração (`LLM_MODEL` + credencial). É o único comando com preflight real de requisito externo.
- **[BP-5] 🟡 `aidd-ops deploy` sem ansible:** `ssh_runner.py:194-197` retorna `Result.fail` com instrução — bom — mas só depois de conectar por SSH (pre-voo paramiko) e construir o inventário efêmero: a descoberta tardia gasta tempo e deixa artefatos temporários.
- **[BP-6] 🟡 `ecossistema.py audit` sem pre-commit/checkov/hadolint:** delega ao pre-commit que reporta `executable not found` do próprio framework (mensagem em inglês, sem rota de install local — `pip install pre-commit`).
- **[BP-7] 🟢 Ponto forte estrutural:** `AGENTS.md §0` já manda o assistente rodar `dependencia verify` na sessão e `bootstrap` se falhar — o fluxo assistido por agente existe; o que falta é o **humano sem agente** ter o mesmo tratamento via CLI.

## 3. Preflight & Assisted Bootstrapper Architecture (design canônico)

### 3.1 `preflight-host` — diagnóstico instantâneo, zero-token
```
python ecossistema.py preflight-host [--json] [--fix]
```
```
Diagnostics (por binário/pacote): { presente, caminho, versao, versao_minima_ok, como_instalar }
  - python:     sys.version_info >= (3,10)
  - git:        git --version (parse), >= 2.30
  - node/npx:   node --version, npx --version (LTS alvo >= 18), shutil.which + shim .cmd no Windows
  - docker:     docker --version + docker compose version (2 binários), daemon acessível (docker info, timeout 3s)
  - hadolint:   which + candidatos comuns (reusar a função que já existe em G_HADOLINT)
  - checkov:    which/checkov.cmd/find_spec (reusar G_INFRA_COMPOSE.py:46-50)
  - pip pkgs:   importlib.util.find_spec(click|dotenv|sqlalchemy|...) mapeados de requirements.txt
  - harness LLM: preflight_llm (só com --ferramenta generate)
Saída: tabela + exit code (0 = tudo ok; 1 = faltando obrigatório p/ comando alvo)
  --json: estrutura consumível por gates e por AGENTS.md §0 (agente lê JSON, não stdout)
  --fix:  delega ao bootstrapper assistido (3.2)
```
**Regra de ouro do design:** uma função de detecção por binário, **fonte única** consumida por (a) CLI, (b) gates (G_HADOLINT/G_INFRA_COMPOSE reusam em vez de duplicar `shutil.which`), (c) `AGENTS.md §0` (verify de sessão passa a incluir preflight-host). Elimina os 4 detectores duplicados que já existem espalhados.

### 3.2 Bootstrapper assistido multi-OS (não invasivo)
```
python ecossistema.py preflight-host --fix [--dry-run]
```
```
para cada item faltante, em ordem de dependência (git → node → docker → pip):
  1. detectar package manager do host:
     Windows: winget (winget --version) > choco > sugestão manual com URL oficial
       ex.: winget install OpenJS.NodeJS.LTS / winget install Docker.DockerDesktop
     macOS:   brew (/opt/homebrew/bin/brew, /usr/local/bin/brew)
       ex.: brew install node | brew install --cask docker
     Linux:   apt > dnf > pacman (com sudo -n check: se pede senha, apenas imprime o comando)
  2. SEMPRE: imprimir comando + pedir confirmação (nunca instalar silenciosamente)
  3. fallback user-space (sem admin/root):
     - node:     download do zip oficial Node LTS p/ ~/.aidd/bin + prepend no PATH da sessão
     - hadolint: binário standalone do GitHub releases p/ ~/.aidd/bin (já é esse o modelo do G_HADOLINT)
     - pip pkgs: pip install --user -r requirements.txt (nunca global sem consentimento)
  4. verificar de novo (o mesmo Diagnostics) e reportar delta
```
- `--dry-run`: mostra exatamente o que faria por SO — testável em CI nas 3 famílias de OS.
- Extensão natural do manifesto: cada entrada de `dependencias_externas.json` ganha campo `preflight` (binário/pacote + versão mínima) — o gestor passa a **declarar requisitos de host**, não só comandos de install.

### 3.3 Self-healing de Python/.venv (fecha BP-1)
```
No início do ecossistema.py (antes de import click/dotenv):
  1. if sys.version_info < (3,10): mensagem clara + exit 1
  2. try: import click, dotenv
     except ImportError:
       print("[AIDD] Dependências Python ausentes.")
       print("[AIDD] Rode: python -m pip install -r requirements.txt  (ou use o .venv do projeto)")
       if "--auto-bootstrap" no argv ou confirmação: subprocess.run([sys.executable, -m, pip, install, -r, requirements.txt])
       exit 1
```
- Import incondicional de click/dotenv vira import protegido; o resto do CLI não muda.
- Documentar `python -m venv .venv` no README com o mesmo texto da mensagem (fonte única da instrução).

## 4. Actionable Roadmap (priorizado)

| # | Pri | Ação | Fecha | Critério de pronto |
|:--|:--:|:--|:--|:--|
| 1 | **P0** | Self-healing de imports no `ecossistema.py` (guarda click/dotenv + versão Python ≥3.10 + oferta de auto-bootstrap) | [BP-1] | Máquina virgem: `python ecossistema.py` exibe instrução clara e exit 1 (nunca traceback); com `--auto-bootstrap` instala e segue |
| 2 | **P0** | `preflight-host` (diagnóstico JSON + tabela) com detectores únicos reutilizando os que já existem (hadolint/checkov/sops/ansible) | §3.1 | Comando roda < 2s, zero rede (exceto docker info opcional); `--json` consumido pelo `dependencia verify` |
| 3 | **P0** | Tratar `FileNotFoundError` do bootstrap POSIX + traduzir falha Windows em diagnóstico ("Node.js ausente — rode preflight-host --fix") | [BP-2] | Bootstrap sem npx: mensagem com causa e comando sugerido, relatório de skills já instaladas preservado |
| 4 | **P1** | Bootstrapper assistido `--fix` com detecção winget/choco/brew/apt/dnf/pacman + confirmação explícita + fallback user-space (`~/.aidd/bin`) | §3.2 | `--dry-run` valida comandos nas 3 famílias de OS em CI; nenhum install sem consentimento |
| 5 | **P1** | Campo `preflight` (binário + versão mínima) em `dependencias_externas.json`; gestor verify inclui host prerequisites | §3.2/3.1 | Verify falha com lista nominal do que falta no host, não só skills/MCPs |
| 6 | **P1** | Gates de binário externo adotam o detector único e padronizam mensagem de ausência (causa + `preflight-host --fix`) | [BP-3/6] | G_HADOLINT/G_INFRA_COMPOSE sem lógica `shutil.which` própria; mensagem inclui comando de install |
| 7 | **P2** | Preflight de ops antecipado: checar ansible/sops/docker **antes** do pre-voo SSH (falha rápida, sem artefatos temporários órfãos) | [BP-5] | Deploy sem ansible falha em < 1s sem criar inventário efêmero |
| 8 | **P2** | AGENTS.md §0 atualizado: verify de sessão roda `preflight-host --json` e reporta faltantes de host em 1 frase | [BP-7] | Sessão em máquina nova diagnostica host + skills em um único comando |
| 9 | **P2** | README quickstart com a mesma instrução do self-healing (fonte única do texto) | §3.3 | Texto idêntico entre mensagem de erro e README (gate de consistência textual opcional) |

**Sequência:** 1-3 eliminam os três crashes cru reais (import, npx POSIX, npx Windows); 4-6 dão o caminho assistido; 7-9 integram o preflight ao fluxo agente/humano existente (§0) sem duplicar detecção.
