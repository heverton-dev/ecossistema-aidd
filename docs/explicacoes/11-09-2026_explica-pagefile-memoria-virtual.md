# Pagefile (memória virtual): o que é, para que serve e por que o Orca fechava sozinho

> Registrado em 2026-09-11, a partir de um diagnóstico real nesta máquina.
> Sintoma que originou o documento: **"meu Orca está crashando, fechando sozinho, com vários erros"**.

---

## 1. A analogia: a mesa e a gaveta

Pense na memória do computador como uma **mesa de trabalho**:

- A **RAM** é o tampo da mesa. É rápida, mas pequena. Aqui ficam os papéis que você está usando agora.
- O **pagefile** é a **gaveta embaixo da mesa**. É lenta, mas grande. Quando o tampo enche, o Windows
  pega o que você não está olhando no momento e guarda na gaveta. Quando você precisa de novo, ele
  traz de volta.

O pagefile é um arquivo comum no disco, chamado `pagefile.sys`. Ele não é "sujeira" e **não precisa ser
limpo** — o Windows cria, usa e reaproveita sozinho, para sempre.

### O detalhe que quase ninguém sabe (e que causou o problema)

O Windows não espera o tampo encher para começar a contar. Quando um programa abre, ele **reserva** um
espaço, mesmo sem usar ainda. É como reservar cadeiras num restaurante: as pessoas ainda não chegaram,
mas as cadeiras já não estão disponíveis para outros.

A soma de tudo que foi reservado tem um teto:

```
teto total = RAM + pagefile
```

Esse teto é a conta que importa. **Quando ele estoura, o Windows começa a dizer "não" para todo mundo** —
e programas morrem na hora, sem aviso, sem tela de erro. Não é bug do programa. É falta de cadeira.

---

## 2. O que aconteceu nesta máquina

### Configuração encontrada

| O que | Valor |
| --- | --- |
| RAM instalada | 15,69 GB |
| Pagefile configurado em `C:` | 8192 MB fixo (8 GB) |
| Pagefile configurado em `D:` | 64000 MB (64 GB) |
| Pagefile **realmente ativo** | **somente o de `C:`** |
| Teto total resultante | **23,69 GB** |

### O erro escondido

O `D:` é o **HD externo USB Seagate Expansion de 6 TB**.

**O Windows não cria pagefile em disco USB ou removível.** Ele aceitou a configuração no registro, não
reclamou, e simplesmente **nunca criou o arquivo**. Verificação:

```
dir /a D:\pagefile.sys   ->  Arquivo não encontrado
```

Ou seja: os 64 GB existiam só no papel. Na prática só havia 8 GB de gaveta.

### A prova de que estourou

`PeakUsage` do pagefile de `C:`: **8191 MB de 8192 MB — 100% cheio.**

E o próprio Windows avisou, três vezes no mesmo dia:

| Hora | Evento (log do Windows, Id 26) |
| --- | --- |
| 08:37 | "Memória virtual insuficiente" |
| 16:14 | "Memória virtual insuficiente" |
| 19:13 | "Memória virtual insuficiente" |

Nos dias anteriores (08/09 e 10/09) a mensagem era **outra**: *"o Windows está aumentando o tamanho do
arquivo de paginação"*. Isso é comportamento de pagefile **gerenciado**, que cresce sozinho quando
aperta. Ao fixar em 8 GB, essa válvula de escape foi removida.

### Os crashes que vieram logo depois

| Hora | Programa | Código | Tradução |
| --- | --- | --- | --- |
| 16:17 | `dwm.exe` (interface gráfica do Windows) | `0xc00001ad` | Acabaram os recursos |
| 16:17 | `msedgewebview2.exe` | `0xe0000008` | Sem memória |
| 16:18 | **`Orca.exe` 1.4.200** | Id 1002 | Travou e foi fechado |
| 20:23 | `chrome.exe` | `0xe0000008` | Sem memória |
| 20:25 | `dwm.exe` | `0xc00001ad` | Acabaram os recursos |

Também apareceu no log, literalmente:
`"Não existem recursos de sistema suficientes para concluir o serviço solicitado"`.

### Por que o Orca foi o primeiro a cair

Não porque é frágil — porque é o que mais reserva. Na medição desta máquina, rodando normalmente:

| Programa | Processos | RAM |
| --- | --- | --- |
| `node` | 17 | 1475 MB |
| `Orca` | 8 | 1449 MB |
| `claude` | 3 | 1117 MB |
| `bash` | 28 | 272 MB |

Com **30 worktrees simultâneos**, cada um com seus processos, mais Photoshop e navegador, os 23,69 GB
acabam bem antes do fim do dia.

---

## 3. A correção aplicada

Registro em `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management`:

| | Antes | Depois |
| --- | --- | --- |
| `PagingFiles` | `c:\pagefile.sys 8192 8192`<br>`d:\pagefile.sys 64000 64000` (fantasma) | `C:\pagefile.sys 16384 32768` |
| Teto total | 23,69 GB | **~48 GB** |

