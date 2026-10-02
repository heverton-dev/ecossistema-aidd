# 🏭 AIDD Factory

> **Gerador de Código de Aplicação e Integração para Stacks Multi-Serviço.**

O **AIDD Factory** é a fábrica de código e templates de aplicação do ecossistema-aidd, especializada na orquestração determinística e síntese de código limpo orientada a planos de infraestrutura.

---

## 🚀 Invariantes e Diretrizes

1. **Entrada Única (G_FACTORY_INPUT):** Consome exclusivamente `PLANO-INFRAESTRUTURA.json` validado contra schema JSON.
2. **Saída Única (G_FACTORY_OUTPUT):** Produz `FACTORY_OUTPUT.json` listando artefatos e status para o orquestrador de deploy.
3. **Fases Determinísticas:** Fases 1, 4, 5 e 6 são 100% determinísticas (zero LLM). Fases 2, 3 e 7 utilizam gates AST e bandit.
4. **Zero Stubs:** Todo código gerado é funcional, sem stubs ou placeholders.

---

## 💻 Uso via CLI

```bash
# Execução via orquestrador raiz:
python ecossistema.py factory --plano PLANO-INFRAESTRUTURA.json --pasta ./saida
```
