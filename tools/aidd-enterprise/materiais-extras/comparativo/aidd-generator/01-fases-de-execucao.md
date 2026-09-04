# O que Acontece nos Bastidores quando Alguém Usa o aidd-generator

> **Versão documentada:** 2.1 (Commit `7d63085` em `main`)  
> **Para quem é este documento:** Pessoas de produto, gestores, empreendedores e qualquer profissional que deseje compreender, de forma simples e desmistificada, o que acontece "por trás das cortinas" quando o sistema gera um projeto de software completo a partir de uma ideia.

---

## Em uma frase

O **`aidd-generator`** funciona como uma **fábrica autônoma de software**: você digita uma ideia em português comum (por exemplo, *"quero um sistema de controle de frotas com agendamento de manutenção e consumo de combustível"*), e a ferramenta aciona uma linha de montagem com vários especialistas automáticos que projetam a arquitetura, desenham os contratos de dados, criam toda a estrutura de pastas e geram o código com testes e documentação pronta.

---

## A Linha de Montagem: Passo a Passo dos Bastidores

### Estação 0 — "A Inspeção da Oficina" (Pré-voo e Ambiente)
Antes de começar qualquer trabalho, a ferramenta realiza uma checagem rápida no computador:
- Confere se o Python está na versão adequada.
- Verifica se há conexão ou credenciais válidas para os modelos de inteligência artificial (TogetherAI, Groq, NVIDIA ou assistente local).
- Garante que a bancada de trabalho está limpa para que o processo não seja interrompido no meio do caminho.

---

### Estação 1 — "A Entrevista de Requisitos" (Fase 1 — O Pesquisador)
Assim que você informa o que deseja (seja digitando na interface web do navegador ou no terminal), o primeiro especialista entra em ação:
- Ele analisa a sua ideia palavra por palavra sem gastar créditos de inteligência artificial desnecessários (usando cálculos determinísticos rápidos).
- Identifica qual é o ramo de negócio, quem são os usuários do sistema, quais recursos essenciais são necessários e quais módulos devem existir.
- Gera um primeiro dossiê organizando o escopo do projeto.

---

### Estação 2 — "O Arquiteto de Negócios" (Fase 2 — O Analisador)
Com o dossiê da ideia em mãos:
- Um especialista aciona inteligência artificial para decompor o sistema em entidades concretas (por exemplo: Veículo, Motorista, Manutenção, Abastecimento).
- Define como essas informações se conectam e quais são as regras de negócio que não podem ser violadas.
- Registra exatamente quantas palavras foram processadas e qual modelo de IA foi utilizado, mantendo tudo transparente.

---

### Estação 3 — "A Sala de Projetos com 5 Especialistas" (Fase 3 — O Designer)
Aqui entram cinco "projetistas virtuais" trabalhando em paralelo:
1. **O Especialista em Dados:** projeta como o banco de dados armazenará cada linha de informação.
2. **O Especialista em Contratos:** escreve as regras rígidas (schemas) que definem o formato exato de cada campo (por exemplo: placa de veículo deve ser texto de 7 dígitos; valor de combustível deve ser número positivo).
3. **O Especialista em Módulos:** divide o sistema em blocos independentes para que o código fique limpo e organizado.
4. **O Especialista em Testes:** planeja quais simulações de teste deverão ser feitas para garantir que o sistema não quebre.
5. **O Especialista em Experiência:** mapeia a jornada de quem vai usar o sistema.

---

### Estação 4 — "A Seleção de Ferramentas" (Fase 4 — O Decisor)
Com as plantas desenhadas, a fábrica decide quais materiais técnicos usar:
- Escolhe a linguagem de programação (Python), o formato de banco de dados (SQLite com modo de gravação rápida WAL) e as bibliotecas necessárias.
- Se o usuário estiver usando o modo interativo, a fábrica faz perguntas simples para que ele escolha preferências; se estiver no modo automático, ela adota as melhores práticas de mercado por padrão.

---

### Estação 5 — "A Fundação e os Moldes de Concreto" (Fase 5 — O Criador)
Nesta etapa, as máquinas pesadas operam em velocidade máxima sem depender de IA:
- Cria a árvore completa de pastas no computador do usuário.
- Grava todos os arquivos de contratos de dados em formato internacional (JSON Schema).
- Instala os esqueletos de código, arquivos de configuração e manuais básicos.
- Cria o manifesto do projeto para que qualquer desenvolvedor ou agente saiba exatamente o que foi construído.

---

### Estação Opcional — "A Mão de Obra e a Oficina de Testes" (Fase 8 — O Implementador Funcional)
Se o usuário pediu a criação do código funcional completo (usando a opção `--implementar-codigo`):
- A IA escreve o código real das rotinas em Python.
- Cria imediatamente uma bateria de testes automáticos simulando cenários do dia a dia.
- Roda os testes no terminal. Se algum teste falhar, o sistema lê o erro, corrige o código e roda o teste novamente em um ciclo de auto-recuperação.
- Ao final, registra com honestidade total: se 100% dos testes passaram, comemora; se algum detalhe ficou pendente, avisa explicitamente que é necessária uma pequena revisão humana.

---

### Estação 6 — "A Redação dos Manuais e Guias" (Fase 6 — O Documentador)
Com o sistema construído e com base nas peças que foram efetivamente montadas:
- Redige o manual de uso principal (`README.md`).
- Documenta as funções de cada módulo e as instruções passo a passo para rodar o software.
- Registra exemplos práticos de como chamar e usar as funcionalidades.

---

### Estação 7 — "A Vistoria Final e o Selo de Qualidade" (Fase 7 — O Auditor Cego)
Antes de entregar as chaves para o usuário, um auditor independente faz a inspeção final:
- Verifica se alguma senha ou chave de API secreta ficou exposta por engano no código (se encontrar, bloqueia imediatamente).
- Confere se todos os arquivos estão no padrão e se a documentação reflete a realidade do código.
- Emite o laudo final de aprovação e entrega o projeto finalizado na pasta indicada.
