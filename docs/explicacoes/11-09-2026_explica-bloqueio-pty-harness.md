# Por que a execução automática do PLAN-0018 travava (e por que decidimos usar o ORCA real)

> Documento de referência. Gerado em 2026-09-11 a partir de reprodução real —
> cada afirmação aqui foi testada e observada na máquina, não deduzida lendo
> código por cima. Substitui, nos pontos em que divergem, as afirmações de
> `11-09-2026_explica-orca-orquestracao.md` e
> `11-09-2026_explica-orquestracao-git-worktree-nativo.md`.

## A ideia em uma frase

Pensa em ligar um assistente de voz por telefone: ele só "acorda" e escuta
quando reconhece que tem alguém do outro lado da linha de verdade — se você
tenta mandar a mensagem por um bilhete enfiado debaixo da porta, ele nunca
percebe que a mensagem chegou. Foi exatamente isso que aconteceu ao tentar
automatizar os harnesses de IA (mimo, opencode, claude, agy) por trás do
motor Git Worktree nativo: o "bilhete debaixo da porta" (um pipe comum do
Python) nunca chega a ser lido pela tela interativa (TUI) desses programas,
que só aceita entrada quando está ligada a um terminal de verdade.

---

## 1. O que estava sendo testado

O PLAN-0018 (`docs/planos/fazendo/PLAN-0018-seguranca-zero-trust`) tem 10
itens de segurança pra implementar. A ideia era rodar as 10 frentes
automaticamente via `python ecossistema.py orchestrate ... --ambiente
gitworktree --resume`, sem precisar de um humano digitando em cada uma.

Isso expôs, em sequência, 5 problemas reais no motor — cada um confirmado
por reprodução, não por leitura de código.

---

## 2. Os bugs reais encontrados e corrigidos

### 2.1 Caminho da pasta ficava desatualizado após mover pra `fazendo/`

`ecossistema.py` move fisicamente a pasta do plano de `a-fazer/` pra
`fazendo/` no instante em que a execução real começa (`iniciar-execucao`),
mas continuava usando o caminho **antigo** pra resolver a raiz do
repositório git logo em seguida. Resultado: `git rev-parse` rodava com um
diretório de trabalho que não existia mais, e o Windows recusava com
`WinError 267` ("nome de diretório inválido").

**Correção:** depois de mover, o código passou a recalcular o caminho novo
(`docs/planos/fazendo/<nome>`) e usar ele daí em diante.

### 2.2 `opencode` é um atalho `.cmd` no Windows, e isso quebrava toda invocação

No Windows, ferramentas instaladas via `npm -g` (como o `opencode`) viram um
arquivo `.cmd`, não um `.exe`. O `subprocess.run`/`Popen` do Python, quando
recebe uma lista de argumentos (sem usar o shell), **não** aplica a mesma
busca por extensão que um terminal faria — `"opencode"` sozinho não é
encontrado, mesmo estando no `PATH`, e o processo falha com
`WinError 2` antes mesmo de começar.

**Correção:** o motor agora resolve o caminho completo do binário via
`shutil.which()` antes de invocar, o que já inclui a extensão certa.

### 2.3 Trava intermitente do Windows ao apagar uma worktree

Depois que uma frente termina, `git worktree remove` some com o conteúdo da
pasta mas, no Windows, algo (provavelmente antivírus fazendo varredura
em tempo real) segura um identificador de arquivo por uma fração de segundo
a mais — o suficiente pra `git` reportar `Permission denied` ao tentar
remover o diretório vazio que sobrou.

**Correção:** o motor agora tenta de novo (com pequenos intervalos) antes de
desistir, em vez de derrubar a corrida inteira ou depender de limpeza
manual a cada tentativa.

### 2.4 `import os` faltando — o bug mais caro de todos

Esse foi o mais sério: `orchestrator_engine.py` usa `os.getpid()` pra
guardar o "crachá" do processo do robô, mas **nunca importa o módulo `os`**
em lugar nenhum do arquivo. Isso quebra com `NameError` toda vez que uma
frente roda no modo interativo — só que esse erro é capturado por um
`except Exception` genérico que apenas marca a frente como "FALHOU" sem
nunca imprimir o motivo em lugar nenhum. Resultado prático: **nenhuma das
tentativas de hoje chegou a chamar o `opencode` de verdade** antes dessa
correção — o processo morria silenciosamente um passo antes disso, e tudo
que parecia "rodou mas não fez nada" na verdade nunca tinha começado a
rodar.

