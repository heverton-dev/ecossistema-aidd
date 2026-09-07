# Guia Enciclopedico e Arquitetura Tecnica Real do AIDD-Ops

> **Documento:** `docs/explicacoes/01-arquitetura-e-visao-aidd-ops.md`  
> **Status:** Referencia Arquitetural Oficial e Matriz de Decisoes Canonicas  
> **Origem:** Dialogo de Alinhamento Tecnico da Sessao 5 (Validacao Real Isolada)  
> **Classificacao:** Engenharia de Infraestrutura, Orquestracao Soberana e Zero-Lockin  

---

## 1. O Que Realmente E o AIDD-Ops?

O **AIDD-Ops** nao e um mero gerador de arquivos estaticos de Docker, tampouco uma simples replica de ferramentas existentes (como GoHighLevel).

### 1.1 Definicao Canonica
O **AIDD-Ops e o Meta-Orquestrador Agentico de Infraestrutura e Stacks Open Source Soberanas do Ecossistema AIDD**. 

Seu objetivo primordial e:
> **Receber interativamente em linguagem natural as dores, gargalos e necessidades operacionais de uma empresa, pesquisar e curar autonomamente o conjunto otimo de ferramentas open-source consolidadas que saram essas dores, dimensionar a infraestrutura necessaria com precisao de engenharia e orquestrar o provisionamento e deploy ponta a ponta em servidor proprio (VPS), sem friccao, sem limites artificiais de uso e com soberania total de dados.**

---

## 2. A Matriz de Responsabilidades do Ecossistema AIDD

Para eliminar qualquer ambiguidade de papeis entre os modulos do monorepo, a separacao canonica e:

| Dimensao | AIDD-Master / AIDD-Enterprise | AIDD-Ops (Meta-Orquestrador) |
| :--- | :--- | :--- |
| **Objeto de Entrega** | **Codigo-fonte de aplicacao sob medida** (Clean Arch, Fatias Verticais, FastAPI, SQLite WAL, WORM Hash Chain SHA-256). | **Infraestrutura e ecossistema de servicos autonomos** (Orquestracao Docker, redes virtuais, bancos multi-tenant, proxies TLS, SSO/IAM). |
| **Modelo de Execucao** | Roda localmente como microsservico ou super-app com Swagger, Webhooks e MCP Studio. | Roda como orquestrador que configura servidores VPS remotos (Ubuntu, Debian) e gerencia conteineres de alta escala. |
| **Origem dos Modulos** | Modulos construidos do zero a partir de especificacoes de negocio (ex: Faturamento, Prontuario, Auditoria). | Ferramentas open-source maduras de mercado selecionadas para resolver dores reais (ex: Twenty CRM, Chatwoot, Cal.com, Typebot). |

---

## 3. Os 6 Pilares Criticos Levantados na Sessao 5

Durante o alinhamento tecnico da Sessao 5, foram identificados 6 requisitos estruturais mandatorios para a evolucao do AIDD-Ops:

### Pilar 1: Intake Interativo Guiado (Zero Friccao de Linha de Comando)
- **O Problema:** Exigir que o desenvolvedor ou operador leigo digite parametros complexos no terminal (`python ecossistema.py ops plan clinicas --pasta ...`) contraria a premissa de usabilidade agentica.
- **A Solucao:** Um **Assistente de Intake Web Interativo**:
  1. Campo de linguagem natural livre: o usuario relata suas dores (ex: *"Tenho uma clinica medica, recebo muitas mensagens no WhatsApp, perco agendamentos porque a secretaria nao da conta e preciso de um prontuario integrado sem pagar taxas abusivas por contato"*).
  2. O motor do AIDD-Ops interpreta as entidades, faz a curadoria de ferramentas no catalogo e apresenta o plano visual de solucao para aprovacao humana.
  3. Toda a transicao entre fases ocorre por gatilhos visuais no painel com feedback deterministico.

---

### Pilar 2: Coleta Segura de Credenciais e Vault Local (Pacotes 4, 5, 8 e 9)
Cada pacote da esteira de infraestrutura necessita de credenciais exclusivas que **nunca devem trafegar em logs ou parametros abertos de CLI**:

- **Pacote 4 (VPS SSH):** Coleta IP, porta SSH (default 22), usuario (`root`/`ubuntu`) e chave privada (`.pem` / `id_rsa`) ou senha temporaria de primeiro acesso.
- **Pacote 5 (Cloudflare DNS):** Coleta Token de API com escopo restrito `Zone.DNS:Edit` e valida a conectividade antes de criar registros `A` e `CNAME` wildcard.
- **Pacotes 8 e 9 (Deploy):** Gera automaticamente senhas fortes criptograficamente seguras para cada banco logico isolado, gravando-as apenas no `.env` do servidor.

