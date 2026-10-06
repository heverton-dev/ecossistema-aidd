# Manual de Uso — aidd-generator

> **Versão documentada:** 2.1 (Commit/Tag: `7d63085` em `main`)  
> **Repositório oficial:** `https://github.com/heverton-dev/aidd-generator`  
> **Escopo:** Guia prático passo a passo, cobrindo da clonagem e configuração de ambiente até a execução via Interface Web ou Terminal e a análise dos resultados gerados.

---

## 1. O Que É o `aidd-generator`

O **`aidd-generator`** é um gerador determinístico e agêntico de software. A partir de uma descrição de ideia em linguagem natural, ele constrói um projeto completo com:
- Contratos e Schemas JSON (Draft 2020-12).
- Estrutura de código organizada em camadas desacopladas.
- Documentação técnica e manuais de operação.
- Suíte de testes unitários automatizados.
- Código funcional em Python (quando executado com `--implementar-codigo`).
- Interface web local intuitiva com monitoramento em tempo real.

---

## 2. Pré-Requisitos

Antes de iniciar, certifique-se de possuir em seu sistema:
1. **Python 3.10 ou superior** instalado e adicionado ao `PATH`.
2. **Git** instalado.
3. Chave de API de um provedor LLM (caso utilize o modo headless):
   - TogetherAI, NVIDIA NIM, Groq, OpenRouter ou qualquer endpoint compatível com OpenAI.
   - *Nota:* Se estiver executando dentro de um ADE ativo (Claude Code, Gemini CLI, Cursor, etc.), o sistema pode operar no modo delegado sem necessidade de novas chaves de API.

---

## 3. Passo 1 — Clonagem do Repositório

Abra o terminal e execute o clone do repositório oficial:

```bash
git clone https://github.com/heverton-dev/aidd-generator.git
cd aidd-generator
```

Para garantir que você está exatamente no commit estável e documentado (`7d63085`):

```bash
git checkout 7d63085
```

---

## 4. Passo 2 — Instalação das Dependências

Crie e ative um ambiente virtual (recomendado):

```bash
# No Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1

# No Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

Instale as dependências de desenvolvimento e execução:

```bash
pip install -r requirements-dev.txt
```

---

## 5. Passo 3 — Configuração de Credenciais (.env)

Crie seu arquivo de configuração a partir do modelo de exemplo:

```bash
# No Windows:
copy .env.example .env

# No Linux / macOS:
cp .env.example .env
```

Abra o arquivo `.env` e configure o provedor e a chave de sua preferência:

```env
# Exemplo 1: Groq (Rápido e econômico)
LLM_MODEL=groq/llama-3.3-70b-versatile
GROQ_API_KEY=sua_chave_groq_aqui

# Exemplo 2: TogetherAI
LLM_MODEL=together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo
TOGETHERAI_API_KEY=sua_chave_together_aqui

# Exemplo 3: NVIDIA NIM
LLM_MODEL=nvidia_nim/meta/llama-3.3-70b-instruct
NVIDIA_API_KEY=sua_chave_nvidia_aqui

# Exemplo 4: OpenRouter (Suporta modelos gratuitos)
LLM_MODEL=openrouter/meta-llama/llama-3.3-70b-instruct:free
OPENROUTER_API_KEY=sua_chave_openrouter_aqui
```

---

## 6. Passo 4 — Execução via Interface Web Local (Modo Visual)

O `aidd-generator` inclui uma interface gráfica web local para quem prefere não interagir pelo terminal.

### Inicialização:
- **No Windows:** Dê um duplo clique no arquivo `iniciar.bat` ou execute no terminal:
  ```bash
  python web_app.py
  ```
- O navegador padrão abrirá automaticamente no endereço:
  ```
  http://localhost:5000
  ```

### Funcionalidades da Interface Web:
- **Aba Geração:** Campo para digitação da ideia em linguagem natural, botão seletor para ativar a Fase 8 de implementação funcional e seletor de pasta de destino.
- **Aba Workspace:** Monitoramento em tempo real do progresso das fases, logs de execução e visualização da árvore de arquivos gerada.
- **Aba Configurações:** Diagnóstico de conexão com LLM e verificação de saúde do ambiente.

---

## 7. Passo 5 — Execução via Linha de Comando (CLI)

Para desenvolvedores e fluxos de automação, utilize o script `pipeline_completo.py`:

### Modo 1: Geração Estrutural e Arquitetural (Fases 1 a 7 — Rápido e Determinístico)
Gera os schemas, a arquitetura, a documentação e os esqueletos sem sintetizar o código funcional:
```bash
python scripts/pipeline_completo.py "Sistema de gestao de inventario e estoque com alerta de reposicao" --pasta ../meu-inventario
```

### Modo 2: Geração com Código Funcional e Testes (Fases 1 a 8)
Aciona a Fase 8, que programa as rotinas em Python, cria a suíte de testes e executa o loop de autocorreção:
```bash
python scripts/pipeline_completo.py "App de tarefas com prioridades e persistencia sqlite" --pasta ../meu-tarefas-app --implementar-codigo
```

### Modo 3: Modo Interativo
Permite ao usuário opinar e responder a perguntas na Fase 4 para customizar a escolha de componentes:
```bash
python scripts/pipeline_completo.py "Plataforma de cursos com modulos e aulas" --pasta ../cursos-app --interativo
```

---

## 8. Passo 6 — Execução da Suíte de Testes Internos

Para validar a integridade de todas as engrenagens do próprio `aidd-generator`:

```bash
python -m pytest tests/ -v
```

A suíte conta com mais de 200 testes automatizados cobrindo schemas, compilador AST, gates de segurança, persistência de cache e fases do pipeline. O resultado esperado é 100% de aprovação sem falhas ou skips forçados.

---

## 9. Passo 7 — Entregas e Resultados

Ao término da execução, o diretório especificado em `--pasta` conterá a seguinte estrutura organizada:

```
meu-projeto/
├── .aidd/
│   └── cache/data/             # Relatórios JSON auditáveis de cada fase
├── docs/                       # Documentos de arquitetura e design
├── schemas/                    # Contratos de dados em JSON Schema Draft 2020-12
├── scripts/                    # Código funcional gerado (quando Fase 8 ativa)
├── tests/                      # Suíte de testes com pytest
├── PLANO-EXECUCAO-ESTRUTURADO.json # Manifesto de estado e saga da geração
├── README.md                   # Manual completo do projeto gerado
└── requirements.txt            # Dependências necessárias para rodar o projeto
```

### Para testar o projeto gerado:
Navegue até a pasta do projeto e execute seus testes nativos:
```bash
cd ../meu-tarefas-app
python -m pytest tests/ -v
```
