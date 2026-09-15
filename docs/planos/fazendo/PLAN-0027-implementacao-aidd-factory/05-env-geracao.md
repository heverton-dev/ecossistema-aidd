# Item 05: Fase 6 — Gerador de .env

## Escopo
Implementar `src/core/env_generator.py` que gera variaveis de ambiente isoladas por servico.

## Definicao de Pronto
- [ ] `env_generator.py` implementado com 100% determinismo
- [ ] Para cada servico: le `.env.example` do template correspondente
- [ ] Gera senhas criptograficas (OpenSSL rand -base64 32) para cada var sensivel
- [ ] Monta `.env` isolado por servico (ex: `.env.twenty`, `.env.chatwoot`)
- [ ] Monta `.env` unificado para o compose
- [ ] Integra com `cofre_credenciais.py` do aidd-ops para cifrar em `.env.enc`
- [ ] Testes: senhas unicas por execucao, vars obrigatorias preenchidas
- [ ] Gate G_FACTORY_ENV.py verifica completude

## Dependencias
- Item 02 (analisador)

## Evidencia
- 9 `.env.example` existem em `templates/infra/*/.env.example`
- `cofre_credenciais.py` do aidd-ops ja tem `cifrar_env()`
