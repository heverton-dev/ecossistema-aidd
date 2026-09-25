---
name: aidd-planos
description: Generates standard templates and drafts for audit, evolution, or test plans.
---

# AIDD Planos — Gerador Estrutural de Planos

Esta skill formaliza e padroniza a criação de iniciativas de plano em `docs/planos/<nome-da-iniciativa>/` seguindo a arquitetura documental canônica do monorepo ecossistema-aidd.

## Princípio Fundamental e Regras Inegociáveis (Guarda de Segurança)

1. **A skill nunca decide, nem aprova sozinha:** Todo arquivo gerado é entregue estritamente como **RASCUNHO** com status explícito "aguardando aprovação". Nenhuma decisão de escopo, escolha arquitetural ou aprovação de item pode ser fabricada pelo agente.
2. **Determinismo Primeiro (Zero Token Fallacy):** A geração do esqueleto estrutural e a checagem de cercas markdown devem utilizar o comando determinístico CLI oficial `python ecossistema.py plan ...` sempre que possível, evitando geração manual suscetível a erros.
3. **A skill nunca envia prompts a agentes executores sozinha:** A execução, cópia/colagem de prompts ou disparo de subagentes depende de comando e ação expressa do usuário humano.
4. **Sem Git Commit / Push Automático:** A skill não executa comandos git de commit ou push.
5. **Escopo explícito:** O plano gerado traz as seções "Ainda nao especificado" (pertence ao plano, falta decidir) e "Fora de escopo" (deixado de fora). Item fora de escopo nunca volta para o plano atual; se voltar a importar, vira nova iniciativa.
6. **Isolamento em Testes:** Qualquer teste ou validação estrutural deve ser executado em diretório temporário isolado, jamais alterando ou criando lixo em `docs/planos/` em tempo de teste.

---

## Como Usar

No chat ou via CLI:
```bash
python ecossistema.py plan init <nome-da-iniciativa>
```
Para validar conformidade documental:
```bash
python ecossistema.py plan validate <caminho-do-plano>
```