**Correção:** uma linha (`import os` no topo do arquivo). Confirmado por
teste real: depois da correção, o processo do `opencode` finalmente
apareceu na lista de processos do Windows pela primeira vez.

### 2.5 Espelhos multi-harness desatualizados (`G_HARNESS_COMPAT`)

Este projeto mantém uma cópia da skill `orca-plan-orchestrator` dentro da
pasta de cada ferramenta (`.claude/`, `.agents/`, `.opencode/`, `.mimocode/`,
`.gemini/`, `.cursor/`, `.codebuddy/`), e um gate de qualidade
(`G_HARNESS_COMPAT`) barra o commit se essas cópias divergirem da fonte.
Depois de corrigir a fonte em `componentes/compartilhado/`, foi preciso
rodar `python ecossistema.py components sync --tipo skill --force` pra
realinhar as 7 cópias antes do commit passar.

Os 5 itens acima já foram corrigidos, commitados e enviados pro repositório
remoto (commit `ab38f90`).

---

## 3. A descoberta que gastou mais tempo: o formato real da linha de comando de cada harness

O perfil configurado em `.orca/harness_profiles.json` tinha sido escrito por
suposição, nunca confirmado contra o `--help` real de cada ferramenta. Ao
testar de verdade:

| Harness | Suposição anterior (errada) | Realidade confirmada via `--help` |
| :--- | :--- | :--- |
| **opencode** | `opencode --auto --model X --prompt "texto"` na raiz | Não existe `--auto`/`--model`/`--prompt` na raiz. Só existem dentro do subcomando `opencode run`, e mesmo lá **não existe `--prompt`** — a mensagem é um argumento posicional. |
| **mimo** | Igual ao opencode | Na raiz mesmo, `mimo` aceita `--prompt`, `-m/--model` e `--yolo` diretamente — o formato antigo já estava certo pra esse. |
| **claude** | `--dangerously-skip-permissions` + `-p` (modo não-interativo) | Confirmado que existe, mas o projeto **proíbe modo headless** (gate `G_ZERO_HEADLESS`) — então a execução tem que ser sempre interativa, nunca com `-p`. `--chrome` (integração Claude in Chrome) também é uma flag real. |
| **agy** | `--print`/`--prompt` como valor do prompt | `--print`/`--prompt` são apenas atalhos booleanos pro modo não-interativo — o texto do prompt é um argumento posicional separado. |

Isso por si só já explicava por que as primeiras tentativas de hoje "rodavam
sem fazer nada": o comando nem chegava a ser reconhecido pelo `opencode`
como uma tarefa — ele simplesmente abria a tela padrão (TUI) e não sabia o
que fazer com flags que não existem.

---

## 4. A limitação real: TUI precisa de terminal de verdade, não de um pipe

Depois de corrigir os comandos, restava um problema mais fundo: essas 4
ferramentas abrem uma interface de texto interativa (TUI) que **só aceita
entrada quando detecta um terminal de verdade por trás** (o que
programadores chamam de pseudo-terminal, ou PTY). Um `subprocess.Popen`
comum do Python, mesmo conectando um `stdin=PIPE`, não é isso — é só um
cano de bytes, sem as características de um terminal.

**Evidência, passo a passo:**

1. Rodei um script Python que abre o `opencode` com `stdin` ligado a um
   pipe, espera 10 segundos, escreve o prompt de teste no pipe, e espera o
   processo terminar. **Resultado: travou por mais de 2 minutos, sem
   nenhuma saída, sem criar nenhum arquivo.** Precisei matar o processo à
   força.
2. Você reproduziu o mesmo comando (`opencode --pure --auto --agent -m
   opencode/big-pickle`) manualmente, dentro de um terminal de verdade
   aberto pelo ORCA — **e funcionou perfeitamente**, aceitando o prompt
   digitado e executando a tarefa.
