# Template de Auditoria de Ferramenta (Lens 15-D) - INICIAL (Fase 1: Inspetor)

> **Ferramenta Auditada:** `tools/aidd-bridge`  
> **Ciclo de Auditoria:** Ciclo 02  
> **Data:** 2026-09-29  
> **Status:** AUDITADO / ÍNTEGRO (Aprovado na Fase 1)  
> **Papel:** Inspetor (Fase 1 do Pipeline 4F)  
> **Padrão de Governança:** Lens 15-D (The Agentic Anatomical Matrix)

---

## 1. Identificação da Ferramenta

- **Nome da Ferramenta:** `aidd-bridge`
- **Descrição Breve:** Motor do FLUXO 03 (Freedom) para extração, unificação e empacotamento de aplicações Low-Code (Lovable, v0, Bolt) para infraestrutura própria em VPS via Docker Swarm/Compose, com conversão determinística de Supabase para PostgreSQL corporativo, preservação da camada visual de interface e entrega dinâmica do Quarteto Sine Qua Non (`/swagger`, `/webhooks`, `/mcp`, `/docs`).
- **Comando de Gatilho:**
  - CLI Específico: `python ecossistema.py bridge <scan|convert-db|merge|pack|migrate-auth|destroy|unpack>`
  - Slash Command Específico: `/bridge <comando>`
  - CLI Fluxo Tríade Completo: `python ecossistema.py freedom [pasta] [nome]` ou `python ecossistema.py run-fluxo --fluxo freedom <args>`
  - Slash Command Fluxo Completo: `/freedom <export>`

---

## 2. A Matriz Anatômica (Lens 15-D)

### Fase 1: Governança e Blindagem

- **D1. Contratos e Regras:**
  - Subordinação às Leis Invioláveis do ecossistema:
    - **Lei #1 (Determinismo First):** 100% de automação determinística via regex, AST e templates Jinja/f-strings. Zero uso de LLM para tarefas mecânicas de análise, conversão SQL ou empacotamento.
    - **Lei #2 (Qualidade Binária):** Verificação através de testes automatizados e portões dedicados.
    - **Lei #5 (Zero Stubs / Zero Mocks):** 64 testes unitários e de integração reais passando em 3.36s (`pytest tools/aidd-bridge/tests`).
    - **Lei #6 (Agnóstico):** Entrega padronizada em contêineres OCI com suporte a Docker Compose e Docker Swarm com Traefik.
    - **Lei #10 (Quarteto Sine Qua Non Dinâmico):** Geração mandatória dos 4 contratos canônicos em `quarteto_sine_qua_non/`.
  - Contratos documentados em `tools/aidd-bridge/AGENTS.md` e sincronizados nas skills `componentes/compartilhado/skills/aidd-bridge/SKILL.md` e `aidd-freedom/SKILL.md`.

- **D2. Input e Gatilhos:**
  - CLI com `argparse` em `tools/aidd-bridge/aidd_bridge/cli.py` estruturado em 7 subcomandos explícitos:
    - `scan <projeto>`: Análise estrutural estática e geração de `bridge-manifest.json`.
    - `convert-db <migracoes>`: Transpilação e unificação de migrações Supabase em `init-db.sql`.
    - `merge <apps...>`: Unificação multi-app em fatias modulares VSA.
    - `pack <projeto>`: Geração de `Dockerfile`, `docker-compose.yml`, `nginx.conf` e scripts de deploy.
    - `migrate-auth`: Migração segura de credenciais e hashes bcrypt de `auth.users` (modo preview por padrão; escrita apenas sob `--apply`).
    - `destroy`: Limpeza completa de infraestrutura na VPS, volumes e DNS (exige confirmação explícita ou flag `--yes`).
    - `unpack`: Execução ponta a ponta do pipeline determinístico de libertação em 6 fases.
  - Validação estrita de existência de diretórios de entrada com mensagens de erro claras (`exit 1` sob caminhos inexistentes).

- **D3. Raio de Impacto e Isolamento:**
  - O código-fonte de origem é mantido estritamente em modo leitura; todas as transformações e saídas são gravadas no diretório de destino (`--output`).
  - Geração segura de variáveis de ambiente em `.env.production` com segredos criptograficamente seguros gerados deterministicamente via módulo padrão `secrets` do Python.
  - Rede isolada de containers (redes internas segregadas de bancos de dados versus rede pública do proxy reverso Traefik).
  - Trava de segurança no comando destrutivo `destroy` prevenindo deleções acidentais sem autorização humana expressa.

- **D4. Componentes e Fractalidade:**
  - Componentes internos segregados em módulos especializados de responsabilidade única:
    - `LovableScanner`: Varredura estática de rotas, páginas e migrações.
    - `DataBridge` e `SQLTranspiler`: Engenharia reversa e transpilação de SQL proprietário para PostgreSQL padrão.
    - `FrontendLiberator`: Limpeza de referências de clientes proprietários `@supabase/supabase-js`.
    - `DevOpsPackager`: Geração de manifestos OCI, configuração Nginx OWASP e stack Swarm.
    - `BridgeVSAExporter`: Geração dos 4 artefatos do Quarteto Sine Qua Non.
    - `AuthMigrator`: Migração de instâncias de autenticação GoTrue/Supabase.
    - `CloudflareDNSAutomation`: Gerenciamento automatizado de registros DNS.
  - Conexão e handoff para `aidd-master` para agregação no Monólito Modular do ecossistema.

