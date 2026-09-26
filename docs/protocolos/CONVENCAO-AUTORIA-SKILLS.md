# Convenção de Autoria de Skills (manuais de tarefa)

> **Status:** Ativo. Decisões de idioma, nome e tamanho aprovadas pelo usuário em 26/09/2026 (seção 8).
> **Fontes verificadas em:** 26/09/2026 (lista no fim). **Próxima revisão:** até 25/12/2026.
> **Irmã de:** `docs/protocolos/CONVENCAO-AUTORIA-GATES.md` (mesmo esqueleto).

---

## 1. O que é uma skill

Uma skill é um **manual de tarefa**: uma pasta com um `SKILL.md` que ensina o agente a fazer uma coisa específica. O agente não lê todas as skills o tempo todo. Ele lê só o **nome e a descrição** de cada uma (cerca de 100 tokens por skill) e abre o manual inteiro apenas quando a tarefa combina com a descrição.

Consequência prática: **a descrição é o gatilho**. Uma descrição vaga faz a skill nunca ser usada, ou ser usada na hora errada.

## 2. Por que e para que criar

- **Por quê:** para o agente fazer a mesma tarefa do mesmo jeito em toda sessão, sem depender de alguém explicar de novo.
- **Para quê:** guardar o que o modelo não sabe sozinho: o jeito da casa, a ordem certa, os comandos exatos, as armadilhas já vividas.
- **O que não é:** uma skill não é trava. Se a regra precisa ser obrigatória, ela precisa de um guarda (`CONVENCAO-AUTORIA-GATES.md`). A skill ensina; o guarda confere.

## 3. Quando criar, e quando não

**Crie quando:**
- você explicou a mesma coisa ao agente pela segunda vez;
- a tarefa tem uma ordem de passos que não pode variar (baixa liberdade);
- existe um script pronto que o agente deve rodar em vez de reescrever;
- uma ferramenta nova precisa de um "como usar" para o agente.

**Não crie quando:**
- já existe uma skill que faz isso: procure no catálogo primeiro (`docs/auditoria/mapa-pecas/catalogo-pecas.json`, lista `skills`);
- a ideia é um "atalho com outro nome" para uma skill existente: veja a seção 6.3 sobre aliases;
- o conteúdo é algo que o modelo já sabe (explicar o que é um PDF, o que é Git): isso só gasta contexto;
- o que você quer é bloquear um erro: isso é trabalho de guarda, não de skill.

## 4. Onde criar

| O quê | Onde | Observação |
|---|---|---|
| **Fonte única** | `componentes/compartilhado/skills/<nome>/` | Único lugar onde se edita. Skill de uma ferramenta só: `componentes/<ferramenta>/skills/<nome>/`. |
| Cópias por harness | `.claude/skills/`, `.agents/skills/`, `.opencode/skills/`, `.gemini/…`, `.mimocode/skills/`… | **Geradas** por `python ecossistema.py components sync --tipo skill`. Nunca editar à mão. |
| Skill de terceiros | `gates/dependencias_externas.json` | Registrada com `dependencia add-skill`, e não copiada para a fonte única. |

Dentro da pasta da skill (padrão da especificação aberta):

```
<nome>/
├── SKILL.md       obrigatório: frontmatter + instruções
├── scripts/       opcional: código que o agente EXECUTA (não lê)
├── references/    opcional: material lido só quando preciso
└── assets/        opcional: moldes, schemas, imagens
```

## 5. Formato do `SKILL.md`

### 5.1 Frontmatter: o núcleo que funciona em todo harness

| Campo | Obrigatório | Regra |
|---|---|---|
| `name` | sim | 1 a 64 caracteres, só `a-z`, `0-9` e hífen simples (`^[a-z0-9]+(-[a-z0-9]+)*$`). **Igual ao nome da pasta.** Sem as palavras `anthropic` ou `claude`. Segue as regras de nome da seção 5.3. |
| `description` | sim | 1 a 1024 caracteres, **em inglês**, em terceira pessoa, dizendo **o que faz** e **quando usar** ("Use when…"), com as palavras que o usuário diria. Sem `<` ou `>`. |
| `license`, `compatibility`, `metadata` | não | Da especificação aberta. `compatibility` só se houver exigência real de ambiente (máx. 500 caracteres). |

**Campos exclusivos do Claude Code** (`allowed-tools`, `disable-model-invocation`, `user-invocable`, `context: fork`, `paths`, `arguments`…): use só quando precisar. Os outros harnesses **ignoram em silêncio** esses campos, então a skill precisa continuar correta sem eles. Dois usos recomendados:
- `disable-model-invocation: true` em skill de ação com impacto (deploy, commit, push, envio), para ela só rodar quando você chamar;
- `user-invocable: false` em skill que é só referência, e não comando.

**Descrição, exemplo bom e ruim:**

