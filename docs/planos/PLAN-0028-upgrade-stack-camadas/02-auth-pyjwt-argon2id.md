# 02 — Auth: PyJWT + Argon2id

## Nota Atual: 7/10 | Nota Alvo: 8/10 | Prioridade: MÉDIA

## Evidência da Nota Atual
- JWT custom implementado em `security.py` (NIH, ~100 linhas)
- Password hash: PBKDF2-SHA256 com 100k iterações (funcional mas não padrão OWASP 2024+)
- PyJWT 2.14.0 já instalado em `requirements.txt`
- TokenRevocationList in-memory

## O que será implementado
1. Substituir JWTService custom por PyJWT (`jwt.encode/decode`)
2. Substituir PBKDF2 por Argon2id via `argon2-cffi`
3. Manter OIDCService (PKCE) delegando para PyJWT na validação RS256
4. Manter Authentik como camada SSO enterprise

## Arquivos afetados
- `tools/aidd-master/templates/v2/security.py` (refatorar)
- `requirements.txt` (adicionar `argon2-cffi`)

## Critério de aceitação
- [ ] Todos os testes de auth continuam passando
- [ ] JWT encode/decode usando PyJWT
- [ ] Password hashing usando Argon2id
- [ ] OIDC flow funcional com PyJWT

## Estimativa
- Esforço: Médio (~1-2 dias)
- Impacto: +1 ponto (7→8)