---

### Fase 2: O Chão de Fábrica (Workflow Agêntico)

- **D5. Visão e Escopo:**
  - Transformar qualquer projeto frontend exportado de geradores Low-Code (Lovable, v0, Bolt) em uma aplicação conteinerizada autônoma, auto-hospedável em VPS corporativa, livre de dependências de nuvens proprietárias, mantendo integridade estética e conectada ao ecossistema via fatias VSA e contratos do Quarteto.

#### Estágios do Pipeline de Libertação (`pipeline_bridge.py`):

- **[Estágio 1 — Scan & Análise de Componentes]**
  - **D6. O que o Estágio Faz:** Analisa a estrutura de pastas do projeto exportado, mapeando rotas React Router, componentes shadcn/ui, dependências e esquemas de banco de dados.
  - **D7. O que o Estágio Recebe:** Caminho do diretório de origem (`project_dir`).
  - **D8. O que o Estágio Processa:** Parser determinístico em AST e regex (`LovableScanner`), detectando arquivos `.tsx`, `.jsx`, `.sql` e metadados em `package.json`.
  - **D9. O que o Estágio Entrega:** Manifesto estruturado `bridge-manifest.json` com o inventário da aplicação.

- **[Estágio 2 — Desacoplamento de Banco de Dados]**
  - **D6. O que o Estágio Faz:** Converte as migrações SQL proprietárias do Supabase em comandos PostgreSQL padrão com criação de schemas de suporte (`auth`, `storage`) e tratamento de funções PostgREST.
  - **D7. O que o Estágio Recebe:** Lista de arquivos `.sql` e configuração da stack (`lite` ou `full`).
  - **D8. O que o Estágio Processa:** Motor `DataBridge` e `SQLTranspiler` aplicando gramática de substituição para sanitizar comandos específicos de BaaS e isolar migrações dependentes de GoTrue quando aplicável.
  - **D9. O que o Estágio Entrega:** Arquivo `init-db.sql` consolidado e, se na stack full, `post-auth-migrations.sql`.

- **[Estágio 3 — Separação de Camadas & Libertação do Frontend]**
  - **D6. O que o Estágio Faz:** Replica o código do frontend no diretório de saída, substituindo URLs hardcoded e chaves estáticas de provedores de nuvem por variáveis de ambiente padrão.
  - **D7. O que o Estágio Recebe:** Código-fonte original do projeto e diretório de destino.
  - **D8. O que o Estágio Processa:** `FrontendLiberator` substitui ocorrências de domínios como `*.supabase.co` e injeta suporte a `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`.
  - **D9. O que o Estágio Entrega:** Código-fonte do frontend desatado e arquivo `.env.production` configurado.