```yaml
# bom: o que faz + quando usar + palavras-gatilho (inclusive as que o usuário digita em PT-BR)
description: Builds the ecosystem parts catalog and checks every Triad fit. Use when the user asks for an inventory, parts map, duplicated tools, broken fit, "catálogo" or "mapa de peças".

# ruim: vago, sem gatilho, em português
description: Ajuda com o ecossistema.
```

### 5.2 Corpo

- **Idioma: inglês compacto** (Lei #4). O `SKILL.md` e os arquivos de apoio são lidos pela máquina: em inglês o modelo entende melhor e gasta menos tokens. Tudo o que explica a skill **para pessoas** (este manual, os mapas visuais, `docs/`, READMEs, mensagens ao usuário) fica em **PT-BR**.
- **Tamanho: meta de 150 linhas, trava em 450.** Acima de 150, mova o que for consulta para `references/`, com um ponteiro claro no `SKILL.md`. Acima de 450 é reprovado. A especificação aberta aceita até 500; a casa é mais rígida.
- **Referências a um nível só:** o `SKILL.md` aponta direto para cada arquivo de apoio, sem cadeia de referências. Arquivo de apoio com mais de 100 linhas começa com um sumário.
- **Passos com critério de pronto:** cada passo termina numa condição verificável ("o comando saiu com exit 0", e não "entendeu o código").
- **Liberdade na medida certa:** tarefa frágil (migração, deploy) leva o comando exato e "não altere os parâmetros"; tarefa aberta (revisão) leva só a direção.
- **Script em vez de explicação:** operação mecânica vai para `scripts/`, e o manual diz **"rode"**, não "leia". Só a saída do script gasta contexto (Lei #1).
- **Um termo por conceito:** escolha "guarda" ou "gate" e use sempre o mesmo.
- **Nada com data de validade** no texto principal. O que for antigo vai numa seção "padrões antigos".
- **Caminhos com barra normal** (`scripts/x.py`), mesmo no Windows.
- **Ferramentas de MCP com o nome completo** (`Servidor:ferramenta`).
- **Frase positiva:** diga o que fazer. Proibição só como trava, e sempre acompanhada do comportamento certo.

### 5.3 Nomes: um nome só para cada coisa

1. **Skill nossa:** `aidd-<assunto>`, em inglês, com 1 a 3 palavras (`aidd-diagnose`, `aidd-audit-4f`). O assunto é **o que a skill faz**, não como ela roda: sem sufixo `-runner`, sem número (`fluxo-01`) e sem versão.
2. **Uma skill por assunto.** Duas skills com o mesmo trabalho viram uma só; o conteúdo maior e mais recente prevalece, e o resto vai para `references/`.
3. **Skill de ferramenta:** tem o nome exato da ferramenta (`aidd-forge`, `aidd-ops`). Skill de fluxo tem o nome do fluxo (`aidd-pure`, `aidd-open`, `aidd-freedom`).
4. **Atalho para pessoas é comando slash, não skill.** O que o usuário digita (`/pure`, `/melhoria`, `/plan`) mora em `componentes/compartilhado/comandos/` e pode ter nome em PT-BR. O comando só chama a skill `aidd-*`; ele nunca copia o conteúdo.
5. **Skill de terceiros:** mantém o nome original do fornecedor e é registrada em `gates/dependencias_externas.json`, instalada pelo instalador dele. Ela não é copiada para a fonte única.
6. **Nomes vizinhos precisam de descrições que se excluem.** Exemplo: `aidd-planner` (planta do app, `PLANNER.json`) e `aidd-plan` (planos de melhoria do ecossistema, `docs/planos/`). A descrição de cada uma diz qual das duas é.

## 6. Como criar, passo a passo

1. **Procure antes.** No catálogo, busque por nome e por palavras da descrição. Se existir parecida, melhore a existente. **Pronto quando:** você anotou qual skill existente mais se aproxima, ou "nenhuma".
2. **Escreva os testes de comportamento primeiro.** São 3 cenários reais em que o agente erra sem a skill: o pedido do usuário e o que ele deve fazer. Rode sem a skill e anote o resultado; essa é a linha de base. **Pronto quando:** os 3 cenários falham ou saem ruins sem a skill.
3. **Escreva o mínimo que resolve os 3 cenários, em inglês.** Primeiro a descrição (o gatilho), depois os passos. **Pronto quando:** o frontmatter segue a seção 5.1, o nome segue a 5.3 e o corpo tem menos de 150 linhas.
4. **Distribua.** `python ecossistema.py components sync --tipo skill` e depois `python ecossistema.py components verify --tipo skill`. **Pronto quando:** o verify sai com exit 0.
5. **Rode os guardas.** `python gates/G_SKILL_ROT.py` (todo caminho e comando citado existe) e `python gates/G_HARNESS_COMPAT.py`. **Pronto quando:** os dois saem com exit 0.
6. **Teste de verdade.** Chame `/<nome>` direto e depois rode os 3 cenários numa sessão nova. Se a skill não disparou sozinha, o problema está na descrição. **Pronto quando:** os 3 cenários passam, de preferência também num modelo menor (Haiku).
7. **Commit** com o `SKILL.md`, os arquivos de apoio e os testes.

### 6.1 Checklist de pronto

- [ ] não existe outra skill com o mesmo trabalho
- [ ] `name` igual à pasta, `aidd-<assunto>` em inglês, sem `-runner` e sem número
- [ ] `description` em inglês, em terceira pessoa, com "o que faz" e "quando usar"
- [ ] corpo em inglês, com menos de 150 linhas (nunca mais de 450), apoio em `references/`
- [ ] atalho para pessoas, se houver, é um comando slash que só chama a skill
- [ ] passos com critério de pronto verificável
- [ ] operações mecânicas em `scripts/`, e o manual manda rodar
- [ ] 3 cenários de comportamento escritos e passando
- [ ] `components verify` e `G_SKILL_ROT` com exit 0

### 6.2 Quem confere (e onde falta guarda)

| O quê | Guarda | Situação |
|---|---|---|
| Caminhos, comandos e scripts citados existem | `G_SKILL_ROT` | provado |
| Cópia idêntica em todos os harnesses | `G_COMPONENTE_AGNOSTICO`, `G_UNIVERSAL_HARNESS`, `components verify` | provado |
| Compatibilidade de harness | `G_HARNESS_COMPAT` | provado |
| Formato do frontmatter e nomes (5.1 e 5.3), tamanho 450 | `G_SKILL_FORMATO` | **modo aviso** (só imprime) até o fim da renomeação |
| Corpo em inglês | `G_IDIOMA_LEI_4` | **não cobre skills:** o escopo padrão só confere `docs/issues/`. Ampliar para `componentes/*/skills/` |
| Descrição diz "quando usar" | `G_SKILL_FORMATO` (código `SEM_USE_WHEN`) | **modo aviso** |
| Testes de comportamento existem e passam | só `G_PROVA_SKILLS_POCOCK` (4 skills: diagnose, tickets, grill, tdd) | **parcial** |
| Skill repetida (alias) | nenhum | **sem guarda.** Catálogo já detecta (`skills_mesma_descricao`) |

### 6.3 Aliases (mesma skill com dois nomes)

Hoje existem 13 pares com a mesma descrição (`pure`/`aidd-pure`, `plan`/`aidd-plan`…). Pela regra 5.3.4, o atalho vira comando slash e a skill repetida sai. Quando um harness reserva o nome (ex.: `/open` no Antigravity abre arquivo), cria-se outro **comando** (`/aidd-open`), nunca outra skill.

## 7. Erros comuns (medidos em 26/09/2026 nas 75 skills)

- **Descrição sem "quando usar":** só 10 de 75 dizem quando usar. É o principal motivo de skill que não dispara.
- **Skill repetida:** 13 pares com a mesma descrição. O agente não sabe qual escolher.
- **Nenhum teste de comportamento:** fora as 4 skills cobertas por `G_PROVA_SKILLS_POCOCK`, nenhuma prova que muda o que o agente faz. As pastas `tests/` existentes (4) testam scripts, não comportamento.
- **Nomes misturados:** português (`aidd-componentes`, `aidd-sessao`), inglês (`aidd-diagnose`), sufixo `-runner`, número (`fluxo-01-runner`) e apelido sem prefixo (`pure`, `plan`). 18 descrições estão em português, contra a Lei #4.
- **Terceiros copiados para dentro:** 19 skills de fornecedores (14 da Cloudflare, `impeccable` e 4 do code-review-graph) estão na fonte única. `impeccable` e as do code-review-graph também são instaladas pelos instaladores deles, então existem em dobro.

As regras formais da especificação (nome, tamanho, BOM, `<`/`>`) passam nas 75.

## 8. Decisões registradas (usuário, 26/09/2026)

1. **Idioma:** conteúdo da skill (frontmatter e corpo) em inglês, para o modelo entender melhor e gastar menos tokens. Toda explicação para pessoas fica em PT-BR.
2. **Nomes:** `aidd-*` para as skills nossas, com nomenclatura padronizada para acabar com as confusões (seção 5.3). A lista de renomeações está em `docs/auditoria/mapa-pecas/ciclo-01/PROPOSTA-NOMES-SKILLS.md`.
3. **Tamanho:** meta de 150 linhas, trava em 450.

## 9. Fontes (verificadas em 26/09/2026)

- Especificação aberta: <https://agentskills.io/specification>
- Boas práticas da Anthropic: <https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices>
- Skills no Claude Code: <https://code.claude.com/docs/en/skills>
- Skills no opencode: <https://opencode.ai/docs/skills/>
- Escrita para agentes (casa): `componentes/compartilhado/skills/aidd-agent-writing/SKILL.md`
- Distribuição multi-harness (casa): `docs/protocolos/05-09-2026_protocolo-agnosticidade-componentes.md`
