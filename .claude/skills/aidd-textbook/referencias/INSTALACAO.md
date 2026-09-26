# Installing outside this repository

This skill is self-contained: the whole folder (`SKILL.md`, `ativos/`, `referencias/`, `scripts/`) works in any project, with any AI assistant and on any operating system. Nothing here imports code outside the Python standard library.

## 1. Copy the folder to where your assistant reads skills

| Assistant | Where to put the folder |
| :------------------ | :---------------------------------------------------------- |
| Claude Code | `.claude/skills/aidd-textbook/` |
| OpenCode | `.opencode/skills/aidd-textbook/` |
| MimoCode | `.mimocode/skills/aidd-textbook/` |
| Antigravity, Hermes | `.agents/skills/aidd-textbook/` |
| CodeBuddy | `.codebuddy/skills/aidd-textbook/` |
| Gemini CLI | `.gemini/extensions/aidd-textbook/skills/aidd-textbook/` |
| Cursor | point the project rule to this folder's `SKILL.md` |

For every project on the machine, put it in the assistant's personal folder (e.g. `~/.claude/skills/`) instead of the project folder.

In Gemini CLI, add a `gemini-extension.json` next to the folder with the extension name and version: it is the format it needs to see the skill.

Inside the AIDD ecosystem none of this is manual: the source lives in `componentes/compartilhado/skills/aidd-textbook/` and `python ecossistema.py components sync --tipo skill` distributes it.

## 2. Install the two typesetting tools

The skill needs two programs: one that converts text into a document (pandoc) and one that lays it out and produces the PDF (typst). There are two paths, and `livro.py` detects which one is available.

**Path A: programs installed on the system (faster).**

```bash
# Windows
winget install --id JohnMacFarlane.Pandoc
winget install --id Typst.Typst

# macOS
brew install pandoc typst

# Linux (Debian/Ubuntu): pandoc from the package manager; typst from the project binary
sudo apt install pandoc
```

**Path B: Python packages (nothing installed on the system).**

```bash
pip install pypandoc-binary typst
```

Both packages bundle the programs. Good for machines where you cannot install programs, and for CI servers.

Practical difference: in path A pandoc calls typst directly; in path B the `typst` package installs no callable program, only a Python function, so typesetting happens in two steps. The PDF is the same.

## 3. Confirm

```bash
python <skill-folder>/scripts/livro.py doctor
```

The output says which path is in use and warns when it finds a system typst that does not work, e.g. a version below 0.11 (the template uses a feature introduced there) or a package-manager shim pandoc cannot call. In those cases it uses the Python package if installed.

Exit 0 means ready to use.

## 4. Minimum requirements

| Item | Minimum |
| :---------------- | :----------------------------------------------------------------- |
| Python | 3.10 |
| pandoc | 3.0 (tested on 3.9 and 3.10) |
| typst | 0.11; below it the template does not compile |
| Fonts | none required; the template declares fallbacks and typst substitutes what is missing |

Preferred fonts are Inter (text) and Consolas (code). Without them the document is still produced with system substitutes: the look changes, not the content.

## 5. Quick start

```bash
python <skill-folder>/scripts/livro.py init ./my-book --titulo "Minha Obra" --autor "Meu Nome"
python <skill-folder>/scripts/livro.py check ./my-book
python <skill-folder>/scripts/livro.py build ./my-book
```

From the assistant, ask `/aidd-livro-texto` and say what you want to document.