- **[Estágio 4 — Empacotamento DevOps OCI]**
  - **D6. O que o Estágio Faz:** Cria a infraestrutura como código (IaC) pronta para contêineres e deploy em VPS.
  - **D7. O que o Estágio Recebe:** Tipo de runtime detectado (SPA estática vs SSR), gerenciador de pacotes e domínio alvo.
  - **D8. O que o Estágio Processa:** `DevOpsPackager` compila `Dockerfile` multi-stage com usuário non-root, `docker-compose.yml`, `docker-compose.prod.yml` (Docker Swarm com Traefik e Let's Encrypt), `nginx.conf` com cabeçalhos de segurança OWASP e script `deploy.sh`.
  - **D9. O que o Estágio Entrega:** Pacote completo de arquivos de orquestração OCI.

- **[Estágio 5 — Conector VSA & Quarteto Sine Qua Non]**
  - **D6. O que o Estágio Faz:** Constrói os contratos exigidos pela Lei #10 do ecossistema para integração com `aidd-master`.
  - **D7. O que o Estágio Recebe:** Dados estruturados do `bridge-manifest.json`.
  - **D8. O que o Estágio Processa:** `BridgeVSAExporter` sintetiza os quatro pilares dinâmicos a partir das rotas e entidades do modelo de dados.
  - **D9. O que o Estágio Entrega:** Pasta `quarteto_sine_qua_non/` com:
    - `swagger.json` (Swagger Studio / OpenAPI 3.1)
    - `webhooks.json` (Webhook Studio)
    - `mcp-manifest.json` (MCP Studio)
    - `GUIA-DO-USUARIO.md` (Central de Documentação)

- **[Estágio 6 — Quality Gates Locais]**
  - **D6. O que o Estágio Faz:** Executa a bateria de validação determinística sobre o diretório gerado.
  - **D7. O que o Estágio Recebe:** Caminho do diretório de saída empacotado.
  - **D8. O que o Estágio Processa:** Execução dos scripts em `tools/aidd-bridge/gates/` (`G_BRIDGE_VENDOR_LOCKIN`, `G_BRIDGE_DOCKER_OCI`, `G_BRIDGE_POSTGRESQL`, `G_BRIDGE_VSA_COMPAT`).
  - **D9. O que o Estágio Entrega:** Código de retorno binário (exit 0 aprovado / exit 1 bloqueado).

- **D10. Orquestração e Topologia:**
  - Topologia linear determinística e estritamente sequencial coordenada pela classe `BridgePipeline` (`aidd_bridge/pipeline_bridge.py`).
  - Cada fase produz um artefato intermediário persistido em disco que alimenta a fase subsequente.
  - Falha imediata (fail-fast) ao primeiro erro, impedindo avanço em estado inconsistente.

---

### Fase 3: Resiliência e Economia (Engenharia Operacional)

- **D11. Tratamento de Exceções e Fallback:**
  - Tratamento universal de encoding com `_forcar_utf8_stdio` / `PYTHONIOENCODING=utf-8` para garantir compatibilidade impecável no Windows (evitando falhas por caracteres UTF-8 como marcas de verificação `✓`).
  - Suporte resiliente a duas topologias de stack:
    - Stack `lite`: PostgreSQL corporativo standalone com tabelas de autenticação compatíveis no próprio banco.
    - Stack `full`: PostgreSQL com PostgREST e serviço GoTrue de autenticação completo.
  - Confirmação humana obrigatória para operações destrutivas no comando `destroy`.

- **D12. Observabilidade e Frugalidade:**
  - Telemetria no console telegráfica e visualmente informativa sem despejo indiscriminado de arquivos.
  - Frugalidade máxima de tokens: **0 tokens de LLM consumidos** no processo mecânico de scan, transpilação SQL, empacotamento OCI e gates de validação.
  - Metadados completos do projeto arquivados estruturadamente no arquivo `bridge-manifest.json`.

---

### Fase 4: O Inspetor e a Expedição (Validação)

- **D13. Quality Gates (Portões):**
  - Existência e aprovação dos 4 portões dedicados em `tools/aidd-bridge/gates/`:
    1. `G_BRIDGE_VENDOR_LOCKIN.py`: Varredura em profundidade de padrões regex de lock-in em nuvens proprietárias.
    2. `G_BRIDGE_DOCKER_OCI.py`: Verificação de padrões OCI seguros, usuário não-root no Dockerfile e sintaxe de Compose.
    3. `G_BRIDGE_POSTGRESQL.py`: Validação estrutural de compatibilidade do script consolidado `init-db.sql`.
    4. `G_BRIDGE_VSA_COMPAT.py`: Verificação estrita da presença dos 4 componentes do Quarteto Sine Qua Non.
  - Prova fática de execução de testes: 64 testes automatizados em `pytest tools/aidd-bridge/tests` aprovados com 100% de sucesso.

- **D14. Critério de Rejeição (Rollback):**
  - O pipeline retorna `exit 1` e interrompe imediatamente caso:
    - Qualquer URL fixa ou padrão proibido seja detectado nos arquivos do projeto de saída.
    - O Dockerfile utilize usuário `root` ou viole regras OCI.
    - O script `init-db.sql` contenha sintaxe inválida ou falte esquemas essenciais.
    - Qualquer dos 4 arquivos do Quarteto Sine Qua Non esteja ausente.
  - Rollback e limpeza de infraestrutura operacionalizados via `tools/aidd-bridge/aidd_bridge/teardown.py`.

- **D15. Output Consolidado e Handoff:**
  - O produto final entregue pela ferramenta consiste em um diretório completamente autônomo contendo:
    - Código do frontend desacoplado com `.env.production`.
    - `init-db.sql` sanitizado.
    - Manifestos Docker Swarm / Compose com Nginx OWASP.
    - Diretório `quarteto_sine_qua_non/` com especificações `/swagger`, `/webhooks`, `/mcp`, `/docs`.
    - `bridge-manifest.json` com metadados estruturados.
  - Handoff canônico pronto para a convergência no `aidd-master` através da pipeline do FLUXO 03 (`aidd-freedom`).

---

## 3. Matriz de Avaliação da Execução

- [x] A ferramenta isolou seu raio de impacto corretamente? Sim, diretório de origem intocado e saídas confinadas ao diretório de saída com variáveis criptográficas seguras.
- [x] O workflow seguiu as fases sem alucinações de LLM em tarefas mecânicas? Sim, pipeline 100% determinístico com 0 dependência de LLM em tarefas mecânicas.
- [x] O output final passou em todos os Quality Gates e emitiu o Handoff? Sim, 4 portões dedicados de validação e 64 testes automatizados com status de aprovação plena (`exit 0`).

---

## 4. Conclusão do Inspetor (Fase 1)

A ferramenta `aidd-bridge` foi inspecionada minuciosamente no Ciclo 02 e atende com excelência a todos os requisitos de arquitetura, governança determinística e qualidade do Ecossistema AIDD. Todas as 15 dimensões da Lens 15-D estão plenamente cobertas com evidências fáticas e testes reais.