Duas mudanças:

1. **Removido o pagefile fantasma do `D:`** — só ocupava lugar na configuração sem existir.
2. **`C:` passou de 8 GB fixos para 16 GB inicial / 32 GB máximo** — volta a ter margem para crescer.

> **Só passa a valer depois de reiniciar o computador.** Pagefile é montado no boot.

---

## 4. Perguntas diretas

### Preciso limpar o pagefile?

**Não. Nunca.** Ele se administra sozinho. Apagar não libera espaço de verdade — o Windows recria no
próximo boot. A única coisa que se ajusta é o **tamanho**.

### Qual o tamanho certo?

Regra prática: **no mínimo o dobro da RAM** para quem roda muita coisa ao mesmo tempo.

| RAM | Uso leve | Uso pesado (seu caso) |
| --- | --- | --- |
| 16 GB | 16 GB | **32 GB** |
| 32 GB | 16 GB | 48 GB |

### Posso pôr o pagefile no HD externo para poupar o `C:`?

**Não funciona.** Foi exatamente o que causou o problema. O Windows só aceita pagefile em **disco interno
fixo**. Num notebook com um SSD só, ele tem que ficar no `C:`.

### Como saber que vai estourar, antes de estourar?

Abrir `http://localhost:8989/disco` no monitor. A seção **Memória virtual** mostra o teto, o uso atual e
avisa em três níveis:

- **ok** — abaixo de 80%
- **atenção** — 80% a 90%: feche alguma coisa
- **crítico** — acima de 90%, ou pico já encostou em 95%: vai começar a fechar programa sozinho

Ela também detecta automaticamente o erro do "pagefile fantasma" — configurado mas nunca criado.

### E se mesmo assim estourar?

Em ordem de esforço:

1. Reduzir worktrees simultâneos do Orca (cada um custa memória real).
2. Fechar o navegador — Chrome sozinho estava com 10,57 GB só de cache em disco e é dos maiores
   consumidores de RAM.
3. Não usar Photoshop junto com carga pesada de worktrees.
4. Aumentar o máximo do pagefile — desde que sobre espaço no `C:`.
5. Trocar a RAM por 32 GB. É a solução definitiva; o resto é administração de escassez.

---

## 5. Onde cada coisa fica

| O que | Caminho exato |
| --- | --- |
| O arquivo de paginação em si | `C:\pagefile.sys` (oculto, protegido pelo sistema) |
| Onde o tamanho é configurado (registro) | `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management`, valor `PagingFiles` |
| A mesma coisa pela tela do Windows | `Win + R` → `sysdm.cpl` → aba **Avançado** → **Desempenho / Configurações** → aba **Avançado** → **Memória virtual / Alterar** |
| Onde ver os avisos de "memória virtual insuficiente" | `Win + R` → `eventvwr.msc` → Logs do Windows → **Sistema** → filtrar por origem `Application Popup`, Id 26 |
| Onde despejar o crash | `C:\WINDOWS\MEMORY.DMP` e `C:\Windows\Minidump` |
| O painel que vigia tudo isso | `http://localhost:8989/disco` |

> `C:\pagefile.sys` não aparece no Explorador nem com "itens ocultos" ligado — é preciso
> desmarcar também *"Ocultar arquivos protegidos do sistema operacional"* nas opções de pasta.
> Ver pelo terminal é mais simples: `dir /a C:\pagefile.sys`

---

## 6. Como conferir tudo isso você mesmo

```powershell
# Teto total e uso atual
$os = Get-CimInstance Win32_OperatingSystem
"Teto  : {0} MB" -f [math]::Round($os.TotalVirtualMemorySize/1KB,0)
"Livre : {0} MB" -f [math]::Round($os.FreeVirtualMemory/1KB,0)

# Pagefiles REALMENTE ativos (se algo configurado não aparecer aqui, é fantasma)
Get-CimInstance Win32_PageFileUsage |
  Select-Object Name, AllocatedBaseSize, CurrentUsage, PeakUsage

# O que está configurado no registro
(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management').PagingFiles

# Os avisos do Windows sobre memória virtual
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-Date).AddDays(-10)} |
  Where-Object { $_.Message -match 'mem.ria virtual' } |
  Select-Object TimeCreated, Id, Message
```

**O sinal mais importante:** se `PeakUsage` estiver perto de `AllocatedBaseSize`, o pagefile já encheu —
e programas já estão morrendo por isso, mesmo que você ainda não tenha ligado uma coisa à outra.

---

## Documentos relacionados

- [`11-09-2026_explica-limpeza-de-disco.md`](11-09-2026_explica-limpeza-de-disco.md) — onde o espaço do `C:` está indo e como recuperar
- [`11-09-2026_explica-monitor-mission-control.md`](11-09-2026_explica-monitor-mission-control.md) — o painel que vigia tudo isso
