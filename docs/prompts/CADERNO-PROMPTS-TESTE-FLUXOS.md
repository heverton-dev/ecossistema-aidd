# CADERNO DE PROMPTS OPERACIONAIS — ECOSSISTEMA AIDD UNIFICADO
> **Repositório:** `https://github.com/heverton-dev/ecossistema-aidd`  
> **Destino:** `docs/prompts/CADERNO-PROMPTS-TESTE-FLUXOS.md`  
> **Data:** 03/09/2026  
> **Instruções de Uso:** Este documento contém os 4 prompts mestres prontos para copiar e colar diretamente no chat de qualquer agente ou harness (Claude Code, MimoCode, OpenCode, Antigravity ou Cursor) para disparar e validar o fluxo de cada uma das ferramentas do ecossistema.

---

## 1. AIDD FORGE — BOOTSTRAP, MICRO-AMBIENTES & QUALITY GATES

### 🇧🇷 Versão em Português (PT-BR)
```text
MISSÃO: EXECUTAR FLUXO INTEGRAL DO AIDD FORGE NO ECOSSISTEMA

Você deve validar a capacidade de inicialização, blindagem de governança e injeção de qualidade do AIDD Forge neste ambiente.

AÇÕES A EXECUTAR:
1. Dispare a inicialização em uma sandbox de teste executando o comando CLI ou a skill /forge:
   python ecossistema.py forge init ./sandbox-forge-teste --force
2. Confirme se as pastas canônicas de governança foram criadas dentro de 'sandbox-forge-teste/' (.aidd/pipeline/, .agent/, gates/, AGENTS.md).
3. Injete uma nova capacidade de teste via comando forge inject:
   python -m aidd_forge.cli inject skill validador-contratos --descricao "Validacao estrita de contratos" --conteudo "# Skill: validador-contratos\nValida payloads JSON contra schemas." --path ./sandbox-forge-teste
4. Execute o Quality Gate determinístico do Forge:
   python tools/aidd-forge/aidd_forge/templates/gates/G_INJECT.py
5. Execute os testes unitários do pacote para certificar aprovação sem falhas:
   python -m pytest tools/aidd-forge/tests/unit/test_universal_injector.py -q

Apresente um resumo comprovando a criação da sandbox e o código de saída exit 0 em todas as etapas.
```

### 🇺🇸 English Version (EN)
```text
MISSION: EXECUTE FULL AIDD FORGE FLOW WITHIN THE ECOSYSTEM

You are tasked with validating the bootstrap, governance fencing, and quality injection capabilities of AIDD Forge in this environment.

ACTIONS TO EXECUTE:
1. Trigger initialization in a test sandbox using the ecosystem CLI or /forge slash command:
   python ecossistema.py forge init ./sandbox-forge-teste --force
2. Confirm that canonical governance folders were generated within 'sandbox-forge-teste/' (.aidd/pipeline/, .agent/, gates/, AGENTS.md).
3. Inject a new test capability using the forge inject CLI:
   python -m aidd_forge.cli inject skill validador-contratos --descricao "Strict contract validation" --conteudo "# Skill: validador-contratos\nValidates JSON payloads against schemas." --path ./sandbox-forge-teste
4. Run the deterministic Forge Quality Gate:
   python tools/aidd-forge/aidd_forge/templates/gates/G_INJECT.py
5. Execute package unit tests to confirm green status without failures:
   python -m pytest tools/aidd-forge/tests/unit/test_universal_injector.py -q

Provide a concise summary proving the sandbox creation and confirming an exit code 0 across all verification steps.
```

---

## 2. AIDD GENERATOR — FÁBRICA AUTÔNOMA DE SOFTWARE (8 FASES)

