# PROTOCOLO PERMANENTE DE AGNOSTICIDADE DE COMPONENTES

> **Documento Canônico de Governança:** `docs/protocolos/PROTOCOLO-AGNOSTICIDADE-COMPONENTES.md`  
> **Origem:** Seção 5 de `docs/planos/PLANO-CORRECAO-SKILLS-AGNOSTICAS.md`  
> **Vínculo Normativo:** Regra de Ouro #6 de `AGENTS.md` (Supremacia Agnóstica)  
> **Status:** PRODUÇÃO & AUDITADO DETERMINISTICAMENTE (`gates/G_COMPONENTE_AGNOSTICO.py`)  
> **Escopo:** Todo e qualquer componente adicionado ou modificado no ecossistema (skills, specs, MCPs, arquivos de configuração, hooks, comandos, subagentes e scripts), na raiz ou em qualquer subprojeto sob `tools/*`.

---

## 1. DEFINIÇÃO DE "AGNOSTICIDADE" NO ECOSSISTEMA AIDD

Um componente só é considerado agnóstico se atender simultaneamente a quatro independências:

1. **Independência de Stack de Tecnologia:**
   - A mecânica de descoberta, registro e injeção do componente (onde ele é procurado, como é lido e materializado) não pode presumir uma linguagem, framework ou ferramenta proprietária.
   - Conteúdo de negócio de uma spec ou módulo pode ser específico de uma tecnologia por necessidade do domínio; a forma como ela é localizada, versionada e distribuída no monorepo, nunca.

2. **Independência de Harness (Multi-Harness):**
   - O componente deve existir fisicamente e com conteúdo byte-idêntico em todo diretório de harness que o manifesto (`gates/manifesto_harnesses.json`) declarar como aplicável para o seu tipo:
     - Claude Code (`.claude/`)
     - Antigravity / OpenCode / MimoCode (`.agent/`)
     - Gemini CLI (`.gemini/`)
     - Destinos adicionais sem harness (`skills/`, `.skills/`).
   - Nenhuma pasta de harness pode ser deixada desatualizada ou ausente.

3. **Independência de Ambiente de Programação:**
   - Zero dependência de uma IDE ou editor específico para o componente ser descoberto ou executado.
   - Cursor IDE consome regras via `.cursor/rules/aidd.md` apontando para a governança canônica.

4. **Independência de Sistema Operacional:**
   - Nenhum caminho hardcoded com separador de um único SO (`/` vs `\`); use sempre `pathlib.Path` ou `os.path.join`.
   - Nenhuma dependência de symlinks reais que quebrem em ambientes sem privilégios elevados (como Windows sem Developer Mode ativado) — propagação sempre por cópia física com garantia de idempotência.
   - Nenhum comando de shell proprietário ou vendor-locked sem alternativa universal em Python.

---

## 2. CHECKLIST OBRIGATÓRIO DE CRIAÇÃO E ATUALIZAÇÃO

Antes de considerar qualquer componente concluído ou pronto para commit, execute rigorosamente os 6 passos abaixo:

```text
[ ] 1. Identificar o tipo do componente (skill, mcp, spec, config, command, hook, sub-agent, script)
       e verificar suas regras de distribuição em 'gates/manifesto_harnesses.json'.

[ ] 2. Materializar o componente EXCLUSIVAMENTE dentro de sua pasta canônica na fonte única:
       componentes/<ferramenta ou compartilhado>/<pasta_fonte>/<nome>/...

[ ] 3. Executar a sincronização multi-harness via CLI:
       python ecossistema.py components sync --tipo <tipo> [--ferramenta <nome>]

[ ] 4. Validar que nenhuma pasta de harness declarada no manifesto ficou ausente ou divergente:
       python ecossistema.py components verify --tipo <tipo> [--ferramenta <nome>]
       (Exit code 0 estrito obrigatório).

[ ] 5. Checar hardcodes que quebram agnosticidade no código do componente:
       - Caminhos absolutos ou literais com separador fixo de SO.
       - Nomes de harness como condição de funcionamento interno do componente.
       - Dependências não documentadas ou proprietárias.

[ ] 6. Rodar a bateria completa de auditoria do meta-repositório:
       python ecossistema.py audit
       (Todos os 6 Quality Gates devem ser aprovados com exit code 0).
```

---

## 3. AUDITORIA AUTOMATIZADA EM CI / GATES

A conformidade deste protocolo é validada de forma binária e determinística pelo Quality Gate:
- `gates/G_COMPONENTE_AGNOSTICO.py`: Roda a verificação multi-harness sobre todos os componentes tocados no diff do commit, falhando imediatamente (`exit 1`) se qualquer pasta de harness estiver ausente ou divergente da fonte canônica.