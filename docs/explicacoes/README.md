# Explicações

Diagnósticos e explicações técnicas em linguagem simples, a partir de problemas reais
desta máquina. Cada documento traz o sintoma, a causa medida, a correção aplicada e como
conferir por conta própria.

| # | Documento | Assunto |
| --- | --- | --- |
| 01 | [Pagefile e memória virtual](11-09-2026_explica-pagefile-memoria-virtual.md) | Por que o Orca fechava sozinho — e por que pagefile em HD externo não funciona |
| 02 | [Limpeza de disco](11-09-2026_explica-limpeza-de-disco.md) | Onde estão os 230 GB do `C:` e o que dá para recuperar sem perder nada |
| 03 | [Monitor Mission Control](11-09-2026_explica-monitor-mission-control.md) | A página `/disco`, os endpoints novos e as travas de segurança |

---

## Resumo de 2026-09-11

**Sintoma:** Orca fechando sozinho, vários erros, trabalho interrompido.

**Causa:** o pagefile de 64 GB estava configurado no `D:` — um **HD externo USB**. O Windows
não aceita pagefile em disco removível, então **nunca criou o arquivo**. Sobrou apenas o `C:`
com 8 GB fixos, dando um teto de 23,69 GB para 16 GB de RAM. Esse teto encheu (pico de
8191 de 8192 MB) e o Windows passou a negar memória para todos os programas.

**Correção:** pagefile fantasma do `D:` removido; `C:` passou de 8 GB fixos para 16 GB inicial
e 32 GB máximo. Teto vai de 23,69 GB para ~48 GB. **Exige reiniciar o computador.**

**Prevenção:** o monitor agora tem a página `/disco`, que avisa antes de estourar e detecta
sozinho o erro do pagefile fantasma.

**Limpeza executada às 21h**, com autorização explícita:

| Tarefa | Liberou |
| --- | --- |
| Grupo verde (cópias guardadas) | 16,63 GB em 199.688 arquivos |
| Modelos de IA do HuggingFace | 39,20 GB |
| Biblioteca do Calibre movida para `D:` | 21,63 GB (3206 de 3206 arquivos, zero falhas) |
| Pasta do LM Studio | 6,14 GB |

**`C:` foi de 52,1 GB para 136,6 GB livres — ganho de 84,5 GB.**