### 🇧🇷 Versão em Português (PT-BR)
```text
MISSÃO: EXECUTAR FLUXO INTEGRAL DO AIDD GENERATOR NO ECOSSISTEMA

Você deve validar a geração autônoma de um sistema de software completo pelo AIDD Generator a partir de uma ideia em linguagem natural.

AÇÕES A EXECUTAR:
1. Dispare a criação de um novo projeto executando o comando CLI ou a skill /generate:
   python ecossistema.py generate "Sistema de Agendamento e Gestao de Consultas Medicas" --pasta ./output-clinica --nao-interativo
2. Acompanhe a execução sequencial passando pelas Fases 1 a 7 com carregamento dinâmico e purga de contexto.
3. Inspecione o arquivo 'output-clinica/AVALIACAO-AUTO-CRITICA.md' e o banco SQLite 'output-clinica/estado_projeto.db'.
4. Valide a presença do arquivo 'output-clinica/test_result.json' confirmando status COMPLETO e score acima de 90/100.
5. Execute o Quality Gate do gerador para certificar a conformidade do projeto criado:
   python tools/aidd-generator/scripts/gates/G_INJECT.py

Apresente um resumo detalhando a pontuação da auto-crítica, o tempo de geração e os artefatos gerados.
```

### 🇺🇸 English Version (EN)
```text
MISSION: EXECUTE FULL AIDD GENERATOR FLOW WITHIN THE ECOSYSTEM

You are tasked with validating autonomous software generation via AIDD Generator starting from a natural language concept.

ACTIONS TO EXECUTE:
1. Trigger the creation of a new software project using the ecosystem CLI or /generate slash command:
   python ecossistema.py generate "Sistema de Agendamento e Gestao de Consultas Medicas" --pasta ./output-clinica --nao-interativo
2. Monitor sequential execution across Phases 1 through 7 with dynamic micro-environment loading and context-purge.
3. Inspect 'output-clinica/AVALIACAO-AUTO-CRITICA.md' and the SQLite state database 'output-clinica/estado_projeto.db'.
4. Verify 'output-clinica/test_result.json' to confirm a COMPLETO status with a quality score above 90/100.
5. Run the generator Quality Gate to certify the integrity of the newly created project:
   python tools/aidd-generator/scripts/gates/G_INJECT.py

Provide a concise summary detailing the auto-critique score, execution duration, and generated artifacts.
```

---

## 3. AIDD MASTER — ARQUITETURA MODULAR & RESULT MONAD

### 🇧🇷 Versão em Português (PT-BR)
```text
MISSÃO: EXECUTAR FLUXO INTEGRAL DO AIDD MASTER NO ECOSSISTEMA

Você deve validar a criação de fatias verticais de negócio desacopladas e o padrão funcional Result Monad no AIDD Master.

AÇÕES A EXECUTAR:
1. Crie uma nova fatia vertical de negócio executando o comando CLI ou a skill /master:
   python ecossistema.py master add-module estoque
2. Confirme se os arquivos reais de domínio foram criados em 'tools/aidd-master/src/modules/estoque/' (routes.py, services.py, models.py).
3. Verifique se o frontend correspondente foi instanciado em 'tools/aidd-master/src/static/components/estoque.html'.
4. Injete uma nova skill com fan-out sincronizado para os 5 harnesses:
   python tools/aidd-master/scripts/aidd.py inject skill controle-patrimonial --descricao "Gestao e controle de inventario fisico"
5. Execute o Quality Gate e a suíte de testes do AIDD Master:
   python tools/aidd-master/scripts/gates/G_INJECT.py
   python -m pytest tools/aidd-master/tests/unit/test_injector_core.py -q

Apresente um resumo comprovando a criação do módulo 'estoque', a atualização do CAPABILITIES.json e o status verde dos testes.
```

