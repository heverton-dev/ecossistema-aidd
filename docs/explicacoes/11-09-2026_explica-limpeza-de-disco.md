# Limpeza de disco: onde cada coisa fica, com o caminho completo

> Auditoria real em 2026-09-11. Números medidos, não estimados.
> **Todos os caminhos abaixo são os reais desta máquina**, verificados um a um.

---

## Regra inviolável

> **Nada é removido sem permissão explícita.**

Não é só combinado — está **escrito no código** e coberto por **31 testes automáticos**:

- por padrão a limpeza roda em **modo ensaio**: mostra o que sairia e não tira nada;
- só apaga os itens que você **marcar um por um**;
- **recusa** os itens marcados como `manual`, **mesmo se mandarem confirmar**;
- recusa qualquer pasta fora das áreas permitidas.

---

## Como ler um caminho do Windows

Três atalhos aparecem o tempo todo. Todos apontam para dentro da sua pasta pessoal,
`C:\Users\trcnologia`:

| Atalho | Caminho de verdade | O que guarda |
| --- | --- | --- |
| `%LOCALAPPDATA%` | `C:\Users\trcnologia\AppData\Local` | Coisas **desta máquina só**: cópias guardadas, programas instalados por você |
| `%APPDATA%` | `C:\Users\trcnologia\AppData\Roaming` | Configurações e dados que acompanhariam seu usuário |
| `%TEMP%` | `C:\Users\trcnologia\AppData\Local\Temp` | Rascunhos descartáveis |

A pasta `AppData` é **oculta**. Para chegar nela: aperte `Win + R`, cole o caminho e dê Enter.
Funciona também colar na barra de endereço do Explorador de Arquivos.

---

## O estado ANTES (2026-09-11, 20h)

`C:` com 455 GB, **apenas 52 GB livres**.

### 🟢 SEGURO — cópias guardadas, 23,5 GB

Some e o próprio programa baixa de novo. Você não perde nada.

| Item | GB | **Caminho completo** |
| --- | --- | --- |
| Cache do npm | 10,72 | `C:\Users\trcnologia\AppData\Local\npm-cache` |
| Cache do uv | 6,75 | `C:\Users\trcnologia\AppData\Local\uv` |
| Cache do pip | 1,95 | `C:\Users\trcnologia\AppData\Local\pip\Cache` |
| Cache do Chrome | 1,76 | `C:\Users\trcnologia\AppData\Local\Google\Chrome\User Data\<perfil>\Cache` * |
| Temporários do usuário | 1,06 | `C:\Users\trcnologia\AppData\Local\Temp` |
| Cache do Electron | 0,47 | `C:\Users\trcnologia\AppData\Local\electron` |
| Cache do Edge | 0,27 | `C:\Users\trcnologia\AppData\Local\Microsoft\Edge\User Data\<perfil>\Cache` * |
| Cache do electron-builder | 0,24 | `C:\Users\trcnologia\AppData\Local\electron-builder` |
| Temporários da Adobe | 0,22 | `C:\adobeTemp` |
| Relatórios de travamento | 0,07 | `C:\Users\trcnologia\AppData\Local\CrashDumps` |
| Temporários do Windows | 0,01 | `C:\WINDOWS\Temp` |
| Instaladores do Windows Update | ~0 | `C:\WINDOWS\SoftwareDistribution\Download` |
| Relatórios de erro do Windows | ~0 | `C:\ProgramData\Microsoft\Windows\WER` |
| Cache de testes | ~0 | `C:\Users\trcnologia\Desktop\monitoramento-pc\.pytest_cache` |

\* **Atenção ao `<perfil>`:** esta máquina tem **24 perfis do Chrome**, chamados `Profile 1` até
`Profile 33` — e **nenhum chamado `Default`**. Cada perfil tem cinco pastas de cópias guardadas
(`Cache`, `Code Cache`, `GPUCache`, `DawnCache`, `ShaderCache`), num total de **33 pastas**.
A ferramenta varre todas. Exemplo real:
`C:\Users\trcnologia\AppData\Local\Google\Chrome\User Data\Profile 11\Code Cache`

Isso **não** apaga senha, histórico, favorito nem aba aberta — só as páginas guardadas
para carregar mais rápido.

### 🟡 CUIDADO — 5,3 GB

Voltam sozinhos, mas custam download.

| Item | GB | **Caminho completo** | Observação |
| --- | --- | --- | --- |
| Depósito do pnpm | 2,05 | `C:\Users\trcnologia\AppData\Local\pnpm` | ⚠️ Projetos já instalados **apontam para cá**. Prefira `pnpm store prune` |
| Navegadores do Playwright | 1,35 | `C:\Users\trcnologia\AppData\Local\ms-playwright` | Volta com `playwright install` |
| Cache do OpenCode | 0,96 | `C:\Users\trcnologia\.cache\opencode` | Refaz no próximo uso |
| Navegadores do Puppeteer | 0,94 | `C:\Users\trcnologia\.cache\puppeteer` | Rebaixa no próximo uso |

### 🔴 MANUAL — 103,2 GB — a ferramenta nunca apaga

