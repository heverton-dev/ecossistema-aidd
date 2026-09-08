# Item 7 — Protótipo real: bootstrap de dependências (PyJWT/cryptography) no `compose_suite.py` (aidd-master)

> Evidência de reprodução real referenciada em `docs/planos/a-fazer/02-direcionamento-estrategico-anti-nih/07-bootstrap-de-dependencias-do-produto-gerado-por-ferramenta-forge-nao-eh-chamado-por-nenhuma-das-outras-4.md`.
> Data: 2026-09-07.

## Achado (antes da correção)

- `tools/aidd-master/scripts/compose_suite.py` gera `src/server.py` a partir de um template (`SERVER_TEMPLATE`) que **sempre** registra as rotas de SSO Corporativo (OAuth2/OIDC + PKCE): `/api/auth/oauth/login` e `/api/auth/oauth/callback`.
- A rota de callback chama `OIDCService.validate_id_token` (`templates/core/security.py:167-185`), que faz `import jwt` (PyJWT) e usa `jwt.algorithms.RSAAlgorithm` (que depende do pacote `cryptography`) para validar o `id_token` via JWKS/RS256.
- O `requirements.txt` gerado em `compose_suite.py:1833-1838` (antes da correção) só continha `pytest`, `mutmut`, `requests` (+ `psycopg2-binary` condicional a `--db postgres`). Nunca incluía `pyjwt`/`cryptography`.
- Consequência real: qualquer empresa que configure as variáveis `OIDC_*` (o próprio server gerado documenta isso como "Zero Fricção") recebe `RuntimeError("PyJWT não instalado...")` ao tentar logar via SSO — não é hipotético, é o comportamento do código antes da correção.

## Correção aplicada

`tools/aidd-master/scripts/compose_suite.py`, bloco de geração de `requirements.txt` (~linha 1833): `pyjwt>=2.8.0` e `cryptography>=42.0.0` passam a ser incluídos de forma **incondicional** (a rota SSO é sempre registrada em todo produto composto por essa ferramenta).

Teste de regressão adicionado: `tools/aidd-master/tests/unit/test_compose_suite.py::test_requirements_gerado_inclui_pyjwt_e_cryptography`.

## Reprodução real — passo a passo

Isolado em pastas temporárias fora do repositório (`%TEMP%\...\scratchpad\item7-proto\`), sem poluir arquivos de produção.

### 1. Gerar produto "antes" (código original, via `git stash` do único arquivo alterado)

```
python compose_suite.py <tmp>/antes "TesteBootstrap" vendas --db sqlite
```

`requirements.txt` resultante:
```
pytest>=7.4.0
mutmut>=2.4.0
requests>=2.31.0
```

### 2. Gerar produto "depois" (com a correção aplicada)

```
python compose_suite.py <tmp>/depois "TesteBootstrap" vendas --db sqlite
```

`requirements.txt` resultante:
```
pytest>=7.4.0
mutmut>=2.4.0
requests>=2.31.0
pyjwt>=2.8.0
cryptography>=42.0.0
```

### 3. `pip install` real em venvs limpos e isolados

```
python -m venv venv-antes && venv-antes/Scripts/python -m pip install -r antes/requirements.txt
python -m venv venv-depois && venv-depois/Scripts/python -m pip install -r depois/requirements.txt
```

- `venv-antes`: `pip list` confirma ausência de `pyjwt`/`cryptography` (só `pytest`, `requests`).
- `venv-depois`: `pip list` confirma `PyJWT==2.13.0` e `cryptography==50.0.1` instalados de fato (não só declarados).

### 4. Teste funcional real — token RS256 genuíno via JWKS

Gerado um par de chaves RSA + `id_token` assinado (RS256) de verdade com `cryptography`/`PyJWT` (`gerar_token.py`, rodado uma vez no `venv-depois`), salvo em JSON puro. Depois, `testar_oidc.py` carrega esse JSON (sem precisar de `jwt`/`cryptography` para o carregamento) e chama `OIDCService.validate_id_token(...)` — exatamente o que a rota `/api/auth/oauth/callback` do `server.py` gerado faz em produção.

**Resultado no `venv-antes` (projeto "antes", sem a correção):**
```
VALIDATE_RUNTIME_ERROR: PyJWT não instalado. Para SSO OIDC, instale: pip install pyjwt cryptography
```

**Resultado no `venv-depois` (projeto "depois", com a correção):**
```
VALIDATE_OK: {'iss': 'https://sso.exemplo.com', 'aud': 'cliente-teste', 'sub': 'usuario@exemplo.com', 'groups': ['admin']}
```

A dependência está de fato instalada, e a funcionalidade que dependia dela (validação real de token RS256 via JWKS) funciona de ponta a ponta — não é apenas um arquivo copiado ou uma linha adicionada a um manifesto.

## Gates rodados

- `tools/aidd-master`: `python -m pytest` → **215 passed, 4 skipped, 0 failed** (era 214 passed antes; +1 é o teste de regressão novo, `test_requirements_gerado_inclui_pyjwt_e_cryptography`).
- `tools/aidd-master`: `python scripts/aidd.py audit` (bateria completa: G_ESTRUTURA, G_QUALIDADE, G_TESTES, G_CONTRACTS, G_SEGREDOS, G_HARNESS_COMPAT, G_SEGURANCA) → **REPROVADO no consolidado (6/7 gates OK)**, mas a única falha é **pré-existente e não relacionada** a este item:
  - `G_ESTRUTURA`: 22/23 validações OK; falha em "Manifesto `PLANO-EXECUCAO-ESTRUTURADO.json` ausente na raiz" — **confirmado via `git stash` que essa falha ocorre de forma idêntica com e sem a correção deste item** (esse manifesto é gerado apenas em *produtos compostos*, não existe nem existia no repositório-fonte da própria ferramenta `aidd-master`; não é gerado nem afetado por `compose_suite.py`).
  - `G_QUALIDADE`: OK (aviso não-bloqueador de "177 crashes" no fuzzing contínuo de APIs — pré-existente, fuzzing genérico do harness, não relacionado a `compose_suite.py`/`security.py`).
  - `G_TESTES`: OK — 215 passed, 4 skipped, 0 failed.
  - `G_CONTRACTS`, `G_SEGREDOS`, `G_HARNESS_COMPAT`: OK.
  - `G_SEGURANCA`: OK — inclui "Camada 8: CVE Dependency Audit" com **"Nenhuma vulnerabilidade HIGH/CRITICAL encontrada em requirements.txt"**, confirmando que adicionar `pyjwt`/`cryptography` não introduziu risco conhecido. Score 88.9% (nota A+).
- `python ecossistema.py audit` (gate global do ecossistema): **G_ECOSSISTEMA_INTEGRIDADE** e **G_INFRA_COMPOSE** aprovados; **G_TESTES_REAIS** reprovado, mas por falhas **pré-existentes e não relacionadas** a este item — `aidd-generator` (2 failed) e `aidd-ops` (8 failed). `aidd-master` (ferramenta onde este protótipo foi feito) está 100% verde nos testes reais (0 failed). As falhas de generator/ops pertencem a outros itens do plano tático (`docs/planos/correcao-pos-auditoria-sem-maquiagem/`), fora do escopo deste item 7.

**Conclusão sobre gates:** nenhum gate falha por causa da correção deste item. As duas falhas encontradas (G_ESTRUTURA local do aidd-master, G_TESTES_REAIS global) são pré-existentes, reproduzidas como já presentes antes da mudança, e pertencem a outros itens do plano — não bloqueiam a Definição de Pronto deste item 7.