### 🇺🇸 English Version (EN)
```text
MISSION: EXECUTE FULL AIDD MASTER FLOW WITHIN THE ECOSYSTEM

You are tasked with validating the creation of decoupled vertical business slices and the Result Monad pattern in AIDD Master.

ACTIONS TO EXECUTE:
1. Create a new vertical domain slice using the ecosystem CLI or /master slash command:
   python ecossistema.py master add-module estoque
2. Verify that production domain files were generated under 'tools/aidd-master/src/modules/estoque/' (routes.py, services.py, models.py).
3. Confirm that the web frontend was created at 'tools/aidd-master/src/static/components/estoque.html'.
4. Inject a new capability with synchronized fan-out across all 5 harnesses:
   python tools/aidd-master/scripts/aidd.py inject skill controle-patrimonial --descricao "Physical inventory management"
5. Run the Quality Gate and the unit test suite for AIDD Master:
   python tools/aidd-master/scripts/gates/G_INJECT.py
   python -m pytest tools/aidd-master/tests/unit/test_injector_core.py -q

Provide a concise summary proving the creation of the 'estoque' module, the update in CAPABILITIES.json, and green test execution.
```

---

## 4. AIDD MASTER ENTERPRISE — CONFORMIDADE & HASHES SHA-256

### 🇧🇷 Versão em Português (PT-BR)
```text
MISSÃO: EXECUTAR FLUXO INTEGRAL DO AIDD MASTER ENTERPRISE NO ECOSSISTEMA

Você deve validar a injeção corporativa de componentes regulados com validação criptográfica SHA-256 no AIDD Master Enterprise.

AÇÕES A EXECUTAR:
1. Injete uma skill de conformidade e uma regra de governança usando o comando CLI ou a skill /enterprise:
   python ecossistema.py enterprise inject skill pci-dss-compliance --descricao "Validacao automatica de conformidade financeira PCI-DSS"
   python ecossistema.py enterprise inject rule mtls-enforcement --descricao "Exigencia mandatória de comunicacao mTLS"
2. Inspecione 'tools/aidd-master-enterprise/COMPONENT-REGISTRY.json' e confirme se as duas entradas foram registradas com seus respectivos hashes SHA-256 e timestamps UTC.
3. Confirme se os arquivos de skill foram sincronizados em todos os diretórios de harness (.claude/, .agent/, .mimocode/, .gemini/, .skills/).
4. Execute o Quality Gate do Enterprise para certificar integridade contratual e criptográfica:
   python tools/aidd-master-enterprise/scripts/gates/G_INJECT.py
5. Execute os testes dedicados do injetor corporativo:
   python -m pytest tools/aidd-master-enterprise/tests/unit/test_aidd_core_injector.py -q

Apresente um parecer técnico demonstrando os hashes calculados, a atualização do catálogo e a aprovação com exit 0.
```

### 🇺🇸 English Version (EN)
```text
MISSION: EXECUTE FULL AIDD MASTER ENTERPRISE FLOW WITHIN THE ECOSYSTEM

You are tasked with validating corporate component injection with SHA-256 cryptographic verification in AIDD Master Enterprise.

ACTIONS TO EXECUTE:
1. Inject a compliance skill and a governance rule using the ecosystem CLI or /enterprise slash command:
   python ecossistema.py enterprise inject skill pci-dss-compliance --descricao "Automated PCI-DSS financial compliance verification"
   python ecossistema.py enterprise inject rule mtls-enforcement --descricao "Mandatory mTLS communication enforcement"
2. Inspect 'tools/aidd-master-enterprise/COMPONENT-REGISTRY.json' and verify that both entries were recorded with valid SHA-256 hashes and UTC timestamps.
3. Confirm that skill files were mirrored across all harness directories (.claude/, .agent/, .mimocode/, .gemini/, .skills/).
4. Run the Enterprise Quality Gate to certify contractual and cryptographic integrity:
   python tools/aidd-master-enterprise/scripts/gates/G_INJECT.py
5. Run the dedicated enterprise unit tests:
   python -m pytest tools/aidd-master-enterprise/tests/unit/test_aidd_core_injector.py -q

Provide a technical report detailing the computed hashes, the catalog update, and verification approval with exit code 0.
```