---

### Pilar 3: Estrategia de Build, Dockerfile e Imagens Pre-compiladas
- **Aplicacoes de Terceiros (Twenty, Chatwoot, Cal.com, Postgres, Traefik):**
  - **Diretriz Mandatoria:** Utilizar **exclusivamente imagens oficiais homologadas dos mantenedores**.
  - **Justificativa Tecnica:** Buildar o Chatwoot (Ruby on Rails + Node assets) ou o Twenty (monorepo Nest/React) a partir de Dockerfile local demoraria mais de 45 minutos por deploy e exigiria mais de 16 GB de RAM na VPS apenas para o processo de build.
- **Modulos Proprios (Gateway de Integracao e AppShell White-Label):**
  - O AIDD-Ops gera o `Dockerfile` multi-stage otimizado (imagens Alpine/Distroless < 50MB).
  - Suporta build e push no Docker Hub ou build in-situ direto no daemon Docker da VPS remota.
- **Gestao Operacional Visual (Portainer / Dockge):**
  - Opcionalmente provisionado como conteiner de observabilidade na VPS para que o operador humano tenha gestao grafica de conteineres, logs ao vivo e consumo de hardware.

---

### Pilar 4: A Suite Agregadora White-Label (O Padrao Ouro AIDD)
O AIDD-Ops nao deve entregar apenas servicos desconexos. Ele incorpora a **Suite Quintupla Canonica** homologada no ecossistema:

1. **Frontend AppShell Unificador (White-Label):**
   - Painel central SPA (Zinc/Dark) que unifica CRM, Chat e Agendamento sob uma identidade visual corporativa unica, conectando os apps via SSO (Authentik/OIDC) sem friccao de abas dispersas.
2. **Swagger Studio Central (OpenAPI 3.1):**
   - Catalogo vivo e interativo documentando todos os endpoints do Gateway proprio de webhooks e microsservicos.
3. **Webhook Studio Interativo:**
   - Interface visual para testar, simular eventos em tempo real (ex: novo lead no WhatsApp) e validar assinaturas HMAC SHA-256.
4. **MCP Native Studio (JSON-RPC 2.0):**
   - Servidor MCP integrado permitindo que assistentes de IA (Claude Desktop, Cursor, agentes autonomos) inspecionem a VPS, consultem metricas de saude e realizem manutencoes preventivas.
5. **Guia Enciclopedico Tecnico e Operacional:**
   - Manual completo em abas explicando para leigos e administradores como operar cada ferramenta, fluxos de backup e resolucao de incidentes.

---

### Pilar 5: Convivencia em VPS Compartilhada e Blast Radius Zero
Quando o usuario disponibiliza uma VPS que **ja possui outras aplicacoes em producao**, o AIDD-Ops aplica blindagem rigorosa para garantir que nada preexistente seja corrompido:

1. **Rede Virtual Isolada (`aidd_internal_network`):**
   - Os conteineres provisionados comunicam-se exclusivamente entre si. Nao ha exposicao desnecessaria de portas no host alem das estritamente homologadas.
2. **Auditoria Previa de Conflito de Portas:**
   - O `preflight_runner` escaneia via SSH as portas do host (`ss -tulpn`). Se portas como 80, 443 ou 5432 ja estiverem ocupadas pelo Nginx ou Postgres do usuario, o AIDD-Ops **nao as sobrescreve**: aloca portas alternativas seguras ou configura upstream no proxy existente.
3. **Isolamento de Diretorios no Host:**
   - Todos os arquivos, volumes e logs residem estritamente em `/opt/aidd-ops/<ambiente>/` e volumes nomeados com prefixo `aidd_*`.

---

### Pilar 6: Desinstalacao Atomica com 1 Comando (`uninstall.sh`)
Em qualquer ambiente compartilhado, a reversibilidade deve ser total e deterministica:
- Todo deploy gera na raiz do projeto o script `/opt/aidd-ops/<ambiente>/uninstall.sh`.
- **Modo Padrao (`./uninstall.sh`):** Interrompe os conteineres e redes da suite AIDD sem remover dados persistentes. As demais aplicacoes da VPS permanecem 100% inalteradas.
- **Modo Purge (`./uninstall.sh --purge-data`):** Remove conteineres, redes e volumes da suite AIDD e limpa a pasta `/opt/aidd-ops/<ambiente>/`, devolvendo a VPS ao seu estado original exato com zero residuos orfaos.

---

## 4. Conclusao e Roadmap

Com a incorporacao destes 6 pilares, o **AIDD-Ops** consolida-se como a plataforma mais avancada e segura para orquestracao de infraestrutura agentica, unindo facilidade leiga, rigor formal de engenharia e soberania absoluta sobre dados e servidores.

