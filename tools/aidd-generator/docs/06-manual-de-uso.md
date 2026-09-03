# Manual de Uso: aidd-generator v2.1 (Guia Universal)

> **Versão do Framework:** 2.1 (Pós-Elevação para Nota 10.0+ / Homologado)  
> **Para quem é este documento:** Este manual foi desenhado para **qualquer pessoa**: desde quem nunca escreveu uma única linha de código na vida até doutores e especialistas em Engenharia Agêntica.

---

# 👶 Seção Especial: "Nunca programei na vida, como eu uso?"

### O que é o AIDD Generator?
Imagine que você contratou um time completo de desenvolvedores seniores: um arquiteto de software, um designer de banco de dados, um programador experiente e um auditor de segurança.
Em vez de você ter que estudar programação por anos, você apenas diz em bom português o que precisa:
> *"Quero um sistema para controlar as vendas e o estoque da minha padaria"*

A ferramenta cuida de tudo: cria as pastas, desenha o banco de dados, escreve o código com segurança profissional, testa se funciona e entrega tudo pronto na sua máquina.

### Como usar em 3 Passos Simples:

#### Passo 1 — Abrir a Ferramenta (1 Clique)
- Se você usa **Windows**: dê um duplo clique no arquivo `iniciar.bat`.
- Se você usa **Linux** ou **Mac**: execute `./iniciar.sh` no seu terminal.
- Uma tela visual intuitiva e amigável abrirá automaticamente no navegador da sua internet (`http://localhost:5000`). Não é preciso digitar comandos complexos.

#### Passo 2 — Pedir o Sistema
- No campo de texto, digite em palavras simples o que você quer construir. Exemplo:
  *"Crie um sistema para gerenciar pacientes e consultas da minha clínica com agendamento online."*
- Clique no botão **"Gerar Projeto"**.

#### Passo 3 — Acompanhar e Usar
- A ferramenta mostrará a linha de montagem trabalhando em tempo real:
  1. Entendendo sua ideia;
  2. Desenhando os dados;
  3. Escrevendo o código seguro;
  4. Testando tudo para garantir que nada quebra.
- Ao final, uma mensagem verde avisará que seu projeto está pronto, com pasta organizada, documentação e banco de dados configurado!

---

# 💻 Seção Técnica: Para Desenvolvedores e Engenheiros de Software

Se você é desenvolvedor, arquiteto ou usa IDEs de IA como **Claude Code**, **Antigravity**, **Cursor** ou **Codex**, você conta com comandos rápidos e controle fino sobre a esteira.

## 1. Comandos Rápidos (Slash Commands)

Dentro do chat da sua ferramenta de IA, você pode disparar o gerador diretamente:

| Comando | O que faz | Exemplo |
| :--- | :--- | :--- |
| `/generate <ideia>` | Dispara o pipeline completo | `/generate API de pagamentos com webhook PIX` |
| `/aidd-gen <ideia>` | Alias oficial do comando | `/aidd-gen Sistema de gestão de frotas` |
| `/gen <ideia>` | Atalho ultra-curto | `/gen Habit tracker com SQLite` |
| `/continue` | Retoma um pipeline interrompido | `/continue` |
| `/status` | Exibe o status da esteira e frota | `/status` |
| `/help` | Lista todos os comandos e parâmetros | `/help` |

## 2. Reconhecimento de Linguagem Natural (Intent Router)

O sistema reconhece automaticamente sua intenção sem exigir comandos decorados. Qualquer frase como as listadas abaixo aciona o pipeline:
- *"crie um sistema de gestão escolar"*
- *"quero um app para controle financeiro pessoal"*
- *"construa uma API REST para catálogo de produtos"*
- *"preciso de um bot para monitorar preços de passagens"*
- *"create a REST API for task management"*

## 3. Parâmetros Opcionais de Linha de Comando

Você pode complementar seus comandos com argumentos técnicos:

```bash
# Gerar código funcional real (Fase 8 ativada)
python scripts/pipeline_completo.py "Sistema ERP" --implementar-codigo

# Especificar pasta de destino customizada
python scripts/pipeline_completo.py "App de Delivery" --pasta "C:/meus-projetos/delivery"

# Modo interativo (permite escolher banco de dados e opções na Fase 4)
python scripts/pipeline_completo.py "CRM Imobiliário" --interativo
```

## 4. Executando os Testes e Gates Mecânicos

Para auditar o código a qualquer momento:

```powershell
# Executar a suíte completa de 678 testes automatizados
pytest -o pythonpath=.

# Rodar todos os gates obrigatórios (Segredos, I3 Cross-Script e OWASP)
python scripts/verificar_gates.py .
```
