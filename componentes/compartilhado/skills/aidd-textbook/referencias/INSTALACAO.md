# Instalação fora deste repositório

Esta habilidade é autocontida: a pasta inteira (`SKILL.md`, `ativos/`, `referencias/`,
`scripts/`) funciona em qualquer projeto, com qualquer assistente de IA e em qualquer
sistema operacional. Nada aqui importa código de fora da biblioteca padrão do Python.

## 1. Copie a pasta para o lugar que o seu assistente lê

| Assistente          | Onde colocar a pasta                                      |
| :------------------ | :---------------------------------------------------------- |
| Claude Code         | `.claude/skills/aidd-livro-texto/`                        |
| OpenCode            | `.opencode/skills/aidd-livro-texto/`                      |
| MimoCode            | `.mimocode/skills/aidd-livro-texto/`                      |
| Antigravity, Hermes | `.agents/skills/aidd-livro-texto/`                        |
| CodeBuddy           | `.codebuddy/skills/aidd-livro-texto/`                     |
| Gemini CLI          | `.gemini/extensions/aidd-livro-texto/skills/aidd-livro-texto/` |
| Cursor              | Aponte a regra do projeto para o `SKILL.md` desta pasta   |

Para uso em todos os projetos da máquina, coloque na pasta pessoal do assistente (por
exemplo `~/.claude/skills/`) em vez da pasta do projeto.

No Gemini CLI, acrescente ao lado da pasta um arquivo `gemini-extension.json` com o
nome e a versão da extensão — é o formato que ele exige para enxergar a habilidade.

Dentro do ecossistema AIDD, nada disso é manual: a fonte fica em
`componentes/compartilhado/skills/aidd-livro-texto/` e a distribuição é feita por
`python ecossistema.py components sync --tipo skill`.

## 2. Instale as duas ferramentas de composição

A habilidade precisa de dois programas: um que converte texto em documento (pandoc) e
outro que faz a diagramação e gera o PDF (typst). Há dois caminhos, e o `livro.py`
detecta sozinho qual está disponível.

**Caminho A — programas instalados no sistema (mais rápido).**

```bash
# Windows
winget install --id JohnMacFarlane.Pandoc
winget install --id Typst.Typst

# macOS
brew install pandoc typst

# Linux (Debian/Ubuntu): pandoc pelo gerenciador; typst pelo binário do projeto
sudo apt install pandoc
```

**Caminho B — pacotes Python (não exige instalar nada no sistema).**

```bash
pip install pypandoc-binary typst
```

Esses dois pacotes trazem os programas dentro deles. Serve bem para máquina onde você
não pode instalar programas, e para servidores de integração contínua.

Diferença prática: no caminho A o pandoc chama o typst diretamente; no caminho B o
pacote `typst` não instala um programa chamável, só uma função Python, então a
composição acontece em dois passos. O resultado em PDF é o mesmo.

## 3. Confirme

```bash
python <pasta-da-habilidade>/scripts/livro.py doctor
```

A saída informa qual caminho está em uso e avisa quando encontra um typst no sistema
que não serve — por exemplo, uma versão anterior à 0.11 (o modelo visual usa um recurso
introduzido nela) ou um atalho de instalação por gerenciador de pacotes que o pandoc não
consegue acionar. Nesses casos ele usa o pacote Python, se estiver instalado.

Saída 0 significa pronto para usar.

## 4. Requisitos mínimos

| Item              | Mínimo                                                          |
| :---------------- | :----------------------------------------------------------------- |
| Python            | 3.10                                                            |
| pandoc            | 3.0 (testado em 3.9 e 3.10)                                     |
| typst             | 0.11 — abaixo disso o modelo visual não compila                 |
| Fontes            | Nenhuma obrigatória; o modelo declara alternativas e o typst substitui o que faltar |

As fontes preferidas são Inter (texto) e Consolas (código). Sem elas, o documento
continua sendo gerado com as substitutas do sistema — muda a aparência, não o conteúdo.

## 5. Uso imediato

```bash
python <pasta-da-habilidade>/scripts/livro.py init ./meu-livro --titulo "Minha Obra" --autor "Meu Nome"
python <pasta-da-habilidade>/scripts/livro.py check ./meu-livro
python <pasta-da-habilidade>/scripts/livro.py build ./meu-livro
```

Pelo assistente, basta pedir `/aidd-livro-texto` e dizer o que quer documentar.
