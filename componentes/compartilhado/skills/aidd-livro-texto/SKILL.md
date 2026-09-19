---
name: aidd-livro-texto
description: Generates and updates auditable corporate textbooks as PDF via pandoc and typst.
---

# AIDD Livro-Texto — Gerador e Atualizador de Livro-Texto Corporativo

Produz e mantém livros-texto em PDF com diagramação corporativa, estrutura macro→micro,
rastreabilidade por capítulo e auditoria determinística. Funciona em qualquer harness,
qualquer sistema operacional e qualquer repositório — nada aqui depende de um projeto
específico.

**Acionamento:** `/aidd-livro-texto <ação> <alvo>` · CLI: `python <skill>/scripts/livro.py <subcomando>`

## 1. Antes de tudo: descubra se é OBRA NOVA ou ATUALIZAÇÃO

```bash
python <skill>/scripts/livro.py doctor               # pandoc + typst + fontes
python <skill>/scripts/livro.py status <pasta>       # existe livro.json ali?
```

- `status` responde → **atualização**. Vá para a seção 4.
- `status` falha com "manifesto ausente" → **obra nova**. Vá para a seção 3.

Nunca crie uma obra nova por cima de uma existente: `init` sem `--force` recusa, e
forçar apaga o manifesto e o histórico de revisões.

## 2. As seis leis desta obra (inegociáveis)

1. **Determinismo primeiro.** Concatenar, compilar, auditar, medir e versionar é
   trabalho do `livro.py` — zero token. Você escreve **apenas** o Markdown das partes.
2. **Rastreabilidade obrigatória.** Todo capítulo termina com uma seção
   *Rastreabilidade* nomeando os arquivos/fontes que sustentam suas afirmações.
   Afirmação sem fonte não entra.
3. **Honestidade de rótulo.** O que está incompleto, vermelho ou pendente de decisão
   humana é registrado com data e motivo — inclusive num apêndice "Estado honesto".
   Livro que só mostra o que funciona é folheto de vendas.
4. **Evidência antes de prosa.** Leia o material real (código, configuração, dados)
   antes de escrever o capítulo. Nunca descreva intenção como se fosse implementação.
5. **Estrutura fixa.** Macro → meso → micro, com o mesmo gabarito repetido em cada
   nível, para que o leitor compare dois objetos lendo a mesma seção de cada capítulo.
6. **Economia de tokens.** Veja a seção 5. Ela vale durante toda a execução.

## 3. Obra nova — o ciclo completo

```bash
# 3.1 esqueleto (cria partes/, livro.json e o frontmatter com metadados de capa)
python <skill>/scripts/livro.py init <pasta> \
  --titulo "<Título>" --subtitulo "<Subtítulo>" --autor "<Autor>" \
  --instituicao "<Rodapé>" --eyebrow "<ETIQUETA DA CAPA>" --tagline "<uma linha>"

# 3.2 (opcional) identidade visual própria
python <skill>/scripts/livro.py init <pasta> ... --copiar-template

# 3.3 uma parte por bloco da obra
python <skill>/scripts/livro.py add-parte <pasta> --nome 02-meso --titulo "PARTE II — ..."
```

**3.4 Levante a evidência.** Antes de escrever, leia as fontes reais e anote o caminho
de cada uma. Se houver grafo de código ou índice do projeto, consulte-o antes de
varredura textual. Colete números medindo, não estimando.

**3.5 Escreva as partes** em `<pasta>/partes/*.md`, seguindo
`referencias/ESTRUTURA.md` (gabarito) e `referencias/DIAGRAMACAO.md` (layout).
Carregue essas referências **só quando for escrever** — não no início da sessão.

**3.6 Audite e compile:**

```bash
python <skill>/scripts/livro.py check <pasta> --raiz-evidencia <raiz-do-projeto>
python <skill>/scripts/livro.py build <pasta>
python <skill>/scripts/livro.py preview <pasta>    # PNG por página, para inspeção
```

`check` sai com 1 quando acha cerca de código ímpar, bloco typst desbalanceado, coluna
de tabela estreita demais, tabela que não ocupará a largura do corpo, falta de
acentuação em PT-BR ou arquivo citado que não existe. Corrija antes de compilar.

**3.7 Inspecione de fato.** Abra ao menos a capa, o sumário, uma página de tabela larga
e uma de diagrama nos PNGs. Só declare pronto depois de ver — `build` com saída 0
significa que compilou, não que ficou bom.

## 4. Atualização de livro existente

```bash
python <skill>/scripts/livro.py status <pasta>      # o PDF está em dia com o fonte?
# ... edite apenas as partes afetadas em <pasta>/partes/ ...
python <skill>/scripts/livro.py update <pasta> --nota "o que mudou nesta revisão"
```

`update` compara o hash do fonte, roda `check`, recompila **só se algo mudou** e grava
a revisão (data, hash, palavras, nota) em `livro.json`. Detalhes de escopo, do que
reescrever e do que preservar: `referencias/ATUALIZACAO.md`.

Regra dura: **atualizar é cirurgia, não reescrita.** Toque apenas nas partes afetadas
pelo fato novo; se a estrutura precisar mudar, diga isso ao usuário antes de mexer.

## 5. Economia de tokens (vale o tempo todo)

- Trabalho mecânico → `livro.py`. Nunca concatene, conte palavras ou valide layout "na
  mão"; nunca reescreva um arquivo inteiro para mudar um parágrafo.
- Carregue `referencias/*.md` **sob demanda**, uma por vez, e só a que o passo exige.
- Nunca despeje no contexto: PDF, log de compilação, arquivo `.typ` gerado, listagem de
  diretório longa ou o Markdown consolidado. Use `| tail -n 20` em comando verboso.
- Escreva a parte **uma vez**, revisada — retrabalho é o maior gasto de tokens da obra.
- Em obra grande, trate cada parte como unidade independente: leia a evidência daquele
  capítulo, escreva-o, libere o contexto, siga para o próximo.
- Reaproveite: números já medidos ficam no texto; não remeça a cada capítulo.

## 6. Referências (abra apenas quando precisar)

| Arquivo                          | Abra quando                                             |
| :------------------------------- | :------------------------------------------------------- |
| `referencias/ESTRUTURA.md`       | For definir o índice ou escrever qualquer capítulo       |
| `referencias/DIAGRAMACAO.md`     | For montar tabela, diagrama, painel ou ficha técnica     |
| `referencias/ATUALIZACAO.md`     | For atualizar uma obra já existente                      |
| `referencias/INSTALACAO.md`      | For instalar a skill fora deste repositório              |

## 7. Saídas

| Artefato                  | O que é                                                        |
| :------------------------ | :--------------------------------------------------------------- |
| `<pasta>/partes/*.md`     | A fonte editável — é aqui que o conteúdo vive                    |
| `<pasta>/livro.json`      | Manifesto: ordem das partes, hash, histórico de revisões         |
| `<nome-base>.md`          | Markdown consolidado (gerado; não edite à mão)                   |
| `<nome-base>.pdf`         | O livro                                                          |
| `<pasta>/preview/`        | PNG por página, para inspeção visual (descartável)               |
