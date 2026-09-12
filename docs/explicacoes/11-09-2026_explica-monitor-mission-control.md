# Mission Control — o que foi acrescentado ao monitor

> Projeto: `C:\Users\trcnologia\Desktop\monitoramento-pc`
> Alterações de 2026-09-11. Backup do arquivo original em `app.py.bak-pre-disco`.

---

## O que já existia

Servidor HTTP local em arquivo único (`app.py`, Python + `psutil`), em `http://localhost:8989`:
CPU, RAM, discos, temperatura, rede, bateria, USB, top de processos, encerrar processo,
limpar temporários, ejetar unidade, score de estabilidade, histórico em `telemetry_log.jsonl`.

## O que faltava

O painel media RAM e disco, mas **não media a memória virtual (pagefile)** — que foi justamente
o que derrubou o Orca — e **não mostrava onde o espaço do `C:` estava indo**.

---

## O que foi acrescentado

### 1. Página `/disco`

Tela nova, no mesmo tema escuro. Duas seções:

**Memória virtual** — teto total, uso atual, e a coluna que importa: **maior pico já atingido**.
Semáforo em três níveis, com texto em português explicando o que fazer. Detecta sozinho o
"pagefile fantasma" (configurado num disco USB e portanto nunca criado) — a causa exata do
problema desta máquina.

**Espaço por pasta** — 27 pastas mapeadas, cada uma com tamanho medido, o que é, e como se
recupera se for apagada. Ordenadas da maior para a menor, com etiqueta de risco.

### 2. Três endpoints novos

| Endpoint | O que faz |
| --- | --- |
| `GET /api/disk-audit` | Mede as 27 pastas. **Só leitura.** Cache de 5 min |
| `GET /api/disk-clean?itens=...` | **Simulação** por padrão. Só apaga com `&confirmar=1` |
| `GET /api/pagefile-health` | Saúde da memória virtual, com alertas em português |

### 3. A regra inviolável, escrita no código

> **Nada é removido sem permissão explícita.**

Quatro travas independentes:

1. **`disk_audit()` nunca escreve.** Só `os.scandir` e `stat`.
2. **Simulação é o padrão.** Sem `confirmar=1`, `disk_clean()` mede e relata, e nada mais.
3. **Itens `manual` são intocáveis.** `parse_clean_keys()` os **recusa mesmo com `confirmar=1`**.
   São 9 pastas — modelos de IA, livros, Docker, WSL, Notion, AnythingLLM — somando 103 GB.
4. **Caminho fora da área permitida é ignorado**, mesmo que a chave seja válida.

Mais: a chave passa por `^[a-z0-9_]{1,32}$` (bloqueia `../`, `;`, `&`), a pasta raiz nunca é
removida — só esvaziada —, arquivo em uso é pulado sem travar, e há limite de 40 itens por chamada
e espera de 1,5 s entre ações.

---

## Onde cada arquivo fica

| O que | Caminho exato |
| --- | --- |
| O programa inteiro | `C:\Users\trcnologia\Desktop\monitoramento-pc\app.py` |
| Backup antes das mudanças | `C:\Users\trcnologia\Desktop\monitoramento-pc\app.py.bak-pre-disco` |
| Os testes | `C:\Users\trcnologia\Desktop\monitoramento-pc\tests\test_app.py` |
| Os portões de qualidade | `C:\Users\trcnologia\Desktop\monitoramento-pc\gates\G_*.py` |
| Histórico de leituras | `C:\Users\trcnologia\Desktop\monitoramento-pc\telemetry_log.jsonl` |
| Atalho na área de trabalho | `C:\Users\trcnologia\Desktop\Mission Control.lnk` |
| O que o atalho dispara | `C:\Users\trcnologia\Desktop\monitoramento-pc\mission_control_start.vbs` |
| Endereço do painel | `http://localhost:8989` — e a tela nova em `http://localhost:8989/disco` |

### Sobre o atalho `Mission Control.lnk`

**Funciona normalmente com a versão nova** — ele chama o `.vbs`, que por sua vez sobe o
`app.py` da mesma pasta. Como o arquivo foi editado no lugar, o atalho já carrega o código novo.

**Mas há um detalhe:** o `.vbs` só liga o servidor **se a porta 8989 estiver livre**. Se o
monitor antigo ainda estiver rodando, o atalho vai apenas abrir o navegador — e você verá a
versão velha, sem a tela `/disco`. Para trocar de versão, encerre o processo antigo primeiro:

```powershell
Get-NetTCPConnection -LocalPort 8989 -State Listen |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

Depois é só clicar no atalho normalmente.

---

## Verificação executada

| Verificação | Resultado |
| --- | --- |
| Suíte de testes | **57 passaram** (eram 28; 29 novos) |
| Gates de qualidade | **8 de 8 OK** |
| Rotas ponta a ponta | **14 checagens, todas OK** (exit 0) |
| Sintaxe | OK |

### Dois defeitos encontrados e corrigidos durante o uso real

1. **Chrome medindo zero.** O catálogo apontava para `User Data\Default\Cache`, mas esta máquina
   tem 24 perfis (`Profile 1`…`Profile 33`) e **nenhum `Default`**. Agora varre todos os perfis e
   cinco tipos de cache cada — 33 pastas, 1,76 GB que antes não apareciam.
2. **Relatório dizendo "0 GB" depois de liberar 3,35 GB.** Quando um arquivo está travado, o
   apagamento da subpasta falha no meio — mas já removeu parte. O total agora é medido por
   diferença (mediu antes, mediu depois), nunca pelo que se pretendia apagar.

Ambos estão travados por teste para não voltarem.

### 3. A tela `/disco` tinha um visual diferente do resto do app

Na primeira versão, usei um tema próprio ("GitHub escuro") em vez do visual do painel
principal, e usei a caixinha de confirmação do próprio navegador (aquela cinza, do sistema
operacional) em vez de um aviso desenhado pelo app. Reescrevi a tela inteira reaproveitando
**as mesmas cores, fontes, botões e cartões** já usados na tela principal — é o mesmo
arquivo de estilo, não uma cópia parecida — e troquei a confirmação pelo **modal que o
próprio Mission Control já usa** (o mesmo aviso que aparece, por exemplo, ao encerrar um
processo pesado). Resultado: parece a mesma casa, não duas telas de aplicativos diferentes.

Provado com um navegador de verdade rodando escondido (Chromium, via Playwright): abri a
página, cliquei em "marcar tudo que é seguro", cliquei em "Simular", cliquei no botão de
apagar e confirmei que **o aviso que aparece é o do próprio app** — nenhuma caixinha do
Windows/navegador chegou a disparar. Também confirmei que o botão de alternar tema e o
link de voltar para o painel principal funcionam.

Os testes novos cobrem: recusa de todos os 9 alvos `manual`, recusa de travessia de caminho
(`../../etc`, `..\..\windows`, `C:\`, `npm;rm`, `npm&del`), recusa de chave desconhecida e de lista
gigante, estrutura das respostas, e presença de explicação em todos os 27 itens.

O teste mais importante é o **canário**: cria arquivos reais, roda a simulação, e confirma que
continuam lá byte por byte. Depois roda com confirmação e verifica que saíram — e que a pasta raiz
sobreviveu.

---

## Como usar

```bash
cd C:\Users\trcnologia\Desktop\monitoramento-pc
python app.py
```

Depois abra `http://localhost:8989/disco`.

> Se o monitor já estiver rodando, **feche e abra de novo** — a instância antiga não tem as rotas novas.

Rotina sugerida, a cada duas semanas: abrir `/disco`, olhar o semáforo da memória virtual,
clicar em **Simular**, e limpar o que estiver verde.

---

## Arquivos alterados

| Arquivo | Mudança |
| --- | --- |
| `app.py` | +`disk_audit`, `disk_clean`, `parse_clean_keys`, `pagefile_health`, `HTML_DISCO`, 4 rotas |
| `tests/test_app.py` | +19 testes das proteções |
| `app.py.bak-pre-disco` | Backup do original |

---

## Ideias para depois

- Registrar o pico da memória virtual no `telemetry_log.jsonl`, para ver a tendência ao longo dos dias
- Alerta sonoro quando a memória virtual passar de 85%
- Contar quantos worktrees do Orca estão abertos e quanto cada um custa de memória
- Botão para mover a Biblioteca do Calibre para o `D:` (com confirmação, claro)

---

## Documentos relacionados

- [`11-09-2026_explica-pagefile-memoria-virtual.md`](11-09-2026_explica-pagefile-memoria-virtual.md) — por que o Orca fechava sozinho
- [`11-09-2026_explica-limpeza-de-disco.md`](11-09-2026_explica-limpeza-de-disco.md) — onde estão os 103 GB
