---
name: dependencia-runner
description: Adiciona e instala skills e MCPs de terceiros usados pelo agente que desenvolve neste monorepo, mantendo gates/dependencias_externas.json como fonte única.
---

# Dependência Runner

Esta skill registra e instala **dependências externas usadas pelo próprio agente de IA**
que trabalha neste repositório — skills de terceiros (ex.: `impeccable`) e servidores MCP
de terceiros (ex.: Playwright, GitHub, Supabase, Cloudflare) que o agente usa como
ferramenta durante o desenvolvimento.

**Fora de escopo desta skill:** um MCP que deve virar parte de um produto/ferramenta
gerado por `aidd-forge`/`aidd-generator`/`aidd-master`/`aidd-enterprise`/`aidd-ops` (ex.:
o `cloudflare-mcp` que o `aidd-ops` expõe) segue outro padrão, já pronto e testado:
`componentes/<escopo>/mcps/<nome>/server.py`, sincronizado por
`python ecossistema.py components sync --tipo mcp --ferramenta <escopo>`. Se o pedido for
sobre isso, redirecione para esse padrão em vez de usar esta skill.

## Como Usar
No chat do assistente:
```text
/dependencia bootstrap
/dependencia skill <nome ou pedido em linguagem natural>
/dependencia mcp <nome ou pedido em linguagem natural>
```

Via CLI Python:
```bash
python ecossistema.py dependencia bootstrap [--tipo skills|mcps|todos] [--dry-run]
python ecossistema.py dependencia add-skill --nome <n> --pacote <p> --instalar "<comando>" --verificar <caminho> [--gitignore "padrao1,padrao2"]
python ecossistema.py dependencia add-mcp --nome <n> --pacote <p> --comando <cmd> [--args="a,b"] [--env VAR1,VAR2] [--harnesses claude-code]
# atenção: se o primeiro valor de --args começar com "-" (ex.: "-y,pacote@latest"),
# use sempre a forma --args="-y,pacote@latest" (com "="), senão o argparse confunde
# o valor com uma flag nova e falha com "expected one argument".
python ecossistema.py dependencia list
python ecossistema.py dependencia verify
```

## Protocolo ao ser acionada

1. **`bootstrap`** — sem perguntas: rode `python ecossistema.py dependencia bootstrap` e
   reporte o resultado. É o comando de "primeiro uso após clone".

2. **`skill <pedido>`** — descubra com o usuário: nome curto (kebab-case), pacote exato,
   comando de instalação completo (ex.: `npx <pacote> install ...`) e o caminho de um
   arquivo que só existe depois de instalado (`--verificar`, usado para checar
   idempotência). Se o usuário não souber o comando exato, peça o link/nome do pacote e
   proponha um comando plausível para confirmação antes de rodar. Depois:
   `python ecossistema.py dependencia add-skill --nome ... --pacote ... --instalar "..." --verificar ... --gitignore "..."`.
   Sugira padrões de `.gitignore` cobrindo a pasta da skill em cada harness (ex.:
   `*/skills/<nome>/`) — o footprint de um instalador de terceiro é regenerável, não deve
   ser commitado.

3. **`mcp <pedido>`** — descubra: nome curto, pacote/comando real (ex.: `npx -y
   @playwright/mcp@latest`), e **nomes** de variáveis de ambiente que ele precisa (nunca
   peça ou grave o valor do segredo — só o nome da variável, ex.: `GITHUB_TOKEN`). Confirme
   com o usuário se o alvo é só `claude-code` (único harness com schema de `.mcp.json`
   confirmado nesta v1) antes de tentar outro harness. Depois:
   `python ecossistema.py dependencia add-mcp --nome ... --pacote ... --comando ... --args="..." --env VAR1,VAR2 --harnesses claude-code`.
   Lembre o usuário de exportar o valor real da variável de ambiente na própria máquina
   (nunca commitado) antes de usar o MCP.

4. Sempre finalize rodando `python ecossistema.py dependencia list` e reportando o status
   real (instalado/registrado ou não) — nunca declare sucesso sem essa confirmação.
