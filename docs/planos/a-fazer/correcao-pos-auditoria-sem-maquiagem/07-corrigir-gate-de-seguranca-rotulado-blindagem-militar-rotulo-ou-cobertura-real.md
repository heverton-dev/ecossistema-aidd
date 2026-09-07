# Item 7 — Corrigir gate de seguranca rotulado blindagem militar (rotulo ou cobertura real)

> **Escopo:** Entra: decidir entre (a) aumentar cobertura funcional real de `scripts/gates/G_SEGURANCA.py` (enterprise) até o rótulo ser justo, ou (b) corrigir o rótulo/mensagem de saída para refletir o que de fato é testado. Não entra: reescrever `G_CONTRACTS` (achado relacionado, escopo próprio se vier a virar item).
> **Status:** [RASCUNHO — Aguardando Aprovacao Humana — rota depende de decisão do usuário]
> **Modelo sugerido:** Claude Opus · Antigravity Gemini 3.8 · MiMo mimo-v2.5-pro (decisão de escopo: quanto investir em cobertura real vs. só corrigir o rótulo)

---

## Contexto ja investigado

- Confirmado por fork de auditoria: dos "21 testes" do gate, ~4 são funcionais reais — `G_SEGURANCA.py:100-131` gera um JWT, adultera o payload e confirma rejeição, testa expiração, e verifica hash de senha PBKDF2 certo/errado. O resto é checagem estática: `G_SEGURANCA.py:67-95` confere presença de 5 headers HTTP e ausência de `unsafe-eval` (valor de dicionário, não requisição real); `:136-179` faz grep de padrões (`ALLOW_ANONYMOUS`+`dev_guest`; 4 regexes de SQL concatenada) em todo `.py` de `src/`; `:184-230` faz grep de string em `nginx.conf`/`Dockerfile` sem subir Nginx nem testar rate-limit de verdade.
- Mensagem de saída atual: "Score de Blindagem: 100.0% (NOTA A+)" / "CERTIFICAÇÃO CONCEDIDA: APLICAÇÃO 100% BLINDADA E HOMOLOGADA PARA PRODUÇÃO GLOBAL" — linguagem de marketing incompatível com o rigor real da checagem (17 dos 21 itens são grep/config estático).

## Definicao de Pronto

1. Rota escolhida com o usuário, registrada aqui com justificativa, antes de codar.
2. Se rota (a): pelo menos SQLi e XSS passam a ser testados executando um payload real contra um endpoint de teste (não só grep) — reproduzir com um payload conhecido e confirmar que o gate pega de verdade.
3. Se rota (b): nome do gate e mensagem de saída deixam de usar "blindagem militar"/"homologada para produção global" e passam a descrever a cobertura real (ex.: "Auditoria de Configuração e Autenticação — 4/21 checks funcionais, 17/21 checks estáticos").
4. Suíte de testes do gate continua verde após a mudança, reexecutada e conferida.

## Criterio de saida

- Arquivos criados ou alterados no local correto.
- Testes reais passando sem stubs falsos.
- Gates de integridade aprovados.

## Prompt de Execucao (PT-BR)

> Copie o bloco abaixo integralmente para o agente executor:

```
Voce vai implementar o Item 7: Corrigir gate de seguranca rotulado blindagem militar (rotulo ou cobertura real).
Siga rigorosamente a Definicao de Pronto acima.
Nao invente aprovacoes e mantenha as regras do monorepo.
```

## Prompt de Execucao — English version

> Copy the block below in full to the executor agent:

```
You are going to implement Item 7: Corrigir gate de seguranca rotulado blindagem militar (rotulo ou cobertura real).
Strictly follow the Definition of Done above.
Do not fabricate approvals and maintain monorepo governance rules.
```
