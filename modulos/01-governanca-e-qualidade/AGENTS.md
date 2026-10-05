# Leis e Invariantes Locais — Governança e Qualidade

1. **Determinismo Estrito (Lei #1):** Comandos e gates operam sem dependência de estado externo estocástico.
2. **Sem API Keys Privadas (Contrato C1):** O harness hospedeiro provê o modelo via protocolo delegado.
3. **Imutabilidade de Peças:** Cópias em projetos derivam do almoxarifado sob verificação determinística de SHA-256.
4. **Isolamento de Testes:** Proibido gravar na árvore real do monorepo durante execuções de teste.