| Item | GB | **Caminho completo** | Como reduzir com segurança |
| --- | --- | --- | --- |
| Modelos de IA (HuggingFace) | 39,20 | `C:\Users\trcnologia\.cache\huggingface\hub` | Apagar pasta a pasta; cada modelo é uma pasta `models--Autor--Nome` |
| Biblioteca do Calibre | 21,63 | `C:\Users\trcnologia\Biblioteca do calibre` | Mover para o HD externo |
| AnythingLLM | 9,23 | `C:\Users\trcnologia\AppData\Roaming\anythingllm-desktop` | Remover documentos pelo próprio aplicativo |
| Docker | 7,24 | `C:\Users\trcnologia\AppData\Local\Docker` | `docker system prune -a` — **nunca** apague a pasta |
| Gemini CLI | 6,15 | `C:\Users\trcnologia\.gemini` | Revisar manualmente |
| LM Studio | 6,14 | `C:\Users\trcnologia\.lmstudio` | Remover modelos pelo próprio LM Studio |
| Notion | 5,42 | `C:\Users\trcnologia\AppData\Roaming\Notion` | Limpar pelo próprio Notion |
| WSL (Linux) | 5,27 | `C:\Users\trcnologia\AppData\Local\wsl` | Apagar **destrói suas distribuições Linux** |
| DICloak | 2,96 | `C:\.DICloakCache` | Limpar pelo próprio aplicativo |

---

## O que foi executado em 2026-09-11, às 21h

Com autorização explícita, quatro tarefas:

### 1. Grupo verde limpo — 16,63 GB, 199.688 arquivos

Todos os 14 itens 🟢. Três ficaram parciais porque estavam **em uso naquele momento**
(a ferramenta pula arquivo travado em vez de forçar):

| Item | Liberou | Observação |
| --- | --- | --- |
| Cache do npm | 10,72 GB | 165.817 arquivos |
| Cache do pip | 1,95 GB | |
| Cache do Chrome | 1,76 GB | 21.474 arquivos, 33 pastas |
| Temporários do usuário | 1,02 GB | 11 arquivos em uso, pulados |
| Cache do uv | ~3,35 GB | **parcial** — 4 processos `uv`/`uvx` rodando seguravam 3,40 GB |

### 2. Modelos de IA removidos — 39,20 GB

`C:\Users\trcnologia\.cache\huggingface\hub` — 178 arquivos. Os maiores eram:

| Modelo | GB |
| --- | --- |
| `models--HumeAI--tada-codec` | 9,99 |
| `models--HumeAI--tada-3b-ml` | 8,26 |
| `models--Qwen--Qwen3-TTS-12Hz-1.7B-Base` | 4,23 |
| `models--ResembleAI--chatterbox` | 2,99 |
| `models--Qwen--Qwen3-TTS-12Hz-0.6B-Base` | 2,98 |
| `models--microsoft--llmlingua-2-xlm-roberta-large-meetingbank` | 2,10 |
| vários `whisper` (transcrição de áudio) | ~6,00 |

Todos são rebaixáveis de `huggingface.co` quando forem necessários de novo.

### 3. Biblioteca do Calibre movida — 21,63 GB

```
DE : C:\Users\trcnologia\Biblioteca do calibre
PARA: D:\Biblioteca do calibre
```

**3206 de 3206 arquivos, 1198 pastas, zero falhas**, a 63 MB/s. O índice
`D:\Biblioteca do calibre\metadata.db` (4,1 MB) chegou íntegro.

> **Ao abrir o Calibre**, ele vai reclamar que não acha a biblioteca. Clique em
> **Biblioteca de calibre → Trocar/criar biblioteca** e aponte para `D:\Biblioteca do calibre`.
> E lembre: o `D:` é o HD externo — com ele desconectado, a biblioteca não abre.

### 4. LM Studio removido — 6,14 GB

`C:\Users\trcnologia\.lmstudio`, 4388 arquivos (modelos 3,11 GB + extensões 2,63 GB).
O LM Studio **não estava instalado como programa** — não havia nada em
`AppData\Local\Programs` nem registro de desinstalação. Existia só essa pasta de dados.

---

## O resultado

| | Antes | Depois |
| --- | --- | --- |
| **Livre no `C:`** | **52,1 GB** | **136,6 GB** |

**Ganho: 84,5 GB.** De 11% para 30% do disco livre.

O que ainda resta mapeado: 3,56 GB 🟢 (o cache do `uv` travado e o que já voltou a acumular),
5,30 GB 🟡 e 36,27 GB 🔴.

---

## Como repetir isso sozinho

1. Abra `http://localhost:8989/disco`
2. Clique em **"Marcar tudo que é seguro"** — marca só o 🟢, nunca o 🔴
3. Clique em **"Simular"** — mostra o que sairia. **Nada é apagado aqui**
4. Conferiu? Clique no botão vermelho e confirme

Pela linha de comando, com as mesmas travas:

```bash
curl "http://localhost:8989/api/disk-audit"                              # só lê
curl "http://localhost:8989/api/disk-clean?itens=npm,pip,uv"             # ensaio
curl "http://localhost:8989/api/disk-clean?itens=npm,pip,uv&confirmar=1" # executa
curl "http://localhost:8989/api/disk-clean?itens=huggingface&confirmar=1" # RECUSADO
```

Para ver uma pasta com os próprios olhos antes de decidir: `Win + R`, cole o caminho, Enter.

---

## Comandos que a ferramenta deliberadamente não executa

Mexem em estado de aplicativo — rode você, conscientemente:

```bash
docker system prune -a     # imagens e containers do Docker
pnpm store prune           # só o que nenhum projeto usa mais
npm cache clean --force    # mesma coisa que o item npm, pela via oficial
```

---

## Documentos relacionados

- [Pagefile e memória virtual](11-09-2026_explica-pagefile-memoria-virtual.md)
- [Monitor Mission Control](11-09-2026_explica-monitor-mission-control.md)
