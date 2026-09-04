# aidd-generator

Gerador de projetos de software usando a metodologia **AIDD** (AI-Driven Development). Dada uma ideia em linguagem natural, o pipeline percorre 7-8 fases e produz um projeto completo: schemas, scripts, testes, documentação e — opcionalmente — código funcional gerado por LLM.

## 🌐 SUPREMACIA AGNÓSTICA — Princípio da Universalidade Total

Este projeto foi construído sob o princípio inegociável da **Supremacia Agnóstica** da Engenharia Agêntica Aplicada (AIDD).

NADA aqui é proprietário ou dependente de um único ecossistema:

1. 💻 **Ambiente e SO Agnóstico:** Roda de forma 100% idêntica em Windows, Linux e macOS (Python puro).
2. 🤖 **Harness e ADE Agnóstico:** Suporte nativo e transparente a **OpenCode, Antigravity, Claude Code, MimoCode, Freebuff, Hermes, DeepSeek, Codex, Cursor e Gemini CLI**.
3. 🧠 **LLM e Cognição Agnóstica:**
   - *Modo Delegado:* Aproveita a sessão do agente já autenticado no host (Zero API Keys necessárias).
   - *Modo Headless:* Fallback universal via LiteLLM para dezenas de provedores (Groq, NVIDIA NIM, OpenAI, Anthropic, Ollama local).
4. 🔀 **Orquestração Adaptativa em 3 Níveis:**
   - *Nível Fleet:* Git Worktrees concorrentes por agente (quando em ORCA ADE).
   - *Nível Harness:* Subagentes nativos do assistente em uso.
   - *Nível Local:* `ContextPurgeEngine` com fatiamento limpo e purga estrita de memória a cada fase (CLI puro e CI/CD).
5. 📦 **Artefatos Universais:** Skills, MCPs, JSON Schemas Draft 2020-12, Slash Commands e `AGENTS.md` são escritos uma única vez e projetados deterministicamente para todos os harnesses ativos (Zero Duplicidade).

## O que é

O aidd-generator automatiza a criação de projetos seguindo 5 camadas:

1. **Contratos/Schemas** — JSON Schemas (Draft 2020-12) definem as estruturas de dados antes de qualquer código
2. **Determinismo primeiro** — toda lógica mecânica roda em Python puro, sem LLM (Zero Token)
3. **Gates mecânicos** — validações binárias (`exit 0` / `exit 1`) que bloqueiam erros em cascata
4. **Persistência estruturada** — estado do projeto em JSON/SQLite, não na memória volátil de conversa
5. **Bundles modulares** — cada fase gera artefatos autocontidos e auditáveis

### Pipeline de fases

| Fase | Descrição |
|------|-----------|
| 1 | Pesquisa e coleta de requisitos |
| 2 | Análise e decomposição |
| 3 | Design e arquitetura |
| 4 | Decisões técnicas |
| 5 | Criação de artefatos |
| 6 | Documentação |
| 7 | Autocrítica e auditoria |
| 8 | **(opcional)** Implementação funcional via LLM |

A Fase 8 só roda quando você passa `--implementar-codigo`. Ela gera scripts Python funcionais com testes, usando LLM com loop de correção automático.

## Instalação

```bash
git clone https://github.com/heverton-dev/aidd-generator.git
cd aidd-generator
pip install -r requirements-dev.txt
```

## Configuração de credenciais

Copie o exemplo e preencha com suas chaves:

```bash
cp .env.example .env
```

Provedores suportados (configure via variável `LLM_MODEL` no `.env`):

| Provedor | Exemplo de modelo |
|----------|-------------------|
| TogetherAI | `together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo` |
| NVIDIA NIM | `nvidia_nim/meta/llama-3.3-70b-instruct` |
| Groq | `groq/llama-3.3-70b-versatile` |
| OpenRouter | `openrouter/meta-llama/llama-3.3-70b-instruct:free` |
| OpenAI-compatível | `openai/<modelo>` (requer `OPENAI_API_BASE`) |

O `.env.example` tem todas as variáveis documentadas. O `.env` nunca é commitado (está no `.gitignore`).

## Uso

```bash
# Pipeline completo (Fases 1-7): gera projeto sem código funcional
python scripts/pipeline_completo.py "app de tarefas com autenticacao" --pasta ../meu-projeto

# Com Fase 8: gera código funcional via LLM
python scripts/pipeline_completo.py "app de tarefas com autenticacao" --pasta ../meu-projeto --implementar-codigo

# Modo interativo
python scripts/pipeline_completo.py "app de tarefas" --pasta ../meu-projeto --interativo
```

## Testes

```bash
python -m pytest tests/ -v
```

215 testes, cobrindo schemas, gates, persistência, compilação, fases e pipeline completo.

## Disclaimer sobre a Fase 8 (geração de código funcional)

A Fase 8 usa LLM para gerar código Python funcional com testes. Resultados reais de auditoria interna:

- **Taxa de sucesso real: 55% a 91%**, dependendo da complexidade da ideia
- **Não é garantia de 100% funcional de primeira** — o mecanismo pode gerar código que falha em parte dos testes
- O pipeline reporta falha honestamente quando acontece (status `FALHOU` no index, com `requer_intervencao_manual: true`)
- Em caso de falha, o projeto gerado ainda tem schemas, design e documentação válidos — só o código funcional precisa de revisão manual
- O loop de correção tenta até N vezes corrigir erros automaticamente, mas não garante convergência

**Resumo**: Fases 1-7 são determinísticas e confiáveis. A Fase 8 é um assistente que acelera, não substitui revisão humana.

## Dica: orquestração multi-agente com ORCA

O aidd-generator funciona sozinho, via CLI direto — nenhuma ferramenta extra é necessária. Mas se você estiver rodando múltiplos harnesses de IA ao mesmo tempo (Claude Code, Antigravity, MimoCode, OpenCode, etc.), o **ORCA** pode ajudar a organizar o trabalho:

- **Worktrees isoladas** — cada agente trabalha em sua própria cópia do repositório, sem conflito de arquivos
- **Fase 8 em paralelo** — rode a implementação de código com LLMs diferentes ao mesmo tempo e compare resultados lado a lado
- **Auditoria/revisão concorrente** — paralelize a revisão do código gerado por diferentes agentes sem que um atrapalhe o outro
- **Terminais gerenciados** — cada agente tem seu próprio terminal, sem disputa de recursos

É uma ferramenta complementar, não um requisito. Se você usa apenas um harness por vez, o aidd-generator via CLI direto já resolve.

## Licença

MIT — veja [LICENSE](LICENSE).
