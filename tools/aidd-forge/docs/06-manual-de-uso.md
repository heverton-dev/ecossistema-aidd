# Manual Completo de Uso: AIDD Forge

> **Versão oficial:** 1.0.0 (Homologada com Nota 10.0+)  
> **Repositório oficial:** [https://github.com/heverton-dev/aidd-forge](https://github.com/heverton-dev/aidd-forge)  
> **Para quem é este guia:** Desde quem **não sabe nada de programação** até **engenheiros com doutorado em IA**. A linguagem foi desenhada para ser simples, clara e sem barreiras técnicas, com analogias do dia a dia e passos mastigados.

---

# 👶 Seção Especial: "Nunca programei na vida, como eu uso o AIDD Forge?"

### O que o AIDD Forge faz por você?
Imagine que você contratou um assistente de Inteligência Artificial para criar um software para você.
Se você deixar a IA solta, ela pode esquecer regras no meio do caminho, inventar códigos que não funcionam ou até vazar senhas importantes sem você perceber.

O **AIDD Forge** é como **um escudo protetor e um mestre de obras** que você coloca ao lado da IA:
Ele organiza as tarefas em salas separadas, corta o desperdício de dinheiro com tokens desnecessários e coloca fiscais de qualidade na porta para garantir que tudo o que a IA criar seja seguro, rápido e profissional.

### Como usar em 3 Passos Simples:
1. **Passo 1 (Dois Cliques com o Mouse):**  
   Dentro da pasta do projeto, dê um **duplo clique no arquivo `setup.bat`** (no Windows) ou digite no chat da sua IA:  
   > *"Por favor, prepare o ambiente e configure este projeto com AIDD Forge."*
2. **Passo 2 (A Mágica em 1 Segundo):**  
   O Forge inspeciona seu computador, descobre quais ferramentas de IA você tem, instala os fiscais de segurança e exibe a mensagem verde:  
   > `[OK] AIDD Forge configurado com sucesso neste projeto.`
3. **Passo 3 (Crie Seu Sistema com Tranquilidade Total):**  
   Pronto! Agora você pode pedir qualquer coisa para a IA (como *"crie uma página de login"* ou *"faça um sistema de vendas"*).  
   O Forge trabalhará nos bastidores garantindo que a IA não erre a sintaxe, não gaste tokens à toa e nunca quebre o seu projeto.

---

## 1. O Que É o AIDD Forge? (Explicado de Forma Simples)

Imagine que você vai construir uma casa e contrata pedreiros, encanadores e eletricistas. Se cada um trabalhar de qualquer jeito, sem um plano e sem ninguém inspecionando, a obra vira um caos e você gasta uma fortuna em material.

O **`AIDD Forge`** é como o **engenheiro-chefe e mestre de obras** para projetos que usam Inteligência Artificial:
- Ele chega no seu projeto (esteja ele em branco ou já iniciado).
- Identifica quais assistentes de IA você tem no computador (Cursor, Claude, Antigravity, etc.).
- Organiza a "obra" em salas separadas (fases do projeto).
- Impede que a IA se perca ou gaste dinheiro à toa com tokens desnecessários.
- Coloca fiscais de qualidade automáticos (Quality Gates) na porta: se a IA tentar salvar código com erros ou senhas expostas, o Forge bloqueia na hora!

Tudo isso acontece em **menos de 1 segundo**, sem complicação.

---

## 2. O Que Você Precisa Ter Instalado (Pré-Requisitos)

Apenas duas coisas gratuitas:

1. **Python (versão 3.10 ou superior):**  
   - Se ainda não tiver: baixe no site oficial [python.org](https://www.python.org/downloads/) (no Windows, marque a caixinha *"Add Python to PATH"* durante a instalação).
2. **Git (opcional, mas recomendado):**  
   - Baixe em [git-scm.com](https://git-scm.com/downloads).

*Não precisa cadastrar cartão de crédito nem contratar APIs caras para rodar a mecânica do Forge!*

---

## 3. Três Formas de Usar (Escolha a Mais Fácil Para Você)

### 🥇 Nível 1: O Caminho Super Fácil (Com 2 Cliques do Mouse)
*Perfeito para quem nunca abriu uma tela preta de terminal na vida.*

1. Baixe ou abra a pasta do `aidd-forge`.
2. No Windows: dê um **duplo clique no arquivo `setup.bat`**.
3. No Mac ou Linux: dê dois cliques ou rode o `setup.sh`.
4. Uma janela se abrirá, fará todas as verificações nos bastidores e exibirá uma mensagem verde:
   ```text
   [OK] AIDD Forge configurado com sucesso neste projeto.
   ```
5. **Pronto!** O projeto agora está totalmente blindado e pronto.

---

### 🥈 Nível 2: Pelo Chat da Sua Ferramenta de IA (Zero Fricção)
*Perfeito para quem usa Cursor, Claude Code, Antigravity, Open Code ou MimoCode.*

Abra a janela de conversa do seu assistente de IA dentro do projeto e digite qualquer uma destas opções:

**Opção A — Pelo comando de barra:**
```text
/forge
```

**Opção B — Conversando normalmente em português:**
```text
Por favor, prepare o ambiente e configure este projeto com AIDD Forge.
```

O próprio assistente de IA entenderá a intenção e executará o bootstrap silenciosamente sem você precisar sair do editor!

---

### 🥉 Nível 3: Pelo Terminal / Linha de Comando
*Perfeito para desenvolvedores, DevOps e pipelines de CI/CD.*

1. Abra o terminal na pasta do projeto e instale localmente:
   ```bash
   pip install -e .
   ```
2. Inicialize no projeto atual:
   ```bash
   forge init
   ```
3. Se quiser aplicar em outra pasta arbitrária:
   ```bash
   forge init C:\Users\SeuUsuario\Desktop\outro-projeto
   ```
4. Se quiser restaurar todas as regras originais de fábrica (modo auto-recuperação):
   ```bash
   forge init --force
   ```

---

## 4. O Que Aparece no Seu Projeto Depois de Rodar?

Quando o Forge termina, você verá novas pastas organizadas na raiz do seu projeto:

```text
seu-projeto/
│
├── .aidd/
│   └── pipeline/                      ──► Salas de trabalho isoladas por etapa
│       ├── phase_00_bootstrap/        ──► Checagem de computador e git
│       ├── phase_01_requirements/     ──► Requisitos do produto (Filesystem)
│       ├── phase_02_architecture/     ──► Desenho de contratos e banco
│       ├── phase_03_implementation/   ──► Criação de código e testes
│       └── phase_04_audit_security/   ──► Auditoria de segurança OWASP
│
├── .agent/
│   ├── commands/                      ──► Comandos universais (/forge)
│   └── skills/                        ──► 6 habilidades prontas para os agentes
│
├── .claude/commands/                  ──► Comandos prontos para Claude Code
├── .cursor/rules/                     ──► Regras prontas para Cursor IDE
│
├── governance/
│   └── AGENTS.md                      ──► As regras canônicas de convivência das IAs
│
├── CLAUDE.md                          ──► Atalho oficial de regras para o Claude
├── setup.bat                          ──► Botão de 1-clique para Windows
└── setup.sh                           ──► Botão de 1-clique para Linux/Mac
```

---

## 5. As 6 Habilidades (Skills) Que Seus Agentes Ganham

Ao configurar com o Forge, qualquer IA que trabalhar no seu projeto ganha automaticamente 6 superpoderes especializados:

1. **`caveman-ultra` (Economia Máxima de Tokens):** A IA pensa de forma telegráfica internamente e responde em português claro, economizando até 50% da sua fatura de tokens.
2. **`orca-orchestration` (Trabalho em Equipe):** Se você tiver mais de um assistente de IA, eles trabalham em frentes separadas sem bater cabeça.
3. **`impeccable-ui` (Design Profissional):** Garante telas bonitas, modernas e sem poluição visual ou emojis infantis no código de produção.
4. **`open-code-review` (Revisor Crítico):** Analisa se o código está bem estruturado e fácil de dar manutenção no futuro.
5. **`post-mortem` (Detetive de Falhas):** Se algo der errado, investiga a causa-raiz perguntando "Por quê?" até descobrir o problema real.
6. **`cybersecurity-audit` (Escudo de Segurança):** Bloqueia brechas perigosas de hackers (vazamento de dados, injeções maliciosas).

---

## 6. Como os 7 Inspetores (Quality Gates) Te Protegem

Toda vez que você ou a IA tenta salvar uma alteração no Git (`git commit`), sete inspetores robóticos entram em ação automaticamente:

1. **Guarda-Costas de Segredos (`G_BLOQUEAR_SEGREDOS`):** Se alguém acidentalmente esquecer uma senha ou chave de API dentro do código, o commit é barrado na hora.
2. **Inspetor de Gramática do Código (`G_ESTRUTURA_AST`):** Impede que códigos com erros de digitação entrem no projeto.
3. **Sincronizador de Ferramentas (`G_HARNESS_COMPAT`):** Garante que Cursor, Claude e Antigravity estejam lendo as mesmas regras.
4. **Validador de Contratos (`G_CONTRACTS`):** Confere se os formatos de dados combinados estão sendo respeitados.
5. **Testador Incansável (`G_TESTES_REAIS`):** Roda todos os testes de software e só autoriza o commit se 100% passar.
6. **Escudo Cibernético (`G_CYBERSECURITY_OWASP`):** Bloqueia instruções perigosas que possam abrir portas para invasores.
7. **Radar de Velocidade (`G_PERFORMANCE`):** Garante que o sistema continue rápido e responsivo.

---

## 7. Perguntas Frequentes (FAQ Desmistificado)

### ❓ P: "Eu não sou programador, posso estragar meu computador rodando isso?"
**R:** **Não.** O AIDD Forge é 100% seguro. Ele não mexe no seu sistema operacional, não altera arquivos fora da pasta onde você o aciona e não instala programas estranhos. Ele apenas cria arquivos de texto e regras organizadas.

### ❓ P: "E se eu não tiver todas essas ferramentas de IA instaladas?"
**R:** Não tem problema nenhum! O Forge é inteligente: se você tiver apenas uma ferramenta instalada (por exemplo, só o Antigravity ou só o Cursor), ele adapta tudo para rodar perfeitamente nela, sem dar nenhum erro.

### ❓ P: "Quanto custa rodar o AIDD Forge?"
**R:** **Zero reais.** Toda a mecânica de verificação, cópia de regras, análise de arquivos e testes roda no seu próprio computador usando Python puro. Você não paga nem 1 centavo de chamada de IA para executar o Forge.

### ❓ P: "Apareceu uma mensagem em vermelho dizendo que o commit foi bloqueado. O que fazer?"
**R:** Isso é uma notícia excelente! Significa que os Quality Gates te salvaram de subir um erro ou uma senha exposta. Leia a mensagem que apareceu na tela: ela aponta a linha exata que causou o bloqueio. Corrija e tente o commit novamente.

---

## 8. Resumo em 3 Passos para Começar Agora Mesmo

1. Coloque a pasta do **`aidd-forge`** no seu computador.
2. Dê **dois cliques em `setup.bat`** (ou envie `/forge` no chat do seu assistente).
3. Deixe o motor trabalhar e comece a criar seus softwares com governança de padrão industrial!