3. Depois de corrigir o bug do `import os` (item 2.4), repeti o teste
   **dentro do próprio motor de orquestração** — desta vez o `opencode`
   realmente foi lançado (processo real confirmado na lista de processos do
   Windows), mas travou exatamente do mesmo jeito que no teste isolado:
   sem saída, sem mudança nenhuma, precisando ser encerrado à força.

A conclusão é definitiva: o motor Git Worktree nativo, hoje, não tem como
"digitar" numa TUI real — ele só consegue lançar o programa e mandar bytes
por um cano que a TUI não escuta.

---

## 5. Por que não construir um PTY do zero (princípio anti-NIH)

Antes de decidir construir isso, verifiquei três coisas:

- **Nenhum código deste monorepo** já implementa suporte a pseudo-terminal
  (`pty`, `ConPTY`, `winpty`, `node-pty`) em lugar nenhum.
- **Nenhuma biblioteca de PTY** (`pywinpty`, `pexpect`, `ptyprocess`) está
  instalada no ambiente Python usado por este projeto.
- **O aplicativo ORCA real já resolve exatamente isso**, com um mecanismo
  próprio (`terminal create` → `terminal wait --for tui-idle` → `terminal
  send`), já testado e comprovadamente funcional (item 4.2 acima).

Ou seja: construir um PTY aqui dentro seria reinventar, do zero e com
risco de bugs novos, uma peça que já existe pronta e funcionando em outro
lugar do próprio ecossistema. Pelo princípio de evitar reinvenção
desnecessária ("Not Invented Here"), a decisão foi **usar o ambiente ORCA
real para o PLAN-0018**, e deixar "suporte a PTY no motor nativo" registrado
como uma melhoria futura — só valeria a pena se um dia for preciso rodar
sem o aplicativo ORCA instalado.

---

## 6. Um bug adicional encontrado (ainda não corrigido)

Ao conferir a mecânica real de criação de worktree
(`git worktree add <caminho> -b <branch>`, sintaxe confirmada contra a
documentação oficial do Git), notei que `worktree_engine.criar_worktree()`
usa o nome puro da frente (`orca/sandbox-nivel-1`) como nome do branch e da
pasta — e **não** o rótulo completo (`PLAN-0018-fase-01-sandbox-nivel-1`)
que a skill `/orchestrate` documenta como obrigatório para permitir
identificar de qual plano cada mesa pertence. Isso ainda não foi corrigido;
fica registrado aqui para uma próxima rodada.

---

## 7. O que as duas explicações anteriores erraram

- `11-09-2026_explica-orca-orquestracao.md` afirma que o motor **já**
  "espera ~10 segundos e digita a instrução" na TUI. Isso não existia até
  eu construir essa lógica durante esta própria investigação — antes disso,
  o motor só embutia o prompt como argumento de linha de comando, o que nem
  sequer é aceito pela maioria dos harnesses (ver seção 3).
- `11-09-2026_explica-orquestracao-git-worktree-nativo.md` descreve um
  processo **manual** (humano cria a worktree com `git worktree add -b ...
  .worktrees/...`, entra na pasta, roda o harness na mão, comita na mão),
  usando uma convenção de pasta (`.worktrees/`) e nomes de modelo
  (`gemini-2.5-pro`, `gpt-4o`) que não correspondem ao código real deste
  projeto (que usa `wt-<nome>` na raiz do repo e os modelos definidos em
  `.orca/harness_profiles.json`).

Os dois documentos parecem ter sido escritos lendo o código por cima, sem
rodar nada de verdade — o oposto do princípio deste ecossistema de sempre
auditar por reprodução real.

---

## 8. Estado atual e próximo passo

- PLAN-0018 está em `docs/planos/fazendo/PLAN-0018-seguranca-zero-trust`,
  nenhuma das 10 frentes foi integrada ainda.
- Os 5 bugs da seção 2 estão corrigidos e no branch `main` (commit
  `ab38f90`).
- Decisão tomada: retomar o PLAN-0018 pelo ambiente **ORCA (aplicativo
  real)**, aproveitando o mecanismo de terminal que já funciona lá.
