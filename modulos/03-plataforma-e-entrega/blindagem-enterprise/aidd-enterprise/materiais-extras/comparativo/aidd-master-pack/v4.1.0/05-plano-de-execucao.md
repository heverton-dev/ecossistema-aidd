# Manifesto de Plano de Execução — AIDD Master Pack v4.1.0

> **Tag documentada:** `v4.1.0` (commit `1daf757`, 31/08/2026)

---

## 1. Declaração Direta: Esta Tag NÃO Gera o Manifesto Automaticamente

Diferente de versões posteriores do framework (v5.x, que possuem um comando explícito `aidd.py plan` produzindo um `PLANO-EXECUCAO-ESTRUTURADO.json` com esquema formal e rico), **nenhum dos 4 scripts presentes no snapshot da tag `v4.1.0`** (`scripts/aidd.py`, `scripts/provision_project.py`, `scripts/add_module.py`, `scripts/compose_suite.py`) contém lógica para **criar** esse arquivo. Uma busca no código-fonte confirma que o único ponto de contato do CLI com `PLANO-EXECUCAO-ESTRUTURADO.json` é em **leitura**, dentro de `cmd_status()` em `scripts/aidd.py`:

```python
def cmd_status(args):
    print("[AIDD STATUS] Inspecionando saude do projeto modular...")
    import json
    if os.path.exists("PLANO-EXECUCAO-ESTRUTURADO.json"):
        with open("PLANO-EXECUCAO-ESTRUTURADO.json", "r", encoding="utf-8") as f:
            plano = json.load(f)
        print(f"Projeto: {plano.get('projeto', {}).get('nome')} (v{plano.get('projeto', {}).get('versao')})")
        print(f"Status: {plano.get('projeto', {}).get('status')}")
        ...
```

Ou seja: `python scripts/aidd.py status` **espera** que o arquivo já exista, mas nenhum comando desta tag o produz. Se ele não existir, `status` simplesmente pula esse bloco e segue para listar os diretórios de `src/modules` (se existirem).

## 2. Como o Arquivo Realmente Aparece nos Exemplos desta Tag

Apenas **5 dos 13 projetos de exemplo** do diretório `examples/` desta tag possuem um `PLANO-EXECUCAO-ESTRUTURADO.json`:

- `catalogo-digital-v3/`
- `catalogo-digital-whatsapp/`
- `plataforma-de-membros/`
- `plataforma-membros-v3/`
- `plataforma-modular-assinaturas/`

Os outros 8 exemplos (`crm-omnichannel-v2/v3`, `erp-financeiro-v2/v3`, `helpdesk-sla-v2/v3`, `enterprise-suite-v4`, `logistica-hub-v4`) **não têm** esse arquivo. Isso confirma que o manifesto, nesta versão do framework, é um **artefato opcional produzido manualmente pelo agente de IA durante a fase de planejamento em linguagem natural** (documentado nas regras `templates/rules/02_golden_rules.md`, que menciona "reiniciar sessões usando o Plano JSON"), e não um output determinístico e obrigatório de um script.

## 3. Esquema Observado — Sem Padronização Formal

Comparando os 5 exemplos existentes, os campos usados **variam de projeto para projeto**, evidenciando que não há um JSON Schema validado nesta tag (não existe gate `G_CONTRACTS` ou equivalente que valide a estrutura do manifesto). Exemplo real de `examples/catalogo-digital-v3/PLANO-EXECUCAO-ESTRUTURADO.json`:

```json
{
  "projeto": {
    "nome": "catalogo-digital-e",
    "descricao": "Catalogo Digital e Loja com Checkout WhatsApp e Painel Admin",
    "arquitetura": "AIDD 4 Camadas",
    "zero_api_key_mode": true,
    "status": "INICIALIZADO"
  },
  "fases": [
    {
      "id": "fase-01-analise",
      "nome": "Analise e Modelagem de Contratos",
      "status": "PENDENTE",
      "mesa_orca": "mesa-analise",
      "expected_outputs": ["docs/ARQUITETURA.md"]
    }
  ]
}
```

Já `examples/plataforma-modular-assinaturas/PLANO-EXECUCAO-ESTRUTURADO.json` usa um conjunto de campos diferente, com `versao`, `dual_database`, `openapi_swagger`, `docker_ready` e `modulos_instalados`, ausentes no exemplo do catálogo digital:

```json
{
  "projeto": {
    "nome": "plataforma-de-assinaturas",
    "descricao": "Plataforma de Assinaturas e Cursos Modular",
    "versao": "2.0.0",
    "arquitetura": "AIDD Modular Data-Driven",
    "dual_database": true,
    "openapi_swagger": true,
    "docker_ready": true,
    "status": "INICIALIZADO"
  },
  "modulos_instalados": ["core"],
  "fases": [
    {
      "id": "fase-01-core-setup",
      "nome": "Configuracao do Core, Dual Database e EventBus",
      "status": "CONCLUIDO",
      "expected_outputs": ["src/core/database.py", "src/core/events.py", "src/core/openapi.py"]
    }
  ]
}
```

### 3.1 Campos observados (união entre os 5 exemplos, nenhum obrigatório de fato)

| Campo | Presente em todos os 5? | Observação |
| :--- | :---: | :--- |
| `projeto.nome` | Sim | Único campo consistentemente presente e lido por `cmd_status()`. |
| `projeto.descricao` | Sim | Texto livre. |
| `projeto.status` | Sim | Valores livres observados: `"INICIALIZADO"`. Sem enum fixo, sem validação. |
| `projeto.versao` | Não | Só aparece em `plataforma-modular-assinaturas`. `cmd_status()` tenta ler `versao` mas ela não existe na maioria dos exemplos (retorna `None`). |
| `projeto.arquitetura` | Sim (texto varia) | `"AIDD 4 Camadas"` em um exemplo, `"AIDD Modular Data-Driven"` em outro. |
| `projeto.zero_api_key_mode` / `dual_database` / `openapi_swagger` / `docker_ready` | Não | Flags booleanas ad-hoc, diferentes por projeto — não há um conjunto fixo de flags. |
| `modulos_instalados` | Não | Só em `plataforma-modular-assinaturas`. Não é lido por `cmd_status()` (que prefere listar `src/modules` do disco). |
| `fases[].id` / `.nome` / `.status` / `.expected_outputs` | Sim (estrutura similar) | Padrão mais consistente entre os exemplos: uma lista de fases com id, nome, status (`PENDENTE`/`CONCLUIDO`) e outputs esperados. |
| `fases[].mesa_orca` | Não | Só aparece em `catalogo-digital-v3`/`catalogo-digital-whatsapp`, referenciando a mesa de trabalho ORCA responsável pela fase. |

## 4. Como o Planejamento de Execução Funciona de Fato Nesta Versão

Na ausência de um comando dedicado, o planejamento em `v4.1.0` funciona por **convenção documental**, não por automação:

1. O agente de IA (Claude/Cursor/etc.), seguindo as instruções do `SKILL.md` e dos arquivos `CLAUDE.md`/`AGENTS.md`/`.cursorrules` presentes em cada projeto, conversa em linguagem natural com o usuário sobre o escopo.
2. Opcionalmente, o agente redige à mão um `PLANO-EXECUCAO-ESTRUTURADO.json` com fases livres (não há template/gerador oficial desta tag para isso), seguindo o hábito observado nos 5 exemplos que o possuem.
3. O agente então invoca as ferramentas determinísticas reais desta tag para executar o plano: `python scripts/aidd.py init`, `add-module`, `audit`, `test`, `deploy`.
4. `python scripts/aidd.py status` pode ser chamado a qualquer momento para reler esse JSON (se existir) e reportar nome/versão/status do projeto e a lista de módulos presentes em `src/modules`.

## 5. Conclusão

O manifesto `PLANO-EXECUCAO-ESTRUTURADO.json` nesta tag é **um hábito de convenção adotado em parte dos exemplos, não um recurso automatizado do framework**. Ele não possui schema formal, não é gerado por nenhum script, é lido apenas parcialmente (só `projeto.nome`, `projeto.versao` e `projeto.status`) pelo único comando que o consome (`aidd.py status`), e sua estrutura de campos difere de projeto para projeto. A padronização e automação completa desse manifesto (comando `plan` dedicado, schema fixo, geração determinística) é uma característica de versões posteriores do framework, fora do escopo desta tag.
